"""FastAPI application factory for AuditEng.

This module creates and configures the FastAPI application instance with:
- Lifespan management for startup/shutdown events
- Database connection validation
- CORS middleware
- Exception handlers
- API routers
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import get_settings
from app.db import async_session_factory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifespan events.

    Performs startup validation and cleanup on shutdown.

    Args:
        app: The FastAPI application instance.

    Yields:
        None after startup is complete.
    """
    # Startup
    logger.info("AuditEng API starting")

    # Verify database connection
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            logger.info("Database connection verified")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        # Don't raise - let health check report the status
        # This allows the app to start even if DB is temporarily unavailable

    yield

    # Shutdown
    logger.info("AuditEng API shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-powered electrical engineering audit analysis system",
        lifespan=lifespan,
    )

    # Add CORS middleware with explicit origins (no wildcards)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )

    # Import and include routers
    from app.api.health import router as health_router
    from app.api.upload import router as upload_router

    app.include_router(health_router)
    app.include_router(upload_router)

    # Register exception handlers
    from app.core.exceptions import (
        AuditEngException,
        audit_eng_exception_handler,
        generic_exception_handler,
    )

    app.add_exception_handler(AuditEngException, audit_eng_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    return app


# Create the application instance
app = create_app()
