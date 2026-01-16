"""Megger (insulation resistance) test validator.

Validates insulation resistance per IEEE 43 standards.
"""

from app.core.extraction.megger import MeggerExtractionResult, MeggerMeasurement
from app.core.validation.base import BaseValidator
from app.core.validation.schemas import Finding, ValidationResult, ValidationSeverity


class MeggerValidator(BaseValidator):
    """Validator for insulation resistance (Megger) tests per IEEE 43."""

    @property
    def test_type(self) -> str:
        """Return test type identifier."""
        return "megger"

    def validate(self, extraction: MeggerExtractionResult) -> ValidationResult:
        """Validate Megger extraction against IEEE 43.

        Args:
            extraction: Megger extraction result to validate.

        Returns:
            ValidationResult with findings.
        """
        findings: list[Finding] = []
        equipment_tag = extraction.equipment.equipment_tag.value

        for i, measurement in enumerate(extraction.measurements):
            self._validate_polarization_index(findings, measurement, i)
            self._validate_insulation_resistance(findings, measurement, i)

        return self.create_result(findings, equipment_tag=equipment_tag)

    def _validate_polarization_index(
        self,
        findings: list[Finding],
        measurement: MeggerMeasurement,
        index: int,
    ) -> None:
        """Validate Polarization Index >= 2.0 per IEEE 43."""
        pi = measurement.polarization_index
        min_pi = self.config.megger.min_pi

        if pi is None:
            self.add_finding(
                findings=findings,
                rule_id="MEGG-001",
                severity=ValidationSeverity.MAJOR,
                message="Polarization Index not calculated (missing 1min or 10min reading)",
                field_path=f"measurements[{index}].polarization_index",
                extracted_value=None,
                threshold=min_pi,
                # standard_reference from config via _get_default_reference()
                remediation="Ensure 1-minute and 10-minute readings are recorded",
            )
            return

        if pi < min_pi:
            severity = ValidationSeverity.CRITICAL if pi < 1.5 else ValidationSeverity.MAJOR
            self.add_finding(
                findings=findings,
                rule_id="MEGG-002",
                severity=severity,
                message=f"Polarization Index {pi:.2f} below minimum {min_pi}",
                field_path=f"measurements[{index}].polarization_index",
                extracted_value=pi,
                threshold=min_pi,
                # standard_reference from config via _get_default_reference()
                remediation="Insulation may be contaminated or degraded. Investigate cause.",
            )
        else:
            self.add_finding(
                findings=findings,
                rule_id="MEGG-003",
                severity=ValidationSeverity.INFO,
                message=f"Polarization Index {pi:.2f} acceptable",
                field_path=f"measurements[{index}].polarization_index",
                extracted_value=pi,
                threshold=min_pi,
                # standard_reference from config via _get_default_reference()
            )

    def _validate_insulation_resistance(
        self,
        findings: list[Finding],
        measurement: MeggerMeasurement,
        index: int,
    ) -> None:
        """Validate IR against voltage-based thresholds."""
        ir_value = measurement.ir_1min
        test_voltage = measurement.test_voltage.value

        if ir_value is None:
            return  # Already flagged in PI validation

        if not isinstance(test_voltage, (int, float)):
            return

        min_ir = self.config.megger.get_min_ir_for_voltage(int(test_voltage))

        if ir_value < min_ir:
            severity = (
                ValidationSeverity.CRITICAL
                if ir_value < min_ir * 0.5
                else ValidationSeverity.MAJOR
            )
            self.add_finding(
                findings=findings,
                rule_id="MEGG-004",
                severity=severity,
                message=f"Insulation resistance {ir_value:.1f}MΩ below minimum {min_ir}MΩ for {test_voltage}V test",
                field_path=f"measurements[{index}].ir_1min",
                extracted_value=ir_value,
                threshold=min_ir,
                # standard_reference from config via _get_default_reference()
                remediation="Low insulation resistance indicates degradation. Investigate moisture, contamination, or aging.",
            )
        else:
            self.add_finding(
                findings=findings,
                rule_id="MEGG-005",
                severity=ValidationSeverity.INFO,
                message=f"Insulation resistance {ir_value:.1f}MΩ acceptable for {test_voltage}V test",
                field_path=f"measurements[{index}].ir_1min",
                extracted_value=ir_value,
                threshold=min_ir,
                # standard_reference from config via _get_default_reference()
            )
