"""Extraction worker for background document processing.

This module provides the Dramatiq actor for processing uploaded documents
through the extraction pipeline with retry logic and status tracking.
Includes automatic validation of extraction results with finding generation.
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
from app.services.finding import FindingService
from app.services.verdict import VerdictService
from app.services.audit import AuditService
from app.core.validation import ValidationOrchestrator
from app.worker.broker import broker
from app.worker.status import JobStatus, set_job_status

# Default model version - can be overridden from config
MODEL_VERSION = "claude-sonnet-4"

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

            # 5. Run validation on extraction result
            orchestrator = ValidationOrchestrator()
            validation_result = orchestrator.validate(result)

            # 6. Generate findings and compute verdict using services
            verdict, compliance_score, confidence_score = (
                VerdictService.compute_analysis_verdict(validation_result, result)
            )

            logger.info(
                f"Task {task_id} validated: verdict={verdict.value}, "
                f"compliance_score={compliance_score:.1f}%, "
                f"confidence_score={confidence_score:.2f}, "
                f"findings={len(validation_result.findings)}"
            )

            # 7. Create Analysis record with validation results
            analysis = Analysis(
                task_id=task_uuid,
                equipment_type=equipment_type or "unknown",
                test_type=test_type_str or "unknown",
                equipment_tag=equipment_tag,
                verdict=verdict.value,
                compliance_score=compliance_score,
                confidence_score=confidence_score,
                extraction_result={
                    "raw_data": result.model_dump(mode="json"),
                    "extraction_errors": result.extraction_errors,
                    "needs_review": result.needs_review,
                },
                validation_result={
                    "is_valid": validation_result.is_valid,
                    "test_type": validation_result.test_type,
                    "critical_count": validation_result.critical_count,
                    "major_count": validation_result.major_count,
                    "minor_count": validation_result.minor_count,
                    "info_count": validation_result.info_count,
                },
            )
            session.add(analysis)
            await session.flush()  # Get analysis.id before creating findings

            # 8. Audit logging - extraction start (logged retroactively with analysis.id)
            prompt_version = f"{test_type_str or 'unknown'}_v1"
            try:
                await AuditService.log_extraction_start(
                    session, analysis.id, MODEL_VERSION, prompt_version
                )
            except Exception as audit_err:
                logger.warning(f"Audit log failed (extraction_start): {audit_err}")

            # 9. Audit logging - extraction complete
            field_count = len(result.model_dump(mode="json").get("measurements", []))
            try:
                await AuditService.log_extraction_complete(
                    session, analysis.id, confidence_score, field_count
                )
            except Exception as audit_err:
                logger.warning(f"Audit log failed (extraction_complete): {audit_err}")

            # 10. Generate and persist findings using FindingService
            finding_creates = FindingService.generate_findings_from_validation(
                validation_result, analysis.id
            )
            await FindingService.persist_findings(session, finding_creates)

            # 11. Audit logging - log each finding generated
            for finding in validation_result.findings:
                try:
                    await AuditService.log_finding_generated(
                        session,
                        analysis.id,
                        finding.rule_id,
                        finding.severity.value,
                        finding.message,
                    )
                except Exception as audit_err:
                    logger.warning(f"Audit log failed (finding_generated): {audit_err}")

            # 12. Audit logging - validation complete
            try:
                await AuditService.log_validation_complete(
                    session, analysis.id, verdict.value, compliance_score
                )
            except Exception as audit_err:
                logger.warning(f"Audit log failed (validation_complete): {audit_err}")

            # 13. Update task status
            task.status = TaskStatus.COMPLETED.value
            await session.commit()

            set_job_status(
                task_id,
                JobStatus.COMPLETED,
                result={
                    "analysis_id": str(analysis.id),
                    "verdict": verdict.value,
                    "compliance_score": compliance_score,
                    "needs_review": result.needs_review or verdict.value == "review",
                    "confidence_score": confidence_score,
                    "findings_count": len(validation_result.findings),
                },
            )
            logger.info(
                f"Task {task_id} completed: analysis_id={analysis.id}, "
                f"verdict={verdict.value}, compliance={compliance_score:.1f}%"
            )

        except Exception as e:
            logger.exception(f"Extraction failed for task {task_id}: {e}")

            # Audit logging - extraction failed
            # Note: analysis may not exist if failure occurred before creation
            try:
                if "analysis" in locals():
                    await AuditService.log_extraction_failed(
                        session, analysis.id, str(e)
                    )
            except Exception as audit_err:
                logger.warning(f"Audit log failed (extraction_failed): {audit_err}")

            # Update task with error
            task.status = TaskStatus.FAILED.value
            task.error_message = str(e)
            await session.commit()

            set_job_status(task_id, JobStatus.FAILED, error=str(e))

            # Re-raise for Dramatiq retry mechanism
            raise
