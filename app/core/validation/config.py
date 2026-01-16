"""Externalized validation thresholds configuration.

This module provides validation thresholds per NETA/IEEE standards.
Thresholds are externalized for easy adjustment without code changes.

VALD-08: Validation rules are externalized in configuration (not hard-coded)
"""

from functools import lru_cache

from pydantic import BaseModel, Field

from app.schemas.enums import EquipmentType


class GroundingThresholds(BaseModel):
    """Grounding resistance thresholds per equipment type.

    Based on NETA ATS Table 100.1 and Microsoft CxPOR requirements.
    Values are maximum acceptable resistance in ohms.
    """

    general_max: float = 5.0  # General equipment
    data_center_max: float = 1.0  # Data center (Microsoft CxPOR)
    panel_max: float = 5.0
    ups_max: float = 1.0
    ats_max: float = 5.0
    gen_max: float = 5.0
    xfmr_max: float = 5.0

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
    """Insulation resistance thresholds per IEEE 43.

    IEEE 43 provides guidance on minimum acceptable insulation resistance
    values and polarization index requirements.
    """

    min_ir_megohms: float = 100.0  # Minimum 1-minute IR
    min_pi: float = 2.0  # Minimum Polarization Index
    min_ir_by_voltage: dict[int, float] = Field(
        default_factory=lambda: {
            500: 25.0,  # 500V test: min 25 MΩ
            1000: 100.0,  # 1000V test: min 100 MΩ
            2500: 500.0,  # 2500V test: min 500 MΩ
            5000: 1000.0,  # 5000V test: min 1000 MΩ
        }
    )

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


class ThermographyThresholds(BaseModel):
    """Temperature delta thresholds per NETA MTS.

    NETA MTS Table 100.18 provides delta-T classifications
    for thermographic inspections.
    """

    # Delta-T thresholds in Celsius
    normal_max: float = 5.0
    attention_max: float = 15.0
    intermediate_max: float = 35.0
    serious_max: float = 70.0
    # Above serious_max = CRITICAL

    def classify_delta(self, delta_t: float) -> str:
        """Classify temperature delta into severity category.

        Args:
            delta_t: Temperature difference in Celsius.

        Returns:
            str: Classification (normal, attention, intermediate, serious, critical).
        """
        if delta_t <= self.normal_max:
            return "normal"
        elif delta_t <= self.attention_max:
            return "attention"
        elif delta_t <= self.intermediate_max:
            return "intermediate"
        elif delta_t <= self.serious_max:
            return "serious"
        else:
            return "critical"


class CalibrationConfig(BaseModel):
    """Calibration certificate validation settings."""

    max_days_expired: int = 0  # 0 = no expired allowed
    warn_days_before_expiry: int = 30


class ValidationConfig(BaseModel):
    """Complete validation configuration.

    Aggregates all threshold configurations for easy access.
    """

    grounding: GroundingThresholds = Field(default_factory=GroundingThresholds)
    megger: MeggerThresholds = Field(default_factory=MeggerThresholds)
    thermography: ThermographyThresholds = Field(default_factory=ThermographyThresholds)
    calibration: CalibrationConfig = Field(default_factory=CalibrationConfig)


@lru_cache
def get_validation_config() -> ValidationConfig:
    """Get cached validation configuration.

    Uses lru_cache for determinism - same config every time.
    Future: Could load from YAML/JSON file.

    Returns:
        ValidationConfig: Validation configuration instance.
    """
    return ValidationConfig()
