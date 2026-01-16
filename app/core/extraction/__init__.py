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
