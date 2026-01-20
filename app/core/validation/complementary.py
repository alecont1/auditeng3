"""Complementary validation for cross-document consistency.

This module provides validators for cross-validation rules that complement
test-type specific validators. These validate consistency between different
parts of the report (e.g., serial numbers on certificate vs photos,
temperatures vs hygrometer readings, phase coverage).

Rule IDs:
- COMP-001: CALIBRATION_EXPIRED - Camera calibration certificate expired
- COMP-002: SERIAL_MISMATCH - Camera serial doesn't match certificate
- COMP-003: VALUE_MISMATCH - Reflected temperature differs from hygrometer
- COMP-004: PHOTO_MISSING - Thermal images missing for expected phases
- COMP-005: SPEC_NON_COMPLIANCE - High delta-T without required comments
"""

from datetime import date, datetime, timedelta

from app.core.extraction.ocr import CertificateOCRResult, HygrometerOCRResult
from app.core.extraction.thermography import (
    Hotspot,
    ThermographyExtractionResult,
)
from app.core.validation.base import BaseValidator
from app.core.validation.config import ValidationConfig, get_validation_config
from app.core.validation.schemas import Finding, ValidationResult, ValidationSeverity
from app.core.validation.standards import StandardProfile


class ComplementaryValidator(BaseValidator):
    """Validator for cross-document consistency checks.

    Performs complementary validations that span multiple documents:
    - Certificate calibration status vs inspection date
    - Camera serial number consistency between report and certificate photo
    - Reflected temperature vs thermo-hygrometer reading
    - Phase coverage (all expected phases have thermal images)
    - SPEC compliance for high delta-T readings
    """

    @property
    def test_type(self) -> str:
        """Return test type identifier."""
        return "complementary"

    def validate(
        self,
        extraction: ThermographyExtractionResult,
        certificate_ocr: CertificateOCRResult | None = None,
        hygrometer_ocr: HygrometerOCRResult | None = None,
        expected_phases: list[str] | None = None,
        report_comments: str | None = None,
        inspection_date: date | None = None,
    ) -> ValidationResult:
        """Validate cross-document consistency.

        Args:
            extraction: Thermography extraction result from report.
            certificate_ocr: Optional OCR result from calibration certificate photo.
            hygrometer_ocr: Optional OCR result from thermo-hygrometer photo.
            expected_phases: Optional list of phases that should have thermal images.
            report_comments: Optional comments section from report.
            inspection_date: Optional inspection date for calibration check.

        Returns:
            ValidationResult with cross-validation findings.
        """
        findings: list[Finding] = []
        equipment_tag = extraction.equipment.equipment_tag.value

        # Determine inspection date from extraction if not provided
        if inspection_date is None and extraction.test_conditions.inspection_date:
            date_str = extraction.test_conditions.inspection_date.value
            if date_str:
                try:
                    # Try common date formats
                    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
                        try:
                            inspection_date = datetime.strptime(str(date_str), fmt).date()
                            break
                        except ValueError:
                            continue
                except (ValueError, TypeError):
                    pass

        # COMP-001: Check calibration expiry
        if extraction.calibration and inspection_date:
            self._check_calibration_expired(
                findings, extraction, inspection_date
            )

        # COMP-002: Check serial number match
        if certificate_ocr:
            self._check_serial_mismatch(findings, extraction, certificate_ocr)

        # COMP-003: Check reflected temp vs hygrometer
        if hygrometer_ocr:
            self._check_value_mismatch(findings, extraction, hygrometer_ocr)

        # COMP-004: Check phase coverage
        if expected_phases:
            self._check_photo_missing(findings, extraction, expected_phases)

        # COMP-005: Check SPEC compliance for high delta-T
        self._check_spec_compliance(findings, extraction, report_comments)

        return self.create_result(findings, equipment_tag=equipment_tag)

    def _check_calibration_expired(
        self,
        findings: list[Finding],
        extraction: ThermographyExtractionResult,
        inspection_date: date,
    ) -> None:
        """Check if camera calibration was valid on inspection date.

        Per CONTEXT.md:
        - Camera calibration certificate must be valid on the inspection date
        - Expired calibration invalidates all temperature readings
        """
        config = self.config.complementary
        calibration = extraction.calibration

        if not calibration or not calibration.expiration_date:
            return

        exp_date_val = calibration.expiration_date.value
        if not exp_date_val:
            return

        try:
            # Parse expiration date
            if isinstance(exp_date_val, date):
                exp_date = exp_date_val
            elif isinstance(exp_date_val, datetime):
                exp_date = exp_date_val.date()
            else:
                # Try common formats
                exp_date = None
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
                    try:
                        exp_date = datetime.strptime(str(exp_date_val), fmt).date()
                        break
                    except ValueError:
                        continue
                if exp_date is None:
                    return
        except (ValueError, TypeError):
            return

        if inspection_date > exp_date:
            days_expired = (inspection_date - exp_date).days
            self.add_finding(
                findings=findings,
                rule_id="COMP-001",
                severity=ValidationSeverity.CRITICAL,
                message=(
                    f"Camera calibration expired on inspection date: "
                    f"calibration expired {exp_date.isoformat()}, "
                    f"inspection was {inspection_date.isoformat()} "
                    f"({days_expired} days after expiry)"
                ),
                field_path="calibration.expiration_date",
                extracted_value=exp_date.isoformat(),
                threshold=f"Must be valid on {inspection_date.isoformat()}",
                standard_reference=config.standard_reference,
                remediation="Use camera with valid calibration certificate",
            )

    def _check_serial_mismatch(
        self,
        findings: list[Finding],
        extraction: ThermographyExtractionResult,
        certificate_ocr: CertificateOCRResult,
    ) -> None:
        """Compare camera serial from report vs calibration certificate photo.

        Per CONTEXT.md:
        - Serial number in report must match serial on calibration certificate
        - OCR confidence below threshold flags for review but doesn't block
        """
        config = self.config.complementary

        # Get serial from report (test_conditions.camera_serial)
        if not extraction.test_conditions.camera_serial:
            return  # No serial in report to compare

        report_serial = extraction.test_conditions.camera_serial.value
        if not report_serial:
            return

        # Get serial from OCR
        ocr_serial = certificate_ocr.serial_number.value
        ocr_confidence = certificate_ocr.serial_number.confidence

        if not ocr_serial:
            return  # OCR didn't extract serial

        # Check OCR confidence
        if ocr_confidence < config.serial_confidence_threshold:
            self.add_finding(
                findings=findings,
                rule_id="COMP-002",
                severity=ValidationSeverity.MINOR,
                message=(
                    f"Serial number OCR confidence low ({ocr_confidence:.2f}): "
                    f"manual verification recommended for '{ocr_serial}'"
                ),
                field_path="certificate.serial_number",
                extracted_value=ocr_serial,
                threshold=f"confidence >= {config.serial_confidence_threshold}",
                standard_reference=config.standard_reference,
                remediation="Verify serial number manually from certificate photo",
            )
            return  # Don't compare if OCR is unreliable

        # Normalize for comparison (remove spaces, uppercase)
        report_normalized = str(report_serial).replace(" ", "").replace("-", "").upper()
        ocr_normalized = str(ocr_serial).replace(" ", "").replace("-", "").upper()

        if report_normalized != ocr_normalized:
            self.add_finding(
                findings=findings,
                rule_id="COMP-002",
                severity=ValidationSeverity.CRITICAL,
                message=(
                    f"Camera serial mismatch: report='{report_serial}', "
                    f"certificate photo='{ocr_serial}'"
                ),
                field_path="test_conditions.camera_serial",
                extracted_value=report_serial,
                threshold=f"Must match certificate: {ocr_serial}",
                standard_reference=config.standard_reference,
                remediation="Verify correct calibration certificate is attached",
            )

    def _check_value_mismatch(
        self,
        findings: list[Finding],
        extraction: ThermographyExtractionResult,
        hygrometer_ocr: HygrometerOCRResult,
    ) -> None:
        """Compare reflected temperature from report vs hygrometer photo.

        Per CONTEXT.md:
        - Primary: Compare reflected temp in report vs OCR from thermo-hygrometer photo
        - Fallback: If ALL reflected temps are identical, flag as suspicious copy-paste
        """
        config = self.config.complementary

        # Get reflected temperature from thermal data
        thermal_data = extraction.thermal_data
        if not thermal_data.reflected_temperature:
            return  # No reflected temp in report

        report_temp = thermal_data.reflected_temperature.value
        if report_temp is None:
            return

        # Get temperature from hygrometer OCR
        hygrometer_temp = hygrometer_ocr.ambient_temperature
        if not hygrometer_temp or hygrometer_temp.value is None:
            return  # OCR didn't extract temperature

        try:
            report_val = float(report_temp)
            ocr_val = float(hygrometer_temp.value)
        except (ValueError, TypeError):
            return  # Can't compare non-numeric values

        # Check if difference exceeds tolerance
        diff = abs(report_val - ocr_val)
        if diff > config.temp_match_tolerance:
            self.add_finding(
                findings=findings,
                rule_id="COMP-003",
                severity=ValidationSeverity.CRITICAL,
                message=(
                    f"Reflected temperature mismatch: report={report_val}C, "
                    f"hygrometer photo={ocr_val}C (diff={diff:.1f}C, tolerance={config.temp_match_tolerance}C)"
                ),
                field_path="thermal_data.reflected_temperature",
                extracted_value=report_val,
                threshold=f"{ocr_val} +/- {config.temp_match_tolerance}C",
                standard_reference=config.standard_reference,
                remediation="Verify reflected temperature matches actual ambient conditions",
            )

    def _check_photo_missing(
        self,
        findings: list[Finding],
        extraction: ThermographyExtractionResult,
        expected_phases: list[str],
    ) -> None:
        """Check that all expected phases have corresponding thermal images.

        Per CONTEXT.md:
        - Parse report structure to find which phases SHOULD exist
        - Compare against hotspots which represent actual thermal images
        """
        if not expected_phases:
            return

        # Extract phases that have thermal images from hotspots
        documented_phases = set()
        for hotspot in extraction.hotspots:
            if hotspot.location and hotspot.location.value:
                # Normalize: "Phase A", "Fase A", "A" -> "A"
                location = str(hotspot.location.value).upper()
                for phase in ["A", "B", "C", "N"]:  # Common phase designations
                    if phase in location:
                        documented_phases.add(phase)

        # Also check common patterns like "R", "S", "T" (Brazilian)
        for hotspot in extraction.hotspots:
            if hotspot.location and hotspot.location.value:
                location = str(hotspot.location.value).upper()
                for phase in ["R", "S", "T"]:
                    if phase in location:
                        documented_phases.add(phase)

        # Normalize expected phases
        expected_normalized = set()
        for phase in expected_phases:
            phase_upper = phase.upper()
            for p in ["A", "B", "C", "N", "R", "S", "T"]:
                if p in phase_upper:
                    expected_normalized.add(p)

        # Find missing phases
        missing = expected_normalized - documented_phases
        if missing:
            missing_str = ", ".join(sorted(missing))
            self.add_finding(
                findings=findings,
                rule_id="COMP-004",
                severity=ValidationSeverity.CRITICAL,
                message=f"Thermal images missing for phase(s): {missing_str}",
                field_path="hotspots",
                extracted_value=sorted(documented_phases),
                threshold=f"Expected phases: {sorted(expected_normalized)}",
                standard_reference=self.config.complementary.standard_reference,
                remediation="Include thermal images for all phases being tested",
            )

    def _check_spec_compliance(
        self,
        findings: list[Finding],
        extraction: ThermographyExtractionResult,
        report_comments: str | None,
    ) -> None:
        """Check SPEC compliance: delta > 10C must have required comments.

        Per CONTEXT.md:
        - Triggered when delta-T > 10C (Microsoft standard)
        - Check for keywords in COMMENTS section: terminals, insulators, torque, conductors
        - Section must exist AND contain relevant keywords
        """
        config = self.config.complementary

        # Find hotspots exceeding SPEC threshold
        exceeding_hotspots = []
        for hotspot in extraction.hotspots:
            if hotspot.delta_t and hotspot.delta_t > config.spec_delta_t_threshold:
                exceeding_hotspots.append(hotspot)

        if not exceeding_hotspots:
            return  # No hotspots exceed threshold

        # Check if comments exist and contain required keywords
        if not report_comments:
            locations = [h.location.value for h in exceeding_hotspots if h.location]
            self.add_finding(
                findings=findings,
                rule_id="COMP-005",
                severity=ValidationSeverity.CRITICAL,
                message=(
                    f"SPEC non-compliance: {len(exceeding_hotspots)} hotspot(s) with "
                    f"delta-T > {config.spec_delta_t_threshold}C but no comments section found"
                ),
                field_path="comments",
                extracted_value=None,
                threshold=f"Required keywords: {config.spec_required_keywords[:4]}...",
                standard_reference=config.standard_reference,
                remediation="Add comments section addressing high delta-T findings",
            )
            return

        # Check for required keywords (case-insensitive)
        comments_lower = report_comments.lower()
        found_keywords = [
            kw for kw in config.spec_required_keywords
            if kw.lower() in comments_lower
        ]

        if not found_keywords:
            self.add_finding(
                findings=findings,
                rule_id="COMP-005",
                severity=ValidationSeverity.CRITICAL,
                message=(
                    f"SPEC non-compliance: delta-T > {config.spec_delta_t_threshold}C "
                    f"but comments lack required keywords"
                ),
                field_path="comments",
                extracted_value=report_comments[:100] + "..." if len(report_comments) > 100 else report_comments,
                threshold=f"Must contain: {config.spec_required_keywords[:4]}",
                standard_reference=config.standard_reference,
                remediation="Comments must address: terminals, insulators, torque, or conductors",
            )
