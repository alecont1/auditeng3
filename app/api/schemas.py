"""API response schemas for analyses endpoints.

These schemas define the response models for the analyses API,
including submission, status polling, and results retrieval.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AnalysisSubmitResponse(BaseModel):
    """Response for document submission."""

    task_id: UUID = Field(..., description="ID of the created processing task")
    status: str = Field(..., description="Initial task status (queued)")

    model_config = {"from_attributes": True}


class AnalysisStatusResponse(BaseModel):
    """Response for analysis status polling."""

    analysis_id: UUID = Field(..., description="Analysis ID")
    status: str = Field(..., description="Current task status")
    message: str = Field(..., description="Human-readable status message")

    model_config = {"from_attributes": True}


class FindingEvidence(BaseModel):
    """Evidence supporting a finding."""

    extracted_value: Any = Field(None, description="Value extracted from document")
    threshold: Any = Field(None, description="Expected threshold value")
    standard_reference: str = Field("N/A", description="Reference to standard")


class FindingDetail(BaseModel):
    """Detailed finding in analysis response."""

    rule_id: str = Field(..., description="Identifier of the compliance rule")
    severity: str = Field(..., description="Finding severity (critical/major/minor/info)")
    message: str = Field(..., description="Human-readable finding message")
    field_path: str | None = Field(None, description="Path to the field in extracted data")
    evidence: FindingEvidence | None = Field(None, description="Evidence supporting the finding")
    remediation: str | None = Field(None, description="Suggested remediation action")

    model_config = {"from_attributes": True}


class AnalysisResponse(BaseModel):
    """Complete analysis response with findings."""

    id: UUID = Field(..., description="Analysis ID")
    equipment_type: str = Field(..., description="Type of equipment analyzed")
    test_type: str = Field(..., description="Type of test performed")
    equipment_tag: str | None = Field(None, description="Equipment identifier tag")
    verdict: str | None = Field(None, description="Analysis verdict (approved/review/rejected)")
    compliance_score: float | None = Field(None, ge=0, le=100, description="Compliance score 0-100")
    confidence_score: float | None = Field(None, ge=0, le=1, description="Extraction confidence 0-1")
    findings: list[FindingDetail] = Field(default_factory=list, description="List of validation findings")
    extraction_result: dict[str, Any] | None = Field(None, description="Raw extraction data")
    created_at: datetime = Field(..., description="When the analysis was created")

    model_config = {"from_attributes": True}


class AuditEventResponse(BaseModel):
    """Response model for a single audit event."""

    id: UUID = Field(..., description="Unique identifier for the audit log entry")
    event_type: str = Field(..., description="Type of event (extraction_started, validation_rule_applied, etc.)")
    event_timestamp: datetime = Field(..., description="When the event occurred")
    details: dict[str, Any] | None = Field(None, description="Event-specific data")
    model_version: str | None = Field(None, description="Claude model version used")
    prompt_version: str | None = Field(None, description="Internal prompt version used")
    confidence_score: float | None = Field(None, ge=0, le=1, description="Extraction confidence score")
    rule_id: str | None = Field(None, description="Validation rule ID if applicable")

    model_config = {"from_attributes": True}


class AuditTrailResponse(BaseModel):
    """Response model for complete audit trail."""

    analysis_id: UUID = Field(..., description="Analysis ID the audit trail belongs to")
    event_count: int = Field(..., ge=0, description="Number of events in the trail")
    events: list[AuditEventResponse] = Field(default_factory=list, description="Chronological list of audit events")

    model_config = {"from_attributes": True}


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""

    total: int = Field(..., ge=0, description="Total count of items")
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    per_page: int = Field(..., ge=1, description="Number of items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

    model_config = {"from_attributes": True}


class AnalysisListItem(BaseModel):
    """Summary item for analysis list view."""

    id: UUID = Field(..., description="Analysis ID")
    equipment_type: str = Field(..., description="Type of equipment analyzed")
    test_type: str = Field(..., description="Type of test performed")
    equipment_tag: str | None = Field(None, description="Equipment identifier tag")
    verdict: str | None = Field(None, description="Analysis verdict (approved/review/rejected)")
    compliance_score: float | None = Field(None, ge=0, le=100, description="Compliance score 0-100")
    status: str = Field(..., description="Current task status")
    created_at: datetime = Field(..., description="When the analysis was created")
    original_filename: str = Field(..., description="Original uploaded filename")

    model_config = {"from_attributes": True}


class AnalysisListResponse(BaseModel):
    """Paginated response for analysis list."""

    items: list[AnalysisListItem] = Field(default_factory=list, description="List of analysis items")
    meta: PaginationMeta = Field(..., description="Pagination metadata")

    model_config = {"from_attributes": True}


class RejectRequest(BaseModel):
    """Request body for rejecting an analysis."""

    reason: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Reason for rejection (required, 10-1000 chars)"
    )


class ApproveRejectResponse(BaseModel):
    """Response for approve/reject actions."""

    analysis_id: UUID = Field(..., description="Analysis ID")
    verdict: str = Field(..., description="New verdict (approved/rejected)")
    message: str = Field(..., description="Success message")

    model_config = {"from_attributes": True}
