"""Cross-field validation.

Validates consistency across fields and presence of required data.
"""

from typing import Any

from app.core.validation.base import BaseValidator
from app.core.validation.schemas import Finding, ValidationResult, ValidationSeverity


class CrossFieldValidator(BaseValidator):
    """Validator for cross-field consistency checks."""

    @property
    def test_type(self) -> str:
        """Return test type identifier."""
        return "cross_field"

    def validate(self, extraction: Any) -> ValidationResult:
        """Validate cross-field consistency.

        Args:
            extraction: Any extraction result to validate.

        Returns:
            ValidationResult with findings.
        """
        findings: list[Finding] = []
        equipment_tag = None

        if hasattr(extraction, "equipment"):
            equipment_tag = extraction.equipment.equipment_tag.value

            if not equipment_tag or equipment_tag == "":
                self.add_finding(
                    findings=findings,
                    rule_id="CROSS-001",
                    severity=ValidationSeverity.MAJOR,
                    message="Equipment TAG is missing or empty",
                    field_path="equipment.equipment_tag",
                    extracted_value=equipment_tag,
                    threshold="Non-empty TAG required",
                    remediation="Verify equipment TAG is clearly visible in document",
                )

            eq_type = extraction.equipment.equipment_type.value
            if not eq_type:
                self.add_finding(
                    findings=findings,
                    rule_id="CROSS-002",
                    severity=ValidationSeverity.MINOR,
                    message="Equipment type not identified",
                    field_path="equipment.equipment_type",
                    extracted_value=eq_type,
                    threshold="Equipment type recommended",
                    remediation="Add equipment type for proper threshold selection",
                )

        self._validate_measurement_units(findings, extraction)

        return self.create_result(findings, equipment_tag=equipment_tag)

    def _validate_measurement_units(
        self, findings: list[Finding], extraction: Any
    ) -> None:
        """Validate that measurements have units."""
        if hasattr(extraction, "measurements"):
            for i, m in enumerate(extraction.measurements):
                if hasattr(m, "resistance_unit"):
                    if not m.resistance_unit:
                        self.add_finding(
                            findings=findings,
                            rule_id="CROSS-003",
                            severity=ValidationSeverity.MINOR,
                            message=f"Measurement {i} missing unit specification",
                            field_path=f"measurements[{i}].resistance_unit",
                            extracted_value=None,
                            threshold="Unit required (ohms, MΩ, etc.)",
                        )

        if hasattr(extraction, "hotspots"):
            for i, h in enumerate(extraction.hotspots):
                if h.max_temperature.value is None:
                    self.add_finding(
                        findings=findings,
                        rule_id="CROSS-004",
                        severity=ValidationSeverity.MAJOR,
                        message=f"Hotspot {i} missing max temperature",
                        field_path=f"hotspots[{i}].max_temperature",
                        extracted_value=None,
                        threshold="Temperature value required",
                    )
