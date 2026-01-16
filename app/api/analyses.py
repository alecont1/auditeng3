"""Analysis submission and results API endpoints.

This module provides protected API endpoints for:
- Document submission for analysis
- Analysis status polling
- Complete results retrieval with findings
"""

import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.auth import CurrentUser
from app.core.dependencies import DbSession
from app.core.exceptions import AuthorizationError
from app.db.models import Analysis, Task
from app.schemas.enums import TaskStatus
from app.schemas.upload import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    UploadError,
)
from app.services.storage import save_file, delete_task_files
from app.worker.extraction import process_document_task
from app.worker.tasks import enqueue_task

from .schemas import (
    AnalysisSubmitResponse,
    AnalysisStatusResponse,
    AnalysisResponse,
    FindingDetail,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analyses", tags=["analyses"])


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename.

    Args:
        filename: The original filename.

    Returns:
        str: Lowercase file extension without the dot.
    """
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def validate_file_type(filename: str) -> None:
    """Validate that the file has an allowed extension.

    Args:
        filename: The original filename.

    Raises:
        HTTPException: 400 if file type is not allowed.
    """
    extension = get_file_extension(filename)
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=UploadError(
                error_code="INVALID_FILE_TYPE",
                detail=f"File type '.{extension}' is not allowed. "
                f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            ).model_dump(),
        )


def validate_file_size(content_length: int | None) -> None:
    """Validate that file size is within limits.

    Args:
        content_length: The Content-Length header value.

    Raises:
        HTTPException: 413 if file is too large.
    """
    if content_length is not None and content_length > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=UploadError(
                error_code="FILE_TOO_LARGE",
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)}MB.",
            ).model_dump(),
        )


async def verify_analysis_ownership(
    db: DbSession,
    analysis_id: UUID,
    user_id: UUID,
) -> Analysis:
    """Verify that the user owns the analysis.

    Args:
        db: Database session.
        analysis_id: The analysis UUID.
        user_id: The user's UUID.

    Returns:
        The Analysis object if ownership is verified.

    Raises:
        HTTPException: 404 if analysis not found.
        AuthorizationError: 403 if user doesn't own the analysis.
    """
    result = await db.execute(
        select(Analysis)
        .options(
            selectinload(Analysis.findings),
            selectinload(Analysis.task),
        )
        .where(Analysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis {analysis_id} not found",
        )

    if analysis.task.user_id != user_id:
        raise AuthorizationError(
            detail="You do not have access to this analysis",
            error_code="AUTHZ_001",
        )

    return analysis


@router.post(
    "/submit",
    response_model=AnalysisSubmitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit document for analysis",
    description="Upload a PDF or image file for commissioning report analysis. Requires authentication.",
    responses={
        201: {"description": "Document submitted successfully and queued for processing"},
        400: {"description": "Invalid file type", "model": UploadError},
        401: {"description": "Not authenticated"},
        413: {"description": "File too large", "model": UploadError},
        500: {"description": "Storage error", "model": UploadError},
    },
)
async def submit_document(
    db: DbSession,
    current_user: CurrentUser,
    file: UploadFile = File(..., description="PDF or image file to upload"),
) -> AnalysisSubmitResponse:
    """Submit a document for analysis.

    Accepts PDF files and images (PNG, JPG, TIFF) up to 50MB.
    Creates a Task record owned by the current user and queues for processing.

    Args:
        db: Database session.
        current_user: Authenticated user from JWT token.
        file: The uploaded file.

    Returns:
        AnalysisSubmitResponse: Task information including ID and status.

    Raises:
        HTTPException: 400 for invalid file type.
        HTTPException: 401 for missing/invalid authentication.
        HTTPException: 413 for file too large.
        HTTPException: 500 for storage errors.
    """
    # Validate file type
    filename = file.filename or "document"
    validate_file_type(filename)

    # Validate file size from Content-Length header (preliminary check)
    validate_file_size(file.size)

    # Generate task ID
    task_id = uuid4()

    try:
        # Save file to disk (streams in chunks)
        file_path, actual_size = await save_file(task_id, file)

        # Validate actual file size (definitive check)
        if actual_size > MAX_FILE_SIZE:
            # Clean up the file
            delete_task_files(task_id)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=UploadError(
                    error_code="FILE_TOO_LARGE",
                    detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)}MB.",
                ).model_dump(),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Storage error for task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=UploadError(
                error_code="STORAGE_ERROR",
                detail="Failed to store uploaded file. Please try again.",
            ).model_dump(),
        ) from e

    # Create Task record owned by authenticated user
    task = Task(
        id=task_id,
        user_id=current_user.id,
        status=TaskStatus.QUEUED.value,
        original_filename=filename,
        file_path=str(file_path),
        file_size=actual_size,
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Enqueue processing job
    enqueue_task(process_document_task, str(task_id))

    logger.info(
        f"Document submitted: task_id={task_id}, user_id={current_user.id}, "
        f"filename={filename}, size={actual_size}"
    )

    return AnalysisSubmitResponse(
        task_id=task.id,
        status=task.status,
    )


@router.get(
    "/{analysis_id}/status",
    response_model=AnalysisStatusResponse,
    summary="Get analysis status",
    description="Poll the current status of an analysis. Requires authentication and ownership.",
    responses={
        200: {"description": "Analysis status retrieved"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access denied"},
        404: {"description": "Analysis not found"},
    },
)
async def get_analysis_status(
    analysis_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> AnalysisStatusResponse:
    """Get the current status of an analysis.

    Args:
        analysis_id: The analysis UUID.
        db: Database session.
        current_user: Authenticated user from JWT token.

    Returns:
        AnalysisStatusResponse: Current analysis status and progress message.

    Raises:
        HTTPException: 401 for missing/invalid authentication.
        HTTPException: 403 if user doesn't own the analysis.
        HTTPException: 404 if analysis not found.
    """
    analysis = await verify_analysis_ownership(db, analysis_id, current_user.id)

    # Determine status message based on task status
    task_status = analysis.task.status
    if task_status == TaskStatus.QUEUED.value:
        message = "Analysis is queued for processing"
    elif task_status == TaskStatus.PROCESSING.value:
        message = "Analysis is currently being processed"
    elif task_status == TaskStatus.COMPLETED.value:
        message = "Analysis complete - results ready"
    elif task_status == TaskStatus.FAILED.value:
        message = f"Analysis failed: {analysis.task.error_message or 'Unknown error'}"
    else:
        message = f"Status: {task_status}"

    return AnalysisStatusResponse(
        analysis_id=analysis.id,
        status=task_status,
        message=message,
    )


@router.get(
    "/{analysis_id}",
    response_model=AnalysisResponse,
    summary="Get analysis results",
    description="Retrieve complete analysis results with findings. Requires authentication and ownership.",
    responses={
        200: {"description": "Analysis results retrieved"},
        202: {"description": "Analysis still processing"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access denied"},
        404: {"description": "Analysis not found"},
    },
)
async def get_analysis_results(
    analysis_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> AnalysisResponse:
    """Get the complete results of an analysis including findings.

    Returns 202 Accepted if the analysis is still processing.

    Args:
        analysis_id: The analysis UUID.
        db: Database session.
        current_user: Authenticated user from JWT token.

    Returns:
        AnalysisResponse: Complete analysis with findings, scores, and verdict.

    Raises:
        HTTPException: 202 if still processing.
        HTTPException: 401 for missing/invalid authentication.
        HTTPException: 403 if user doesn't own the analysis.
        HTTPException: 404 if analysis not found.
    """
    analysis = await verify_analysis_ownership(db, analysis_id, current_user.id)

    # If still processing, return 202
    task_status = analysis.task.status
    if task_status in [TaskStatus.QUEUED.value, TaskStatus.PROCESSING.value]:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={
                "status": task_status,
                "message": "Analysis is still being processed. Please check back later.",
            },
        )

    # Build findings list
    findings = [
        FindingDetail(
            rule_id=finding.rule_id,
            severity=finding.severity,
            message=finding.message,
            field_path=finding.evidence.get("field_path") if finding.evidence else None,
            evidence={
                "extracted_value": finding.evidence.get("extracted_value") if finding.evidence else None,
                "threshold": finding.evidence.get("threshold") if finding.evidence else None,
                "standard_reference": finding.evidence.get("standard_reference", "N/A") if finding.evidence else "N/A",
            } if finding.evidence else None,
            remediation=finding.remediation,
        )
        for finding in analysis.findings
    ]

    return AnalysisResponse(
        id=analysis.id,
        equipment_type=analysis.equipment_type,
        test_type=analysis.test_type,
        equipment_tag=analysis.equipment_tag,
        verdict=analysis.verdict,
        compliance_score=analysis.compliance_score,
        confidence_score=analysis.confidence_score,
        findings=findings,
        extraction_result=analysis.extraction_result,
        created_at=analysis.created_at or datetime.now(timezone.utc),
    )
