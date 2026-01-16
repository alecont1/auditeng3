"""Common extraction schemas with confidence scoring.

This module defines the base schemas used across all extraction types,
including confidence scoring patterns for field-level reliability tracking.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FieldConfidence(BaseModel):
    """A field value with associated confidence score.

    Used to track extraction reliability at the field level,
    enabling downstream review of low-confidence extractions.

    Attributes:
        value: The extracted value (any type).
        confidence: Confidence score from 0.0 (uncertain) to 1.0 (certain).
        source_text: Original text that was extracted from, for auditability.
    """

    value: Any
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score from 0 (uncertain) to 1 (certain)",
    )
    source_text: str | None = Field(
        default=None,
        description="Original text the value was extracted from",
    )


class ExtractionMetadata(BaseModel):
    """Metadata about an extraction operation.

    Tracks model version, timing, and resource usage for audit trails.

    Attributes:
        model_version: The Claude model version used.
        extraction_timestamp: When the extraction was performed.
        page_numbers: Which pages were processed (if applicable).
        total_tokens_used: Total input + output tokens consumed.
        retry_count: Number of retry attempts made.
    """

    model_version: str
    extraction_timestamp: datetime
    page_numbers: list[int] = Field(default_factory=list)
    total_tokens_used: int = 0
    retry_count: int = 0


class BaseExtractionResult(BaseModel):
    """Base class for all extraction results.

    Provides common fields for metadata, confidence, and review flags
    that all test-type-specific extraction results inherit.

    Attributes:
        metadata: Extraction operation metadata.
        overall_confidence: Aggregate confidence across all fields.
        extraction_errors: List of errors/warnings during extraction.
        needs_review: True if any field confidence is below threshold (0.7).
    """

    metadata: ExtractionMetadata | None = None
    overall_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall confidence across all extracted fields",
    )
    extraction_errors: list[str] = Field(default_factory=list)
    needs_review: bool = Field(
        default=False,
        description="True if any field has confidence below 0.7",
    )


class EquipmentInfo(BaseModel):
    """Equipment identification information.

    Common across all test types - identifies the equipment being tested.

    Attributes:
        equipment_tag: Equipment TAG/ID with confidence.
        serial_number: Equipment serial number with confidence.
        equipment_type: Type of equipment (PANEL, UPS, ATS, GEN, XFMR).
        manufacturer: Equipment manufacturer.
        model: Equipment model number/name.
    """

    equipment_tag: FieldConfidence
    serial_number: FieldConfidence | None = None
    equipment_type: FieldConfidence
    manufacturer: FieldConfidence | None = None
    model: FieldConfidence | None = None


class CalibrationInfo(BaseModel):
    """Calibration certificate information.

    Tracks calibration validity for measurement equipment.

    Attributes:
        certificate_number: Calibration certificate number.
        calibration_date: Date when calibration was performed.
        expiration_date: Date when calibration expires.
        calibration_lab: Name of calibration laboratory.
        is_valid: Computed from expiration_date vs current date.
    """

    certificate_number: FieldConfidence | None = None
    calibration_date: FieldConfidence | None = None
    expiration_date: FieldConfidence
    calibration_lab: FieldConfidence | None = None
    is_valid: bool = Field(
        default=True,
        description="True if calibration has not expired",
    )
