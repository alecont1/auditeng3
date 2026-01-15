"""Analysis schema definitions."""

from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, IDMixin, TimestampMixin
from app.schemas.enums import AnalysisVerdict, EquipmentType, TestType


class AnalysisBase(BaseSchema):
    """Base analysis schema with common fields."""

    equipment_type: EquipmentType
    test_type: TestType
    equipment_tag: str | None = None


class ExtractionResult(BaseSchema):
    """Result of data extraction from document."""

    raw_data: dict[str, Any] = Field(default_factory=dict)
    confidence_scores: dict[str, float] = Field(default_factory=dict)
    extraction_errors: list[str] = Field(default_factory=list)


class ValidationResult(BaseSchema):
    """Result of compliance validation."""

    is_valid: bool
    compliance_score: float = Field(..., ge=0, le=100, description="Compliance score 0-100")
    findings_count: int = Field(..., ge=0)


class AnalysisCreate(AnalysisBase):
    """Schema for creating a new analysis."""

    task_id: UUID


class Analysis(AnalysisBase, IDMixin, TimestampMixin):
    """Analysis schema for API responses."""

    task_id: UUID
    verdict: AnalysisVerdict
    compliance_score: float = Field(..., ge=0, le=100)
    confidence_score: float = Field(..., ge=0, le=1)
    extraction_result: ExtractionResult | None = None
    validation_result: ValidationResult | None = None
