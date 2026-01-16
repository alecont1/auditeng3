"""JWT authentication and password hashing utilities for AuditEng.

This module provides:
- Password hashing using bcrypt via passlib
- JWT token generation and verification using python-jose
- FastAPI dependency for protected routes
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.dependencies import get_db
from app.core.exceptions import AuthenticationError
from app.db.models.user import User

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# JWT configuration
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password to hash.

    Returns:
        Hashed password string.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password to verify.
        hashed_password: Hashed password to compare against.

    Returns:
        True if passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token.

    Args:
        data: Payload data to encode in the token. Should include "sub" for user ID.
        expires_delta: Optional custom expiration time. Defaults to settings value.

    Returns:
        Encoded JWT token string.
    """
    settings = get_settings()
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict | None:
    """Verify and decode a JWT token.

    Args:
        token: JWT token string to verify.

    Returns:
        Decoded payload dict if valid, None if invalid or expired.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """FastAPI dependency to get the current authenticated user.

    Extracts and validates the JWT token from the Authorization header,
    then fetches the corresponding user from the database.

    Args:
        token: JWT token extracted from Authorization header.
        db: Database session.

    Returns:
        User model instance for the authenticated user.

    Raises:
        AuthenticationError: If token is invalid, expired, or user not found.
    """
    payload = verify_token(token)
    if payload is None:
        raise AuthenticationError(
            detail="Invalid or expired token",
            error_code="AUTH_002",
        )

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise AuthenticationError(
            detail="Token missing user identifier",
            error_code="AUTH_003",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise AuthenticationError(
            detail="User not found",
            error_code="AUTH_004",
        )

    if not user.is_active:
        raise AuthenticationError(
            detail="User account is inactive",
            error_code="AUTH_005",
        )

    return user


# Type alias for cleaner endpoint signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
