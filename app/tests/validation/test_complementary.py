"""Tests for ComplementaryValidator.

Tests cover all 5 cross-validation rules:
- COMP-001: CALIBRATION_EXPIRED
- COMP-002: SERIAL_MISMATCH
- COMP-003: VALUE_MISMATCH
- COMP-004: PHOTO_MISSING
- COMP-005: SPEC_NON_COMPLIANCE
"""

from datetime import date

import pytest

from app.core.extraction.ocr import CertificateOCRResult, HygrometerOCRResult
from app.core.extraction.schemas import CalibrationInfo, EquipmentInfo, FieldConfidence
from app.core.extraction.thermography import (
    Hotspot,
    ThermalImageData,
    ThermographyExtractionResult,
    ThermographyTestConditions,
)
from app.core.validation.complementary import ComplementaryValidator
from app.core.validation.schemas import ValidationSeverity


@pytest.fixture
def validator():
    """Create ComplementaryValidator instance."""
    return ComplementaryValidator()


@pytest.fixture
def basic_equipment():
    """Create basic equipment info for tests."""
    return EquipmentInfo(
        equipment_tag=FieldConfidence(value="PANEL-001", confidence=0.9),
        equipment_type=FieldConfidence(value="PANEL", confidence=0.9),
    )


@pytest.fixture
def basic_thermal_data():
    """Create basic thermal data for tests."""
    return ThermalImageData(
        reflected_temperature=FieldConfidence(value=25.0, confidence=0.9),
    )


def create_hotspot(location: str, max_temp: float, ref_temp: float) -> Hotspot:
    """Helper to create hotspot with delta-T."""
    return Hotspot(
        location=FieldConfidence(value=location, confidence=0.9),
        max_temperature=FieldConfidence(value=max_temp, confidence=0.9),
        reference_temperature=FieldConfidence(value=ref_temp, confidence=0.9),
    )


class TestCalibrationExpired:
    """Tests for CALIBRATION_EXPIRED (COMP-001)."""

    def test_expired_calibration(
        self, validator, basic_equipment, basic_thermal_data
    ):
        """Expired calibration on inspection date -> CRITICAL."""
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=ThermographyTestConditions(
                inspection_date=FieldConfidence(value="2024-06-15", confidence=0.9),
            ),
            thermal_data=basic_thermal_data,
            hotspots=[],
            calibration=CalibrationInfo(
                expiration_date=FieldConfidence(value="2024-06-01", confidence=0.9),
            ),
            overall_confidence=0.9,
        )

        result = validator.validate(
            extraction,
            inspection_date=date(2024, 6, 15),
        )

        comp001_findings = [f for f in result.findings if f.rule_id == "COMP-001"]
        assert len(comp001_findings) == 1
        assert comp001_findings[0].severity == ValidationSeverity.CRITICAL

    def test_valid_calibration(
        self, validator, basic_equipment, basic_thermal_data
    ):
        """Valid calibration on inspection date -> no finding."""
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=ThermographyTestConditions(
                inspection_date=FieldConfidence(value="2024-06-15", confidence=0.9),
            ),
            thermal_data=basic_thermal_data,
            hotspots=[],
            calibration=CalibrationInfo(
                expiration_date=FieldConfidence(value="2024-12-31", confidence=0.9),
            ),
            overall_confidence=0.9,
        )

        result = validator.validate(
            extraction,
            inspection_date=date(2024, 6, 15),
        )

        comp001_findings = [f for f in result.findings if f.rule_id == "COMP-001"]
        assert len(comp001_findings) == 0


class TestSerialMismatch:
    """Tests for SERIAL_MISMATCH (COMP-002)."""

    def test_serial_mismatch(
        self, validator, basic_equipment, basic_thermal_data
    ):
        """Mismatched serial numbers -> CRITICAL."""
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=ThermographyTestConditions(
                inspection_date=FieldConfidence(value="2024-06-15", confidence=0.9),
                camera_serial=FieldConfidence(value="CAM-12345", confidence=0.9),
            ),
            thermal_data=basic_thermal_data,
            hotspots=[],
            overall_confidence=0.9,
        )
        certificate_ocr = CertificateOCRResult(
            serial_number=FieldConfidence(value="CAM-99999", confidence=0.95),
        )

        result = validator.validate(extraction, certificate_ocr=certificate_ocr)

        comp002_findings = [f for f in result.findings if f.rule_id == "COMP-002"]
        assert len(comp002_findings) == 1
        assert comp002_findings[0].severity == ValidationSeverity.CRITICAL

    def test_serial_match(
        self, validator, basic_equipment, basic_thermal_data
    ):
        """Matching serial numbers -> no finding."""
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=ThermographyTestConditions(
                inspection_date=FieldConfidence(value="2024-06-15", confidence=0.9),
                camera_serial=FieldConfidence(value="CAM-12345", confidence=0.9),
            ),
            thermal_data=basic_thermal_data,
            hotspots=[],
            overall_confidence=0.9,
        )
        certificate_ocr = CertificateOCRResult(
            serial_number=FieldConfidence(value="CAM-12345", confidence=0.95),
        )

        result = validator.validate(extraction, certificate_ocr=certificate_ocr)

        comp002_findings = [f for f in result.findings if f.rule_id == "COMP-002"]
        assert len(comp002_findings) == 0

    def test_low_ocr_confidence(
        self, validator, basic_equipment, basic_thermal_data
    ):
        """Low OCR confidence -> MINOR (review flag)."""
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=ThermographyTestConditions(
                inspection_date=FieldConfidence(value="2024-06-15", confidence=0.9),
                camera_serial=FieldConfidence(value="CAM-12345", confidence=0.9),
            ),
            thermal_data=basic_thermal_data,
            hotspots=[],
            overall_confidence=0.9,
        )
        certificate_ocr = CertificateOCRResult(
            serial_number=FieldConfidence(value="CAM-12???", confidence=0.5),  # Low confidence
        )

        result = validator.validate(extraction, certificate_ocr=certificate_ocr)

        comp002_findings = [f for f in result.findings if f.rule_id == "COMP-002"]
        assert len(comp002_findings) == 1
        assert comp002_findings[0].severity == ValidationSeverity.MINOR


class TestValueMismatch:
    """Tests for VALUE_MISMATCH (COMP-003)."""

    def test_temperature_mismatch(
        self, validator, basic_equipment
    ):
        """Temperature differs by more than tolerance -> CRITICAL."""
        thermal_data = ThermalImageData(
            reflected_temperature=FieldConfidence(value=25.0, confidence=0.9),
        )
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=ThermographyTestConditions(
                inspection_date=FieldConfidence(value="2024-06-15", confidence=0.9),
            ),
            thermal_data=thermal_data,
            hotspots=[],
            overall_confidence=0.9,
        )
        hygrometer_ocr = HygrometerOCRResult(
            ambient_temperature=FieldConfidence(value=30.0, confidence=0.95),  # 5C diff
        )

        result = validator.validate(extraction, hygrometer_ocr=hygrometer_ocr)

        comp003_findings = [f for f in result.findings if f.rule_id == "COMP-003"]
        assert len(comp003_findings) == 1
        assert comp003_findings[0].severity == ValidationSeverity.CRITICAL

    def test_temperature_within_tolerance(
        self, validator, basic_equipment
    ):
        """Temperature within tolerance -> no finding."""
        thermal_data = ThermalImageData(
            reflected_temperature=FieldConfidence(value=25.0, confidence=0.9),
        )
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=ThermographyTestConditions(
                inspection_date=FieldConfidence(value="2024-06-15", confidence=0.9),
            ),
            thermal_data=thermal_data,
            hotspots=[],
            overall_confidence=0.9,
        )
        hygrometer_ocr = HygrometerOCRResult(
            ambient_temperature=FieldConfidence(value=26.0, confidence=0.95),  # 1C diff
        )

        result = validator.validate(extraction, hygrometer_ocr=hygrometer_ocr)

        comp003_findings = [f for f in result.findings if f.rule_id == "COMP-003"]
        assert len(comp003_findings) == 0


class TestPhotoMissing:
    """Tests for PHOTO_MISSING (COMP-004)."""

    def test_missing_phase(
        self, validator, basic_equipment, basic_thermal_data
    ):
        """Missing phase thermal image -> CRITICAL."""
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=ThermographyTestConditions(
                inspection_date=FieldConfidence(value="2024-06-15", confidence=0.9),
            ),
            thermal_data=basic_thermal_data,
            hotspots=[
                create_hotspot("Phase A", 35.0, 30.0),
                create_hotspot("Phase C", 36.0, 30.0),
                # Phase B missing
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(
            extraction,
            expected_phases=["Phase A", "Phase B", "Phase C"],
        )

        comp004_findings = [f for f in result.findings if f.rule_id == "COMP-004"]
        assert len(comp004_findings) == 1
        assert "B" in comp004_findings[0].message

    def test_all_phases_present(
        self, validator, basic_equipment, basic_thermal_data
    ):
        """All phases have thermal images -> no finding."""
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=ThermographyTestConditions(
                inspection_date=FieldConfidence(value="2024-06-15", confidence=0.9),
            ),
            thermal_data=basic_thermal_data,
            hotspots=[
                create_hotspot("Phase A", 35.0, 30.0),
                create_hotspot("Phase B", 34.0, 30.0),
                create_hotspot("Phase C", 36.0, 30.0),
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(
            extraction,
            expected_phases=["Phase A", "Phase B", "Phase C"],
        )

        comp004_findings = [f for f in result.findings if f.rule_id == "COMP-004"]
        assert len(comp004_findings) == 0


class TestSpecNonCompliance:
    """Tests for SPEC_NON_COMPLIANCE (COMP-005)."""

    def test_high_delta_no_comments(
        self, validator, basic_equipment, basic_thermal_data
    ):
        """Delta > 10C without comments -> CRITICAL."""
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=ThermographyTestConditions(
                inspection_date=FieldConfidence(value="2024-06-15", confidence=0.9),
            ),
            thermal_data=basic_thermal_data,
            hotspots=[
                create_hotspot("Breaker 1", 45.0, 30.0),  # 15C delta
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction, report_comments=None)

        comp005_findings = [f for f in result.findings if f.rule_id == "COMP-005"]
        assert len(comp005_findings) == 1
        assert comp005_findings[0].severity == ValidationSeverity.CRITICAL

    def test_high_delta_with_valid_comments(
        self, validator, basic_equipment, basic_thermal_data
    ):
        """Delta > 10C with proper comments -> no finding."""
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=ThermographyTestConditions(
                inspection_date=FieldConfidence(value="2024-06-15", confidence=0.9),
            ),
            thermal_data=basic_thermal_data,
            hotspots=[
                create_hotspot("Breaker 1", 45.0, 30.0),  # 15C delta
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(
            extraction,
            report_comments="Loose terminals identified. Torque check recommended.",
        )

        comp005_findings = [f for f in result.findings if f.rule_id == "COMP-005"]
        assert len(comp005_findings) == 0

    def test_high_delta_irrelevant_comments(
        self, validator, basic_equipment, basic_thermal_data
    ):
        """Delta > 10C with irrelevant comments -> CRITICAL."""
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=ThermographyTestConditions(
                inspection_date=FieldConfidence(value="2024-06-15", confidence=0.9),
            ),
            thermal_data=basic_thermal_data,
            hotspots=[
                create_hotspot("Breaker 1", 45.0, 30.0),  # 15C delta
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(
            extraction,
            report_comments="Weather was sunny. Equipment looked fine.",
        )

        comp005_findings = [f for f in result.findings if f.rule_id == "COMP-005"]
        assert len(comp005_findings) == 1

    def test_delta_below_threshold(
        self, validator, basic_equipment, basic_thermal_data
    ):
        """Delta <= 10C -> no SPEC check needed."""
        extraction = ThermographyExtractionResult(
            equipment=basic_equipment,
            test_conditions=ThermographyTestConditions(
                inspection_date=FieldConfidence(value="2024-06-15", confidence=0.9),
            ),
            thermal_data=basic_thermal_data,
            hotspots=[
                create_hotspot("Breaker 1", 38.0, 30.0),  # 8C delta
            ],
            overall_confidence=0.9,
        )

        result = validator.validate(extraction, report_comments=None)

        comp005_findings = [f for f in result.findings if f.rule_id == "COMP-005"]
        assert len(comp005_findings) == 0
