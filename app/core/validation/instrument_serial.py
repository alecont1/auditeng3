"""Instrument serial number validation for all test types.

This module validates that ALL instrument serial numbers in a report
match the serial numbers from calibration certificate/equipment photos.

This validation applies to ALL test types with their respective equipment:
- Thermography: camera + thermo-hygrometer
- Grounding: earth tester / clamp meter
- Megger: insulation tester

Per CAL-03 specification: "Serial instrumento != serial certificado = CRITICAL"

Rule IDs:
- CALIB-007: SERIAL_MISMATCH - Primary instrument serial doesn't match certificate
- CALIB-008: HYGROMETER_SERIAL_MISMATCH - Hygrometer serial doesn't match photo
"""

from dataclasses import dataclass
from typing import Any

from app.core.extraction.grounding import GroundingExtractionResult
from app.core.extraction.megger import MeggerExtractionResult
from app.core.extraction.ocr import CertificateOCRResult, HygrometerOCRResult
from app.core.extraction.schemas import BaseExtractionResult, FieldConfidence
from app.core.extraction.thermography import ThermographyExtractionResult
from app.core.validation.base import BaseValidator
from app.core.validation.schemas import Finding, ValidationResult, ValidationSeverity


@dataclass
class EquipmentSerialCheck:
    """Represents a serial number check for one piece of equipment."""

    equipment_name: str
    report_serial: str | None
    ocr_serial: str | None
    ocr_confidence: float
    rule_id: str
    field_path: str


class InstrumentSerialValidator(BaseValidator):
    """Validator for ALL instrument serial numbers across test types.

    Compares serial numbers from the report against serial numbers
    extracted via OCR from calibration certificates and equipment photos.

    Validates:
    - Thermography: camera_serial vs certificate, hygrometer_serial vs photo
    - Grounding: instrument_serial vs certificate
    - Megger: instrument_serial vs certificate
    """

    @property
    def test_type(self) -> str:
        """Return test type identifier."""
        return "instrument_serial"

    def validate(
        self,
        extraction: BaseExtractionResult,
        certificate_ocr: CertificateOCRResult | None = None,
        hygrometer_ocr: HygrometerOCRResult | None = None,
    ) -> ValidationResult:
        """Validate ALL instrument serial numbers match their sources.

        Args:
            extraction: Any extraction result with test_conditions.
            certificate_ocr: OCR result from calibration certificate photo.
            hygrometer_ocr: OCR result from hygrometer photo (thermography only).

        Returns:
            ValidationResult with serial validation findings.
        """
        findings: list[Finding] = []

        # Get equipment tag for result
        equipment_tag = None
        if hasattr(extraction, "equipment"):
            equipment_tag = extraction.equipment.equipment_tag.value

        # Build list of equipment to validate based on test type
        checks = self._build_equipment_checks(
            extraction, certificate_ocr, hygrometer_ocr
        )

        # Validate each equipment serial
        for check in checks:
            self._validate_serial(findings, check)

        return self.create_result(findings, equipment_tag=equipment_tag)

    def _build_equipment_checks(
        self,
        extraction: BaseExtractionResult,
        certificate_ocr: CertificateOCRResult | None,
        hygrometer_ocr: HygrometerOCRResult | None,
    ) -> list[EquipmentSerialCheck]:
        """Build list of equipment serial checks based on test type.

        Args:
            extraction: Extraction result from any test type.
            certificate_ocr: OCR from calibration certificate.
            hygrometer_ocr: OCR from hygrometer photo.

        Returns:
            List of EquipmentSerialCheck objects to validate.
        """
        checks: list[EquipmentSerialCheck] = []
        test_conditions = getattr(extraction, "test_conditions", None)

        if test_conditions is None:
            return checks

        # Thermography: camera + hygrometer
        if isinstance(extraction, ThermographyExtractionResult):
            # Camera serial validation
            if certificate_ocr is not None:
                camera_serial = self._get_field_value(
                    getattr(test_conditions, "camera_serial", None)
                )
                checks.append(EquipmentSerialCheck(
                    equipment_name="Thermal Camera",
                    report_serial=camera_serial,
                    ocr_serial=certificate_ocr.serial_number.value,
                    ocr_confidence=certificate_ocr.serial_number.confidence,
                    rule_id="CALIB-007",
                    field_path="test_conditions.camera_serial",
                ))

            # Hygrometer serial validation
            if hygrometer_ocr is not None and hygrometer_ocr.serial_number is not None:
                hygrometer_serial = self._get_field_value(
                    getattr(test_conditions, "hygrometer_serial", None)
                )
                checks.append(EquipmentSerialCheck(
                    equipment_name="Thermo-Hygrometer",
                    report_serial=hygrometer_serial,
                    ocr_serial=hygrometer_ocr.serial_number.value,
                    ocr_confidence=hygrometer_ocr.serial_number.confidence,
                    rule_id="CALIB-008",
                    field_path="test_conditions.hygrometer_serial",
                ))

        # Grounding: instrument serial
        elif isinstance(extraction, GroundingExtractionResult):
            if certificate_ocr is not None:
                instrument_serial = self._get_field_value(
                    getattr(test_conditions, "instrument_serial", None)
                )
                checks.append(EquipmentSerialCheck(
                    equipment_name="Earth Tester / Clamp Meter",
                    report_serial=instrument_serial,
                    ocr_serial=certificate_ocr.serial_number.value,
                    ocr_confidence=certificate_ocr.serial_number.confidence,
                    rule_id="CALIB-007",
                    field_path="test_conditions.instrument_serial",
                ))

        # Megger: instrument serial
        elif isinstance(extraction, MeggerExtractionResult):
            if certificate_ocr is not None:
                instrument_serial = self._get_field_value(
                    getattr(test_conditions, "instrument_serial", None)
                )
                checks.append(EquipmentSerialCheck(
                    equipment_name="Insulation Tester (Megger)",
                    report_serial=instrument_serial,
                    ocr_serial=certificate_ocr.serial_number.value,
                    ocr_confidence=certificate_ocr.serial_number.confidence,
                    rule_id="CALIB-007",
                    field_path="test_conditions.instrument_serial",
                ))

        # Generic fallback for other test types
        else:
            if certificate_ocr is not None:
                # Try instrument_serial first, then camera_serial
                serial_field = getattr(test_conditions, "instrument_serial", None)
                field_path = "test_conditions.instrument_serial"
                if serial_field is None:
                    serial_field = getattr(test_conditions, "camera_serial", None)
                    field_path = "test_conditions.camera_serial"

                if serial_field is not None:
                    checks.append(EquipmentSerialCheck(
                        equipment_name="Measurement Instrument",
                        report_serial=self._get_field_value(serial_field),
                        ocr_serial=certificate_ocr.serial_number.value,
                        ocr_confidence=certificate_ocr.serial_number.confidence,
                        rule_id="CALIB-007",
                        field_path=field_path,
                    ))

        return checks

    def _validate_serial(
        self,
        findings: list[Finding],
        check: EquipmentSerialCheck,
    ) -> None:
        """Validate a single equipment serial number.

        Args:
            findings: List to append findings to.
            check: The equipment serial check to validate.
        """
        # Skip if no report serial
        if check.report_serial is None:
            return

        # Skip if no OCR serial
        if check.ocr_serial is None:
            return

        config = self.config.complementary

        # Check OCR confidence
        if check.ocr_confidence < config.serial_confidence_threshold:
            self.add_finding(
                findings=findings,
                rule_id=check.rule_id,
                severity=ValidationSeverity.MINOR,
                message=(
                    f"{check.equipment_name} serial OCR confidence low "
                    f"({check.ocr_confidence:.2f}): manual verification recommended "
                    f"for '{check.ocr_serial}'"
                ),
                field_path=f"certificate.{check.equipment_name.lower().replace(' ', '_')}_serial",
                extracted_value=check.ocr_serial,
                threshold=f"confidence >= {config.serial_confidence_threshold}",
                standard_reference=config.standard_reference,
                remediation=f"Verify {check.equipment_name} serial number manually from photo",
            )
            return

        # Normalize for comparison (remove spaces, hyphens, uppercase)
        report_normalized = str(check.report_serial).replace(" ", "").replace("-", "").upper()
        ocr_normalized = str(check.ocr_serial).replace(" ", "").replace("-", "").upper()

        if report_normalized != ocr_normalized:
            self.add_finding(
                findings=findings,
                rule_id=check.rule_id,
                severity=ValidationSeverity.CRITICAL,
                message=(
                    f"{check.equipment_name} serial mismatch: "
                    f"report='{check.report_serial}', photo='{check.ocr_serial}'"
                ),
                field_path=check.field_path,
                extracted_value=check.report_serial,
                threshold=f"Must match photo: {check.ocr_serial}",
                standard_reference=config.standard_reference,
                remediation=(
                    f"Verify correct calibration certificate/photo is attached "
                    f"for {check.equipment_name}"
                ),
            )

    def _get_field_value(self, field: Any) -> str | None:
        """Extract value from a field, handling FieldConfidence objects.

        Args:
            field: Field value or FieldConfidence object.

        Returns:
            String value or None if not found.
        """
        if field is None:
            return None

        if isinstance(field, FieldConfidence):
            return field.value
        elif hasattr(field, "value"):
            return field.value

        return str(field) if field else None
