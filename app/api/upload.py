"""File upload endpoint for commissioning reports.

This module provides the API endpoint for uploading PDF documents
and images (PNG, JPG, TIFF) for analysis.
"""

import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import DbSession
from app.db.models import Task, User
from app.schemas.upload import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    UploadError,
    UploadResponse,
)
from app.services.storage import save_file
from app.worker.extraction import process_document_task
from app.worker.tasks import enqueue_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["upload"])

# Placeholder user ID until authentication is implemented (Phase 5)
# This is a fixed UUID used for all uploads in development
PLACEHOLDER_USER_ID = UUID("00000000-0000-0000-0000-000000000000")
PLACEHOLDER_USER_EMAIL = "system@auditeng.local"


async def ensure_placeholder_user(db: AsyncSession) -> None:
    """Ensure the placeholder user exists for pre-auth uploads.

    Creates the system user if it doesn't exist. This is a temporary
    solution until authentication is implemented in Phase 5.

    Args:
        db: Database session.
    """
    result = await db.execute(select(User).where(User.id == PLACEHOLDER_USER_ID))
    if result.scalar_one_or_none() is None:
        user = User(
            id=PLACEHOLDER_USER_ID,
            email=PLACEHOLDER_USER_EMAIL,
            hashed_password="placeholder",  # Not a real password, user cannot login
            is_active=True,
        )
        db.add(user)
        await db.commit()


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


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document for analysis",
    description="Upload a PDF or image file (PNG, JPG, TIFF) for commissioning report analysis.",
    responses={
        201: {"description": "File uploaded successfully and queued for processing"},
        400: {"description": "Invalid file type", "model": UploadError},
        413: {"description": "File too large", "model": UploadError},
        500: {"description": "Storage error", "model": UploadError},
    },
)
async def upload_file(
    db: DbSession,
    file: UploadFile = File(..., description="PDF or image file to upload"),
) -> UploadResponse:
    """Upload a document for analysis.

    Accepts PDF files and images (PNG, JPG, TIFF) up to 50MB.
    Creates a Task record and queues the document for background processing.

    Args:
        db: Database session.
        file: The uploaded file.

    Returns:
        UploadResponse: Task information including ID and status.

    Raises:
        HTTPException: 400 for invalid file type.
        HTTPException: 413 for file too large.
        HTTPException: 500 for storage errors.
    """
    # Ensure placeholder user exists (temporary until Phase 5 auth)
    await ensure_placeholder_user(db)

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
            from app.services.storage import delete_task_files

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

    # Create Task record
    task = Task(
        id=task_id,
        user_id=PLACEHOLDER_USER_ID,  # TODO: Replace with authenticated user in Phase 5
        status="QUEUED",
        original_filename=filename,
        file_path=str(file_path),
        file_size=actual_size,
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Enqueue processing job
    enqueue_task(process_document_task, str(task_id))

    logger.info(f"File uploaded: task_id={task_id}, filename={filename}, size={actual_size}")

    return UploadResponse(
        task_id=task.id,
        filename=filename,
        file_size=actual_size,
        status=task.status,
        created_at=task.created_at or datetime.now(timezone.utc),
    )
