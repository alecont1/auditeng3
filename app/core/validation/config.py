"""Externalized validation thresholds configuration.

This module provides validation thresholds per NETA/IEEE standards.
Thresholds are externalized for easy adjustment without code changes.

VALD-08: Validation rules are externalized in configuration (not hard-coded)
VALD-09: Same extraction can be validated against different standards
"""

from functools import lru_cache

from pydantic import BaseModel, Field

from app.core.validation.standards import (
    MICROSOFT_THRESHOLDS,
    NETA_THRESHOLDS,
    StandardProfile,
    get_standard_reference,
)
from app.schemas.enums import EquipmentType


class GroundingThresholds(BaseModel):
    """Grounding resistance thresholds per equipment type.

    Based on NETA ATS Table 100.1 and Microsoft CxPOR requirements.
    Values are maximum acceptable resistance in ohms.
    """

    # Ground resistance thresholds
    general_max: float = 5.0  # General equipment
    data_center_max: float = 5.0  # Data center (NETA default)
    panel_max: float = 5.0
    ups_max: float = 5.0
    ats_max: float = 5.0
    gen_max: float = 5.0
    xfmr_max: float = 5.0

    # Ground bond threshold
    ground_bond_max: float = 0.1  # Maximum ground bond resistance

    # Standard reference for audit traceability
    standard_reference: str = "NETA ATS-2025 Table 100.1"

    def get_threshold(self, equipment_type: EquipmentType | None) -> float:
        """Get threshold for specific equipment type.

        Args:
            equipment_type: Type of equipment being validated.

        Returns:
            float: Maximum acceptable resistance in ohms.
        """
        if equipment_type is None:
            return self.general_max

        thresholds = {
            EquipmentType.PANEL: self.panel_max,
            EquipmentType.UPS: self.ups_max,
            EquipmentType.ATS: self.ats_max,
            EquipmentType.GEN: self.gen_max,
            EquipmentType.XFMR: self.xfmr_max,
        }
        return thresholds.get(equipment_type, self.general_max)


class MeggerThresholds(BaseModel):
    """Insulation resistance thresholds per IEEE 43 and NETA ATS.

    IEEE 43 provides guidance on minimum acceptable insulation resistance
    values and polarization index requirements.
    """

    # IR thresholds
    min_ir_megohms: float = 100.0  # Minimum 1-minute IR (good)
    excellent_ir_megohms: float = 1000.0  # Excellent IR threshold

    # Polarization Index thresholds
    min_pi: float = 2.0  # Minimum Polarization Index (good)
    excellent_pi: float = 4.0  # Excellent PI threshold

    # Dielectric Absorption Ratio (60s/30s)
    min_dar: float = 1.25  # Minimum DAR

    min_ir_by_voltage: dict[int, float] = Field(
        default_factory=lambda: {
            500: 25.0,  # 500V test: min 25 MΩ
            1000: 100.0,  # 1000V test: min 100 MΩ
            2500: 500.0,  # 2500V test: min 500 MΩ
            5000: 1000.0,  # 5000V test: min 1000 MΩ
        }
    )

    # Standard reference for audit traceability
    standard_reference: str = "IEEE 43-2013 Section 12.3"

    def get_min_ir_for_voltage(self, test_voltage: int) -> float:
        """Get minimum IR for test voltage.

        Args:
            test_voltage: Test voltage in volts.

        Returns:
            float: Minimum acceptable IR in megohms.
        """
        # Find the closest voltage not exceeding test voltage
        applicable_voltages = [v for v in self.min_ir_by_voltage.keys() if v <= test_voltage]
        if not applicable_voltages:
            return self.min_ir_megohms
        return self.min_ir_by_voltage[max(applicable_voltages)]

    def classify_ir(self, ir_value: float) -> str:
        """Classify IR value.

        Args:
            ir_value: Insulation resistance in MΩ.

        Returns:
            str: Classification (excellent, good, fail).
        """
        if ir_value >= self.excellent_ir_megohms:
            return "excellent"
        elif ir_value >= self.min_ir_megohms:
            return "good"
        else:
            return "fail"

    def classify_pi(self, pi_value: float) -> str:
        """Classify Polarization Index.

        Args:
            pi_value: Polarization Index value.

        Returns:
            str: Classification (excellent, good, fail).
        """
        if pi_value >= self.excellent_pi:
            return "excellent"
        elif pi_value >= self.min_pi:
            return "good"
        else:
            return "fail"


class ThermographyThresholds(BaseModel):
    """Temperature delta thresholds per NETA MTS and Microsoft standards.

    Thresholds vary by standard:
    NETA MTS-2023:
    - ≤10°C: Normal
    - 11-25°C: Attention (monitor)
    - 26-40°C: Serious (schedule repair)
    - 41-50°C: Critical (urgent repair)
    - >50°C: Emergency (de-energize)

    Microsoft CxPOR (more restrictive):
    - ≤3°C: Normal
    - 4-10°C: Attention (monitor)
    - 11-20°C: Serious (schedule repair)
    - 21-30°C: Critical (urgent repair)
    - >30°C: Emergency (de-energize)
    """

    # Delta-T thresholds in Celsius (defaults to NETA)
    normal_max: float = 10.0
    attention_max: float = 25.0
    serious_max: float = 40.0
    critical_max: float = 50.0
    # Above critical_max = EMERGENCY

    # Standard reference for audit traceability
    standard_reference: str = "NETA MTS-2023 Table 100.18"

    def classify_delta(self, delta_t: float) -> str:
        """Classify temperature delta into severity category.

        Args:
            delta_t: Temperature difference in Celsius.

        Returns:
            str: Classification (normal, attention, serious, critical, emergency).
        """
        if delta_t <= self.normal_max:
            return "normal"
        elif delta_t <= self.attention_max:
            return "attention"
        elif delta_t <= self.serious_max:
            return "serious"
        elif delta_t <= self.critical_max:
            return "critical"
        else:
            return "emergency"


class CalibrationConfig(BaseModel):
    """Calibration certificate validation settings."""

    max_days_expired: int = 0  # 0 = no expired allowed
    warn_days_before_expiry: int = 30

    # Standard reference for audit traceability
    standard_reference: str = "NETA ATS-2025 Section 7.2"


class FATConfig(BaseModel):
    """FAT validation settings."""

    required_signatures: list[str] = Field(
        default_factory=lambda: ["manufacturer", "client"]
    )
    allow_pending_items: bool = False
    min_checklist_items: int = 1


class ComplementaryConfig(BaseModel):
    """Complementary validation settings.

    Thresholds for cross-validation rules that complement
    test-type specific validators. These validate consistency
    between different parts of the report (e.g., serial numbers
    on certificate vs photos, temperatures vs hygrometer readings).
    """

    # Serial number OCR confidence threshold
    # Below this = SERIAL_ILLEGIBLE (review flag, not blocker)
    serial_confidence_threshold: float = 0.7

    # Temperature match tolerance in Celsius
    # Reflected temp vs hygrometer reading can differ by this amount
    temp_match_tolerance: float = 2.0

    # SPEC compliance threshold (Microsoft standard)
    spec_delta_t_threshold: float = 10.0

    # Required keywords in COMMENTS section when delta > threshold
    spec_required_keywords: list[str] = Field(
        default_factory=lambda: [
            "terminals", "insulators", "torque", "conductors",
            "terminais", "isoladores", "torque", "condutores"  # Portuguese
        ]
    )

    # Standard reference for complementary validations
    standard_reference: str = "Microsoft SPEC 26 05 00"


class ValidationConfig(BaseModel):
    """Complete validation configuration.

    Aggregates all threshold configurations for easy access.
    Now supports multi-standard profiles (NETA, Microsoft).
    """

    grounding: GroundingThresholds = Field(default_factory=GroundingThresholds)
    megger: MeggerThresholds = Field(default_factory=MeggerThresholds)
    thermography: ThermographyThresholds = Field(default_factory=ThermographyThresholds)
    calibration: CalibrationConfig = Field(default_factory=CalibrationConfig)
    fat: FATConfig = Field(default_factory=FATConfig)
    complementary: ComplementaryConfig = Field(default_factory=ComplementaryConfig)

    # Active standard profile for this configuration
    active_standard: StandardProfile = StandardProfile.NETA


def get_config_for_standard(standard: StandardProfile) -> ValidationConfig:
    """Build validation config for a specific standard profile.

    Constructs a ValidationConfig instance with thresholds from the specified
    standard profile (NETA or MICROSOFT).

    Args:
        standard: Which standard profile to use.

    Returns:
        ValidationConfig with thresholds for the specified standard.
    """
    thresholds = NETA_THRESHOLDS if standard == StandardProfile.NETA else MICROSOFT_THRESHOLDS

    # Build GroundingThresholds from standard
    grounding_th = thresholds["grounding"]
    grounding = GroundingThresholds(
        general_max=grounding_th["general_max"].value,
        data_center_max=grounding_th["data_center_max"].value,
        panel_max=grounding_th["panel_max"].value,
        ups_max=grounding_th["ups_max"].value,
        ats_max=grounding_th["ats_max"].value,
        gen_max=grounding_th["gen_max"].value,
        xfmr_max=grounding_th["xfmr_max"].value,
        ground_bond_max=grounding_th["ground_bond_max"].value,
        standard_reference=get_standard_reference(standard, "grounding", "general_max"),
    )

    # Build MeggerThresholds from standard
    megger_th = thresholds["megger"]
    min_ir_by_voltage_value = megger_th["min_ir_by_voltage"].value
    # Ensure it's a dict[int, float]
    if isinstance(min_ir_by_voltage_value, dict):
        min_ir_by_voltage = {int(k): float(v) for k, v in min_ir_by_voltage_value.items()}
    else:
        min_ir_by_voltage = {500: 25.0, 1000: 100.0, 2500: 500.0, 5000: 1000.0}

    megger = MeggerThresholds(
        min_ir_megohms=megger_th["min_ir_megohms"].value,
        excellent_ir_megohms=megger_th["excellent_ir_megohms"].value,
        min_pi=megger_th["min_pi"].value,
        excellent_pi=megger_th["excellent_pi"].value,
        min_dar=megger_th["min_dar"].value,
        min_ir_by_voltage=min_ir_by_voltage,
        standard_reference=get_standard_reference(standard, "megger", "min_ir_megohms"),
    )

    # Build ThermographyThresholds from standard
    thermo_th = thresholds["thermography"]
    thermography = ThermographyThresholds(
        normal_max=thermo_th["normal_max"].value,
        attention_max=thermo_th["attention_max"].value,
        serious_max=thermo_th["serious_max"].value,
        critical_max=thermo_th["critical_max"].value,
        standard_reference=get_standard_reference(standard, "thermography", "normal_max"),
    )

    # Build CalibrationConfig from standard
    calib_th = thresholds["calibration"]
    calibration = CalibrationConfig(
        max_days_expired=calib_th["max_days_expired"].value,
        warn_days_before_expiry=calib_th["warn_days_before_expiry"].value,
        standard_reference=get_standard_reference(standard, "calibration", "max_days_expired"),
    )

    # ComplementaryConfig uses defaults for both NETA and Microsoft
    # These are cross-validation rules that apply regardless of standard
    complementary = ComplementaryConfig()

    return ValidationConfig(
        grounding=grounding,
        megger=megger,
        thermography=thermography,
        calibration=calibration,
        complementary=complementary,
        active_standard=standard,
    )


@lru_cache
def get_validation_config(standard: StandardProfile = StandardProfile.NETA) -> ValidationConfig:
    """Get cached validation configuration for specific standard.

    Uses lru_cache for determinism - same standard always returns same config.
    Cache is keyed by standard profile.

    Args:
        standard: Which standard profile to use (NETA or MICROSOFT).
                  Defaults to NETA for backward compatibility.

    Returns:
        ValidationConfig: Validation configuration instance for the standard.
    """
    return get_config_for_standard(standard)
