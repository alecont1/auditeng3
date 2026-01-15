"""AuditEng Pydantic schemas."""

from app.schemas.base import BaseSchema, IDMixin, TimestampMixin
from app.schemas.enums import (
    AnalysisVerdict,
    EquipmentType,
    FindingSeverity,
    TaskStatus,
    TestType,
)
from app.schemas.user import User, UserBase, UserCreate, UserInDB
from app.schemas.task import Task, TaskBase, TaskCreate
from app.schemas.analysis import (
    Analysis,
    AnalysisBase,
    AnalysisCreate,
    ExtractionResult,
    ValidationResult,
)
from app.schemas.finding import Finding, FindingBase, FindingCreate, FindingEvidence

__all__ = [
    # Base
    "BaseSchema",
    "IDMixin",
    "TimestampMixin",
    # Enums
    "TaskStatus",
    "AnalysisVerdict",
    "FindingSeverity",
    "EquipmentType",
    "TestType",
    # User
    "UserBase",
    "UserCreate",
    "UserInDB",
    "User",
    # Task
    "TaskBase",
    "TaskCreate",
    "Task",
    # Analysis
    "AnalysisBase",
    "AnalysisCreate",
    "Analysis",
    "ExtractionResult",
    "ValidationResult",
    # Finding
    "FindingBase",
    "FindingCreate",
    "Finding",
    "FindingEvidence",
]
