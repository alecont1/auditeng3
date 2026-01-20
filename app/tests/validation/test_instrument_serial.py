"""Tests for InstrumentSerialValidator.

Tests:
- CALIB-007: Instrument serial number must match calibration certificate.
- CALIB-008: Hygrometer serial number must match photo.

This validation applies to ALL test types (grounding, megger, thermography)
and validates ALL equipment used in each test type.
"""

import pytest

from app.core.extraction.grounding import (
    GroundingExtractionResult,
    GroundingTestConditions,
)
from app.core.extraction.megger import (
    MeggerExtractionResult,
    MeggerTestConditions,
)
from app.core.extraction.ocr import CertificateOCRResult, HygrometerOCRResult
from app.core.extraction.schemas import (
    CalibrationInfo,
    EquipmentInfo,
    FieldConfidence,
)
from app.core.extraction.thermography import (
    ThermalImageData,
    ThermographyExtractionResult,
    ThermographyTestConditions,
)
from app.core.validation.instrument_serial import InstrumentSerialValidator
from app.core.validation.schemas import ValidationSeverity


class TestGroundingSerialMismatch:
    """Tests for serial mismatch detection in grounding tests."""

    @pytest.fixture
    def validator(self) -> InstrumentSerialValidator:
        return InstrumentSerialValidator()

    @pytest.fixture
    def grounding_extraction(self) -> GroundingExtractionResult:
        """Sample grounding extraction with instrument serial."""
        return GroundingExtractionResult(
            equipment=EquipmentInfo(
                equipment_tag=FieldConfidence(value="CE1-UPS02", confidence=0.95),
                equipment_type=FieldConfidence(value="UPS", confidence=0.90),
            ),
            test_conditions=GroundingTestConditions(
                test_date=FieldConfidence(value="2024-01-15", confidence=0.95),
                instrument_serial=FieldConfidence(
                    value="66860197MV", confidence=0.95
                ),
            ),
            measurements=[],
            overall_confidence=0.90,
        )

    def test_grounding_serial_mismatch_detected(
        self, validator: InstrumentSerialValidator,
        grounding_extraction: GroundingExtractionResult,
    ) -> None:
        """Test that serial mismatch is detected for grounding tests."""
        certificate_ocr = CertificateOCRResult(
            serial_number=FieldConfidence(value="F223 6559", confidence=0.95),
        )

        result = validator.validate(grounding_extraction, certificate_ocr=certificate_ocr)

        assert len(result.findings) == 1
        finding = result.findings[0]
        assert finding.rule_id == "CALIB-007"
        assert finding.severity == ValidationSeverity.CRITICAL
        assert "66860197MV" in finding.message
        assert "F223 6559" in finding.message
        assert finding.field_path == "test_conditions.instrument_serial"

    def test_grounding_serial_match_no_finding(
        self, validator: InstrumentSerialValidator,
        grounding_extraction: GroundingExtractionResult,
    ) -> None:
        """Test that no finding when serials match."""
        certificate_ocr = CertificateOCRResult(
            serial_number=FieldConfidence(value="66860197MV", confidence=0.95),
        )

        result = validator.validate(grounding_extraction, certificate_ocr=certificate_ocr)

        assert len(result.findings) == 0

    def test_grounding_serial_normalized_comparison(
        self, validator: InstrumentSerialValidator,
        grounding_extraction: GroundingExtractionResult,
    ) -> None:
        """Test that serials are normalized before comparison."""
        # Certificate has serial with different formatting but same value
        certificate_ocr = CertificateOCRResult(
            serial_number=FieldConfidence(value="66860197-MV", confidence=0.95),
        )

        result = validator.validate(grounding_extraction, certificate_ocr=certificate_ocr)

        # Should match after normalization (remove hyphens)
        assert len(result.findings) == 0

    def test_low_ocr_confidence_minor_finding(
        self, validator: InstrumentSerialValidator,
        grounding_extraction: GroundingExtractionResult,
    ) -> None:
        """Test that low OCR confidence generates MINOR finding."""
        certificate_ocr = CertificateOCRResult(
            serial_number=FieldConfidence(value="F223 6559", confidence=0.5),
        )

        result = validator.validate(grounding_extraction, certificate_ocr=certificate_ocr)

        assert len(result.findings) == 1
        finding = result.findings[0]
        assert finding.rule_id == "CALIB-007"
        assert finding.severity == ValidationSeverity.MINOR
        assert "confidence low" in finding.message.lower()

    def test_no_certificate_ocr_no_finding(
        self, validator: InstrumentSerialValidator,
        grounding_extraction: GroundingExtractionResult,
    ) -> None:
        """Test that no finding when certificate OCR not provided."""
        result = validator.validate(grounding_extraction, certificate_ocr=None)

        assert len(result.findings) == 0


class TestMeggerSerialMismatch:
    """Tests for serial mismatch detection in megger tests."""

    @pytest.fixture
    def validator(self) -> InstrumentSerialValidator:
        return InstrumentSerialValidator()

    @pytest.fixture
    def megger_extraction(self) -> MeggerExtractionResult:
        """Sample megger extraction with instrument serial."""
        return MeggerExtractionResult(
            equipment=EquipmentInfo(
                equipment_tag=FieldConfidence(value="MTR-001", confidence=0.95),
                equipment_type=FieldConfidence(value="Motor", confidence=0.90),
            ),
            calibration=CalibrationInfo(
                instrument_model=FieldConfidence(value="Megger MIT525", confidence=0.95),
                instrument_serial=FieldConfidence(value="MIT12345", confidence=0.95),
                expiration_date=FieldConfidence(value="2025-12-31", confidence=0.95),
            ),
            test_conditions=MeggerTestConditions(
                test_date=FieldConfidence(value="2024-01-15", confidence=0.95),
                instrument_serial=FieldConfidence(value="MIT12345", confidence=0.95),
            ),
            measurements=[],
            overall_confidence=0.90,
        )

    def test_megger_serial_mismatch_detected(
        self, validator: InstrumentSerialValidator,
        megger_extraction: MeggerExtractionResult,
    ) -> None:
        """Test that serial mismatch is detected for megger tests."""
        certificate_ocr = CertificateOCRResult(
            serial_number=FieldConfidence(value="MIT99999", confidence=0.95),
        )

        result = validator.validate(megger_extraction, certificate_ocr=certificate_ocr)

        assert len(result.findings) == 1
        finding = result.findings[0]
        assert finding.rule_id == "CALIB-007"
        assert finding.severity == ValidationSeverity.CRITICAL
        assert finding.field_path == "test_conditions.instrument_serial"


class TestThermographySerialMismatch:
    """Tests for serial mismatch detection in thermography tests."""

    @pytest.fixture
    def validator(self) -> InstrumentSerialValidator:
        return InstrumentSerialValidator()

    @pytest.fixture
    def thermography_extraction(self) -> ThermographyExtractionResult:
        """Sample thermography extraction with camera serial."""
        return ThermographyExtractionResult(
            equipment=EquipmentInfo(
                equipment_tag=FieldConfidence(value="SB-001", confidence=0.95),
                equipment_type=FieldConfidence(value="Switchboard", confidence=0.90),
            ),
            test_conditions=ThermographyTestConditions(
                inspection_date=FieldConfidence(value="2024-01-15", confidence=0.95),
                camera_serial=FieldConfidence(value="CAM12345", confidence=0.95),
            ),
            thermal_data=ThermalImageData(),
            hotspots=[],
            overall_confidence=0.90,
        )

    def test_thermography_serial_mismatch_detected(
        self, validator: InstrumentSerialValidator,
        thermography_extraction: ThermographyExtractionResult,
    ) -> None:
        """Test that serial mismatch is detected for thermography tests."""
        certificate_ocr = CertificateOCRResult(
            serial_number=FieldConfidence(value="CAM99999", confidence=0.95),
        )

        result = validator.validate(thermography_extraction, certificate_ocr=certificate_ocr)

        assert len(result.findings) == 1
        finding = result.findings[0]
        assert finding.rule_id == "CALIB-007"
        assert finding.severity == ValidationSeverity.CRITICAL
        assert finding.field_path == "test_conditions.camera_serial"


class TestOrchestratorIntegration:
    """Tests for InstrumentSerialValidator integration with orchestrator."""

    def test_orchestrator_calls_serial_validation_for_grounding(self) -> None:
        """Test that orchestrator validates serial for grounding tests."""
        from app.core.validation.orchestrator import ValidationOrchestrator

        extraction = GroundingExtractionResult(
            equipment=EquipmentInfo(
                equipment_tag=FieldConfidence(value="CE1-UPS02", confidence=0.95),
                equipment_type=FieldConfidence(value="UPS", confidence=0.90),
            ),
            test_conditions=GroundingTestConditions(
                test_date=FieldConfidence(value="2024-01-15", confidence=0.95),
                instrument_serial=FieldConfidence(value="66860197MV", confidence=0.95),
            ),
            measurements=[],
            overall_confidence=0.90,
        )

        certificate_ocr = CertificateOCRResult(
            serial_number=FieldConfidence(value="F223 6559", confidence=0.95),
        )

        orchestrator = ValidationOrchestrator()
        result = orchestrator.validate(extraction, certificate_ocr=certificate_ocr)

        serial_findings = [f for f in result.findings if f.rule_id == "CALIB-007"]
        assert len(serial_findings) == 1
        assert serial_findings[0].severity == ValidationSeverity.CRITICAL

    def test_orchestrator_no_serial_validation_without_ocr(self) -> None:
        """Test that orchestrator skips serial validation without OCR."""
        from app.core.validation.orchestrator import ValidationOrchestrator

        extraction = GroundingExtractionResult(
            equipment=EquipmentInfo(
                equipment_tag=FieldConfidence(value="CE1-UPS02", confidence=0.95),
                equipment_type=FieldConfidence(value="UPS", confidence=0.90),
            ),
            test_conditions=GroundingTestConditions(
                test_date=FieldConfidence(value="2024-01-15", confidence=0.95),
                instrument_serial=FieldConfidence(value="66860197MV", confidence=0.95),
            ),
            measurements=[],
            overall_confidence=0.90,
        )

        orchestrator = ValidationOrchestrator()
        result = orchestrator.validate(extraction, certificate_ocr=None)

        serial_findings = [f for f in result.findings if f.rule_id == "CALIB-007"]
        assert len(serial_findings) == 0


class TestHygrometerSerialValidation:
    """Tests for thermo-hygrometer serial validation (CALIB-008)."""

    @pytest.fixture
    def validator(self) -> InstrumentSerialValidator:
        return InstrumentSerialValidator()

    @pytest.fixture
    def thermography_with_hygrometer(self) -> ThermographyExtractionResult:
        """Thermography extraction with camera and hygrometer serials."""
        return ThermographyExtractionResult(
            equipment=EquipmentInfo(
                equipment_tag=FieldConfidence(value="SB-001", confidence=0.95),
                equipment_type=FieldConfidence(value="Switchboard", confidence=0.90),
            ),
            test_conditions=ThermographyTestConditions(
                inspection_date=FieldConfidence(value="2024-01-15", confidence=0.95),
                camera_serial=FieldConfidence(value="CAM12345", confidence=0.95),
                hygrometer_serial=FieldConfidence(value="HYG98765", confidence=0.95),
            ),
            thermal_data=ThermalImageData(),
            hotspots=[],
            overall_confidence=0.90,
        )

    def test_hygrometer_serial_mismatch_detected(
        self,
        validator: InstrumentSerialValidator,
        thermography_with_hygrometer: ThermographyExtractionResult,
    ) -> None:
        """Test that hygrometer serial mismatch generates CALIB-008 CRITICAL."""
        certificate_ocr = CertificateOCRResult(
            serial_number=FieldConfidence(value="CAM12345", confidence=0.95),
        )
        hygrometer_ocr = HygrometerOCRResult(
            ambient_temperature=FieldConfidence(value=25.0, confidence=0.95),
            serial_number=FieldConfidence(value="HYG00000", confidence=0.95),  # Different!
        )

        result = validator.validate(
            thermography_with_hygrometer,
            certificate_ocr=certificate_ocr,
            hygrometer_ocr=hygrometer_ocr,
        )

        # Should have one finding for hygrometer mismatch (camera matches)
        hygrometer_findings = [f for f in result.findings if f.rule_id == "CALIB-008"]
        assert len(hygrometer_findings) == 1
        finding = hygrometer_findings[0]
        assert finding.severity == ValidationSeverity.CRITICAL
        assert "HYG98765" in finding.message
        assert "HYG00000" in finding.message
        assert "Thermo-Hygrometer" in finding.message

    def test_hygrometer_serial_match_no_finding(
        self,
        validator: InstrumentSerialValidator,
        thermography_with_hygrometer: ThermographyExtractionResult,
    ) -> None:
        """Test that no finding when hygrometer serial matches."""
        certificate_ocr = CertificateOCRResult(
            serial_number=FieldConfidence(value="CAM12345", confidence=0.95),
        )
        hygrometer_ocr = HygrometerOCRResult(
            ambient_temperature=FieldConfidence(value=25.0, confidence=0.95),
            serial_number=FieldConfidence(value="HYG98765", confidence=0.95),  # Matches!
        )

        result = validator.validate(
            thermography_with_hygrometer,
            certificate_ocr=certificate_ocr,
            hygrometer_ocr=hygrometer_ocr,
        )

        # No hygrometer mismatch findings
        hygrometer_findings = [f for f in result.findings if f.rule_id == "CALIB-008"]
        assert len(hygrometer_findings) == 0

    def test_both_camera_and_hygrometer_mismatch(
        self,
        validator: InstrumentSerialValidator,
        thermography_with_hygrometer: ThermographyExtractionResult,
    ) -> None:
        """Test that both camera and hygrometer mismatches are detected."""
        certificate_ocr = CertificateOCRResult(
            serial_number=FieldConfidence(value="CAM_WRONG", confidence=0.95),
        )
        hygrometer_ocr = HygrometerOCRResult(
            ambient_temperature=FieldConfidence(value=25.0, confidence=0.95),
            serial_number=FieldConfidence(value="HYG_WRONG", confidence=0.95),
        )

        result = validator.validate(
            thermography_with_hygrometer,
            certificate_ocr=certificate_ocr,
            hygrometer_ocr=hygrometer_ocr,
        )

        # Should have TWO findings: one for camera, one for hygrometer
        camera_findings = [f for f in result.findings if f.rule_id == "CALIB-007"]
        hygrometer_findings = [f for f in result.findings if f.rule_id == "CALIB-008"]

        assert len(camera_findings) == 1
        assert len(hygrometer_findings) == 1
        assert camera_findings[0].severity == ValidationSeverity.CRITICAL
        assert hygrometer_findings[0].severity == ValidationSeverity.CRITICAL

    def test_no_hygrometer_ocr_skips_validation(
        self,
        validator: InstrumentSerialValidator,
        thermography_with_hygrometer: ThermographyExtractionResult,
    ) -> None:
        """Test that hygrometer validation is skipped without OCR."""
        certificate_ocr = CertificateOCRResult(
            serial_number=FieldConfidence(value="CAM12345", confidence=0.95),
        )

        result = validator.validate(
            thermography_with_hygrometer,
            certificate_ocr=certificate_ocr,
            hygrometer_ocr=None,  # No hygrometer OCR
        )

        # No hygrometer findings (only camera validation runs)
        hygrometer_findings = [f for f in result.findings if f.rule_id == "CALIB-008"]
        assert len(hygrometer_findings) == 0

    def test_hygrometer_ocr_without_serial_skips_validation(
        self,
        validator: InstrumentSerialValidator,
        thermography_with_hygrometer: ThermographyExtractionResult,
    ) -> None:
        """Test that validation is skipped when OCR has no serial."""
        certificate_ocr = CertificateOCRResult(
            serial_number=FieldConfidence(value="CAM12345", confidence=0.95),
        )
        hygrometer_ocr = HygrometerOCRResult(
            ambient_temperature=FieldConfidence(value=25.0, confidence=0.95),
            serial_number=None,  # No serial extracted
        )

        result = validator.validate(
            thermography_with_hygrometer,
            certificate_ocr=certificate_ocr,
            hygrometer_ocr=hygrometer_ocr,
        )

        # No hygrometer findings
        hygrometer_findings = [f for f in result.findings if f.rule_id == "CALIB-008"]
        assert len(hygrometer_findings) == 0


class TestOrchestratorMultiEquipmentValidation:
    """Tests for orchestrator integration with multiple equipment validation."""

    def test_orchestrator_validates_hygrometer_for_thermography(self) -> None:
        """Test orchestrator validates hygrometer serial for thermography."""
        from app.core.validation.orchestrator import ValidationOrchestrator

        extraction = ThermographyExtractionResult(
            equipment=EquipmentInfo(
                equipment_tag=FieldConfidence(value="SB-001", confidence=0.95),
                equipment_type=FieldConfidence(value="Switchboard", confidence=0.90),
            ),
            test_conditions=ThermographyTestConditions(
                inspection_date=FieldConfidence(value="2024-01-15", confidence=0.95),
                camera_serial=FieldConfidence(value="CAM12345", confidence=0.95),
                hygrometer_serial=FieldConfidence(value="HYG98765", confidence=0.95),
            ),
            thermal_data=ThermalImageData(),
            hotspots=[],
            overall_confidence=0.90,
        )

        certificate_ocr = CertificateOCRResult(
            serial_number=FieldConfidence(value="CAM12345", confidence=0.95),
        )
        hygrometer_ocr = HygrometerOCRResult(
            ambient_temperature=FieldConfidence(value=25.0, confidence=0.95),
            serial_number=FieldConfidence(value="HYG_WRONG", confidence=0.95),
        )

        orchestrator = ValidationOrchestrator()
        result = orchestrator.validate(
            extraction,
            certificate_ocr=certificate_ocr,
            hygrometer_ocr=hygrometer_ocr,
        )

        # Should have hygrometer mismatch finding
        hygrometer_findings = [f for f in result.findings if f.rule_id == "CALIB-008"]
        assert len(hygrometer_findings) == 1
        assert hygrometer_findings[0].severity == ValidationSeverity.CRITICAL
