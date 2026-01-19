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


# Keywords for test type detection (weighted by specificity)
# High-weight keywords are very specific to the test type
TEST_TYPE_KEYWORDS: dict[str, list[str]] = {
    "grounding": [
        # English terms
        "ground resistance",
        "earth resistance",
        "resistance to ground",
        "grounding test",
        "grounding report",
        "grounding system",
        "soil resistivity",
        "ground grid",
        "ground electrode",
        "ground rod",
        "ground mesh",
        "fall of potential",
        "3-point method",
        "step voltage",
        "touch voltage",
        # Portuguese terms
        "aterramento",
        "resistência de aterramento",
        "malha de aterramento",
        "sistema de aterramento",
        "eletrodo de aterramento",
        "haste de aterramento",
        # Common in reports
        "ohm",  # Grounding uses low ohm values
        "spda",  # Lightning protection system
        "nbr 5419",
        "nbr 5410",
        "ieee 80",
        "ieee 81",
    ],
    "megger": [
        # English terms
        "insulation resistance",
        "megger",
        "ir test",
        "polarization index",
        "insulation test",
        "megaohm",
        "dielectric absorption",
        "absorption ratio",
        "pi test",
        "dar test",
        # Portuguese terms
        "resistência de isolação",
        "resistência de isolamento",
        "isolamento",
        "teste de isolação",
        "índice de polarização",
        # Common in reports
        "ieee 43",
        "neta",
        "1 minute",
        "10 minute",
    ],
    "thermography": [
        # English terms
        "thermal",
        "infrared",
        "thermograph",
        "thermographic",
        "temperature",
        "hotspot",
        "hot spot",
        "delta-t",
        "delta t",
        "emissivity",
        "thermal image",
        "ir inspection",
        "thermal inspection",
        "thermal scan",
        # Portuguese terms
        "termografia",
        "termográfico",
        "termográfica",
        "imagem térmica",
        "ponto quente",
        "inspeção térmica",
        "análise térmica",
        # Common in reports
        "flir",
        "fluke",
        "°c",  # Celsius symbol
        "celsius",
    ],
}


def detect_test_type_from_filename(filename: str) -> TestType | None:
    """Detect test type from filename.

    Fallback detection using filename patterns.

    Args:
        filename: Name of the file (with or without path).

    Returns:
        TestType enum value, or None if unable to detect.
    """
    filename_lower = filename.lower()

    # Check for explicit test type indicators in filename
    filename_patterns = {
        "grounding": ["grounding", "ground", "aterramento", "spda", "earth"],
        "megger": ["megger", "insulation", "isolamento", "isolação", "ir-test"],
        "thermography": [
            "thermo",
            "thermal",
            "termograf",
            "infrared",
            "ir-scan",
            "flir",
        ],
    }

    for test_type, patterns in filename_patterns.items():
        for pattern in patterns:
            if pattern in filename_lower:
                logger.info(f"Detected test type from filename: {test_type}")
                return TestType(test_type)

    return None


def detect_test_type(content: str, filename: str | None = None) -> TestType | None:
    """Detect test type from document content using keyword matching.

    Uses weighted keyword matching to identify the test type.
    Falls back to filename detection if content-based detection fails.

    Args:
        content: Text content from the document.
        filename: Optional filename for fallback detection.

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
        logger.warning("Could not detect test type from content, trying filename")
        # Fallback to filename detection
        if filename:
            return detect_test_type_from_filename(filename)
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


async def extract_pdf_images(
    file_path: Path,
    min_width: int = 200,
    min_height: int = 200,
    max_images: int = 20,
    max_size_bytes: int = 5_000_000,  # 5MB per image max
) -> list[tuple[int, bytes]]:
    """Extract images from PDF for thermal analysis.

    Extracts embedded images that may contain thermal camera captures.
    Filters out small images (logos, icons) and limits total count to avoid
    exceeding API request size limits.

    Args:
        file_path: Path to the PDF file.
        min_width: Minimum image width to include (filters logos/icons).
        min_height: Minimum image height to include.
        max_images: Maximum number of images to return (largest first).
        max_size_bytes: Maximum size per image in bytes.

    Returns:
        List of (page_number, image_bytes) tuples.
    """
    import pymupdf

    # Collect all candidate images with metadata
    candidates: list[tuple[int, bytes, int, int, int]] = []  # (page, bytes, width, height, size)

    doc = pymupdf.open(file_path)
    try:
        for page_num, page in enumerate(doc, 1):
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                xref = img[0]
                try:
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    width = base_image.get("width", 0)
                    height = base_image.get("height", 0)

                    # Filter: skip small images (likely logos, icons, borders)
                    if width < min_width or height < min_height:
                        logger.debug(
                            f"Skipping small image {img_index + 1} from page {page_num}: "
                            f"{width}x{height} (min: {min_width}x{min_height})"
                        )
                        continue

                    # Filter: skip oversized images
                    if len(image_bytes) > max_size_bytes:
                        logger.warning(
                            f"Skipping oversized image {img_index + 1} from page {page_num}: "
                            f"{len(image_bytes)} bytes (max: {max_size_bytes})"
                        )
                        continue

                    candidates.append((page_num, image_bytes, width, height, len(image_bytes)))
                    logger.debug(
                        f"Found thermal image candidate on page {page_num}: "
                        f"{width}x{height}, {len(image_bytes)} bytes"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to extract image {img_index + 1} from page {page_num}: {e}"
                    )
    finally:
        doc.close()

    logger.info(f"Found {len(candidates)} thermal image candidates")

    # Sort by size (larger images are more likely to be thermal captures)
    # and take top N
    candidates.sort(key=lambda x: x[2] * x[3], reverse=True)  # Sort by area
    selected = candidates[:max_images]

    # Sort back by page order for logical processing
    selected.sort(key=lambda x: x[0])

    images = [(page, img_bytes) for page, img_bytes, _, _, _ in selected]

    logger.info(
        f"Selected {len(images)} images from {len(candidates)} candidates "
        f"(max: {max_images})"
    )
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
            test_type = detect_test_type(all_text, filename=file_path.name)
            if not test_type:
                raise ValueError(
                    "Could not auto-detect test type from content or filename. "
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
