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

    # Ground resistance thresholds
    general_max: float = 5.0  # General equipment
    data_center_max: float = 1.0  # Data center (Microsoft CxPOR)
    panel_max: float = 5.0
    ups_max: float = 1.0
    ats_max: float = 5.0
    gen_max: float = 5.0
    xfmr_max: float = 5.0

    # Ground bond threshold
    ground_bond_max: float = 0.1  # Maximum ground bond resistance

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

    Updated thresholds based on Microsoft Data Center requirements:
    - ≤3°C: Normal
    - 4-10°C: Attention (monitor)
    - 11-20°C: Serious (schedule repair)
    - 21-30°C: Critical (urgent repair)
    - >30°C: Emergency (de-energize)
    """

    # Delta-T thresholds in Celsius (Microsoft/NETA standards)
    normal_max: float = 3.0
    attention_max: float = 10.0
    serious_max: float = 20.0
    critical_max: float = 30.0
    # Above critical_max = EMERGENCY

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


class FATConfig(BaseModel):
    """FAT validation settings."""

    required_signatures: list[str] = Field(
        default_factory=lambda: ["manufacturer", "client"]
    )
    allow_pending_items: bool = False
    min_checklist_items: int = 1


class ValidationConfig(BaseModel):
    """Complete validation configuration.

    Aggregates all threshold configurations for easy access.
    """

    grounding: GroundingThresholds = Field(default_factory=GroundingThresholds)
    megger: MeggerThresholds = Field(default_factory=MeggerThresholds)
    thermography: ThermographyThresholds = Field(default_factory=ThermographyThresholds)
    calibration: CalibrationConfig = Field(default_factory=CalibrationConfig)
    fat: FATConfig = Field(default_factory=FATConfig)


@lru_cache
def get_validation_config() -> ValidationConfig:
    """Get cached validation configuration.

    Uses lru_cache for determinism - same config every time.
    Future: Could load from YAML/JSON file.

    Returns:
        ValidationConfig: Validation configuration instance.
    """
    return ValidationConfig()
