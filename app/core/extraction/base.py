"""Base extractor class for all test-type extractors.

This module defines the abstract base class that all specific
extractors (Grounding, Megger, Thermography) inherit from.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from app.core.extraction.client import extract_structured
from app.core.extraction.schemas import BaseExtractionResult, FieldConfidence

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """Abstract base class for all test-type extractors.

    Defines the common interface and patterns that all extractors must follow.
    Subclasses implement test-type-specific schemas and prompts.

    Attributes:
        CONFIDENCE_THRESHOLD: Minimum confidence before flagging for review.
    """

    CONFIDENCE_THRESHOLD: float = 0.7

    @property
    @abstractmethod
    def test_type(self) -> str:
        """Return test type identifier.

        Returns:
            str: One of 'grounding', 'megger', 'thermography'.
        """
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt for this extraction type.

        The prompt should describe:
        - What data to extract
        - Expected format and units
        - How to assess confidence

        Returns:
            str: System prompt for Claude.
        """
        pass

    @abstractmethod
    def get_response_model(self) -> type[BaseExtractionResult]:
        """Return the Pydantic model for extraction response.

        Returns:
            type[BaseExtractionResult]: Subclass of BaseExtractionResult.
        """
        pass

    async def extract(
        self,
        content: str | list[str],
        page_numbers: list[int] | None = None,
    ) -> BaseExtractionResult:
        """Extract structured data from content.

        Args:
            content: Text content (str) or list of base64-encoded images.
            page_numbers: Optional list of page numbers being processed.

        Returns:
            BaseExtractionResult: Extraction result with confidence scores.
        """
        is_image = isinstance(content, list)

        logger.info(
            f"Starting {self.test_type} extraction: "
            f"content_type={'image' if is_image else 'text'}, "
            f"pages={page_numbers or 'unknown'}"
        )

        # Call the extraction function
        result, metadata = await extract_structured(
            prompt=self.system_prompt,
            response_model=self.get_response_model(),
            images=content if is_image else None,
            text_content=content if not is_image else None,
        )

        # Update metadata with page numbers
        if page_numbers:
            metadata.page_numbers = page_numbers

        # Set metadata on result
        result.metadata = metadata

        # Check if needs review based on confidence
        result.needs_review = self._check_needs_review(result)

        logger.info(
            f"Extraction complete: test_type={self.test_type}, "
            f"overall_confidence={result.overall_confidence:.2f}, "
            f"needs_review={result.needs_review}"
        )

        return result

    def _check_needs_review(self, result: BaseExtractionResult) -> bool:
        """Check if any field has confidence below threshold.

        Scans all FieldConfidence attributes in the result to find
        any with confidence below CONFIDENCE_THRESHOLD.

        Args:
            result: The extraction result to check.

        Returns:
            bool: True if any field needs review.
        """
        # Check overall confidence first
        if result.overall_confidence < self.CONFIDENCE_THRESHOLD:
            return True

        # Recursively check all FieldConfidence instances
        return self._has_low_confidence_field(result)

    def _has_low_confidence_field(self, obj: Any) -> bool:
        """Recursively check for low-confidence fields.

        Args:
            obj: Object to scan for FieldConfidence instances.

        Returns:
            bool: True if any FieldConfidence has low confidence.
        """
        if isinstance(obj, FieldConfidence):
            return obj.confidence < self.CONFIDENCE_THRESHOLD

        if hasattr(obj, "model_fields"):
            # Pydantic model
            for field_name in obj.model_fields:
                value = getattr(obj, field_name, None)
                if value is not None and self._has_low_confidence_field(value):
                    return True

        if isinstance(obj, list):
            for item in obj:
                if self._has_low_confidence_field(item):
                    return True

        return False

    def calculate_overall_confidence(self, *confidences: FieldConfidence | None) -> float:
        """Calculate overall confidence from field confidences.

        Computes the mean of all non-None field confidences.

        Args:
            *confidences: FieldConfidence instances to average.

        Returns:
            float: Mean confidence score.
        """
        valid = [c.confidence for c in confidences if c is not None]
        if not valid:
            return 0.0
        return sum(valid) / len(valid)
