"""Finding schema definitions."""

from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, IDMixin
from app.schemas.enums import FindingSeverity


class FindingBase(BaseSchema):
    """Base finding schema with common fields."""

    severity: FindingSeverity
    rule_id: str = Field(..., description="Identifier of the compliance rule")
    message: str = Field(..., description="Human-readable finding message")


class FindingEvidence(BaseSchema):
    """Evidence supporting a finding."""

    extracted_value: Any = Field(..., description="Value extracted from document")
    threshold: Any = Field(..., description="Expected threshold value")
    standard_reference: str = Field(..., description="Reference to standard (e.g., NFPA 70)")


class FindingCreate(FindingBase):
    """Schema for creating a new finding."""

    analysis_id: UUID
    evidence: FindingEvidence | None = None
    remediation: str | None = None


class Finding(FindingBase, IDMixin):
    """Finding schema for API responses."""

    analysis_id: UUID
    evidence: FindingEvidence | None = None
    remediation: str | None = Field(None, description="Suggested remediation action")
