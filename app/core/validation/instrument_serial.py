"""Instrument serial number validation for all test types.

This module validates that the instrument serial number in a report
matches the serial number from the calibration certificate photo.

This validation applies to ALL test types (grounding, megger, thermography)
per CAL-03 specification: "Serial instrumento != serial certificado = CRITICAL"

Rule ID:
- CALIB-007: SERIAL_MISMATCH - Instrument serial doesn't match certificate
"""

from typing import Any

from app.core.extraction.grounding import GroundingExtractionResult
from app.core.extraction.megger import MeggerExtractionResult
from app.core.extraction.ocr import CertificateOCRResult
from app.core.extraction.schemas import BaseExtractionResult, FieldConfidence
from app.core.extraction.thermography import ThermographyExtractionResult
from app.core.validation.base import BaseValidator
from app.core.validation.schemas import Finding, ValidationResult, ValidationSeverity


class InstrumentSerialValidator(BaseValidator):
    """Validator for instrument serial number consistency.

    Compares the instrument/camera serial number from the report
    against the serial number extracted via OCR from the calibration
    certificate photo.

    This is a common validator that applies to all test types.
    """

    @property
    def test_type(self) -> str:
        """Return test type identifier."""
        return "instrument_serial"

    def validate(
        self,
        extraction: BaseExtractionResult,
        certificate_ocr: CertificateOCRResult | None = None,
    ) -> ValidationResult:
        """Validate instrument serial number matches certificate.

        Args:
            extraction: Any extraction result with test_conditions.
            certificate_ocr: OCR result from calibration certificate photo.

        Returns:
            ValidationResult with serial validation findings.
        """
        findings: list[Finding] = []

        # Get equipment tag for result
        equipment_tag = None
        if hasattr(extraction, "equipment"):
            equipment_tag = extraction.equipment.equipment_tag.value

        # Skip if no certificate OCR provided
        if certificate_ocr is None:
            return self.create_result(findings, equipment_tag=equipment_tag)

        # Get instrument serial from extraction based on test type
        report_serial = self._get_report_serial(extraction)
        if report_serial is None:
            return self.create_result(findings, equipment_tag=equipment_tag)

        # Get serial from OCR
        ocr_serial = certificate_ocr.serial_number.value
        ocr_confidence = certificate_ocr.serial_number.confidence

        if not ocr_serial:
            return self.create_result(findings, equipment_tag=equipment_tag)

        # Get config threshold
        config = self.config.complementary

        # Check OCR confidence
        if ocr_confidence < config.serial_confidence_threshold:
            self.add_finding(
                findings=findings,
                rule_id="CALIB-007",
                severity=ValidationSeverity.MINOR,
                message=(
                    f"Instrument serial OCR confidence low ({ocr_confidence:.2f}): "
                    f"manual verification recommended for '{ocr_serial}'"
                ),
                field_path="certificate.serial_number",
                extracted_value=ocr_serial,
                threshold=f"confidence >= {config.serial_confidence_threshold}",
                standard_reference=config.standard_reference,
                remediation="Verify serial number manually from certificate photo",
            )
            return self.create_result(findings, equipment_tag=equipment_tag)

        # Normalize for comparison (remove spaces, hyphens, uppercase)
        report_normalized = str(report_serial).replace(" ", "").replace("-", "").upper()
        ocr_normalized = str(ocr_serial).replace(" ", "").replace("-", "").upper()

        if report_normalized != ocr_normalized:
            # Determine field path based on test type
            field_path = self._get_serial_field_path(extraction)

            self.add_finding(
                findings=findings,
                rule_id="CALIB-007",
                severity=ValidationSeverity.CRITICAL,
                message=(
                    f"Instrument serial mismatch: report='{report_serial}', "
                    f"certificate photo='{ocr_serial}'"
                ),
                field_path=field_path,
                extracted_value=report_serial,
                threshold=f"Must match certificate: {ocr_serial}",
                standard_reference=config.standard_reference,
                remediation="Verify correct calibration certificate is attached for this instrument",
            )

        return self.create_result(findings, equipment_tag=equipment_tag)

    def _get_report_serial(self, extraction: BaseExtractionResult) -> str | None:
        """Extract instrument serial from any extraction type.

        Args:
            extraction: Extraction result from any test type.

        Returns:
            Serial number string or None if not found.
        """
        test_conditions = getattr(extraction, "test_conditions", None)
        if test_conditions is None:
            return None

        # Thermography uses camera_serial
        if isinstance(extraction, ThermographyExtractionResult):
            serial_field = getattr(test_conditions, "camera_serial", None)
        # Grounding and Megger use instrument_serial
        elif isinstance(extraction, (GroundingExtractionResult, MeggerExtractionResult)):
            serial_field = getattr(test_conditions, "instrument_serial", None)
        else:
            # Try instrument_serial as default
            serial_field = getattr(test_conditions, "instrument_serial", None)
            if serial_field is None:
                serial_field = getattr(test_conditions, "camera_serial", None)

        if serial_field is None:
            return None

        # Handle FieldConfidence objects
        if isinstance(serial_field, FieldConfidence):
            return serial_field.value
        elif hasattr(serial_field, "value"):
            return serial_field.value

        return serial_field

    def _get_serial_field_path(self, extraction: BaseExtractionResult) -> str:
        """Get the field path for serial based on test type.

        Args:
            extraction: Extraction result from any test type.

        Returns:
            Field path string for the serial number.
        """
        if isinstance(extraction, ThermographyExtractionResult):
            return "test_conditions.camera_serial"
        return "test_conditions.instrument_serial"
