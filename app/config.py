"""Application configuration using pydantic-settings.

This module centralizes all application configuration using environment variables
with type validation and defaults.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Environment variables can be set directly or via a .env file.
    """

    # Application metadata
    APP_NAME: str = "AuditEng"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database configuration
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/auditeng"

    # Redis configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS configuration - explicit origins only, no wildcards
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Uses lru_cache to avoid re-reading environment variables on every call.

    Returns:
        Settings: Application configuration instance.
    """
    return Settings()
