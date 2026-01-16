"""Grounding test validator.

Validates grounding resistance measurements against NETA ATS thresholds.
"""

from app.core.extraction.grounding import GroundingExtractionResult, GroundingMeasurement
from app.core.validation.base import BaseValidator
from app.core.validation.schemas import Finding, ValidationResult, ValidationSeverity
from app.schemas.enums import EquipmentType


class GroundingValidator(BaseValidator):
    """Validator for grounding resistance measurements."""

    @property
    def test_type(self) -> str:
        """Return test type identifier."""
        return "grounding"

    def validate(self, extraction: GroundingExtractionResult) -> ValidationResult:
        """Validate grounding extraction against NETA thresholds.

        Args:
            extraction: Grounding extraction result to validate.

        Returns:
            ValidationResult with findings.
        """
        findings: list[Finding] = []

        # Get equipment type for threshold lookup
        equipment_type = self._get_equipment_type(extraction)
        threshold = self.config.grounding.get_threshold(equipment_type)

        # Get equipment tag for result
        equipment_tag = extraction.equipment.equipment_tag.value

        # Validate each measurement
        for i, measurement in enumerate(extraction.measurements):
            self._validate_measurement(
                findings=findings,
                measurement=measurement,
                index=i,
                threshold=threshold,
            )

        return self.create_result(findings, equipment_tag=equipment_tag)

    def _get_equipment_type(
        self, extraction: GroundingExtractionResult
    ) -> EquipmentType | None:
        """Extract equipment type from extraction result."""
        try:
            type_value = extraction.equipment.equipment_type.value
            return EquipmentType(type_value) if type_value else None
        except (ValueError, AttributeError):
            return None

    def _validate_measurement(
        self,
        findings: list[Finding],
        measurement: GroundingMeasurement,
        index: int,
        threshold: float,
    ) -> None:
        """Validate single measurement against threshold."""
        resistance = measurement.resistance_value.value

        if not isinstance(resistance, (int, float)):
            self.add_finding(
                findings=findings,
                rule_id="GRND-001",
                severity=ValidationSeverity.MAJOR,
                message=f"Invalid resistance value: {resistance}",
                field_path=f"measurements[{index}].resistance_value",
                extracted_value=resistance,
                threshold=threshold,
                remediation="Verify resistance measurement is a valid number",
            )
            return

        resistance = float(resistance)

        if resistance > threshold:
            # Determine severity based on how far over threshold
            if resistance > threshold * 2:
                severity = ValidationSeverity.CRITICAL
            elif resistance > threshold * 1.5:
                severity = ValidationSeverity.MAJOR
            else:
                severity = ValidationSeverity.MINOR

            self.add_finding(
                findings=findings,
                rule_id="GRND-002",
                severity=severity,
                message=f"Grounding resistance {resistance:.2f}Ω exceeds threshold {threshold:.2f}Ω",
                field_path=f"measurements[{index}].resistance_value",
                extracted_value=resistance,
                threshold=threshold,
                standard_reference="NETA ATS Table 100.1",
                remediation="Investigate ground connection, consider adding ground rods",
            )
        else:
            self.add_finding(
                findings=findings,
                rule_id="GRND-003",
                severity=ValidationSeverity.INFO,
                message=f"Grounding resistance {resistance:.2f}Ω within threshold",
                field_path=f"measurements[{index}].resistance_value",
                extracted_value=resistance,
                threshold=threshold,
                standard_reference="NETA ATS Table 100.1",
            )
