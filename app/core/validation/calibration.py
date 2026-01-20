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

        reference_date = self._get_reference_date(test_date_str)
        self._validate_expiration(findings, expiration, reference_date)

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

    def _get_reference_date(self, test_date_str: str | None) -> date:
        """Get reference date for validation."""
        if test_date_str:
            parsed = self._parse_date(test_date_str)
            if parsed:
                return parsed
        return date.today()

    def _validate_expiration(
        self,
        findings: list[Finding],
        expiration: date,
        reference_date: date,
    ) -> None:
        """Validate expiration against reference date."""
        config = self.config.calibration
        days_until_expiry = (expiration - reference_date).days

        if days_until_expiry < 0:
            self.add_finding(
                findings=findings,
                rule_id="CALIB-004",
                severity=ValidationSeverity.CRITICAL,
                message=f"Calibration expired {abs(days_until_expiry)} days ago on {expiration}",
                field_path="calibration.expiration_date",
                extracted_value=str(expiration),
                threshold=f"max_days_expired={config.max_days_expired}",
                standard_reference="ISO/IEC 17025",
                remediation="Recalibrate instrument before use. Test results may be invalid.",
            )
        elif days_until_expiry == 0:
            # Special case: expires TODAY - needs immediate attention
            self.add_finding(
                findings=findings,
                rule_id="CALIB-005",
                severity=ValidationSeverity.MAJOR,
                message=f"Calibration expires TODAY ({expiration})",
                field_path="calibration.expiration_date",
                extracted_value=str(expiration),
                threshold=f"warn_days={config.warn_days_before_expiry}",
                standard_reference="ISO/IEC 17025",
                remediation="Calibration expires today. Schedule immediate recalibration.",
            )
        elif days_until_expiry <= config.warn_days_before_expiry:
            self.add_finding(
                findings=findings,
                rule_id="CALIB-005",
                severity=ValidationSeverity.MINOR,
                message=f"Calibration expires in {days_until_expiry} days on {expiration}",
                field_path="calibration.expiration_date",
                extracted_value=str(expiration),
                threshold=f"warn_days={config.warn_days_before_expiry}",
                standard_reference="ISO/IEC 17025",
                remediation="Schedule recalibration before expiration",
            )
        else:
            self.add_finding(
                findings=findings,
                rule_id="CALIB-006",
                severity=ValidationSeverity.INFO,
                message=f"Calibration valid until {expiration} ({days_until_expiry} days remaining)",
                field_path="calibration.expiration_date",
                extracted_value=str(expiration),
                threshold="Not expired",
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
        if test_conditions and hasattr(test_conditions, "test_date"):
            test_date = (
                test_conditions.test_date.value if test_conditions.test_date else None
            )

        findings = self.validate_calibration(calibration, test_date)
        equipment_tag = None
        if hasattr(extraction, "equipment"):
            equipment_tag = extraction.equipment.equipment_tag.value

        return self.create_result(findings, equipment_tag=equipment_tag)
