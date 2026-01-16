"""Task status and result API endpoints.

This module provides endpoints for checking task processing status
and retrieving analysis results.
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.dependencies import DbSession
from app.db.models import Analysis, Task
from app.schemas.enums import TaskStatus
from app.worker.status import get_job_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskStatusResponse(BaseModel):
    """Response model for task status endpoint."""

    task_id: UUID
    status: str
    original_filename: str
    file_size: int
    created_at: datetime
    error_message: str | None = None
    analysis_id: UUID | None = None
    needs_review: bool | None = None


class AnalysisResult(BaseModel):
    """Nested analysis result in task response."""

    id: UUID
    equipment_type: str
    test_type: str
    equipment_tag: str | None = None
    confidence_score: float | None = None
    extraction_result: dict[str, Any] | None = None
    created_at: datetime


class TaskResultResponse(BaseModel):
    """Response model for task result endpoint."""

    task_id: UUID
    status: str
    original_filename: str
    error_message: str | None = None
    analysis: AnalysisResult | None = None


@router.get(
    "/{task_id}",
    response_model=TaskStatusResponse,
    summary="Get task status",
    description="Retrieve the current status of a processing task.",
    responses={
        200: {"description": "Task status retrieved"},
        404: {"description": "Task not found"},
    },
)
async def get_task_status(
    task_id: UUID,
    db: DbSession,
) -> TaskStatusResponse:
    """Get the current status of a task.

    Args:
        task_id: The task UUID.
        db: Database session.

    Returns:
        TaskStatusResponse: Current task status.

    Raises:
        HTTPException: 404 if task not found.
    """
    # Get task with analysis relationship
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.analysis))
        .where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    # Get needs_review from job status in Redis
    needs_review = None
    job_status = get_job_status(str(task_id))
    if job_status and job_status.get("result"):
        needs_review = job_status["result"].get("needs_review")

    return TaskStatusResponse(
        task_id=task.id,
        status=task.status,
        original_filename=task.original_filename,
        file_size=task.file_size,
        created_at=task.created_at,
        error_message=task.error_message,
        analysis_id=task.analysis.id if task.analysis else None,
        needs_review=needs_review,
    )


@router.get(
    "/{task_id}/result",
    response_model=TaskResultResponse,
    summary="Get task result",
    description="Retrieve the full analysis result for a completed task.",
    responses={
        200: {"description": "Analysis result retrieved"},
        202: {"description": "Task still processing"},
        404: {"description": "Task not found"},
    },
)
async def get_task_result(
    task_id: UUID,
    db: DbSession,
) -> TaskResultResponse:
    """Get the full result of a completed task.

    Returns 202 Accepted if the task is still processing.

    Args:
        task_id: The task UUID.
        db: Database session.

    Returns:
        TaskResultResponse: Task with full analysis result.

    Raises:
        HTTPException: 404 if task not found.
        HTTPException: 202 if task still processing.
    """
    # Get task with analysis relationship
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.analysis))
        .where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    # If still processing, return 202
    if task.status in [TaskStatus.QUEUED.value, TaskStatus.PROCESSING.value]:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={
                "status": task.status,
                "message": "Task is still being processed. Please check back later.",
            },
        )

    # Build analysis response
    analysis_result = None
    if task.analysis:
        analysis_result = AnalysisResult(
            id=task.analysis.id,
            equipment_type=task.analysis.equipment_type,
            test_type=task.analysis.test_type,
            equipment_tag=task.analysis.equipment_tag,
            confidence_score=task.analysis.confidence_score,
            extraction_result=task.analysis.extraction_result,
            created_at=task.analysis.created_at,
        )

    return TaskResultResponse(
        task_id=task.id,
        status=task.status,
        original_filename=task.original_filename,
        error_message=task.error_message,
        analysis=analysis_result,
    )
