"""Upload request/response schemas for file upload API."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema
from app.schemas.enums import TaskStatus


# Maximum file size: 50MB
MAX_FILE_SIZE: int = 50 * 1024 * 1024


class AllowedFileType(StrEnum):
    """Allowed file types for upload."""

    PDF = "pdf"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    TIFF = "tiff"


# Set of allowed extensions for validation
ALLOWED_EXTENSIONS: set[str] = {ext.value for ext in AllowedFileType}


class UploadResponse(BaseSchema):
    """Response schema for successful file upload."""

    task_id: UUID
    filename: str
    file_size: int = Field(..., ge=0, description="File size in bytes")
    status: TaskStatus
    created_at: datetime


class UploadError(BaseSchema):
    """Error response schema for upload failures."""

    error_code: str
    detail: str
