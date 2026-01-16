"""AuditEng services package."""

from app.services.storage import (
    delete_task_files,
    get_file,
    get_file_path,
    save_file,
)
from app.services.extraction import (
    detect_test_type,
    extract_pdf_images,
    extract_pdf_text,
    get_extractor,
    process_document,
)
from app.services.finding import (
    FindingService,
    generate_findings_from_validation,
)
from app.services.verdict import (
    VerdictService,
    compute_compliance_score,
    compute_verdict,
)

__all__ = [
    # Storage
    "delete_task_files",
    "get_file",
    "get_file_path",
    "save_file",
    # Extraction
    "detect_test_type",
    "extract_pdf_images",
    "extract_pdf_text",
    "get_extractor",
    "process_document",
    # Finding
    "FindingService",
    "generate_findings_from_validation",
    # Verdict
    "VerdictService",
    "compute_compliance_score",
    "compute_verdict",
]
