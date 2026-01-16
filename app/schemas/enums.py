"""Enumerations for AuditEng domain models."""

from enum import StrEnum


class TaskStatus(StrEnum):
    """Status of an analysis task."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisVerdict(StrEnum):
    """Verdict result of an analysis."""

    APPROVED = "approved"
    REVIEW = "review"
    REJECTED = "rejected"


class FindingSeverity(StrEnum):
    """Severity level of a finding."""

    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


class EquipmentType(StrEnum):
    """Type of electrical equipment being analyzed."""

    PANEL = "panel"
    UPS = "ups"
    ATS = "ats"
    GEN = "gen"
    XFMR = "xfmr"


class TestType(StrEnum):
    """Type of electrical test performed."""

    GROUNDING = "grounding"
    MEGGER = "megger"
    THERMOGRAPHY = "thermography"
    FAT = "fat"  # Factory Acceptance Test
