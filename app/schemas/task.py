"""Task schema definitions."""

from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, IDMixin, TimestampMixin
from app.schemas.enums import TaskStatus


class TaskBase(BaseSchema):
    """Base task schema with common fields."""

    status: TaskStatus = TaskStatus.QUEUED
    original_filename: str
    file_size: int = Field(..., ge=0, description="File size in bytes")


class TaskCreate(TaskBase):
    """Schema for creating a new task."""

    user_id: UUID


class Task(TaskBase, IDMixin, TimestampMixin):
    """Task schema for API responses."""

    user_id: UUID
    analysis_id: UUID | None = None
