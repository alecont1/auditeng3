"""Health check endpoints for monitoring and orchestration.

This module provides health check endpoints used by:
- Monitoring systems to track service health
- Container orchestrators (K8s) for liveness/readiness probes
- Load balancers for traffic routing decisions
"""

from datetime import datetime, timezone

import redis.asyncio as redis
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text

from app.config import get_settings
from app.db import async_session_factory

router = APIRouter(prefix="/api/health", tags=["health"])
settings = get_settings()


class HealthResponse(BaseModel):
    """Health check response model.

    Attributes:
        status: Overall health status ("healthy" or "degraded").
        version: Application version.
        database: Database connection status ("connected" or "disconnected").
        redis: Redis connection status ("connected" or "disconnected").
        timestamp: UTC timestamp of the health check.
    """

    status: str
    version: str
    database: str
    redis: str
    timestamp: datetime


class LivenessResponse(BaseModel):
    """Simple liveness response."""

    status: str


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    status: str
    database: str


async def check_database() -> bool:
    """Check database connectivity.

    Returns:
        bool: True if database is accessible, False otherwise.
    """
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False


async def check_redis() -> bool:
    """Check Redis connectivity.

    Returns:
        bool: True if Redis is accessible, False otherwise.
    """
    try:
        client = redis.from_url(settings.REDIS_URL)
        await client.ping()
        await client.close()
        return True
    except Exception:
        return False


@router.get(
    "",
    response_model=HealthResponse,
    summary="Full health check",
    description="Returns detailed health status including database and Redis connectivity.",
    responses={
        200: {"description": "Service is healthy or degraded but functional"},
        503: {"description": "Service is unhealthy - database unavailable"},
    },
)
async def health_check() -> JSONResponse:
    """Full health check with database and Redis status.

    Returns 200 if database is connected (Redis can be down = degraded mode).
    Returns 503 if database is disconnected.
    """
    db_ok = await check_database()
    redis_ok = await check_redis()

    # Determine overall status
    if db_ok and redis_ok:
        overall_status = "healthy"
    elif db_ok:
        overall_status = "degraded"  # Redis down but DB ok
    else:
        overall_status = "unhealthy"

    response = HealthResponse(
        status=overall_status,
        version=settings.APP_VERSION,
        database="connected" if db_ok else "disconnected",
        redis="connected" if redis_ok else "disconnected",
        timestamp=datetime.now(timezone.utc),
    )

    # Return 503 only if database is down
    status_code = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(mode="json"),
    )


@router.get(
    "/live",
    response_model=LivenessResponse,
    summary="Liveness probe",
    description="Simple liveness check for container orchestrators. Always returns 200.",
)
async def liveness() -> LivenessResponse:
    """Liveness probe endpoint.

    Always returns 200 OK to indicate the process is running.
    Used by Kubernetes liveness probes.
    """
    return LivenessResponse(status="alive")


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description="Readiness check for traffic routing. Returns 200 only when database is connected.",
    responses={
        200: {"description": "Service is ready to accept traffic"},
        503: {"description": "Service is not ready - database unavailable"},
    },
)
async def readiness() -> JSONResponse:
    """Readiness probe endpoint.

    Returns 200 only if database is connected and ready for queries.
    Used by Kubernetes readiness probes and load balancers.
    """
    db_ok = await check_database()

    response = ReadinessResponse(
        status="ready" if db_ok else "not_ready",
        database="connected" if db_ok else "disconnected",
    )

    status_code = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(mode="json"),
    )
