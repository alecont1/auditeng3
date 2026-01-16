"""Extraction orchestration service.

This module provides the extraction pipeline orchestration:
- Test type detection from document content
- PDF text and image extraction
- Routing to appropriate extractors
- Multi-page document support
"""

import logging
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel

from app.core.extraction import (
    GroundingExtractor,
    MeggerExtractor,
    ThermographyExtractor,
)
from app.core.extraction.base import BaseExtractor
from app.core.extraction.schemas import BaseExtractionResult
from app.schemas.enums import TestType

logger = logging.getLogger(__name__)


# Keywords for test type detection
TEST_TYPE_KEYWORDS: dict[str, list[str]] = {
    "grounding": [
        "ground resistance",
        "earth resistance",
        "resistance to ground",
        "grounding test",
        "soil resistivity",
        "aterramento",
        "resistência de aterramento",
    ],
    "megger": [
        "insulation resistance",
        "megger",
        "ir test",
        "polarization index",
        "insulation test",
        "megaohm",
        "resistência de isolação",
        "isolamento",
    ],
    "thermography": [
        "thermal",
        "infrared",
        "thermograph",
        "temperature",
        "hotspot",
        "delta-t",
        "termografia",
        "termográfico",
        "imagem térmica",
    ],
}


def detect_test_type(content: str) -> TestType | None:
    """Detect test type from document content using keyword matching.

    Uses weighted keyword matching to identify the test type.

    Args:
        content: Text content from the document.

    Returns:
        TestType enum value, or None if unable to detect.
    """
    content_lower = content.lower()

    scores: dict[str, int] = {
        "grounding": 0,
        "megger": 0,
        "thermography": 0,
    }

    for test_type, keywords in TEST_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in content_lower:
                scores[test_type] += 1

    # Get the type with highest score
    max_score = max(scores.values())
    if max_score == 0:
        logger.warning("Could not detect test type from content")
        return None

    detected = max(scores, key=lambda k: scores[k])
    logger.info(f"Detected test type: {detected} (score: {max_score})")

    return TestType(detected)


def get_extractor(test_type: TestType | str) -> BaseExtractor | None:
    """Get extractor instance for test type.

    Args:
        test_type: TestType enum or string value.

    Returns:
        Appropriate extractor instance, or None if unknown.
    """
    type_str = test_type.value if isinstance(test_type, TestType) else test_type

    extractors: dict[str, BaseExtractor] = {
        "grounding": GroundingExtractor(),
        "megger": MeggerExtractor(),
        "thermography": ThermographyExtractor(),
    }

    return extractors.get(type_str)


async def extract_pdf_text(file_path: Path) -> list[tuple[int, str]]:
    """Extract text from PDF, page by page.

    Uses PyMuPDF for reliable text extraction.

    Args:
        file_path: Path to the PDF file.

    Returns:
        List of (page_number, text_content) tuples.
    """
    import pymupdf

    pages: list[tuple[int, str]] = []

    doc = pymupdf.open(file_path)
    try:
        for page_num, page in enumerate(doc, 1):
            text = page.get_text()
            if text.strip():  # Only include non-empty pages
                pages.append((page_num, text))
                logger.debug(f"Extracted {len(text)} chars from page {page_num}")
    finally:
        doc.close()

    logger.info(f"Extracted text from {len(pages)} pages")
    return pages


async def extract_pdf_images(file_path: Path) -> list[tuple[int, bytes]]:
    """Extract images from PDF for thermal analysis.

    Extracts embedded images that may contain thermal camera captures.

    Args:
        file_path: Path to the PDF file.

    Returns:
        List of (page_number, image_bytes) tuples.
    """
    import pymupdf

    images: list[tuple[int, bytes]] = []

    doc = pymupdf.open(file_path)
    try:
        for page_num, page in enumerate(doc, 1):
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                xref = img[0]
                try:
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    images.append((page_num, image_bytes))
                    logger.debug(
                        f"Extracted image {img_index + 1} from page {page_num} "
                        f"({len(image_bytes)} bytes)"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to extract image {img_index + 1} from page {page_num}: {e}"
                    )
    finally:
        doc.close()

    logger.info(f"Extracted {len(images)} images from PDF")
    return images


async def process_document(
    task_id: UUID,
    file_path: Path,
    test_type: TestType | str | None = None,
) -> BaseExtractionResult:
    """Process a document through the extraction pipeline.

    Orchestrates the full extraction flow:
    1. Determine file type (PDF vs image)
    2. Extract content (text and/or images)
    3. Detect test type if not provided
    4. Route to appropriate extractor
    5. Return structured extraction result

    Args:
        task_id: Task ID for tracking.
        file_path: Path to uploaded file.
        test_type: Optional test type (auto-detected if not provided).

    Returns:
        Extraction result from appropriate extractor.

    Raises:
        ValueError: If test type is unknown or unsupported.
        FileNotFoundError: If file does not exist.
    """
    logger.info(f"Processing document for task {task_id}: {file_path}")

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # 1. Determine file type
    suffix = file_path.suffix.lower()
    is_image = suffix in [".png", ".jpg", ".jpeg", ".tiff", ".tif"]

    # Normalize test_type to TestType enum
    if test_type and isinstance(test_type, str):
        test_type = TestType(test_type)

    # 2. Extract content based on file type
    if is_image:
        # Direct image - likely thermography
        logger.info("Processing as direct image file")
        with open(file_path, "rb") as f:
            image_data = f.read()
        content: list[tuple[int, bytes]] | str = [(1, image_data)]
        test_type = test_type or TestType.THERMOGRAPHY

    else:
        # PDF - extract text and detect type
        logger.info("Processing as PDF document")
        pages = await extract_pdf_text(file_path)
        all_text = "\n".join(text for _, text in pages)

        if not test_type:
            test_type = detect_test_type(all_text)
            if not test_type:
                raise ValueError(
                    "Could not auto-detect test type. "
                    "Please specify test_type parameter."
                )

        if test_type == TestType.THERMOGRAPHY:
            # Extract images from PDF for thermal analysis
            content = await extract_pdf_images(file_path)
            if not content:
                raise ValueError("No images found in PDF for thermography analysis")
        else:
            content = all_text

    # 3. Get appropriate extractor
    extractor = get_extractor(test_type)
    if not extractor:
        raise ValueError(f"Unknown test type: {test_type}")

    logger.info(f"Using {extractor.__class__.__name__} for test type: {test_type}")

    # 4. Run extraction
    if test_type == TestType.THERMOGRAPHY and isinstance(content, list):
        # Special handling for thermal images
        images = [img for _, img in content]
        page_numbers = [pg for pg, _ in content]
        result = await extractor.extract_from_images(
            images=images,
            page_numbers=page_numbers,
        )
    else:
        # Text-based extraction
        result = await extractor.extract(content=content)

    logger.info(
        f"Extraction complete: confidence={result.overall_confidence:.2f}, "
        f"needs_review={result.needs_review}"
    )

    return result
