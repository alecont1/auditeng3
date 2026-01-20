"""Thermography extraction schema and extractor.

This module provides extraction capabilities for thermographic inspection images
using Claude Vision, with hotspot detection and severity classification per NETA MTS.
"""

import base64
import logging
from enum import StrEnum

from pydantic import BaseModel, Field

from app.core.extraction.base import BaseExtractor
from app.core.extraction.schemas import (
    BaseExtractionResult,
    CalibrationInfo,
    EquipmentInfo,
    FieldConfidence,
)

logger = logging.getLogger(__name__)


class HotspotSeverity(StrEnum):
    """Severity classification based on delta-T per NETA MTS.

    Classifications follow NETA Maintenance Testing Specifications
    for thermographic surveys of electrical equipment.

    NORMAL: No action required
    ATTENTION: Schedule repair at next opportunity
    INTERMEDIATE: Schedule repair within 1 month
    SERIOUS: Repair immediately, reduce load if possible
    CRITICAL: Immediate de-energization required
    """

    NORMAL = "normal"
    ATTENTION = "attention"
    INTERMEDIATE = "intermediate"
    SERIOUS = "serious"
    CRITICAL = "critical"


class Hotspot(BaseModel):
    """Detected hotspot in thermal image.

    Represents an abnormal temperature zone with severity classification.

    Attributes:
        location: Description of hotspot location.
        component: Specific component identifier.
        max_temperature: Highest temperature at hotspot (°C).
        reference_temperature: Temperature of similar component (°C).
        delta_t: Temperature difference (derived).
        severity: NETA MTS severity classification (derived).
    """

    location: FieldConfidence
    component: FieldConfidence | None = None
    max_temperature: FieldConfidence
    reference_temperature: FieldConfidence
    delta_t: float | None = None
    severity: HotspotSeverity | None = None

    def model_post_init(self, __context) -> None:
        """Calculate delta-T and classify severity."""
        max_temp = self.max_temperature.value
        ref_temp = self.reference_temperature.value

        if isinstance(max_temp, (int, float)) and isinstance(ref_temp, (int, float)):
            self.delta_t = float(max_temp) - float(ref_temp)
            self.severity = self._classify_severity(self.delta_t)

    @staticmethod
    def _classify_severity(delta_t: float) -> HotspotSeverity:
        """Classify severity based on delta-T per NETA MTS.

        Args:
            delta_t: Temperature difference in Celsius.

        Returns:
            HotspotSeverity: Classification based on NETA thresholds.
        """
        if delta_t < 5:
            return HotspotSeverity.NORMAL
        elif delta_t < 15:
            return HotspotSeverity.ATTENTION
        elif delta_t < 35:
            return HotspotSeverity.INTERMEDIATE
        elif delta_t < 70:
            return HotspotSeverity.SERIOUS
        else:
            return HotspotSeverity.CRITICAL


class ThermalImageData(BaseModel):
    """Camera settings and environmental data from thermal image.

    Attributes:
        image_id: Identifier for the thermal image.
        ambient_temperature: Ambient temperature (°C).
        reflected_temperature: Reflected temperature setting (°C).
        emissivity: Emissivity setting (should be ~0.95 for electrical).
        distance: Distance to target (meters).
        humidity: Relative humidity (%).
    """

    image_id: str | None = None
    ambient_temperature: FieldConfidence | None = None
    reflected_temperature: FieldConfidence | None = None
    emissivity: FieldConfidence | None = None
    distance: FieldConfidence | None = None
    humidity: FieldConfidence | None = None


class ThermographyTestConditions(BaseModel):
    """Test conditions during thermographic inspection.

    Load conditions are critical for proper interpretation of thermal data.

    Attributes:
        inspection_date: Date of inspection.
        inspector_name: Name of thermographer.
        load_conditions: Load during inspection (e.g., "75% rated load").
        camera_model: Thermal camera model.
        camera_serial: Camera serial number.
        hygrometer_model: Thermo-hygrometer model.
        hygrometer_serial: Thermo-hygrometer serial number.
    """

    inspection_date: FieldConfidence
    inspector_name: FieldConfidence | None = None
    load_conditions: FieldConfidence | None = None
    camera_model: FieldConfidence | None = None
    camera_serial: FieldConfidence | None = None
    hygrometer_model: FieldConfidence | None = None
    hygrometer_serial: FieldConfidence | None = None


class ThermographyExtractionResult(BaseExtractionResult):
    """Complete thermography extraction result.

    Contains all data from thermographic inspection including
    hotspot analysis and NETA severity classification.

    Attributes:
        equipment: Equipment identification.
        calibration: Camera calibration info.
        test_conditions: Inspection conditions.
        thermal_data: Camera settings and environment.
        hotspots: Detected temperature anomalies.
        max_delta_t: Maximum temperature difference (derived).
        max_severity: Highest severity found (derived).
        critical_count: Number of critical hotspots (derived).
        serious_count: Number of serious hotspots (derived).
    """

    equipment: EquipmentInfo
    calibration: CalibrationInfo | None = None
    test_conditions: ThermographyTestConditions
    thermal_data: ThermalImageData
    hotspots: list[Hotspot] = Field(default_factory=list)

    # Summary fields (calculated in model_post_init)
    max_delta_t: float | None = None
    max_severity: HotspotSeverity | None = None
    critical_count: int = 0
    serious_count: int = 0

    def model_post_init(self, __context) -> None:
        """Calculate summary fields from hotspots."""
        if self.hotspots:
            deltas = [h.delta_t for h in self.hotspots if h.delta_t is not None]
            if deltas:
                self.max_delta_t = max(deltas)

            severities = [h.severity for h in self.hotspots if h.severity is not None]
            if severities:
                # Order: NORMAL < ATTENTION < INTERMEDIATE < SERIOUS < CRITICAL
                severity_order = list(HotspotSeverity)
                self.max_severity = max(severities, key=lambda s: severity_order.index(s))

            self.critical_count = sum(
                1 for h in self.hotspots if h.severity == HotspotSeverity.CRITICAL
            )
            self.serious_count = sum(
                1 for h in self.hotspots if h.severity == HotspotSeverity.SERIOUS
            )


class ThermographyExtractor(BaseExtractor):
    """Extractor for thermographic inspection images using Claude Vision.

    Processes thermal images to detect hotspots and classify severity
    according to NETA MTS guidelines.

    Attributes:
        EMISSIVITY_EXPECTED: Expected emissivity for electrical equipment.
        EMISSIVITY_TOLERANCE: Acceptable deviation from expected emissivity.

    Example:
        extractor = ThermographyExtractor()
        with open("thermal_image.jpg", "rb") as f:
            result = await extractor.extract_from_images([f.read()])
        print(f"Max delta-T: {result.max_delta_t}°C")
    """

    EMISSIVITY_EXPECTED: float = 0.95
    EMISSIVITY_TOLERANCE: float = 0.05

    @property
    def test_type(self) -> str:
        """Return test type identifier."""
        return "thermography"

    @property
    def system_prompt(self) -> str:
        """Return the system prompt for thermography extraction."""
        from app.core.extraction.prompts import THERMOGRAPHY_EXTRACTION_PROMPT

        return THERMOGRAPHY_EXTRACTION_PROMPT

    def get_response_model(self) -> type[ThermographyExtractionResult]:
        """Return the Pydantic model for thermography extraction."""
        return ThermographyExtractionResult

    # Maximum images per API call to stay under request size limits
    BATCH_SIZE: int = 10

    async def extract_from_images(
        self,
        images: list[bytes],
        page_numbers: list[int] | None = None,
    ) -> ThermographyExtractionResult:
        """Extract thermal data from image bytes with batch processing.

        Processes images in batches to handle large documents without
        exceeding API request size limits. Results are merged into a
        single comprehensive result.

        Args:
            images: List of image bytes (thermal images).
            page_numbers: Optional page numbers for tracking.

        Returns:
            ThermographyExtractionResult: Hotspot analysis results from all batches.
        """
        if not images:
            raise ValueError("No images provided for thermography extraction")

        # If within batch size, process directly
        if len(images) <= self.BATCH_SIZE:
            b64_images = [base64.b64encode(img).decode() for img in images]
            return await self.extract(content=b64_images, page_numbers=page_numbers)

        # Process in batches
        logger.info(
            f"Processing {len(images)} images in batches of {self.BATCH_SIZE}"
        )

        all_results: list[ThermographyExtractionResult] = []
        for batch_idx in range(0, len(images), self.BATCH_SIZE):
            batch_end = min(batch_idx + self.BATCH_SIZE, len(images))
            batch_images = images[batch_idx:batch_end]
            batch_pages = (
                page_numbers[batch_idx:batch_end] if page_numbers else None
            )

            logger.info(
                f"Processing batch {batch_idx // self.BATCH_SIZE + 1}: "
                f"images {batch_idx + 1}-{batch_end} of {len(images)}"
            )

            b64_images = [base64.b64encode(img).decode() for img in batch_images]
            result = await self.extract(content=b64_images, page_numbers=batch_pages)
            all_results.append(result)

        # Merge all batch results
        return self._merge_results(all_results)

    def _merge_results(
        self, results: list[ThermographyExtractionResult]
    ) -> ThermographyExtractionResult:
        """Merge multiple batch results into a single result.

        Takes the base metadata from the first result and aggregates
        hotspots from all results.

        Args:
            results: List of extraction results from batches.

        Returns:
            ThermographyExtractionResult: Merged result with all hotspots.
        """
        if not results:
            raise ValueError("No results to merge")

        if len(results) == 1:
            return results[0]

        # Use first result as base (equipment info, test conditions, etc.)
        base = results[0]

        # Aggregate all hotspots
        all_hotspots: list[Hotspot] = []
        all_errors: list[str] = []
        all_page_numbers: list[int] = []
        confidence_sum = 0.0

        for result in results:
            all_hotspots.extend(result.hotspots)
            all_errors.extend(result.extraction_errors)
            if result.metadata and result.metadata.page_numbers:
                all_page_numbers.extend(result.metadata.page_numbers)
            confidence_sum += result.overall_confidence

        # Calculate average confidence
        avg_confidence = confidence_sum / len(results)

        # Create merged result
        merged = ThermographyExtractionResult(
            equipment=base.equipment,
            calibration=base.calibration,
            test_conditions=base.test_conditions,
            thermal_data=base.thermal_data,
            hotspots=all_hotspots,
            overall_confidence=avg_confidence,
            extraction_errors=all_errors,
            metadata=base.metadata,
        )

        # Update metadata with all page numbers
        if merged.metadata and all_page_numbers:
            merged.metadata.page_numbers = sorted(set(all_page_numbers))

        # Recalculate needs_review
        merged.needs_review = self._check_needs_review(merged)

        logger.info(
            f"Merged {len(results)} batch results: "
            f"{len(all_hotspots)} total hotspots, "
            f"confidence={avg_confidence:.2f}"
        )

        return merged

    def _check_needs_review(self, result: ThermographyExtractionResult) -> bool:
        """Check if thermography extraction needs human review.

        Reviews are flagged when:
        - Overall confidence is below threshold
        - Critical or serious hotspots are detected
        - Emissivity setting is unusual
        - Any hotspot temperature has low confidence

        Args:
            result: The extraction result to check.

        Returns:
            bool: True if the extraction needs review.
        """
        # Check overall confidence
        if result.overall_confidence < self.CONFIDENCE_THRESHOLD:
            return True

        # Critical or serious hotspots ALWAYS need review
        if result.critical_count > 0 or result.serious_count > 0:
            result.extraction_errors.append(
                f"Critical/serious hotspots detected: {result.critical_count} critical, "
                f"{result.serious_count} serious"
            )
            return True

        # Check emissivity setting
        if result.thermal_data.emissivity is not None:
            emissivity = result.thermal_data.emissivity.value
            if isinstance(emissivity, (int, float)):
                if abs(float(emissivity) - self.EMISSIVITY_EXPECTED) > self.EMISSIVITY_TOLERANCE:
                    result.extraction_errors.append(
                        f"Unusual emissivity setting: {emissivity} "
                        f"(expected ~{self.EMISSIVITY_EXPECTED})"
                    )
                    return True

        # Check for low confidence hotspots
        for hotspot in result.hotspots:
            if hotspot.max_temperature.confidence < self.CONFIDENCE_THRESHOLD:
                return True

        return False
