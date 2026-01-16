"""Extraction module for AI-powered document data extraction.

This module provides the Instructor + Claude integration for extracting
structured data from commissioning reports (PDFs and images).
"""

from app.core.extraction.client import (
    DEFAULT_MODEL,
    MAX_RETRIES,
    MAX_TOKENS,
    extract_structured,
    get_anthropic_client,
    get_instructor_client,
)
from app.core.extraction.base import BaseExtractor
from app.core.extraction.fat import (
    FATChecklistItem,
    FATExtractionResult,
    FATExtractor,
    FATSignature,
    FATSpecification,
    FATTestConditions,
)
from app.core.extraction.grounding import (
    GroundingExtractionResult,
    GroundingExtractor,
    GroundingMeasurement,
    GroundingTestConditions,
)
from app.core.extraction.megger import (
    InsulationReading,
    MeggerExtractionResult,
    MeggerExtractor,
    MeggerMeasurement,
    MeggerTestConditions,
)
from app.core.extraction.thermography import (
    Hotspot,
    HotspotSeverity,
    ThermalImageData,
    ThermographyExtractionResult,
    ThermographyExtractor,
    ThermographyTestConditions,
)
from app.core.extraction.schemas import (
    BaseExtractionResult,
    CalibrationInfo,
    EquipmentInfo,
    ExtractionMetadata,
    FieldConfidence,
)

__all__ = [
    # Base
    "BaseExtractor",
    # FAT
    "FATChecklistItem",
    "FATExtractionResult",
    "FATExtractor",
    "FATSignature",
    "FATSpecification",
    "FATTestConditions",
    # Grounding
    "GroundingExtractionResult",
    "GroundingExtractor",
    "GroundingMeasurement",
    "GroundingTestConditions",
    # Megger
    "InsulationReading",
    "MeggerExtractionResult",
    "MeggerExtractor",
    "MeggerMeasurement",
    "MeggerTestConditions",
    # Thermography
    "Hotspot",
    "HotspotSeverity",
    "ThermalImageData",
    "ThermographyExtractionResult",
    "ThermographyExtractor",
    "ThermographyTestConditions",
    # Client
    "DEFAULT_MODEL",
    "MAX_RETRIES",
    "MAX_TOKENS",
    "extract_structured",
    "get_anthropic_client",
    "get_instructor_client",
    # Schemas
    "BaseExtractionResult",
    "CalibrationInfo",
    "EquipmentInfo",
    "ExtractionMetadata",
    "FieldConfidence",
]
