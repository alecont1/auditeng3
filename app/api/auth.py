"""Authentication API endpoints.

This module provides:
- POST /api/auth/register - Create new user account
- POST /api/auth/login - Login with credentials
- GET /api/auth/me - Get current user information
- POST /api/auth/refresh - Refresh access token
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    CurrentUser,
    create_access_token,
    hash_password,
    verify_password,
)
from app.core.dependencies import get_db
from app.core.exceptions import AuthenticationError, AuditEngException
from app.db.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account and return an access token.",
)
async def register(
    request: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Register a new user.

    Args:
        request: Registration data with email and password.
        db: Database session.

    Returns:
        TokenResponse with JWT access token.

    Raises:
        AuditEngException: If email is already registered (409 Conflict).
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise AuditEngException(
            detail="Email already registered",
            status_code=status.HTTP_409_CONFLICT,
            error_code="AUTH_006",
        )

    # Create new user
    user = User(
        email=request.email,
        hashed_password=hash_password(request.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Generate access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(access_token=access_token)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with credentials",
    description="Authenticate with email and password to receive an access token.",
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Login with email and password.

    Uses OAuth2PasswordRequestForm for standard OAuth2 flow compatibility.
    The 'username' field contains the email address.

    Args:
        form_data: OAuth2 form with username (email) and password.
        db: Database session.

    Returns:
        TokenResponse with JWT access token.

    Raises:
        AuthenticationError: If credentials are invalid (401 Unauthorized).
    """
    # Find user by email (username field contains email)
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationError(
            detail="Invalid email or password",
            error_code="AUTH_007",
        )

    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        raise AuthenticationError(
            detail="Invalid email or password",
            error_code="AUTH_007",
        )

    # Check if user is active
    if not user.is_active:
        raise AuthenticationError(
            detail="User account is inactive",
            error_code="AUTH_005",
        )

    # Generate access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(access_token=access_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get information about the currently authenticated user.",
)
async def get_me(current_user: CurrentUser) -> UserResponse:
    """Get current authenticated user information.

    Args:
        current_user: The authenticated user from the token.

    Returns:
        UserResponse with user information.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get a new access token using the current valid token.",
)
async def refresh_token(current_user: CurrentUser) -> TokenResponse:
    """Refresh the access token.

    Requires a valid (non-expired) token. Returns a new token
    with a fresh expiration time.

    Args:
        current_user: The authenticated user from the token.

    Returns:
        TokenResponse with new JWT access token.
    """
    access_token = create_access_token(data={"sub": str(current_user.id)})
    return TokenResponse(access_token=access_token)
