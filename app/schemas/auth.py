"""Authentication schema definitions."""

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.base import BaseSchema


class RegisterRequest(BaseSchema):
    """Schema for user registration request."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        description="User password (minimum 8 characters)",
    )


class LoginRequest(BaseSchema):
    """Schema for user login request.

    Note: OAuth2PasswordRequestForm uses 'username' field,
    but we use 'email' for clarity in our API.
    """

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseSchema):
    """Schema for authentication token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class UserResponse(BaseSchema):
    """Schema for user information response."""

    id: UUID = Field(..., description="User unique identifier")
    email: EmailStr = Field(..., description="User email address")
    is_active: bool = Field(..., description="Whether user account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
