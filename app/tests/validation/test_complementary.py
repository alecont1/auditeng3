"""Tests for ComplementaryValidator."""

import pytest
from datetime import date

from app.core.extraction.ocr import CertificateOCRResult
from app.core.extraction.schemas import CalibrationInfo, EquipmentInfo, FieldConfidence
from app.core.extraction.thermography import (
    ThermographyExtractionResult,
    ThermalImageData,
    ThermographyTestConditions,
)
from app.core.validation.complementary import ComplementaryValidator
from app.core.validation import ValidationSeverity


@pytest.fixture
def validator():
    return ComplementaryValidator()


@pytest.fixture
def basic_equipment():
    return EquipmentInfo(
        equipment_tag=FieldConfidence(value="QD-01", confidence=0.9),
        equipment_type=FieldConfidence(value="panel", confidence=0.9),
    )


@pytest.fixture
def basic_thermal_data():
    return ThermalImageData()


def create_extraction(
    equipment,
    thermal_data,
    inspection_date: str,
    calibration_exp: str | None = None,
    camera_serial: str | None = None,
) -> ThermographyExtractionResult:
    """Helper to create test extraction."""
    calibration = None
    if calibration_exp:
        calibration = CalibrationInfo(
            expiration_date=FieldConfidence(value=calibration_exp, confidence=0.9),
        )

    test_conditions = ThermographyTestConditions(
        inspection_date=FieldConfidence(value=inspection_date, confidence=0.9),
        camera_serial=FieldConfidence(value=camera_serial, confidence=0.9) if camera_serial else None,
    )

    return ThermographyExtractionResult(
        equipment=equipment,
        calibration=calibration,
        test_conditions=test_conditions,
        thermal_data=thermal_data,
        hotspots=[],
        overall_confidence=0.9,
    )


class TestCalibrationExpired:
    """Tests for CALIBRATION_EXPIRED (COMP-001)."""

    def test_calibration_expired_before_inspection(
        self, validator, basic_equipment, basic_thermal_data
    ):
        """Calibration expired before inspection -> CRITICAL."""
        extraction = create_extraction(
            basic_equipment,
            basic_thermal_data,
            inspection_date="2024-06-15",
            calibration_exp="2024-06-01",  # Expired 14 days before
        )

        result = validator.validate(extraction)

        assert not result.is_valid
        assert result.critical_count == 1
        finding = result.findings[0]
        assert finding.rule_id == "COMP-001"
        assert finding.severity == ValidationSeverity.CRITICAL
        assert "14 days before inspection" in finding.message

    def test_calibration_valid_at_inspection(
        self, validator, basic_equipment, basic_thermal_data
    ):
        """Calibration valid at inspection -> no finding."""
        extraction = create_extraction(
            basic_equipment,
            basic_thermal_data,
            inspection_date="2024-06-15",
            calibration_exp="2024-12-31",  # Valid until end of year
        )

        result = validator.validate(extraction)

        comp001_findings = [f for f in result.findings if f.rule_id == "COMP-001"]
        assert len(comp001_findings) == 0

    def test_calibration_expires_same_day(
        self, validator, basic_equipment, basic_thermal_data
    ):
        """Calibration expires same day as inspection -> valid (not expired)."""
        extraction = create_extraction(
            basic_equipment,
            basic_thermal_data,
            inspection_date="2024-06-15",
            calibration_exp="2024-06-15",  # Same day
        )

        result = validator.validate(extraction)

        comp001_findings = [f for f in result.findings if f.rule_id == "COMP-001"]
        assert len(comp001_findings) == 0

    def test_no_calibration_info(
        self, validator, basic_equipment, basic_thermal_data
    ):
        """No calibration info -> no finding (handled by CalibrationValidator)."""
        extraction = create_extraction(
            basic_equipment,
            basic_thermal_data,
            inspection_date="2024-06-15",
            calibration_exp=None,
        )

        result = validator.validate(extraction)

        assert result.critical_count == 0


class TestSerialMismatch:
    """Tests for SERIAL_MISMATCH (COMP-002)."""

    def test_serial_mismatch(
        self, validator, basic_equipment, basic_thermal_data
    ):
        """Serial mismatch -> CRITICAL."""
        extraction = create_extraction(
            basic_equipment,
            basic_thermal_data,
            inspection_date="2024-06-15",
            camera_serial="ABC123",
        )
        certificate_ocr = CertificateOCRResult(
            serial_number=FieldConfidence(value="XYZ789", confidence=0.95),
        )

        result = validator.validate(extraction, certificate_ocr=certificate_ocr)

        assert not result.is_valid
        assert result.critical_count == 1
        finding = result.findings[0]
        assert finding.rule_id == "COMP-002"
        assert finding.severity == ValidationSeverity.CRITICAL
        assert "ABC123" in finding.message
        assert "XYZ789" in finding.message

    def test_serial_match(
        self, validator, basic_equipment, basic_thermal_data
    ):
        """Serial matches -> no finding."""
        extraction = create_extraction(
            basic_equipment,
            basic_thermal_data,
            inspection_date="2024-06-15",
            camera_serial="ABC123",
        )
        certificate_ocr = CertificateOCRResult(
            serial_number=FieldConfidence(value="ABC123", confidence=0.95),
        )

        result = validator.validate(extraction, certificate_ocr=certificate_ocr)

        comp002_findings = [f for f in result.findings if f.rule_id == "COMP-002"]
        assert len(comp002_findings) == 0

    def test_serial_match_case_insensitive(
        self, validator, basic_equipment, basic_thermal_data
    ):
        """Serial comparison is case-insensitive."""
        extraction = create_extraction(
            basic_equipment,
            basic_thermal_data,
            inspection_date="2024-06-15",
            camera_serial="abc123",
        )
        certificate_ocr = CertificateOCRResult(
            serial_number=FieldConfidence(value="ABC123", confidence=0.95),
        )

        result = validator.validate(extraction, certificate_ocr=certificate_ocr)

        comp002_findings = [f for f in result.findings if f.rule_id == "COMP-002"]
        assert len(comp002_findings) == 0

    def test_serial_illegible_low_confidence(
        self, validator, basic_equipment, basic_thermal_data
    ):
        """Low OCR confidence -> MAJOR (SERIAL_ILLEGIBLE), not comparison."""
        extraction = create_extraction(
            basic_equipment,
            basic_thermal_data,
            inspection_date="2024-06-15",
            camera_serial="ABC123",
        )
        certificate_ocr = CertificateOCRResult(
            serial_number=FieldConfidence(value="A?C1?3", confidence=0.5),  # Low confidence
        )

        result = validator.validate(extraction, certificate_ocr=certificate_ocr)

        # Should get SERIAL_ILLEGIBLE, not SERIAL_MISMATCH
        comp006_findings = [f for f in result.findings if f.rule_id == "COMP-006"]
        comp002_findings = [f for f in result.findings if f.rule_id == "COMP-002"]
        assert len(comp006_findings) == 1
        assert len(comp002_findings) == 0
        assert comp006_findings[0].severity == ValidationSeverity.MAJOR

    def test_no_serial_in_report(
        self, validator, basic_equipment, basic_thermal_data
    ):
        """No serial in report -> no comparison."""
        extraction = create_extraction(
            basic_equipment,
            basic_thermal_data,
            inspection_date="2024-06-15",
            camera_serial=None,
        )
        certificate_ocr = CertificateOCRResult(
            serial_number=FieldConfidence(value="XYZ789", confidence=0.95),
        )

        result = validator.validate(extraction, certificate_ocr=certificate_ocr)

        serial_findings = [f for f in result.findings if "COMP-002" in f.rule_id or "COMP-006" in f.rule_id]
        assert len(serial_findings) == 0

    def test_no_ocr_result(
        self, validator, basic_equipment, basic_thermal_data
    ):
        """No OCR result -> no comparison."""
        extraction = create_extraction(
            basic_equipment,
            basic_thermal_data,
            inspection_date="2024-06-15",
            camera_serial="ABC123",
        )

        result = validator.validate(extraction, certificate_ocr=None)

        serial_findings = [f for f in result.findings if "COMP-002" in f.rule_id or "COMP-006" in f.rule_id]
        assert len(serial_findings) == 0
