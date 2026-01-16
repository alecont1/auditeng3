"""Report schema definitions for PDF generation."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema
from app.schemas.enums import AnalysisVerdict, FindingSeverity


class ReportFinding(BaseSchema):
    """Finding representation for PDF report."""

    rule_id: str = Field(..., description="Finding code (e.g., GND-01, THM-02)")
    severity: FindingSeverity = Field(..., description="Finding severity level")
    message: str = Field(..., description="Description of what is wrong")
    remediation: str | None = Field(None, description="How to fix the issue")
    standard_reference: str = Field(
        "N/A", description="Reference to the standard (e.g., NETA 7.1.2)"
    )


class SeverityCounts(BaseSchema):
    """Count of findings by severity level."""

    critical: int = Field(default=0, ge=0, description="Count of CRITICAL findings")
    major: int = Field(default=0, ge=0, description="Count of MAJOR findings")
    minor: int = Field(default=0, ge=0, description="Count of MINOR findings")
    info: int = Field(default=0, ge=0, description="Count of INFO findings")


class ReportData(BaseSchema):
    """Complete data structure for PDF report generation."""

    analysis_id: UUID = Field(..., description="Analysis identifier")
    equipment_type: str = Field(..., description="Type of equipment analyzed")
    test_type: str = Field(..., description="Type of test performed")
    equipment_tag: str | None = Field(None, description="Equipment identifier tag")
    verdict: AnalysisVerdict | None = Field(None, description="Analysis verdict")
    compliance_score: float | None = Field(
        None, ge=0, le=100, description="Compliance score 0-100"
    )
    confidence_score: float | None = Field(
        None, ge=0, le=1, description="Extraction confidence 0-1"
    )
    severity_counts: SeverityCounts = Field(
        default_factory=SeverityCounts, description="Findings count by severity"
    )
    findings: list[ReportFinding] = Field(
        default_factory=list, description="List of findings for the report"
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Report generation timestamp"
    )
