"""Megger (insulation resistance) test extraction schema and extractor.

This module provides extraction capabilities for insulation resistance test reports
following IEEE 43 standards, including Polarization Index calculation.
"""

from pydantic import BaseModel, Field

from app.core.extraction.base import BaseExtractor
from app.core.extraction.schemas import (
    BaseExtractionResult,
    CalibrationInfo,
    EquipmentInfo,
    FieldConfidence,
)


class InsulationReading(BaseModel):
    """Single insulation resistance reading at a specific time.

    Megger tests typically record readings at multiple time intervals
    (15s, 30s, 1min, 10min) to calculate Polarization Index.

    Attributes:
        time_seconds: Time of reading (15, 30, 60, 600 seconds).
        resistance_value: Measured insulation resistance.
        resistance_unit: Unit of measurement (always MΩ).
    """

    time_seconds: int
    resistance_value: FieldConfidence
    resistance_unit: str = "MΩ"


class MeggerMeasurement(BaseModel):
    """Complete Megger measurement for a circuit/phase.

    Contains all timed readings for a single circuit and calculates
    the Polarization Index per IEEE 43.

    Attributes:
        circuit_id: Circuit identifier (e.g., "Phase A-B", "L1-Ground").
        test_voltage: Applied test voltage (e.g., 500V, 1000V, 5000V).
        readings: List of timed resistance readings.
        ir_1min: 1-minute reading in MΩ (derived).
        ir_10min: 10-minute reading in MΩ (derived).
        polarization_index: PI = IR10min / IR1min (derived).
    """

    circuit_id: FieldConfidence
    test_voltage: FieldConfidence
    readings: list[InsulationReading] = Field(default_factory=list)

    # Calculated from readings
    ir_1min: float | None = None
    ir_10min: float | None = None
    polarization_index: float | None = None

    def model_post_init(self, __context) -> None:
        """Calculate IR values and Polarization Index."""
        for reading in self.readings:
            val = reading.resistance_value.value
            if isinstance(val, (int, float)):
                if reading.time_seconds == 60:
                    self.ir_1min = float(val)
                elif reading.time_seconds == 600:
                    self.ir_10min = float(val)

        # Calculate PI if both readings available
        if self.ir_1min and self.ir_10min and self.ir_1min > 0:
            self.polarization_index = self.ir_10min / self.ir_1min


class MeggerTestConditions(BaseModel):
    """Test conditions during Megger measurement.

    Environmental conditions affect insulation resistance readings
    and should be recorded for proper interpretation.

    Attributes:
        test_date: Date when the test was performed.
        tester_name: Name of the person who conducted the test.
        ambient_temperature: Ambient temperature in Celsius.
        humidity: Relative humidity percentage.
        instrument_model: Model of the Megger instrument.
        instrument_serial: Serial number of the instrument.
    """

    test_date: FieldConfidence
    tester_name: FieldConfidence | None = None
    ambient_temperature: FieldConfidence | None = None
    humidity: FieldConfidence | None = None
    instrument_model: FieldConfidence | None = None
    instrument_serial: FieldConfidence | None = None


class MeggerExtractionResult(BaseExtractionResult):
    """Complete Megger test extraction result.

    Contains all extracted data from an insulation resistance test report
    with IEEE 43 compliance checking.

    Attributes:
        equipment: Equipment identification information.
        calibration: Calibration certificate information (required).
        test_conditions: Conditions during the test.
        measurements: List of circuit measurements.
        min_ir: Minimum insulation resistance found (derived).
        min_pi: Minimum Polarization Index found (derived).
        all_pi_acceptable: True if all PI values >= 2.0 (IEEE 43).
    """

    equipment: EquipmentInfo
    calibration: CalibrationInfo
    test_conditions: MeggerTestConditions
    measurements: list[MeggerMeasurement] = Field(default_factory=list)

    # Summary fields (calculated in model_post_init)
    min_ir: float | None = None
    min_pi: float | None = None
    all_pi_acceptable: bool = True

    def model_post_init(self, __context) -> None:
        """Calculate summary fields from measurements."""
        ir_values: list[float] = []
        pi_values: list[float] = []

        for m in self.measurements:
            if m.ir_1min is not None:
                ir_values.append(m.ir_1min)
            if m.polarization_index is not None:
                pi_values.append(m.polarization_index)
                if m.polarization_index < 2.0:
                    self.all_pi_acceptable = False

        if ir_values:
            self.min_ir = min(ir_values)
        if pi_values:
            self.min_pi = min(pi_values)


class MeggerExtractor(BaseExtractor):
    """Extractor for insulation resistance (Megger) test reports.

    Extracts insulation resistance measurements, calculates Polarization Index,
    and validates against IEEE 43 standards.

    Attributes:
        PI_THRESHOLD: Minimum acceptable PI per IEEE 43 (2.0).

    Example:
        extractor = MeggerExtractor()
        result = await extractor.extract(pdf_text)
        print(f"Min PI: {result.min_pi}, Acceptable: {result.all_pi_acceptable}")
    """

    PI_THRESHOLD: float = 2.0  # IEEE 43 minimum acceptable PI

    @property
    def test_type(self) -> str:
        """Return test type identifier."""
        return "megger"

    @property
    def system_prompt(self) -> str:
        """Return the system prompt for Megger extraction."""
        from app.core.extraction.prompts import MEGGER_EXTRACTION_PROMPT

        return MEGGER_EXTRACTION_PROMPT

    def get_response_model(self) -> type[MeggerExtractionResult]:
        """Return the Pydantic model for Megger extraction."""
        return MeggerExtractionResult

    def _check_needs_review(self, result: MeggerExtractionResult) -> bool:
        """Check if Megger extraction needs human review.

        Reviews are flagged when:
        - Overall confidence is below threshold
        - Equipment TAG has low confidence
        - Calibration expiration has low confidence
        - Any PI value is below 2.0 (IEEE 43 threshold)
        - Any measurement voltage has low confidence

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

        # Calibration expiration is critical (higher threshold)
        if result.calibration.expiration_date.confidence < 0.8:
            return True

        # Check for low PI values (requires engineering review)
        if result.min_pi is not None and result.min_pi < self.PI_THRESHOLD:
            result.extraction_errors.append(
                f"Low Polarization Index detected: {result.min_pi:.2f} < {self.PI_THRESHOLD}"
            )
            return True

        # Check if any measurement has low confidence on test voltage
        for m in result.measurements:
            if m.test_voltage.confidence < self.CONFIDENCE_THRESHOLD:
                return True

        return False
