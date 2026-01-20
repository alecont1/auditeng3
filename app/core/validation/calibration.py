"""Calibration certificate validator.

Validates calibration certificate expiration dates.
"""

from datetime import date, datetime
from typing import Any

from app.core.extraction.schemas import CalibrationInfo
from app.core.validation.base import BaseValidator
from app.core.validation.schemas import Finding, ValidationResult, ValidationSeverity


class CalibrationValidator(BaseValidator):
    """Validator for calibration certificate expiration."""

    @property
    def test_type(self) -> str:
        """Return test type identifier."""
        return "calibration"

    def validate_calibration(
        self,
        calibration: CalibrationInfo | None,
        test_date_str: str | None = None,
    ) -> list[Finding]:
        """Validate calibration info and return findings.

        Args:
            calibration: Calibration info from extraction.
            test_date_str: Optional test date to validate against.

        Returns:
            list[Finding]: Calibration validation findings.
        """
        findings: list[Finding] = []

        if calibration is None:
            self.add_finding(
                findings=findings,
                rule_id="CALIB-001",
                severity=ValidationSeverity.MAJOR,
                message="No calibration certificate information found",
                field_path="calibration",
                extracted_value=None,
                threshold="Calibration certificate required",
                remediation="Ensure calibration certificate is included in report",
            )
            return findings

        exp_date = calibration.expiration_date.value
        if exp_date is None:
            self.add_finding(
                findings=findings,
                rule_id="CALIB-002",
                severity=ValidationSeverity.MAJOR,
                message="Calibration expiration date not found",
                field_path="calibration.expiration_date",
                extracted_value=None,
                threshold="Expiration date required",
                remediation="Verify calibration certificate includes expiration date",
            )
            return findings

        expiration = self._parse_date(exp_date)
        if expiration is None:
            self.add_finding(
                findings=findings,
                rule_id="CALIB-003",
                severity=ValidationSeverity.MINOR,
                message=f"Unable to parse expiration date: {exp_date}",
                field_path="calibration.expiration_date",
                extracted_value=exp_date,
                threshold="Valid date format required",
            )
            return findings

        reference_date, is_test_date = self._get_reference_date(test_date_str)
        self._validate_expiration(findings, expiration, reference_date, is_test_date)

        return findings

    def _parse_date(self, date_value: Any) -> date | None:
        """Parse date from various formats."""
        if isinstance(date_value, date):
            return date_value
        if isinstance(date_value, datetime):
            return date_value.date()
        if isinstance(date_value, str):
            try:
                return datetime.fromisoformat(date_value.replace("/", "-")).date()
            except ValueError:
                return None
        return None

    def _get_reference_date(self, test_date_str: str | None) -> tuple[date, bool]:
        """Get reference date for validation.

        Returns:
            tuple: (reference_date, is_test_date) where is_test_date indicates
                   if we found the actual test date or fell back to today.
        """
        if test_date_str:
            parsed = self._parse_date(test_date_str)
            if parsed:
                return parsed, True
        return date.today(), False

    def _validate_expiration(
        self,
        findings: list[Finding],
        expiration: date,
        reference_date: date,
        is_test_date: bool,
    ) -> None:
        """Validate expiration against reference date (test date).

        Args:
            findings: List to append findings to.
            expiration: Calibration expiration date.
            reference_date: Test/inspection date to validate against.
            is_test_date: True if reference_date is from test, False if fallback to today.
        """
        config = self.config.calibration
        days_until_expiry = (expiration - reference_date).days

        # Format reference description for messages
        if is_test_date:
            ref_desc = f"test date ({reference_date})"
        else:
            ref_desc = f"today ({reference_date}) - WARNING: test date not found"

        if days_until_expiry < 0:
            # CRITICAL: Calibration was EXPIRED on test date
            self.add_finding(
                findings=findings,
                rule_id="CALIB-004",
                severity=ValidationSeverity.CRITICAL,
                message=(
                    f"Calibration EXPIRED: certificate expired on {expiration}, "
                    f"{abs(days_until_expiry)} days BEFORE {ref_desc}"
                ),
                field_path="calibration.expiration_date",
                extracted_value=str(expiration),
                threshold=f"Must be valid on test date",
                standard_reference="ISO/IEC 17025",
                remediation="Test performed with EXPIRED calibration. Results are INVALID. Re-test required with calibrated instrument.",
            )
        elif days_until_expiry == 0:
            # CRITICAL: Calibration expired on the SAME day as test
            self.add_finding(
                findings=findings,
                rule_id="CALIB-004",
                severity=ValidationSeverity.CRITICAL,
                message=(
                    f"Calibration EXPIRED on test date: certificate expired on {expiration}, "
                    f"same day as {ref_desc}"
                ),
                field_path="calibration.expiration_date",
                extracted_value=str(expiration),
                threshold=f"Must be valid on test date",
                standard_reference="ISO/IEC 17025",
                remediation="Test performed on calibration expiration date. Results may be invalid. Verify with calibration lab.",
            )
        elif days_until_expiry <= config.warn_days_before_expiry:
            # WARNING: Calibration was close to expiring on test date
            self.add_finding(
                findings=findings,
                rule_id="CALIB-005",
                severity=ValidationSeverity.MINOR,
                message=(
                    f"Calibration was {days_until_expiry} days from expiring on {ref_desc}. "
                    f"Expires on {expiration}"
                ),
                field_path="calibration.expiration_date",
                extracted_value=str(expiration),
                threshold=f"warn_days={config.warn_days_before_expiry}",
                standard_reference="ISO/IEC 17025",
                remediation="Calibration was near expiry during test. Consider scheduling recalibration.",
            )
        else:
            # INFO: Calibration was valid on test date
            self.add_finding(
                findings=findings,
                rule_id="CALIB-006",
                severity=ValidationSeverity.INFO,
                message=(
                    f"Calibration valid: {days_until_expiry} days remaining on {ref_desc}. "
                    f"Expires on {expiration}"
                ),
                field_path="calibration.expiration_date",
                extracted_value=str(expiration),
                threshold="Valid on test date",
                standard_reference="ISO/IEC 17025",
            )

    def validate(self, extraction: Any) -> ValidationResult:
        """Validate extraction's calibration info.

        Args:
            extraction: Any extraction result with calibration attribute.

        Returns:
            ValidationResult with calibration findings.
        """
        calibration = getattr(extraction, "calibration", None)
        test_conditions = getattr(extraction, "test_conditions", None)
        test_date = None

        # Try to get test date from test_conditions
        # Different test types use different field names:
        # - Grounding, Megger, FAT: test_date
        # - Thermography: inspection_date
        if test_conditions:
            # Try test_date first (grounding, megger, fat)
            if hasattr(test_conditions, "test_date") and test_conditions.test_date:
                test_date = test_conditions.test_date.value
            # Try inspection_date (thermography)
            elif hasattr(test_conditions, "inspection_date") and test_conditions.inspection_date:
                test_date = test_conditions.inspection_date.value

        findings = self.validate_calibration(calibration, test_date)
        equipment_tag = None
        if hasattr(extraction, "equipment"):
            equipment_tag = extraction.equipment.equipment_tag.value

        return self.create_result(findings, equipment_tag=equipment_tag)
