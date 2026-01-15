"""Base Pydantic schemas and mixins."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration for all models."""

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        use_enum_values=True,
        extra="forbid",
    )


class IDMixin(BaseModel):
    """Mixin providing ID field."""

    id: UUID


class TimestampMixin(BaseModel):
    """Mixin providing timestamp fields."""

    created_at: datetime
    updated_at: datetime
