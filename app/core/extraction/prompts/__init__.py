"""Extraction prompts for different test types.

This module exports the system prompts used by each extractor type.
"""

from app.core.extraction.prompts.grounding import GROUNDING_EXTRACTION_PROMPT
from app.core.extraction.prompts.megger import MEGGER_EXTRACTION_PROMPT
from app.core.extraction.prompts.thermography import THERMOGRAPHY_EXTRACTION_PROMPT

__all__ = [
    "GROUNDING_EXTRACTION_PROMPT",
    "MEGGER_EXTRACTION_PROMPT",
    "THERMOGRAPHY_EXTRACTION_PROMPT",
]
