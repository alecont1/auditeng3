"""OCR extraction for complementary validations.

This module provides OCR extraction functions for reading data from supporting
documents like calibration certificates and thermo-hygrometer displays.
Uses Claude Vision with structured output for reliable extraction.
"""

import base64
import logging
from typing import Any

from pydantic import BaseModel, Field

from app.core.extraction.client import extract_structured
from app.core.extraction.prompts.complementary import (
    CERTIFICATE_OCR_PROMPT,
    HYGROMETER_OCR_PROMPT,
)
from app.core.extraction.schemas import ExtractionMetadata, FieldConfidence

logger = logging.getLogger(__name__)


class CertificateOCRResult(BaseModel):
    """OCR result from calibration certificate photo.

    Used to extract the camera/device serial number for comparison
    with the serial reported in the thermography report.

    Attributes:
        serial_number: Camera/device serial number with confidence.
        calibration_lab: Name of calibration laboratory if visible.
        calibration_date: Date of calibration if visible.
    """

    serial_number: FieldConfidence = Field(
        description="Camera/device serial number extracted from certificate"
    )
    calibration_lab: FieldConfidence | None = Field(
        default=None,
        description="Name of calibration laboratory if visible",
    )
    calibration_date: FieldConfidence | None = Field(
        default=None,
        description="Date of calibration if visible",
    )


class HygrometerOCRResult(BaseModel):
    """OCR result from thermo-hygrometer display photo.

    Used to extract ambient temperature reading for comparison
    with the reflected temperature value in the thermography report.
    Also extracts serial number for cross-validation.

    Attributes:
        ambient_temperature: Temperature reading in Celsius with confidence.
        humidity: Relative humidity percentage if visible.
        serial_number: Device serial number if visible on equipment/label.
        model: Device model if visible.
    """

    ambient_temperature: FieldConfidence = Field(
        description="Temperature reading from display in Celsius"
    )
    humidity: FieldConfidence | None = Field(
        default=None,
        description="Relative humidity percentage if visible",
    )
    serial_number: FieldConfidence | None = Field(
        default=None,
        description="Device serial number if visible on equipment label",
    )
    model: FieldConfidence | None = Field(
        default=None,
        description="Device model if visible",
    )


async def extract_certificate_serial(
    image: bytes,
) -> tuple[CertificateOCRResult, ExtractionMetadata]:
    """Extract serial number from calibration certificate image.

    Uses Claude Vision to OCR the certificate and extract the camera/device
    serial number with confidence score.

    Args:
        image: Raw image bytes of the calibration certificate.

    Returns:
        tuple: (CertificateOCRResult, ExtractionMetadata)
            - Result contains serial_number, calibration_lab, calibration_date
            - Metadata contains model version and timestamp

    Raises:
        anthropic.APIError: If API call fails after retries.
        instructor.exceptions.ValidationError: If response validation fails.

    Example:
        with open("certificate.jpg", "rb") as f:
            result, metadata = await extract_certificate_serial(f.read())
        print(f"Serial: {result.serial_number.value}")
        print(f"Confidence: {result.serial_number.confidence}")
    """
    # Convert bytes to base64
    b64_image = base64.b64encode(image).decode()

    logger.info("Extracting serial number from calibration certificate")

    result, metadata = await extract_structured(
        prompt=CERTIFICATE_OCR_PROMPT,
        response_model=CertificateOCRResult,
        images=[b64_image],
    )

    logger.info(
        f"Certificate OCR complete: serial={result.serial_number.value}, "
        f"confidence={result.serial_number.confidence:.2f}"
    )

    return result, metadata


async def extract_hygrometer_reading(
    image: bytes,
) -> tuple[HygrometerOCRResult, ExtractionMetadata]:
    """Extract temperature from thermo-hygrometer display image.

    Uses Claude Vision to OCR the digital display and extract the
    ambient temperature reading with confidence score.

    Args:
        image: Raw image bytes of the thermo-hygrometer display.

    Returns:
        tuple: (HygrometerOCRResult, ExtractionMetadata)
            - Result contains ambient_temperature and optionally humidity
            - Metadata contains model version and timestamp

    Raises:
        anthropic.APIError: If API call fails after retries.
        instructor.exceptions.ValidationError: If response validation fails.

    Example:
        with open("hygrometer.jpg", "rb") as f:
            result, metadata = await extract_hygrometer_reading(f.read())
        print(f"Temperature: {result.ambient_temperature.value}C")
        print(f"Confidence: {result.ambient_temperature.confidence}")
    """
    # Convert bytes to base64
    b64_image = base64.b64encode(image).decode()

    logger.info("Extracting temperature from thermo-hygrometer display")

    result, metadata = await extract_structured(
        prompt=HYGROMETER_OCR_PROMPT,
        response_model=HygrometerOCRResult,
        images=[b64_image],
    )

    logger.info(
        f"Hygrometer OCR complete: temp={result.ambient_temperature.value}, "
        f"confidence={result.ambient_temperature.confidence:.2f}"
    )

    return result, metadata
