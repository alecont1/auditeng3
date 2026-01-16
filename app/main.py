"""FastAPI application factory for AuditEng.

This module creates and configures the FastAPI application instance with:
- Lifespan management for startup/shutdown events
- Database connection validation
- Rate limiting middleware
- CORS middleware
- Exception handlers
- API routers
- OpenAPI documentation
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

# OpenAPI tags metadata for grouping endpoints
tags_metadata = [
    {
        "name": "analyses",
        "description": "Analysis submission, status polling, and results retrieval with authentication.",
    },
    {
        "name": "health",
        "description": "Health check endpoints for monitoring and orchestration (liveness, readiness probes).",
    },
    {
        "name": "auth",
        "description": "Authentication endpoints for user registration, login, and token management.",
    },
    {
        "name": "upload",
        "description": "Document upload endpoints for commissioning reports (PDF, images).",
    },
    {
        "name": "tasks",
        "description": "Task status tracking for background processing jobs.",
    },
    {
        "name": "validation",
        "description": "Validation rules, standards thresholds, and compliance checking.",
    },
    {
        "name": "reports",
        "description": "PDF report generation and download.",
    },
    {
        "name": "audit",
        "description": "Audit trail retrieval for compliance verification.",
    },
]

# OpenAPI description with markdown
API_DESCRIPTION = """
## AuditEng API

AI-powered electrical engineering audit analysis system for commissioning reports.

### Overview

AuditEng automates the analysis of commissioning reports for data center electrical systems.
The system uses AI (Claude) to extract structured data from PDFs and images, then applies
deterministic validation rules against industry standards (NETA, IEEE, Microsoft CxPOR).

### Authentication

All endpoints except `/health/*` require JWT Bearer token authentication.

```
Authorization: Bearer <your-token>
```

Obtain a token via `POST /api/auth/login` with your credentials.

### Rate Limiting

The API enforces rate limiting to prevent abuse:

- **Limit:** 10 requests per minute per user
- **Identification:** Authenticated users by user ID, unauthenticated by IP address
- **Response:** 429 Too Many Requests when limit exceeded

Rate limit headers are included in all responses:
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when the window resets

### Error Response Format

All errors return a consistent JSON structure:

```json
{
    "error_code": "AUTH_001",
    "detail": "Authentication required",
    "timestamp": "2026-01-16T12:00:00Z"
}
```

### Supported Test Types

- **Grounding** - Ground resistance measurements
- **Megger** - Insulation resistance testing
- **Thermography** - Infrared thermal imaging analysis
- **FAT** - Factory Acceptance Testing

### Equipment Types

PANEL, UPS, ATS, GEN (Generator), XFMR (Transformer)
"""


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
        description=API_DESCRIPTION,
        lifespan=lifespan,
        openapi_tags=tags_metadata,
        openapi_url="/api/v1/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        contact={
            "name": "AuditEng Team",
            "email": "support@auditeng.io",
        },
        license_info={
            "name": "Proprietary",
            "url": "https://auditeng.io/license",
        },
    )

    # Add rate limiting middleware (before CORS for proper header handling)
    if settings.RATE_LIMIT_ENABLED:
        from app.core.middleware import RateLimitMiddleware

        app.add_middleware(RateLimitMiddleware)
        logger.info(
            f"Rate limiting enabled: {settings.RATE_LIMIT_PER_MINUTE} requests/minute"
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
    from app.api.analyses import router as analyses_router
    from app.api.auth import router as auth_router
    from app.api.health import router as health_router
    from app.api.upload import router as upload_router
    from app.api.tasks import router as tasks_router
    from app.api.validation import router as validation_router
    from app.api.reports import router as reports_router
    from app.api.audit import router as audit_router

    app.include_router(analyses_router)
    app.include_router(auth_router)
    app.include_router(health_router)
    app.include_router(upload_router)
    app.include_router(tasks_router)
    app.include_router(validation_router)
    app.include_router(reports_router)
    app.include_router(audit_router)

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
