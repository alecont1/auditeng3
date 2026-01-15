"""Analysis ORM model."""

import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.finding import Finding
    from app.db.models.task import Task


class Analysis(Base, TimestampMixin):
    """Analysis model storing extraction and validation results."""

    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    equipment_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    test_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    equipment_tag: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    verdict: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    compliance_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    extraction_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    validation_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )

    # Relationships
    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="analysis",
    )
    findings: Mapped[List["Finding"]] = relationship(
        "Finding",
        back_populates="analysis",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Analysis(id={self.id}, verdict={self.verdict}, score={self.compliance_score})>"
