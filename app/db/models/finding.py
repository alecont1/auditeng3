"""Finding ORM model."""

import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.analysis import Analysis


class Finding(Base, TimestampMixin):
    """Finding model representing a validation finding."""

    __tablename__ = "findings"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    rule_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    evidence: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    remediation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    analysis: Mapped["Analysis"] = relationship(
        "Analysis",
        back_populates="findings",
    )

    def __repr__(self) -> str:
        return f"<Finding(id={self.id}, rule_id={self.rule_id}, severity={self.severity})>"
