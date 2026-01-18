"""AuditLog ORM model for compliance traceability."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.analysis import Analysis


class AuditLog(Base, TimestampMixin):
    """Audit log model for tracking extraction and validation events.

    This model provides compliance traceability (AUDT-01 to AUDT-05).
    All records are append-only - no update or delete operations are permitted.

    Attributes:
        id: Unique identifier for the audit log entry.
        analysis_id: Optional reference to the analysis (nullable for pre-analysis events).
        event_type: Type of event (e.g., "extraction_started", "validation_rule_applied").
        event_timestamp: When the event occurred.
        details: JSON storage for event-specific data.
        model_version: Claude model used (e.g., "claude-sonnet-4-20250514").
        prompt_version: Internal prompt version (e.g., "grounding_v1").
        confidence_score: Extraction confidence for extraction events.
        rule_id: Validation rule that triggered for validation events.
        created_at: Record creation timestamp (from TimestampMixin).
    """

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    analysis_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    model_version: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    prompt_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    rule_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Relationships
    analysis: Mapped[Optional["Analysis"]] = relationship(
        "Analysis",
        backref="audit_logs",
    )

    # Indexes
    __table_args__ = (
        Index("ix_audit_logs_analysis_id_event_timestamp", "analysis_id", "event_timestamp"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, event_type={self.event_type}, analysis_id={self.analysis_id})>"
