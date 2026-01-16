"""Instructor-wrapped Claude client for structured extraction.

This module provides the AI extraction infrastructure using Instructor
with Anthropic's Claude model. Instructor enables reliable structured
output with automatic validation and retry.
"""

import base64
import logging
from datetime import datetime, timezone
from functools import lru_cache
from typing import TypeVar

import anthropic
import instructor
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.core.extraction.schemas import ExtractionMetadata

logger = logging.getLogger(__name__)

# Type variable for generic extraction
T = TypeVar("T", bound=BaseModel)

# Default configuration
DEFAULT_MODEL = "claude-sonnet-4-20250514"
MAX_RETRIES = 3
MAX_TOKENS = 4096


@lru_cache
def get_anthropic_client() -> anthropic.Anthropic:
    """Get cached Anthropic client.

    Returns:
        Anthropic: Configured Anthropic client.

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set.
    """
    settings = get_settings()
    if not settings.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


@lru_cache
def get_instructor_client() -> instructor.Instructor:
    """Get cached Instructor-wrapped Anthropic client.

    Uses Instructor's ANTHROPIC_JSON mode for structured output.

    Returns:
        Instructor: Configured Instructor client.
    """
    client = get_anthropic_client()
    return instructor.from_anthropic(client, mode=instructor.Mode.ANTHROPIC_JSON)


def _build_image_content(images: list[str]) -> list[dict]:
    """Build image content blocks for Claude Vision.

    Args:
        images: List of base64-encoded image data.

    Returns:
        list[dict]: Content blocks for the API request.
    """
    content = []
    for img_data in images:
        # Detect media type from base64 header or default to jpeg
        media_type = "image/jpeg"
        if img_data.startswith("data:"):
            # Extract media type from data URL
            header_end = img_data.find(",")
            if header_end > 0:
                header = img_data[:header_end]
                if "image/png" in header:
                    media_type = "image/png"
                elif "image/tiff" in header:
                    media_type = "image/tiff"
                img_data = img_data[header_end + 1 :]

        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": img_data,
                },
            }
        )
    return content


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    reraise=True,
)
async def extract_structured(
    prompt: str,
    response_model: type[T],
    images: list[str] | None = None,
    text_content: str | None = None,
    max_retries: int = MAX_RETRIES,
    model: str = DEFAULT_MODEL,
) -> tuple[T, ExtractionMetadata]:
    """Extract structured data using Instructor and Claude.

    Uses Instructor to get validated Pydantic model responses from Claude.
    Automatically retries on validation failures.

    Args:
        prompt: System prompt describing the extraction task.
        response_model: Pydantic model class for the response.
        images: Optional list of base64-encoded images.
        text_content: Optional text content to analyze.
        max_retries: Maximum retry attempts (default: 3).
        model: Claude model to use (default: claude-sonnet-4).

    Returns:
        tuple[T, ExtractionMetadata]: Extracted data and metadata.

    Raises:
        anthropic.APIError: If API call fails after retries.
        instructor.exceptions.ValidationError: If response validation fails.
    """
    client = get_instructor_client()
    start_time = datetime.now(timezone.utc)

    # Build user message content
    user_content = []

    if images:
        user_content.extend(_build_image_content(images))

    if text_content:
        user_content.append({"type": "text", "text": text_content})

    # If no images or text, use a simple text prompt
    if not user_content:
        user_content = [{"type": "text", "text": "Please extract the requested information."}]

    try:
        # Use Instructor's create method with response_model
        response = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            max_retries=max_retries,
            system=prompt,
            messages=[{"role": "user", "content": user_content}],
            response_model=response_model,
        )

        # Build metadata
        metadata = ExtractionMetadata(
            model_version=model,
            extraction_timestamp=datetime.now(timezone.utc),
            page_numbers=[],
            total_tokens_used=0,  # Instructor doesn't expose this directly
            retry_count=0,
        )

        logger.info(
            f"Extraction complete: model={model}, "
            f"response_type={response_model.__name__}"
        )

        return response, metadata

    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {e}")
        raise
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        raise
