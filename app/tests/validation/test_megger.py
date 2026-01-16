"""Tests for MeggerValidator."""

import pytest
from app.core.extraction.schemas import EquipmentInfo, FieldConfidence, CalibrationInfo
from app.core.extraction.megger import (
    MeggerExtractionResult,
    MeggerMeasurement,
    MeggerTestConditions,
    InsulationReading,
)
from app.core.validation import MeggerValidator, ValidationSeverity


@pytest.fixture
def validator():
    """Create a MeggerValidator instance."""
    return MeggerValidator()


@pytest.fixture
def basic_equipment():
    """Create basic equipment info."""
    return EquipmentInfo(
        equipment_tag=FieldConfidence(value="XFMR-01", confidence=0.9),
        equipment_type=FieldConfidence(value="xfmr", confidence=0.9),
    )


@pytest.fixture
def basic_calibration():
    """Create basic calibration info."""
    return CalibrationInfo(
        expiration_date=FieldConfidence(value="2025-12-31", confidence=0.9),
    )


@pytest.fixture
def basic_test_conditions():
    """Create basic test conditions."""
    return MeggerTestConditions(
        test_date=FieldConfidence(value="2024-01-15", confidence=0.9),
    )


def create_measurement(ir_1min: float, ir_10min: float, voltage: int = 1000) -> MeggerMeasurement:
    """Helper to create a measurement with PI calculation."""
    measurement = MeggerMeasurement(
        circuit_id=FieldConfidence(value="Phase A-B", confidence=0.9),
        test_voltage=FieldConfidence(value=voltage, confidence=0.9),
        readings=[
            InsulationReading(time_seconds=60, resistance_value=FieldConfidence(value=ir_1min, confidence=0.9)),
            InsulationReading(time_seconds=600, resistance_value=FieldConfidence(value=ir_10min, confidence=0.9)),
        ],
    )
    return measurement


class TestMeggerValidator:
    """Tests for MeggerValidator."""

    def test_acceptable_pi(self, validator, basic_equipment, basic_calibration, basic_test_conditions):
        """Test that PI >= 2.0 produces INFO finding."""
        extraction = MeggerExtractionResult(
            equipment=basic_equipment,
            calibration=basic_calibration,
            test_conditions=basic_test_conditions,
            measurements=[
                create_measurement(ir_1min=500, ir_10min=1200),  # PI = 2.4
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        assert result.is_valid
        # Should have INFO finding for acceptable PI
        pi_info = [f for f in result.findings if "MEGG-003" in f.rule_id]
        assert len(pi_info) >= 1

    def test_excellent_pi(self, validator, basic_equipment, basic_calibration, basic_test_conditions):
        """Test that PI >= 4.0 is excellent."""
        extraction = MeggerExtractionResult(
            equipment=basic_equipment,
            calibration=basic_calibration,
            test_conditions=basic_test_conditions,
            measurements=[
                create_measurement(ir_1min=500, ir_10min=2500),  # PI = 5.0
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        assert result.is_valid
        assert result.critical_count == 0

    def test_low_pi_major(self, validator, basic_equipment, basic_calibration, basic_test_conditions):
        """Test that PI 1.5-2.0 produces MAJOR finding."""
        extraction = MeggerExtractionResult(
            equipment=basic_equipment,
            calibration=basic_calibration,
            test_conditions=basic_test_conditions,
            measurements=[
                create_measurement(ir_1min=500, ir_10min=850),  # PI = 1.7
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        major_findings = [f for f in result.findings if f.severity == ValidationSeverity.MAJOR]
        assert len(major_findings) >= 1

    def test_low_pi_critical(self, validator, basic_equipment, basic_calibration, basic_test_conditions):
        """Test that PI < 1.5 produces CRITICAL finding."""
        extraction = MeggerExtractionResult(
            equipment=basic_equipment,
            calibration=basic_calibration,
            test_conditions=basic_test_conditions,
            measurements=[
                create_measurement(ir_1min=500, ir_10min=600),  # PI = 1.2
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        assert not result.is_valid
        assert result.critical_count >= 1

    def test_acceptable_ir(self, validator, basic_equipment, basic_calibration, basic_test_conditions):
        """Test that IR >= min for voltage produces INFO finding."""
        extraction = MeggerExtractionResult(
            equipment=basic_equipment,
            calibration=basic_calibration,
            test_conditions=basic_test_conditions,
            measurements=[
                create_measurement(ir_1min=200, ir_10min=500, voltage=1000),  # 200MΩ >= 100MΩ for 1000V
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        ir_info = [f for f in result.findings if "MEGG-005" in f.rule_id]
        assert len(ir_info) >= 1

    def test_low_ir_major(self, validator, basic_equipment, basic_calibration, basic_test_conditions):
        """Test that low IR produces MAJOR finding."""
        extraction = MeggerExtractionResult(
            equipment=basic_equipment,
            calibration=basic_calibration,
            test_conditions=basic_test_conditions,
            measurements=[
                create_measurement(ir_1min=80, ir_10min=200, voltage=1000),  # 80MΩ < 100MΩ for 1000V
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        # Should have MAJOR finding for low IR
        ir_findings = [f for f in result.findings if "MEGG-004" in f.rule_id]
        assert len(ir_findings) >= 1

    def test_low_ir_critical(self, validator, basic_equipment, basic_calibration, basic_test_conditions):
        """Test that very low IR produces CRITICAL finding."""
        extraction = MeggerExtractionResult(
            equipment=basic_equipment,
            calibration=basic_calibration,
            test_conditions=basic_test_conditions,
            measurements=[
                create_measurement(ir_1min=40, ir_10min=80, voltage=1000),  # 40MΩ < 50MΩ (half of 100)
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        assert not result.is_valid  # Very low IR is critical

    def test_missing_pi_data(self, validator, basic_equipment, basic_calibration, basic_test_conditions):
        """Test that missing PI data produces MAJOR finding."""
        # Measurement with only 1-minute reading (no 10-minute)
        measurement = MeggerMeasurement(
            circuit_id=FieldConfidence(value="Phase A-B", confidence=0.9),
            test_voltage=FieldConfidence(value=1000, confidence=0.9),
            readings=[
                InsulationReading(time_seconds=60, resistance_value=FieldConfidence(value=500, confidence=0.9)),
            ],
        )

        extraction = MeggerExtractionResult(
            equipment=basic_equipment,
            calibration=basic_calibration,
            test_conditions=basic_test_conditions,
            measurements=[measurement],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        # Should have MAJOR finding for missing PI
        pi_findings = [f for f in result.findings if "MEGG-001" in f.rule_id]
        assert len(pi_findings) >= 1


class TestMeggerValidatorVoltageThresholds:
    """Test voltage-specific IR thresholds."""

    def test_500v_threshold(self, basic_equipment, basic_calibration, basic_test_conditions):
        """Test 500V test uses 25MΩ threshold."""
        validator = MeggerValidator()

        extraction = MeggerExtractionResult(
            equipment=basic_equipment,
            calibration=basic_calibration,
            test_conditions=basic_test_conditions,
            measurements=[
                create_measurement(ir_1min=30, ir_10min=70, voltage=500),  # 30MΩ >= 25MΩ
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        # Should pass for IR
        ir_info = [f for f in result.findings if "MEGG-005" in f.rule_id]
        assert len(ir_info) >= 1

    def test_5000v_threshold(self, basic_equipment, basic_calibration, basic_test_conditions):
        """Test 5000V test uses 1000MΩ threshold."""
        validator = MeggerValidator()

        extraction = MeggerExtractionResult(
            equipment=basic_equipment,
            calibration=basic_calibration,
            test_conditions=basic_test_conditions,
            measurements=[
                create_measurement(ir_1min=800, ir_10min=2000, voltage=5000),  # 800MΩ < 1000MΩ
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        # Should fail for IR
        ir_findings = [f for f in result.findings if "MEGG-004" in f.rule_id]
        assert len(ir_findings) >= 1
