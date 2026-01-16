"""Thermography test validator.

Validates temperature deltas against NETA MTS thresholds.
"""

from app.core.extraction.thermography import (
    Hotspot,
    ThermographyExtractionResult,
)
from app.core.validation.base import BaseValidator
from app.core.validation.schemas import Finding, ValidationResult, ValidationSeverity


class ThermographyValidator(BaseValidator):
    """Validator for thermographic inspections per NETA MTS."""

    @property
    def test_type(self) -> str:
        """Return test type identifier."""
        return "thermography"

    def validate(self, extraction: ThermographyExtractionResult) -> ValidationResult:
        """Validate thermography extraction against NETA MTS.

        Args:
            extraction: Thermography extraction result to validate.

        Returns:
            ValidationResult with findings.
        """
        findings: list[Finding] = []
        equipment_tag = extraction.equipment.equipment_tag.value

        if not extraction.hotspots:
            self.add_finding(
                findings=findings,
                rule_id="THRM-001",
                severity=ValidationSeverity.INFO,
                message="No thermal anomalies detected",
                field_path="hotspots",
                extracted_value=0,
                threshold="None expected",
                standard_reference="NETA MTS Table 100.18",
            )
        else:
            for i, hotspot in enumerate(extraction.hotspots):
                self._validate_hotspot(findings, hotspot, i)

        return self.create_result(findings, equipment_tag=equipment_tag)

    def _validate_hotspot(
        self,
        findings: list[Finding],
        hotspot: Hotspot,
        index: int,
    ) -> None:
        """Validate single hotspot delta-T."""
        delta_t = hotspot.delta_t
        thermo_config = self.config.thermography

        if delta_t is None:
            self.add_finding(
                findings=findings,
                rule_id="THRM-002",
                severity=ValidationSeverity.MAJOR,
                message="Unable to calculate temperature delta",
                field_path=f"hotspots[{index}].delta_t",
                extracted_value=None,
                threshold="Calculable delta-T required",
                remediation="Verify max and reference temperatures are present",
            )
            return

        severity_map = {
            "normal": ValidationSeverity.INFO,
            "attention": ValidationSeverity.MINOR,
            "intermediate": ValidationSeverity.MAJOR,
            "serious": ValidationSeverity.MAJOR,
            "critical": ValidationSeverity.CRITICAL,
        }

        classification = thermo_config.classify_delta(delta_t)
        validation_severity = severity_map.get(classification, ValidationSeverity.INFO)

        location = hotspot.location.value if hotspot.location else "Unknown"

        # Build threshold description
        threshold_descs = {
            "normal": f"≤{thermo_config.normal_max}°C",
            "attention": f"{thermo_config.normal_max}-{thermo_config.attention_max}°C",
            "intermediate": f"{thermo_config.attention_max}-{thermo_config.intermediate_max}°C",
            "serious": f"{thermo_config.intermediate_max}-{thermo_config.serious_max}°C",
            "critical": f">{thermo_config.serious_max}°C",
        }
        threshold_desc = threshold_descs.get(classification, "Unknown")

        messages = {
            "normal": f"Hotspot at {location}: ΔT={delta_t:.1f}°C - within normal range",
            "attention": f"Hotspot at {location}: ΔT={delta_t:.1f}°C - schedule repair at next opportunity",
            "intermediate": f"Hotspot at {location}: ΔT={delta_t:.1f}°C - schedule repair within 1 month",
            "serious": f"Hotspot at {location}: ΔT={delta_t:.1f}°C - repair immediately, reduce load if possible",
            "critical": f"Hotspot at {location}: ΔT={delta_t:.1f}°C - IMMEDIATE DE-ENERGIZATION REQUIRED",
        }

        remediation_map = {
            "normal": None,
            "attention": "Schedule repair during next maintenance window",
            "intermediate": "Plan corrective action within 30 days",
            "serious": "Immediate repair required. Consider load reduction until repaired.",
            "critical": "De-energize immediately. Do not re-energize until repaired.",
        }

        self.add_finding(
            findings=findings,
            rule_id=f"THRM-{classification.upper()[:3]}",
            severity=validation_severity,
            message=messages[classification],
            field_path=f"hotspots[{index}].delta_t",
            extracted_value=delta_t,
            threshold=threshold_desc,
            standard_reference="NETA MTS Table 100.18",
            remediation=remediation_map[classification],
        )
