"""Audit service for compliance traceability.

This module provides the AuditService for logging extraction and validation
events. All audit logs are append-only for immutability.
"""

import logging
import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class EventType(StrEnum):
    """Event types for audit logging."""

    EXTRACTION_STARTED = "extraction_started"
    EXTRACTION_COMPLETED = "extraction_completed"
    EXTRACTION_FAILED = "extraction_failed"
    VALIDATION_STARTED = "validation_started"
    VALIDATION_RULE_APPLIED = "validation_rule_applied"
    FINDING_GENERATED = "finding_generated"
    VALIDATION_COMPLETED = "validation_completed"
    HUMAN_REVIEW_APPROVED = "human_review_approved"
    HUMAN_REVIEW_REJECTED = "human_review_rejected"


class AuditService:
    """Service for creating and querying audit logs.

    All methods are static - no instance state needed.
    All log methods are append-only. Never update or delete AuditLog records.
    """

    @staticmethod
    async def log_extraction_start(
        db: AsyncSession,
        analysis_id: uuid.UUID,
        model_version: str,
        prompt_version: str,
    ) -> AuditLog:
        """Log the start of an extraction.

        Args:
            db: Database session.
            analysis_id: ID of the analysis being processed.
            model_version: Claude model version (e.g., "claude-sonnet-4-20250514").
            prompt_version: Internal prompt version (e.g., "grounding_v1").

        Returns:
            Created AuditLog record.
        """
        log = AuditLog(
            id=uuid.uuid4(),
            analysis_id=analysis_id,
            event_type=EventType.EXTRACTION_STARTED,
            event_timestamp=datetime.now(timezone.utc),
            model_version=model_version,
            prompt_version=prompt_version,
            details={"status": "started"},
        )
        db.add(log)
        return log

    @staticmethod
    async def log_extraction_complete(
        db: AsyncSession,
        analysis_id: uuid.UUID,
        confidence_score: float,
        field_count: int,
    ) -> AuditLog:
        """Log the successful completion of an extraction.

        Args:
            db: Database session.
            analysis_id: ID of the analysis.
            confidence_score: Extraction confidence score.
            field_count: Number of fields extracted.

        Returns:
            Created AuditLog record.
        """
        log = AuditLog(
            id=uuid.uuid4(),
            analysis_id=analysis_id,
            event_type=EventType.EXTRACTION_COMPLETED,
            event_timestamp=datetime.now(timezone.utc),
            confidence_score=confidence_score,
            details={
                "status": "completed",
                "field_count": field_count,
            },
        )
        db.add(log)
        return log

    @staticmethod
    async def log_extraction_failed(
        db: AsyncSession,
        analysis_id: uuid.UUID,
        error_message: str,
    ) -> AuditLog:
        """Log a failed extraction.

        Args:
            db: Database session.
            analysis_id: ID of the analysis.
            error_message: Error description.

        Returns:
            Created AuditLog record.
        """
        log = AuditLog(
            id=uuid.uuid4(),
            analysis_id=analysis_id,
            event_type=EventType.EXTRACTION_FAILED,
            event_timestamp=datetime.now(timezone.utc),
            details={
                "status": "failed",
                "error_message": error_message,
            },
        )
        db.add(log)
        return log

    @staticmethod
    async def log_validation_rule(
        db: AsyncSession,
        analysis_id: uuid.UUID,
        rule_id: str,
        passed: bool,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Log a validation rule application.

        Args:
            db: Database session.
            analysis_id: ID of the analysis.
            rule_id: ID of the validation rule.
            passed: Whether the rule passed.
            details: Additional details about the rule application.

        Returns:
            Created AuditLog record.
        """
        log_details = {
            "passed": passed,
        }
        if details:
            log_details.update(details)

        log = AuditLog(
            id=uuid.uuid4(),
            analysis_id=analysis_id,
            event_type=EventType.VALIDATION_RULE_APPLIED,
            event_timestamp=datetime.now(timezone.utc),
            rule_id=rule_id,
            details=log_details,
        )
        db.add(log)
        return log

    @staticmethod
    async def log_finding_generated(
        db: AsyncSession,
        analysis_id: uuid.UUID,
        rule_id: str,
        severity: str,
        message: str,
    ) -> AuditLog:
        """Log a finding generation.

        Args:
            db: Database session.
            analysis_id: ID of the analysis.
            rule_id: ID of the validation rule that generated the finding.
            severity: Severity level of the finding.
            message: Finding message.

        Returns:
            Created AuditLog record.
        """
        log = AuditLog(
            id=uuid.uuid4(),
            analysis_id=analysis_id,
            event_type=EventType.FINDING_GENERATED,
            event_timestamp=datetime.now(timezone.utc),
            rule_id=rule_id,
            details={
                "severity": severity,
                "message": message,
            },
        )
        db.add(log)
        return log

    @staticmethod
    async def log_validation_complete(
        db: AsyncSession,
        analysis_id: uuid.UUID,
        verdict: str,
        compliance_score: float,
    ) -> AuditLog:
        """Log the completion of validation.

        Args:
            db: Database session.
            analysis_id: ID of the analysis.
            verdict: Final verdict (e.g., "approved", "rejected", "review").
            compliance_score: Overall compliance score.

        Returns:
            Created AuditLog record.
        """
        log = AuditLog(
            id=uuid.uuid4(),
            analysis_id=analysis_id,
            event_type=EventType.VALIDATION_COMPLETED,
            event_timestamp=datetime.now(timezone.utc),
            details={
                "status": "completed",
                "verdict": verdict,
                "compliance_score": compliance_score,
            },
        )
        db.add(log)
        return log

    @staticmethod
    async def get_audit_trail(
        db: AsyncSession,
        analysis_id: uuid.UUID,
    ) -> List[AuditLog]:
        """Get the complete audit trail for an analysis.

        Args:
            db: Database session.
            analysis_id: ID of the analysis.

        Returns:
            List of AuditLog records ordered by timestamp (oldest first).
        """
        stmt = (
            select(AuditLog)
            .where(AuditLog.analysis_id == analysis_id)
            .order_by(AuditLog.event_timestamp)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def log_human_review(
        db: AsyncSession,
        analysis_id: uuid.UUID,
        action: str,
        user_id: uuid.UUID,
        reason: Optional[str] = None,
    ) -> AuditLog:
        """Log a human review action (approve/reject).

        Args:
            db: Database session.
            analysis_id: ID of the analysis being reviewed.
            action: "approved" or "rejected".
            user_id: ID of the user performing the review.
            reason: Optional rejection reason (required for rejections).

        Returns:
            Created AuditLog record.
        """
        event_type = (
            EventType.HUMAN_REVIEW_APPROVED
            if action == "approved"
            else EventType.HUMAN_REVIEW_REJECTED
        )

        details: Dict[str, Any] = {
            "action": action,
            "reviewer_id": str(user_id),
        }
        if reason:
            details["reason"] = reason

        log = AuditLog(
            id=uuid.uuid4(),
            analysis_id=analysis_id,
            event_type=event_type,
            event_timestamp=datetime.now(timezone.utc),
            details=details,
        )
        db.add(log)
        return log


async def log_event(
    db: AsyncSession,
    event_type: EventType,
    analysis_id: Optional[uuid.UUID] = None,
    **kwargs: Any,
) -> AuditLog:
    """Convenience function to log an arbitrary event.

    Creates an AuditLog record with current timestamp.
    Does NOT call db.commit() - caller controls transaction.

    Args:
        db: Database session.
        event_type: Type of event.
        analysis_id: Optional analysis ID.
        **kwargs: Additional fields to store in details or as columns.

    Returns:
        Created AuditLog record.
    """
    # Extract known columns from kwargs
    model_version = kwargs.pop("model_version", None)
    prompt_version = kwargs.pop("prompt_version", None)
    confidence_score = kwargs.pop("confidence_score", None)
    rule_id = kwargs.pop("rule_id", None)

    # Everything else goes into details
    details = kwargs if kwargs else None

    log = AuditLog(
        id=uuid.uuid4(),
        analysis_id=analysis_id,
        event_type=event_type,
        event_timestamp=datetime.now(timezone.utc),
        model_version=model_version,
        prompt_version=prompt_version,
        confidence_score=confidence_score,
        rule_id=rule_id,
        details=details,
    )
    db.add(log)
    return log
