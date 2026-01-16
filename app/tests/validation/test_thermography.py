"""Tests for ThermographyValidator."""

import pytest
from app.core.extraction.schemas import EquipmentInfo, FieldConfidence
from app.core.extraction.thermography import (
    ThermographyExtractionResult,
    Hotspot,
    ThermalImageData,
    ThermographyTestConditions,
)
from app.core.validation import ThermographyValidator, ValidationSeverity


@pytest.fixture
def validator():
    """Create a ThermographyValidator instance."""
    return ThermographyValidator()


@pytest.fixture
def basic_equipment():
    """Create basic equipment info."""
    return EquipmentInfo(
        equipment_tag=FieldConfidence(value="QD-01", confidence=0.9),
        equipment_type=FieldConfidence(value="panel", confidence=0.9),
    )


@pytest.fixture
def basic_test_conditions():
    """Create basic test conditions."""
    return ThermographyTestConditions(
        inspection_date=FieldConfidence(value="2024-01-15", confidence=0.9),
    )


@pytest.fixture
def basic_thermal_data():
    """Create basic thermal data."""
    return ThermalImageData()


def create_hotspot(max_temp: float, ref_temp: float, location: str = "Breaker 1") -> Hotspot:
    """Helper to create a hotspot."""
    return Hotspot(
        location=FieldConfidence(value=location, confidence=0.9),
        max_temperature=FieldConfidence(value=max_temp, confidence=0.9),
        reference_temperature=FieldConfidence(value=ref_temp, confidence=0.9),
    )


class TestThermographyValidator:
    """Tests for ThermographyValidator with Microsoft thresholds."""

    def test_no_hotspots(self, validator, basic_equipment, basic_test_conditions, basic_thermal_data):
        """Test that no hotspots produces INFO finding."""
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=basic_test_conditions,
            thermal_data=basic_thermal_data,
            hotspots=[],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        assert result.is_valid
        assert result.critical_count == 0
        # Should have INFO finding for no anomalies
        info_findings = [f for f in result.findings if f.severity == ValidationSeverity.INFO]
        assert len(info_findings) >= 1

    def test_normal_delta(self, validator, basic_equipment, basic_test_conditions, basic_thermal_data):
        """Test ΔT ≤ 3°C is NORMAL."""
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=basic_test_conditions,
            thermal_data=basic_thermal_data,
            hotspots=[
                create_hotspot(max_temp=28.0, ref_temp=26.0),  # ΔT = 2°C
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        assert result.is_valid
        info_findings = [f for f in result.findings if f.severity == ValidationSeverity.INFO]
        assert len(info_findings) >= 1
        assert any("THRM-NOR" in f.rule_id for f in result.findings)

    def test_attention_delta(self, validator, basic_equipment, basic_test_conditions, basic_thermal_data):
        """Test ΔT 4-10°C is ATTENTION (MINOR)."""
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=basic_test_conditions,
            thermal_data=basic_thermal_data,
            hotspots=[
                create_hotspot(max_temp=35.0, ref_temp=28.0),  # ΔT = 7°C
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        assert result.is_valid  # MINOR doesn't invalidate
        minor_findings = [f for f in result.findings if f.severity == ValidationSeverity.MINOR]
        assert len(minor_findings) >= 1
        assert any("THRM-ATT" in f.rule_id for f in result.findings)

    def test_serious_delta(self, validator, basic_equipment, basic_test_conditions, basic_thermal_data):
        """Test ΔT 11-20°C is SERIOUS (MAJOR)."""
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=basic_test_conditions,
            thermal_data=basic_thermal_data,
            hotspots=[
                create_hotspot(max_temp=45.0, ref_temp=30.0),  # ΔT = 15°C
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        major_findings = [f for f in result.findings if f.severity == ValidationSeverity.MAJOR]
        assert len(major_findings) >= 1
        assert any("THRM-SER" in f.rule_id for f in result.findings)

    def test_critical_delta(self, validator, basic_equipment, basic_test_conditions, basic_thermal_data):
        """Test ΔT 21-30°C is CRITICAL."""
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=basic_test_conditions,
            thermal_data=basic_thermal_data,
            hotspots=[
                create_hotspot(max_temp=55.0, ref_temp=30.0),  # ΔT = 25°C
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        assert not result.is_valid
        critical_findings = [f for f in result.findings if f.severity == ValidationSeverity.CRITICAL]
        assert len(critical_findings) >= 1
        assert any("THRM-CRI" in f.rule_id for f in result.findings)

    def test_emergency_delta(self, validator, basic_equipment, basic_test_conditions, basic_thermal_data):
        """Test ΔT > 30°C is EMERGENCY."""
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=basic_test_conditions,
            thermal_data=basic_thermal_data,
            hotspots=[
                create_hotspot(max_temp=70.0, ref_temp=30.0),  # ΔT = 40°C
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        assert not result.is_valid
        critical_findings = [f for f in result.findings if f.severity == ValidationSeverity.CRITICAL]
        assert len(critical_findings) >= 1
        assert any("THRM-EMR" in f.rule_id for f in result.findings)
        # Check for emergency message
        emergency_finding = next(f for f in result.findings if "THRM-EMR" in f.rule_id)
        assert "DE-ENERGIZE IMMEDIATELY" in emergency_finding.message

    def test_multiple_hotspots(self, validator, basic_equipment, basic_test_conditions, basic_thermal_data):
        """Test validation with multiple hotspots."""
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=basic_test_conditions,
            thermal_data=basic_thermal_data,
            hotspots=[
                create_hotspot(max_temp=28.0, ref_temp=26.0, location="Point 1"),  # Normal
                create_hotspot(max_temp=40.0, ref_temp=28.0, location="Point 2"),  # Serious
                create_hotspot(max_temp=60.0, ref_temp=30.0, location="Point 3"),  # Critical
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        assert not result.is_valid  # Critical invalidates
        assert result.critical_count >= 1
        assert len(result.findings) >= 3

    def test_missing_delta(self, validator, basic_equipment, basic_test_conditions, basic_thermal_data):
        """Test that missing delta-T produces MAJOR finding."""
        # Create hotspot with invalid temps that won't calculate delta
        hotspot = Hotspot(
            location=FieldConfidence(value="Unknown", confidence=0.9),
            max_temperature=FieldConfidence(value=None, confidence=0.9),
            reference_temperature=FieldConfidence(value=30.0, confidence=0.9),
        )

        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=basic_test_conditions,
            thermal_data=basic_thermal_data,
            hotspots=[hotspot],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        major_findings = [f for f in result.findings if f.severity == ValidationSeverity.MAJOR]
        assert len(major_findings) >= 1
        assert any("THRM-002" in f.rule_id for f in result.findings)


class TestThermographyThresholdBoundaries:
    """Test exact threshold boundaries."""

    def test_exactly_3_degrees(self, basic_equipment, basic_test_conditions, basic_thermal_data):
        """Test exactly 3°C is NORMAL (≤3)."""
        validator = ThermographyValidator()
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=basic_test_conditions,
            thermal_data=basic_thermal_data,
            hotspots=[create_hotspot(max_temp=33.0, ref_temp=30.0)],  # Exactly 3°C
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        assert any("THRM-NOR" in f.rule_id for f in result.findings)

    def test_exactly_10_degrees(self, basic_equipment, basic_test_conditions, basic_thermal_data):
        """Test exactly 10°C is ATTENTION (≤10)."""
        validator = ThermographyValidator()
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=basic_test_conditions,
            thermal_data=basic_thermal_data,
            hotspots=[create_hotspot(max_temp=40.0, ref_temp=30.0)],  # Exactly 10°C
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        assert any("THRM-ATT" in f.rule_id for f in result.findings)

    def test_exactly_30_degrees(self, basic_equipment, basic_test_conditions, basic_thermal_data):
        """Test exactly 30°C is CRITICAL (≤30)."""
        validator = ThermographyValidator()
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=basic_test_conditions,
            thermal_data=basic_thermal_data,
            hotspots=[create_hotspot(max_temp=60.0, ref_temp=30.0)],  # Exactly 30°C
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        assert any("THRM-CRI" in f.rule_id for f in result.findings)

    def test_31_degrees_emergency(self, basic_equipment, basic_test_conditions, basic_thermal_data):
        """Test 31°C (>30) is EMERGENCY."""
        validator = ThermographyValidator()
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=basic_test_conditions,
            thermal_data=basic_thermal_data,
            hotspots=[create_hotspot(max_temp=61.0, ref_temp=30.0)],  # 31°C
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        assert any("THRM-EMR" in f.rule_id for f in result.findings)
