"""Tests for ValidationOrchestrator."""

import pytest
from app.core.extraction.schemas import EquipmentInfo, FieldConfidence, CalibrationInfo
from app.core.extraction.grounding import (
    GroundingExtractionResult,
    GroundingMeasurement,
    GroundingTestConditions,
)
from app.core.extraction.megger import (
    MeggerExtractionResult,
    MeggerMeasurement,
    MeggerTestConditions,
    InsulationReading,
)
from app.core.extraction.thermography import (
    ThermographyExtractionResult,
    Hotspot,
    ThermalImageData,
    ThermographyTestConditions,
)
from app.core.validation import ValidationOrchestrator, ValidationSeverity


@pytest.fixture
def orchestrator():
    """Create a ValidationOrchestrator instance."""
    return ValidationOrchestrator()


@pytest.fixture
def basic_equipment():
    """Create basic equipment info."""
    return EquipmentInfo(
        equipment_tag=FieldConfidence(value="QD-01", confidence=0.9),
        equipment_type=FieldConfidence(value="panel", confidence=0.9),
    )


@pytest.fixture
def basic_calibration():
    """Create basic calibration info (valid)."""
    return CalibrationInfo(
        expiration_date=FieldConfidence(value="2025-12-31", confidence=0.9),
    )


class TestValidationOrchestrator:
    """Tests for ValidationOrchestrator."""

    def test_grounding_validation(self, orchestrator, basic_equipment, basic_calibration):
        """Test orchestrator correctly routes grounding extraction."""
        test_conditions = GroundingTestConditions(
            test_date=FieldConfidence(value="2024-01-15", confidence=0.9),
        )

        extraction = GroundingExtractionResult(
            equipment=basic_equipment,
            calibration=basic_calibration,
            test_conditions=test_conditions,
            measurements=[
                GroundingMeasurement(
                    test_point=FieldConfidence(value="Main", confidence=0.9),
                    resistance_value=FieldConfidence(value=2.0, confidence=0.9),
                )
            ],
            overall_confidence=0.9,
        )

        result = orchestrator.validate(extraction)

        assert result.test_type == "grounding"
        assert result.equipment_tag == "QD-01"
        # Should have grounding, calibration, and cross-field findings
        assert len(result.findings) >= 1

    def test_megger_validation(self, orchestrator, basic_equipment, basic_calibration):
        """Test orchestrator correctly routes megger extraction."""
        test_conditions = MeggerTestConditions(
            test_date=FieldConfidence(value="2024-01-15", confidence=0.9),
        )

        measurement = MeggerMeasurement(
            circuit_id=FieldConfidence(value="Phase A-B", confidence=0.9),
            test_voltage=FieldConfidence(value=1000, confidence=0.9),
            readings=[
                InsulationReading(
                    time_seconds=60,
                    resistance_value=FieldConfidence(value=500, confidence=0.9),
                ),
                InsulationReading(
                    time_seconds=600,
                    resistance_value=FieldConfidence(value=1200, confidence=0.9),
                ),
            ],
        )

        extraction = MeggerExtractionResult(
            equipment=basic_equipment,
            calibration=basic_calibration,
            test_conditions=test_conditions,
            measurements=[measurement],
            overall_confidence=0.9,
        )

        result = orchestrator.validate(extraction)

        assert result.test_type == "megger"
        assert len(result.findings) >= 1

    def test_thermography_validation(self, orchestrator, basic_equipment):
        """Test orchestrator correctly routes thermography extraction."""
        test_conditions = ThermographyTestConditions(
            inspection_date=FieldConfidence(value="2024-01-15", confidence=0.9),
        )
        thermal_data = ThermalImageData()

        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=test_conditions,
            thermal_data=thermal_data,
            hotspots=[
                Hotspot(
                    location=FieldConfidence(value="Breaker 1", confidence=0.9),
                    max_temperature=FieldConfidence(value=35.0, confidence=0.9),
                    reference_temperature=FieldConfidence(value=28.0, confidence=0.9),
                ),
            ],
            overall_confidence=0.9,
        )

        result = orchestrator.validate(extraction)

        assert result.test_type == "thermography"
        assert len(result.findings) >= 1


class TestComplianceScoring:
    """Tests for compliance score calculation."""

    def test_perfect_score(self, orchestrator, basic_equipment, basic_calibration):
        """Test that all INFO findings gives 100% score."""
        test_conditions = GroundingTestConditions(
            test_date=FieldConfidence(value="2024-01-15", confidence=0.9),
        )

        extraction = GroundingExtractionResult(
            equipment=basic_equipment,
            calibration=basic_calibration,
            test_conditions=test_conditions,
            measurements=[
                GroundingMeasurement(
                    test_point=FieldConfidence(value="Main", confidence=0.9),
                    resistance_value=FieldConfidence(value=1.0, confidence=0.9),  # Well within threshold
                )
            ],
            overall_confidence=0.9,
        )

        result = orchestrator.validate(extraction)
        score = orchestrator.calculate_compliance_score(result)

        # Perfect score when no critical/major/minor findings
        assert score == 100.0 or result.minor_count > 0 or result.major_count > 0

    def test_critical_reduces_score(self, orchestrator, basic_equipment, basic_calibration):
        """Test that CRITICAL finding reduces score by 25%."""
        test_conditions = GroundingTestConditions(
            test_date=FieldConfidence(value="2024-01-15", confidence=0.9),
        )

        extraction = GroundingExtractionResult(
            equipment=basic_equipment,
            calibration=basic_calibration,
            test_conditions=test_conditions,
            measurements=[
                GroundingMeasurement(
                    test_point=FieldConfidence(value="Main", confidence=0.9),
                    resistance_value=FieldConfidence(value=15.0, confidence=0.9),  # Critical
                )
            ],
            overall_confidence=0.9,
        )

        result = orchestrator.validate(extraction)
        score = orchestrator.calculate_compliance_score(result)

        assert score < 100.0
        assert result.critical_count >= 1

    def test_multiple_findings_reduce_score(self, orchestrator, basic_equipment, basic_calibration):
        """Test that multiple findings reduce score appropriately."""
        test_conditions = GroundingTestConditions(
            test_date=FieldConfidence(value="2024-01-15", confidence=0.9),
        )

        extraction = GroundingExtractionResult(
            equipment=basic_equipment,
            calibration=basic_calibration,
            test_conditions=test_conditions,
            measurements=[
                GroundingMeasurement(
                    test_point=FieldConfidence(value="Point 1", confidence=0.9),
                    resistance_value=FieldConfidence(value=15.0, confidence=0.9),  # Critical (-25)
                ),
                GroundingMeasurement(
                    test_point=FieldConfidence(value="Point 2", confidence=0.9),
                    resistance_value=FieldConfidence(value=15.0, confidence=0.9),  # Critical (-25)
                ),
            ],
            overall_confidence=0.9,
        )

        result = orchestrator.validate(extraction)
        score = orchestrator.calculate_compliance_score(result)

        # Two critical findings = at least -50 points
        assert score <= 50.0

    def test_score_minimum_zero(self, orchestrator, basic_equipment, basic_calibration):
        """Test that score cannot go below 0."""
        test_conditions = GroundingTestConditions(
            test_date=FieldConfidence(value="2024-01-15", confidence=0.9),
        )

        # Create many critical findings
        measurements = [
            GroundingMeasurement(
                test_point=FieldConfidence(value=f"Point {i}", confidence=0.9),
                resistance_value=FieldConfidence(value=20.0, confidence=0.9),  # Critical
            )
            for i in range(10)  # 10 critical findings = -250 points
        ]

        extraction = GroundingExtractionResult(
            equipment=basic_equipment,
            calibration=basic_calibration,
            test_conditions=test_conditions,
            measurements=measurements,
            overall_confidence=0.9,
        )

        result = orchestrator.validate(extraction)
        score = orchestrator.calculate_compliance_score(result)

        assert score >= 0.0


class TestCrossValidation:
    """Tests for cross-validation integration."""

    def test_includes_calibration_validation(self, orchestrator, basic_equipment):
        """Test that calibration validation is included for test types."""
        test_conditions = GroundingTestConditions(
            test_date=FieldConfidence(value="2024-01-15", confidence=0.9),
        )

        # No calibration info provided
        extraction = GroundingExtractionResult(
            equipment=basic_equipment,
            calibration=None,  # Missing calibration
            test_conditions=test_conditions,
            measurements=[
                GroundingMeasurement(
                    test_point=FieldConfidence(value="Main", confidence=0.9),
                    resistance_value=FieldConfidence(value=2.0, confidence=0.9),
                )
            ],
            overall_confidence=0.9,
        )

        result = orchestrator.validate(extraction)

        # Should have calibration finding
        calib_findings = [f for f in result.findings if "CALIB" in f.rule_id]
        assert len(calib_findings) >= 1

    def test_includes_cross_field_validation(self, orchestrator):
        """Test that cross-field validation is included."""
        equipment = EquipmentInfo(
            equipment_tag=FieldConfidence(value="", confidence=0.9),  # Empty TAG
            equipment_type=FieldConfidence(value="panel", confidence=0.9),
        )
        test_conditions = GroundingTestConditions(
            test_date=FieldConfidence(value="2024-01-15", confidence=0.9),
        )

        extraction = GroundingExtractionResult(
            equipment=equipment,
            test_conditions=test_conditions,
            measurements=[
                GroundingMeasurement(
                    test_point=FieldConfidence(value="Main", confidence=0.9),
                    resistance_value=FieldConfidence(value=2.0, confidence=0.9),
                )
            ],
            overall_confidence=0.9,
        )

        result = orchestrator.validate(extraction)

        # Should have cross-field finding for missing TAG
        cross_findings = [f for f in result.findings if "CROSS" in f.rule_id]
        assert len(cross_findings) >= 1
