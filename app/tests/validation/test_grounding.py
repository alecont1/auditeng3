"""Tests for GroundingValidator."""

import pytest
from app.core.extraction.schemas import EquipmentInfo, FieldConfidence
from app.core.extraction.grounding import (
    GroundingExtractionResult,
    GroundingMeasurement,
    GroundingTestConditions,
)
from app.core.validation import GroundingValidator, ValidationSeverity


@pytest.fixture
def validator():
    """Create a GroundingValidator instance."""
    return GroundingValidator()


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
    return GroundingTestConditions(
        test_date=FieldConfidence(value="2024-01-15", confidence=0.9),
    )


class TestGroundingValidator:
    """Tests for GroundingValidator."""

    def test_resistance_within_threshold(self, validator, basic_equipment, basic_test_conditions):
        """Test that resistance within threshold produces INFO finding."""
        extraction = GroundingExtractionResult(
            equipment=basic_equipment,
            test_conditions=basic_test_conditions,
            measurements=[
                GroundingMeasurement(
                    test_point=FieldConfidence(value="Main Ground", confidence=0.9),
                    resistance_value=FieldConfidence(value=2.5, confidence=0.9),
                )
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        assert result.is_valid
        assert result.critical_count == 0
        # Should have INFO finding for passing measurement
        info_findings = [f for f in result.findings if f.severity == ValidationSeverity.INFO]
        assert len(info_findings) >= 1

    def test_resistance_exceeds_threshold_minor(self, validator, basic_equipment, basic_test_conditions):
        """Test that resistance slightly over threshold produces MINOR finding."""
        extraction = GroundingExtractionResult(
            equipment=basic_equipment,
            test_conditions=basic_test_conditions,
            measurements=[
                GroundingMeasurement(
                    test_point=FieldConfidence(value="Main Ground", confidence=0.9),
                    resistance_value=FieldConfidence(value=6.0, confidence=0.9),  # >5Ω but <7.5Ω
                )
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        assert result.is_valid  # MINOR doesn't invalidate
        minor_findings = [f for f in result.findings if f.severity == ValidationSeverity.MINOR]
        assert len(minor_findings) >= 1

    def test_resistance_exceeds_threshold_major(self, validator, basic_equipment, basic_test_conditions):
        """Test that resistance well over threshold produces MAJOR finding."""
        extraction = GroundingExtractionResult(
            equipment=basic_equipment,
            test_conditions=basic_test_conditions,
            measurements=[
                GroundingMeasurement(
                    test_point=FieldConfidence(value="Main Ground", confidence=0.9),
                    resistance_value=FieldConfidence(value=8.0, confidence=0.9),  # >7.5Ω but <10Ω
                )
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        major_findings = [f for f in result.findings if f.severity == ValidationSeverity.MAJOR]
        assert len(major_findings) >= 1

    def test_resistance_exceeds_threshold_critical(self, validator, basic_equipment, basic_test_conditions):
        """Test that resistance way over threshold produces CRITICAL finding."""
        extraction = GroundingExtractionResult(
            equipment=basic_equipment,
            test_conditions=basic_test_conditions,
            measurements=[
                GroundingMeasurement(
                    test_point=FieldConfidence(value="Main Ground", confidence=0.9),
                    resistance_value=FieldConfidence(value=15.0, confidence=0.9),  # >10Ω (2x threshold)
                )
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        assert not result.is_valid  # CRITICAL invalidates
        assert result.critical_count >= 1

    def test_invalid_resistance_value(self, validator, basic_equipment, basic_test_conditions):
        """Test that non-numeric resistance value produces MAJOR finding."""
        extraction = GroundingExtractionResult(
            equipment=basic_equipment,
            test_conditions=basic_test_conditions,
            measurements=[
                GroundingMeasurement(
                    test_point=FieldConfidence(value="Main Ground", confidence=0.9),
                    resistance_value=FieldConfidence(value="N/A", confidence=0.9),  # Invalid
                )
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        major_findings = [f for f in result.findings if f.severity == ValidationSeverity.MAJOR]
        assert len(major_findings) >= 1
        assert "GRND-001" in [f.rule_id for f in result.findings]

    def test_multiple_measurements(self, validator, basic_equipment, basic_test_conditions):
        """Test validation with multiple measurements."""
        extraction = GroundingExtractionResult(
            equipment=basic_equipment,
            test_conditions=basic_test_conditions,
            measurements=[
                GroundingMeasurement(
                    test_point=FieldConfidence(value="Point 1", confidence=0.9),
                    resistance_value=FieldConfidence(value=1.5, confidence=0.9),  # Good
                ),
                GroundingMeasurement(
                    test_point=FieldConfidence(value="Point 2", confidence=0.9),
                    resistance_value=FieldConfidence(value=12.0, confidence=0.9),  # Critical
                ),
                GroundingMeasurement(
                    test_point=FieldConfidence(value="Point 3", confidence=0.9),
                    resistance_value=FieldConfidence(value=3.0, confidence=0.9),  # Good
                ),
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        assert not result.is_valid  # One CRITICAL invalidates
        assert result.critical_count >= 1
        # Should have findings for all measurements
        assert len(result.findings) >= 3


class TestGroundingValidatorEquipmentThresholds:
    """Test equipment-specific threshold selection."""

    def test_ups_threshold(self, basic_test_conditions):
        """Test that UPS uses 1.0Ω threshold."""
        validator = GroundingValidator()
        equipment = EquipmentInfo(
            equipment_tag=FieldConfidence(value="UPS-01", confidence=0.9),
            equipment_type=FieldConfidence(value="ups", confidence=0.9),
        )

        extraction = GroundingExtractionResult(
            equipment=equipment,
            test_conditions=basic_test_conditions,
            measurements=[
                GroundingMeasurement(
                    test_point=FieldConfidence(value="Main", confidence=0.9),
                    resistance_value=FieldConfidence(value=1.5, confidence=0.9),  # >1.0Ω for UPS
                )
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        # 1.5Ω should be MINOR for UPS (>1.0 but <1.5)
        minor_findings = [f for f in result.findings if f.severity == ValidationSeverity.MINOR]
        assert len(minor_findings) >= 1

    def test_panel_threshold(self, basic_test_conditions):
        """Test that Panel uses 5.0Ω threshold."""
        validator = GroundingValidator()
        equipment = EquipmentInfo(
            equipment_tag=FieldConfidence(value="PNL-01", confidence=0.9),
            equipment_type=FieldConfidence(value="panel", confidence=0.9),
        )

        extraction = GroundingExtractionResult(
            equipment=equipment,
            test_conditions=basic_test_conditions,
            measurements=[
                GroundingMeasurement(
                    test_point=FieldConfidence(value="Main", confidence=0.9),
                    resistance_value=FieldConfidence(value=4.0, confidence=0.9),  # <5.0Ω for Panel
                )
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction)

        assert result.is_valid
        # Should have INFO finding for passing value
        info_findings = [f for f in result.findings if f.severity == ValidationSeverity.INFO]
        assert len(info_findings) >= 1
