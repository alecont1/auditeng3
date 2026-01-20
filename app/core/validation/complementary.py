"""Complementary validators for cross-validation rules.

These validators complement test-type specific validators by checking
cross-references between report data and supporting evidence (photos,
certificates, etc.).

Per CONTEXT.md decisions:
- Run ALL validations and aggregate findings (no short-circuit)
- CRITICAL severity for blockers, MAJOR for low confidence flags
- "IA extrai, codigo valida" - OCR extraction happens before validation
"""

from datetime import date, datetime
from typing import Any

from app.core.extraction.ocr import CertificateOCRResult, HygrometerOCRResult
from app.core.extraction.schemas import BaseExtractionResult
from app.core.extraction.thermography import ThermographyExtractionResult
from app.core.validation.base import BaseValidator
from app.core.validation.schemas import Finding, ValidationResult, ValidationSeverity


class ComplementaryValidator(BaseValidator):
    """Validator for cross-validation rules.

    Checks cross-references between report data and supporting evidence.
    Requires OCR data to be pre-extracted before validation.

    Validators:
    - CALIBRATION_EXPIRED: calibration.expiration_date < inspection_date
    - SERIAL_MISMATCH: camera_serial != certificate OCR serial
    - VALUE_MISMATCH: reflected_temp != hygrometer OCR reading
    - PHOTO_MISSING: phases without thermal images
    - SPEC_NON_COMPLIANCE: delta > 10C without required comments
    """

    @property
    def test_type(self) -> str:
        return "complementary"

    def validate(
        self,
        extraction: BaseExtractionResult,
        certificate_ocr: CertificateOCRResult | None = None,
        hygrometer_ocr: HygrometerOCRResult | None = None,
        report_comments: str | None = None,
        expected_phases: list[str] | None = None,
    ) -> ValidationResult:
        """Validate extraction with optional OCR data.

        Args:
            extraction: The extraction result to validate.
            certificate_ocr: OCR result from calibration certificate photo.
            hygrometer_ocr: OCR result from thermo-hygrometer photo.
            report_comments: Comments section text from report.
            expected_phases: List of expected phase identifiers.

        Returns:
            ValidationResult with complementary validation findings.
        """
        findings: list[Finding] = []

        # Only run thermography-specific validations for thermography extractions
        if isinstance(extraction, ThermographyExtractionResult):
            self._check_calibration_expired(findings, extraction)

            if certificate_ocr:
                self._check_serial_mismatch(findings, extraction, certificate_ocr)

            # Placeholder methods for future plans
            # if hygrometer_ocr:
            #     self._check_value_mismatch(findings, extraction, hygrometer_ocr)
            # if expected_phases:
            #     self._check_photo_missing(findings, extraction, expected_phases)
            # self._check_spec_compliance(findings, extraction, report_comments)

        equipment_tag = None
        if hasattr(extraction, "equipment"):
            equipment_tag = extraction.equipment.equipment_tag.value

        return self.create_result(findings, equipment_tag=equipment_tag)

    def _parse_date(self, date_value: Any) -> date | None:
        """Parse date from various formats."""
        if isinstance(date_value, date):
            return date_value
        if isinstance(date_value, datetime):
            return date_value.date()
        if isinstance(date_value, str):
            # Try multiple formats
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
                try:
                    return datetime.strptime(date_value, fmt).date()
                except ValueError:
                    continue
            # Try ISO format with potential timezone
            try:
                return datetime.fromisoformat(date_value.replace("/", "-")).date()
            except ValueError:
                return None
        return None

    def _check_calibration_expired(
        self,
        findings: list[Finding],
        extraction: ThermographyExtractionResult,
    ) -> None:
        """Check if calibration was expired at time of inspection.

        This differs from CalibrationValidator which checks against today.
        This checks calibration.expiration_date vs test_conditions.inspection_date.
        """
        calibration = extraction.calibration
        if not calibration or not calibration.expiration_date:
            return  # Handled by CalibrationValidator

        exp_date_value = calibration.expiration_date.value
        if not exp_date_value:
            return

        inspection_date_value = extraction.test_conditions.inspection_date.value
        if not inspection_date_value:
            return

        exp_date = self._parse_date(exp_date_value)
        insp_date = self._parse_date(inspection_date_value)

        if exp_date is None or insp_date is None:
            return  # Can't compare if dates don't parse

        if exp_date < insp_date:
            days_expired = (insp_date - exp_date).days
            self.add_finding(
                findings=findings,
                rule_id="COMP-001",
                severity=ValidationSeverity.CRITICAL,
                message=(
                    f"Calibration expired {days_expired} days before inspection: "
                    f"certificate expired {exp_date}, inspection on {insp_date}"
                ),
                field_path="calibration.expiration_date",
                extracted_value=str(exp_date),
                threshold=f">= {insp_date}",
                standard_reference="ISO/IEC 17025",
                remediation="Recalibrate instrument before use. Test results invalid.",
            )

    def _check_serial_mismatch(
        self,
        findings: list[Finding],
        extraction: ThermographyExtractionResult,
        certificate_ocr: CertificateOCRResult,
    ) -> None:
        """Compare serial number from report vs OCR from certificate photo."""
        config = self.config.complementary

        report_serial = extraction.test_conditions.camera_serial
        if not report_serial or not report_serial.value:
            return  # No serial in report to compare

        photo_serial = certificate_ocr.serial_number
        if not photo_serial or not photo_serial.value:
            return  # OCR didn't extract serial

        # Check OCR confidence first
        if photo_serial.confidence < config.serial_confidence_threshold:
            self.add_finding(
                findings=findings,
                rule_id="COMP-006",
                severity=ValidationSeverity.MAJOR,  # Not a blocker - needs review
                message=(
                    f"Serial number illegible in certificate photo "
                    f"(confidence: {photo_serial.confidence:.0%})"
                ),
                field_path="certificate.serial_number",
                extracted_value=str(photo_serial.value),
                threshold=f"confidence >= {config.serial_confidence_threshold:.0%}",
                standard_reference=config.standard_reference,
                remediation="Manual verification required - cannot read serial clearly",
            )
            return  # Don't compare if low confidence

        # Normalize for comparison (strip whitespace, uppercase)
        report_val = str(report_serial.value).strip().upper()
        photo_val = str(photo_serial.value).strip().upper()

        if report_val != photo_val:
            self.add_finding(
                findings=findings,
                rule_id="COMP-002",
                severity=ValidationSeverity.CRITICAL,
                message=(
                    f"Serial number mismatch: report='{report_val}', "
                    f"certificate photo='{photo_val}'"
                ),
                field_path="test_conditions.camera_serial",
                extracted_value=report_val,
                threshold=f"Expected: {photo_val}",
                standard_reference=config.standard_reference,
                remediation="Verify correct calibration certificate is attached to report",
            )
