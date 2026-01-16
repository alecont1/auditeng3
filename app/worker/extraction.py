"""Extraction worker for background document processing.

This module provides the Dramatiq actor for processing uploaded documents
through the extraction pipeline with retry logic and status tracking.
"""

import asyncio
import logging
from pathlib import Path
from uuid import UUID

import dramatiq

from app.db.models import Analysis, Task
from app.db.session import async_session_factory
from app.schemas.enums import TaskStatus, TestType
from app.services.extraction import process_document
from app.worker.broker import broker
from app.worker.status import JobStatus, set_job_status

logger = logging.getLogger(__name__)


@dramatiq.actor(
    max_retries=3,
    min_backoff=1000,  # 1 second
    max_backoff=300000,  # 5 minutes
    queue_name="default",
    broker=broker,
)
def process_document_task(task_id: str) -> None:
    """Background task to process uploaded document.

    This Dramatiq actor handles the extraction pipeline:
    1. Retrieves task from database
    2. Updates status to PROCESSING
    3. Runs extraction through appropriate extractor
    4. Creates Analysis record with results
    5. Updates task status on completion/failure

    Args:
        task_id: UUID string of the task to process.
    """
    asyncio.run(_process_document_async(task_id))


async def _process_document_async(task_id: str) -> None:
    """Async implementation of document processing.

    Handles the actual extraction work within an async context.

    Args:
        task_id: UUID string of the task to process.
    """
    task_uuid = UUID(task_id)
    logger.info(f"Starting document processing for task {task_id}")

    async with async_session_factory() as session:
        # 1. Get task and validate
        task = await session.get(Task, task_uuid)
        if not task:
            logger.error(f"Task not found: {task_id}")
            set_job_status(task_id, JobStatus.FAILED, error="Task not found")
            return

        if not task.file_path:
            logger.error(f"No file path for task: {task_id}")
            set_job_status(task_id, JobStatus.FAILED, error="No file path")
            task.status = TaskStatus.FAILED.value
            task.error_message = "No file path specified"
            await session.commit()
            return

        # 2. Update status to PROCESSING
        task.status = TaskStatus.PROCESSING.value
        await session.commit()
        set_job_status(task_id, JobStatus.PROCESSING)
        logger.info(f"Task {task_id} status updated to PROCESSING")

        try:
            # 3. Run extraction
            file_path = Path(task.file_path)
            result = await process_document(task_uuid, file_path)

            # 4. Extract equipment info if available
            equipment_type = None
            equipment_tag = None
            test_type_str = None

            if hasattr(result, "equipment") and result.equipment:
                if hasattr(result.equipment, "equipment_type"):
                    eq_type = result.equipment.equipment_type
                    if hasattr(eq_type, "value"):
                        # FieldConfidence
                        equipment_type = eq_type.value
                    else:
                        equipment_type = str(eq_type) if eq_type else None

                if hasattr(result.equipment, "equipment_tag"):
                    eq_tag = result.equipment.equipment_tag
                    if hasattr(eq_tag, "value"):
                        # FieldConfidence
                        equipment_tag = eq_tag.value
                    else:
                        equipment_tag = str(eq_tag) if eq_tag else None

            if hasattr(result, "metadata") and result.metadata:
                if hasattr(result.metadata, "test_type"):
                    test_type_str = result.metadata.test_type

            # Infer test type from extractor if not in metadata
            if not test_type_str:
                result_class = result.__class__.__name__
                if "Grounding" in result_class:
                    test_type_str = TestType.GROUNDING.value
                elif "Megger" in result_class:
                    test_type_str = TestType.MEGGER.value
                elif "Thermography" in result_class:
                    test_type_str = TestType.THERMOGRAPHY.value

            # 5. Create Analysis record
            analysis = Analysis(
                task_id=task_uuid,
                equipment_type=equipment_type or "unknown",
                test_type=test_type_str or "unknown",
                equipment_tag=equipment_tag,
                confidence_score=result.overall_confidence,
                extraction_result={
                    "raw_data": result.model_dump(mode="json"),
                    "extraction_errors": result.extraction_errors,
                    "needs_review": result.needs_review,
                },
            )
            session.add(analysis)

            # 6. Update task status
            task.status = TaskStatus.COMPLETED.value
            await session.commit()

            set_job_status(
                task_id,
                JobStatus.COMPLETED,
                result={
                    "analysis_id": str(analysis.id),
                    "needs_review": result.needs_review,
                    "confidence_score": result.overall_confidence,
                },
            )
            logger.info(
                f"Task {task_id} completed: analysis_id={analysis.id}, "
                f"confidence={result.overall_confidence:.2f}"
            )

        except Exception as e:
            logger.exception(f"Extraction failed for task {task_id}: {e}")

            # Update task with error
            task.status = TaskStatus.FAILED.value
            task.error_message = str(e)
            await session.commit()

            set_job_status(task_id, JobStatus.FAILED, error=str(e))

            # Re-raise for Dramatiq retry mechanism
            raise
