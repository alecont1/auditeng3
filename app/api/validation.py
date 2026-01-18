"""Validation API endpoints.

Provides REST API endpoints for validation operations.
"""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.validation import (
    ValidationConfig,
    ValidationOrchestrator,
    ValidationResult,
    get_validation_config,
)
from app.core.validation.schemas import Finding, ValidationSeverity

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/validation", tags=["validation"])


# Response models
class FindingResponse(BaseModel):
    """Single finding in API response."""

    rule_id: str
    severity: str
    message: str
    field_path: str
    extracted_value: Any
    threshold: Any
    standard_reference: str | None = None
    remediation: str | None = None


class ValidationResponse(BaseModel):
    """Validation result API response."""

    test_type: str
    equipment_tag: str | None = None
    is_valid: bool
    compliance_score: float
    critical_count: int
    major_count: int
    minor_count: int
    info_count: int
    findings: list[FindingResponse]


class StandardsResponse(BaseModel):
    """Standards thresholds API response."""

    grounding: dict[str, Any]
    megger: dict[str, Any]
    thermography: dict[str, Any]
    calibration: dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str


# Helper functions
def finding_to_response(finding: Finding) -> FindingResponse:
    """Convert Finding to API response."""
    return FindingResponse(
        rule_id=finding.rule_id,
        severity=finding.severity.value if hasattr(finding.severity, 'value') else finding.severity,
        message=finding.message,
        field_path=finding.field_path,
        extracted_value=finding.extracted_value,
        threshold=finding.threshold,
        standard_reference=finding.standard_reference,
        remediation=finding.remediation,
    )


def validation_result_to_response(
    result: ValidationResult,
    compliance_score: float,
) -> ValidationResponse:
    """Convert ValidationResult to API response."""
    return ValidationResponse(
        test_type=result.test_type,
        equipment_tag=result.equipment_tag,
        is_valid=result.is_valid,
        compliance_score=compliance_score,
        critical_count=result.critical_count,
        major_count=result.major_count,
        minor_count=result.minor_count,
        info_count=result.info_count,
        findings=[finding_to_response(f) for f in result.findings],
    )


# Endpoints
@router.get("/health", response_model=HealthResponse)
async def validation_health() -> HealthResponse:
    """Health check for validation service."""
    return HealthResponse(status="healthy", service="validation")


@router.get("/standards", response_model=StandardsResponse)
async def get_standards() -> StandardsResponse:
    """Get current validation standards/thresholds.

    Returns all configured thresholds for:
    - Grounding resistance
    - Megger/insulation resistance
    - Thermography delta-T
    - Calibration requirements
    """
    config = get_validation_config()

    return StandardsResponse(
        grounding={
            "general_max_ohms": config.grounding.general_max,
            "data_center_max_ohms": config.grounding.data_center_max,
            "ground_bond_max_ohms": config.grounding.ground_bond_max,
            "equipment_thresholds": {
                "panel": config.grounding.panel_max,
                "ups": config.grounding.ups_max,
                "ats": config.grounding.ats_max,
                "gen": config.grounding.gen_max,
                "xfmr": config.grounding.xfmr_max,
            },
        },
        megger={
            "min_ir_megohms": config.megger.min_ir_megohms,
            "excellent_ir_megohms": config.megger.excellent_ir_megohms,
            "min_polarization_index": config.megger.min_pi,
            "excellent_polarization_index": config.megger.excellent_pi,
            "min_dar": config.megger.min_dar,
            "ir_by_voltage": config.megger.min_ir_by_voltage,
        },
        thermography={
            "normal_max_celsius": config.thermography.normal_max,
            "attention_max_celsius": config.thermography.attention_max,
            "serious_max_celsius": config.thermography.serious_max,
            "critical_max_celsius": config.thermography.critical_max,
            "classifications": {
                "normal": f"ΔT ≤ {config.thermography.normal_max}°C",
                "attention": f"ΔT {config.thermography.normal_max+1}-{config.thermography.attention_max}°C",
                "serious": f"ΔT {config.thermography.attention_max+1}-{config.thermography.serious_max}°C",
                "critical": f"ΔT {config.thermography.serious_max+1}-{config.thermography.critical_max}°C",
                "emergency": f"ΔT > {config.thermography.critical_max}°C",
            },
        },
        calibration={
            "max_days_expired": config.calibration.max_days_expired,
            "warn_days_before_expiry": config.calibration.warn_days_before_expiry,
        },
    )


@router.get("/tasks/{task_id}/validation", response_model=ValidationResponse)
async def get_task_validation(task_id: UUID) -> ValidationResponse:
    """Get validation results for a completed task.

    Args:
        task_id: Task UUID to get validation for.

    Returns:
        ValidationResponse with all findings.

    Raises:
        HTTPException: If task not found or not yet validated.
    """
    # TODO: Integrate with task/analysis storage
    # For now, return 501 Not Implemented
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Task validation lookup not yet implemented. Use /validate endpoint.",
    )


class ValidateRequest(BaseModel):
    """Request body for validation endpoint."""

    test_type: str = Field(description="Type of test: grounding, megger, thermography, fat")
    data: dict[str, Any] = Field(description="Extracted data to validate")


@router.post("/validate", response_model=ValidationResponse)
async def validate_data(request: ValidateRequest) -> ValidationResponse:
    """Validate extraction data directly.

    Accepts extracted data and returns validation results.
    Useful for testing or when extraction was done externally.

    Args:
        request: Validation request with test type and data.

    Returns:
        ValidationResponse with all findings.
    """
    logger.info(f"Validating {request.test_type} data")

    try:
        orchestrator = ValidationOrchestrator()

        # Convert dict to appropriate extraction result based on test type
        # This is a simplified version - in production, would use proper deserialization
        from app.core.extraction import (
            FATExtractionResult,
            GroundingExtractionResult,
            MeggerExtractionResult,
            ThermographyExtractionResult,
        )

        if request.test_type == "grounding":
            extraction = GroundingExtractionResult(**request.data)
        elif request.test_type == "megger":
            extraction = MeggerExtractionResult(**request.data)
        elif request.test_type == "thermography":
            extraction = ThermographyExtractionResult(**request.data)
        elif request.test_type == "fat":
            extraction = FATExtractionResult(**request.data)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown test type: {request.test_type}",
            )

        result = orchestrator.validate(extraction)
        score = orchestrator.calculate_compliance_score(result)

        return validation_result_to_response(result, score)

    except Exception as e:
        logger.exception(f"Validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation failed: {str(e)}",
        )


@router.get("/severity-levels")
async def get_severity_levels() -> dict[str, str]:
    """Get severity level descriptions.

    Returns mapping of severity levels to their meanings.
    """
    return {
        "critical": "Immediate action required - safety or compliance failure",
        "major": "Significant issue requiring attention",
        "minor": "Minor deviation from standards",
        "info": "Informational - no action required",
    }
