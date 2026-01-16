"""FastAPI dependency injection functions.

This module provides common dependencies used across API endpoints.
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.config import get_settings as _get_settings
from app.db import get_async_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database session dependency.

    Provides an async database session that is automatically closed
    when the request completes.

    Yields:
        AsyncSession: Database session for the request.
    """
    async for session in get_async_session():
        yield session


def get_settings() -> Settings:
    """Settings dependency.

    Returns the cached application settings.

    Returns:
        Settings: Application configuration.
    """
    return _get_settings()


# Type aliases for cleaner endpoint signatures
DbSession = Annotated[AsyncSession, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]
