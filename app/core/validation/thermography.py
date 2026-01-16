"""Thermography test validator.

Validates temperature deltas against NETA MTS and Microsoft Data Center thresholds.

Thresholds (Microsoft/NETA):
- ≤3°C: Normal
- 4-10°C: Attention (monitor)
- 11-20°C: Serious (schedule repair)
- 21-30°C: Critical (urgent repair)
- >30°C: Emergency (de-energize immediately)
"""

from app.core.extraction.thermography import (
    Hotspot,
    ThermographyExtractionResult,
)
from app.core.validation.base import BaseValidator
from app.core.validation.schemas import Finding, ValidationResult, ValidationSeverity


class ThermographyValidator(BaseValidator):
    """Validator for thermographic inspections per NETA MTS and Microsoft standards."""

    @property
    def test_type(self) -> str:
        """Return test type identifier."""
        return "thermography"

    def validate(self, extraction: ThermographyExtractionResult) -> ValidationResult:
        """Validate thermography extraction against thresholds.

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
                # standard_reference from config via _get_default_reference()
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

        # Map classification to validation severity
        severity_map = {
            "normal": ValidationSeverity.INFO,
            "attention": ValidationSeverity.MINOR,
            "serious": ValidationSeverity.MAJOR,
            "critical": ValidationSeverity.CRITICAL,
            "emergency": ValidationSeverity.CRITICAL,
        }

        classification = thermo_config.classify_delta(delta_t)
        validation_severity = severity_map.get(classification, ValidationSeverity.INFO)

        location = hotspot.location.value if hotspot.location else "Unknown"

        # Build threshold description based on new thresholds
        threshold_descs = {
            "normal": f"≤{thermo_config.normal_max}°C",
            "attention": f"{thermo_config.normal_max+1}-{thermo_config.attention_max}°C",
            "serious": f"{thermo_config.attention_max+1}-{thermo_config.serious_max}°C",
            "critical": f"{thermo_config.serious_max+1}-{thermo_config.critical_max}°C",
            "emergency": f">{thermo_config.critical_max}°C",
        }
        threshold_desc = threshold_descs.get(classification, "Unknown")

        # Messages aligned with Microsoft Data Center requirements
        messages = {
            "normal": f"Hotspot at {location}: ΔT={delta_t:.1f}°C - within normal range",
            "attention": f"Hotspot at {location}: ΔT={delta_t:.1f}°C - MONITOR: schedule inspection",
            "serious": f"Hotspot at {location}: ΔT={delta_t:.1f}°C - SERIOUS: schedule repair",
            "critical": f"Hotspot at {location}: ΔT={delta_t:.1f}°C - CRITICAL: urgent repair required",
            "emergency": f"Hotspot at {location}: ΔT={delta_t:.1f}°C - EMERGENCY: DE-ENERGIZE IMMEDIATELY",
        }

        remediation_map = {
            "normal": None,
            "attention": "Monitor and schedule inspection during next maintenance window",
            "serious": "Schedule repair within maintenance cycle",
            "critical": "Urgent repair required. Reduce load if possible.",
            "emergency": "DE-ENERGIZE IMMEDIATELY. Do not re-energize until repaired and re-inspected.",
        }

        # Rule ID based on classification
        rule_ids = {
            "normal": "THRM-NOR",
            "attention": "THRM-ATT",
            "serious": "THRM-SER",
            "critical": "THRM-CRI",
            "emergency": "THRM-EMR",
        }

        self.add_finding(
            findings=findings,
            rule_id=rule_ids.get(classification, "THRM-UNK"),
            severity=validation_severity,
            message=messages.get(classification, f"Hotspot at {location}: ΔT={delta_t:.1f}°C"),
            field_path=f"hotspots[{index}].delta_t",
            extracted_value=delta_t,
            threshold=threshold_desc,
            # standard_reference from config via _get_default_reference()
            remediation=remediation_map.get(classification),
        )
