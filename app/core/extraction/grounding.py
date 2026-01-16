"""Grounding test extraction schema and extractor.

This module provides extraction capabilities for grounding/earthing test reports,
including resistance measurements, equipment identification, and test conditions.
"""

from pydantic import BaseModel, Field

from app.core.extraction.base import BaseExtractor
from app.core.extraction.schemas import (
    BaseExtractionResult,
    CalibrationInfo,
    EquipmentInfo,
    FieldConfidence,
)


class GroundingMeasurement(BaseModel):
    """Single grounding resistance measurement.

    Represents one test point's resistance reading with associated metadata.

    Attributes:
        test_point: Description of the test point (e.g., "Main Ground Bus").
        resistance_value: Measured resistance value.
        resistance_unit: Unit of measurement (always ohms for grounding).
        test_method: Method used (e.g., "Fall of Potential", "3-Point").
        soil_conditions: Soil conditions during test.
        temperature: Ambient temperature during test.
        humidity: Humidity during test.
    """

    test_point: FieldConfidence
    resistance_value: FieldConfidence
    resistance_unit: str = "ohms"
    test_method: FieldConfidence | None = None
    soil_conditions: FieldConfidence | None = None
    temperature: FieldConfidence | None = None
    humidity: FieldConfidence | None = None


class GroundingTestConditions(BaseModel):
    """Test conditions during grounding measurement.

    Captures environmental and procedural information about the test.

    Attributes:
        test_date: Date when the test was performed.
        tester_name: Name of the person who conducted the test.
        weather_conditions: Weather during the test.
        instrument_model: Model of the test instrument used.
        instrument_serial: Serial number of the test instrument.
    """

    test_date: FieldConfidence
    tester_name: FieldConfidence | None = None
    weather_conditions: FieldConfidence | None = None
    instrument_model: FieldConfidence | None = None
    instrument_serial: FieldConfidence | None = None


class GroundingExtractionResult(BaseExtractionResult):
    """Complete grounding test extraction result.

    Contains all extracted data from a grounding test report including
    equipment info, calibration data, test conditions, and measurements.

    Attributes:
        equipment: Equipment identification information.
        calibration: Calibration certificate information.
        test_conditions: Conditions during the test.
        measurements: List of resistance measurements.
        min_resistance: Minimum resistance value found.
        max_resistance: Maximum resistance value found.
        avg_resistance: Average resistance across all measurements.
    """

    equipment: EquipmentInfo
    calibration: CalibrationInfo | None = None
    test_conditions: GroundingTestConditions
    measurements: list[GroundingMeasurement] = Field(default_factory=list)

    # Derived fields (calculated in model_post_init)
    min_resistance: float | None = None
    max_resistance: float | None = None
    avg_resistance: float | None = None

    def model_post_init(self, __context) -> None:
        """Calculate derived fields after initialization."""
        if self.measurements:
            values = []
            for m in self.measurements:
                val = m.resistance_value.value
                if isinstance(val, (int, float)):
                    values.append(float(val))

            if values:
                self.min_resistance = min(values)
                self.max_resistance = max(values)
                self.avg_resistance = sum(values) / len(values)


class GroundingExtractor(BaseExtractor):
    """Extractor for grounding/earthing test reports.

    Extracts resistance measurements, equipment identification,
    calibration data, and test conditions from grounding test reports.

    Example:
        extractor = GroundingExtractor()
        result = await extractor.extract(pdf_text)
        print(f"Average resistance: {result.avg_resistance} ohms")
    """

    @property
    def test_type(self) -> str:
        """Return test type identifier."""
        return "grounding"

    @property
    def system_prompt(self) -> str:
        """Return the system prompt for grounding extraction."""
        from app.core.extraction.prompts import GROUNDING_EXTRACTION_PROMPT

        return GROUNDING_EXTRACTION_PROMPT

    def get_response_model(self) -> type[GroundingExtractionResult]:
        """Return the Pydantic model for grounding extraction."""
        return GroundingExtractionResult

    def _check_needs_review(self, result: GroundingExtractionResult) -> bool:
        """Check if grounding extraction needs human review.

        Reviews are flagged when:
        - Overall confidence is below threshold
        - Equipment TAG has low confidence
        - Any resistance measurement has low confidence
        - Calibration expiration date has low confidence

        Args:
            result: The extraction result to check.

        Returns:
            bool: True if the extraction needs review.
        """
        # Check overall confidence
        if result.overall_confidence < self.CONFIDENCE_THRESHOLD:
            return True

        # Check critical field: equipment TAG
        if result.equipment.equipment_tag.confidence < self.CONFIDENCE_THRESHOLD:
            return True

        # Check if any measurement has low confidence
        for m in result.measurements:
            if m.resistance_value.confidence < self.CONFIDENCE_THRESHOLD:
                return True

        # Check calibration expiration (higher threshold for calibration)
        if result.calibration and result.calibration.expiration_date.confidence < 0.8:
            return True

        return False
