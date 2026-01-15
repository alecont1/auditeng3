"""User schema definitions."""

from pydantic import EmailStr, Field

from app.schemas.base import BaseSchema, IDMixin, TimestampMixin


class UserBase(BaseSchema):
    """Base user schema with common fields."""

    email: EmailStr
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=8, description="User password (min 8 characters)")


class UserInDB(UserBase, IDMixin, TimestampMixin):
    """User schema as stored in database (includes hashed password)."""

    hashed_password: str


class User(UserBase, IDMixin, TimestampMixin):
    """User schema for API responses (excludes password)."""

    pass
