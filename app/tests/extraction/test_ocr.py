"""Unit tests for OCR extraction schemas.

Tests focus on schema validation and Pydantic model behavior.
Async extraction functions require Claude API and are tested separately.
"""

import pytest

from app.core.extraction.ocr import CertificateOCRResult, HygrometerOCRResult
from app.core.extraction.schemas import FieldConfidence


class TestCertificateOCRResult:
    """Tests for CertificateOCRResult schema."""

    def test_valid_result_all_fields(self):
        """Test creating valid certificate OCR result with all fields."""
        result = CertificateOCRResult(
            serial_number=FieldConfidence(
                value="ABC123456",
                confidence=0.95,
                source_text="Serial No: ABC123456",
            ),
            calibration_lab=FieldConfidence(
                value="FLUKE",
                confidence=0.9,
                source_text="Calibration Laboratory: FLUKE",
            ),
            calibration_date=FieldConfidence(
                value="2025-06-15",
                confidence=0.85,
                source_text="Date: 15/06/2025",
            ),
        )

        assert result.serial_number.value == "ABC123456"
        assert result.serial_number.confidence == 0.95
        assert result.calibration_lab.value == "FLUKE"
        assert result.calibration_date.value == "2025-06-15"

    def test_minimal_result_required_fields_only(self):
        """Test creating result with only required fields."""
        result = CertificateOCRResult(
            serial_number=FieldConfidence(
                value="XYZ789",
                confidence=0.7,
            ),
        )

        assert result.serial_number.value == "XYZ789"
        assert result.serial_number.confidence == 0.7
        assert result.calibration_lab is None
        assert result.calibration_date is None

    def test_low_confidence_serial(self):
        """Test result with low confidence (illegible text)."""
        result = CertificateOCRResult(
            serial_number=FieldConfidence(
                value="A??123",
                confidence=0.4,
                source_text="Partially obscured text",
            ),
        )

        assert result.serial_number.confidence == 0.4
        assert result.serial_number.value == "A??123"

    def test_alphanumeric_serial_formats(self):
        """Test various serial number formats are accepted."""
        serial_formats = [
            "12345678",  # Numeric only
            "ABC-12345",  # With dash
            "FL001234",  # Mixed alphanumeric
            "SN: 987654",  # With prefix
        ]

        for serial in serial_formats:
            result = CertificateOCRResult(
                serial_number=FieldConfidence(value=serial, confidence=0.9),
            )
            assert result.serial_number.value == serial

    def test_confidence_bounds(self):
        """Test confidence values at boundaries."""
        # Minimum confidence
        result_min = CertificateOCRResult(
            serial_number=FieldConfidence(value="test", confidence=0.0),
        )
        assert result_min.serial_number.confidence == 0.0

        # Maximum confidence
        result_max = CertificateOCRResult(
            serial_number=FieldConfidence(value="test", confidence=1.0),
        )
        assert result_max.serial_number.confidence == 1.0

    def test_confidence_out_of_bounds_raises(self):
        """Test that confidence outside 0-1 range raises error."""
        with pytest.raises(ValueError):
            CertificateOCRResult(
                serial_number=FieldConfidence(value="test", confidence=1.5),
            )

        with pytest.raises(ValueError):
            CertificateOCRResult(
                serial_number=FieldConfidence(value="test", confidence=-0.1),
            )


class TestHygrometerOCRResult:
    """Tests for HygrometerOCRResult schema."""

    def test_valid_result_all_fields(self):
        """Test creating valid hygrometer OCR result with all fields."""
        result = HygrometerOCRResult(
            ambient_temperature=FieldConfidence(
                value=23.5,
                confidence=0.95,
                source_text="Display: 23.5C",
            ),
            humidity=FieldConfidence(
                value=45.0,
                confidence=0.9,
                source_text="Display: 45%",
            ),
        )

        assert result.ambient_temperature.value == 23.5
        assert result.ambient_temperature.confidence == 0.95
        assert result.humidity.value == 45.0
        assert result.humidity.confidence == 0.9

    def test_temperature_only(self):
        """Test result with only temperature (humidity not visible)."""
        result = HygrometerOCRResult(
            ambient_temperature=FieldConfidence(
                value=25.0,
                confidence=0.8,
            ),
        )

        assert result.ambient_temperature.value == 25.0
        assert result.humidity is None

    def test_integer_temperature(self):
        """Test integer temperature values."""
        result = HygrometerOCRResult(
            ambient_temperature=FieldConfidence(
                value=24,
                confidence=0.9,
            ),
        )

        assert result.ambient_temperature.value == 24

    def test_low_confidence_reading(self):
        """Test result with low confidence (blurry display)."""
        result = HygrometerOCRResult(
            ambient_temperature=FieldConfidence(
                value=22.0,
                confidence=0.35,
                source_text="Blurry display, estimated reading",
            ),
            humidity=FieldConfidence(
                value=50.0,
                confidence=0.3,
            ),
        )

        assert result.ambient_temperature.confidence == 0.35
        assert result.humidity.confidence == 0.3

    def test_extreme_temperature_values(self):
        """Test extreme but valid temperature values."""
        # Cold environment
        result_cold = HygrometerOCRResult(
            ambient_temperature=FieldConfidence(value=-5.0, confidence=0.9),
        )
        assert result_cold.ambient_temperature.value == -5.0

        # Hot environment
        result_hot = HygrometerOCRResult(
            ambient_temperature=FieldConfidence(value=45.0, confidence=0.9),
        )
        assert result_hot.ambient_temperature.value == 45.0

    def test_humidity_range(self):
        """Test various humidity percentages."""
        humidity_values = [0.0, 20.0, 50.0, 80.0, 100.0]

        for humidity in humidity_values:
            result = HygrometerOCRResult(
                ambient_temperature=FieldConfidence(value=25.0, confidence=0.9),
                humidity=FieldConfidence(value=humidity, confidence=0.9),
            )
            assert result.humidity.value == humidity

    def test_confidence_validation(self):
        """Test confidence must be between 0 and 1."""
        # Valid boundary values
        HygrometerOCRResult(
            ambient_temperature=FieldConfidence(value=25.0, confidence=0.0),
        )
        HygrometerOCRResult(
            ambient_temperature=FieldConfidence(value=25.0, confidence=1.0),
        )

        # Invalid values
        with pytest.raises(ValueError):
            HygrometerOCRResult(
                ambient_temperature=FieldConfidence(value=25.0, confidence=1.1),
            )


class TestFieldConfidenceIntegration:
    """Test FieldConfidence behavior in OCR contexts."""

    def test_source_text_preserved(self):
        """Test that source_text is correctly preserved."""
        result = CertificateOCRResult(
            serial_number=FieldConfidence(
                value="ABC123",
                confidence=0.9,
                source_text="S/N: ABC123 (from certificate header)",
            ),
        )

        assert "from certificate header" in result.serial_number.source_text

    def test_none_source_text(self):
        """Test that source_text can be None."""
        result = HygrometerOCRResult(
            ambient_temperature=FieldConfidence(
                value=24.0,
                confidence=0.85,
                source_text=None,
            ),
        )

        assert result.ambient_temperature.source_text is None

    def test_value_types_flexibility(self):
        """Test that FieldConfidence.value accepts different types."""
        # String value (serial number)
        cert_result = CertificateOCRResult(
            serial_number=FieldConfidence(value="ABC123", confidence=0.9),
        )
        assert isinstance(cert_result.serial_number.value, str)

        # Float value (temperature)
        hygro_result = HygrometerOCRResult(
            ambient_temperature=FieldConfidence(value=23.5, confidence=0.9),
        )
        assert isinstance(hygro_result.ambient_temperature.value, float)

        # Int value (also valid for temperature)
        hygro_result_int = HygrometerOCRResult(
            ambient_temperature=FieldConfidence(value=24, confidence=0.9),
        )
        assert isinstance(hygro_result_int.ambient_temperature.value, int)
