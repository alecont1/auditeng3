"""Rate limiting middleware for AuditEng API.

This module provides:
- Redis-based distributed rate limiting
- Per-user or per-IP rate limiting (10 requests/minute)
- Graceful degradation when Redis is unavailable (fail open)
- Standard rate limit headers (X-RateLimit-*)
"""

import logging
import time
from typing import Callable

from fastapi import Depends, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import get_settings
from app.core.auth import verify_token

logger = logging.getLogger(__name__)


def get_rate_limit_key(request: Request) -> str:
    """Generate rate limit key from JWT user_id or client IP.

    Args:
        request: The incoming HTTP request.

    Returns:
        Rate limit key in format "rate_limit:{identifier}:{minute_bucket}"
    """
    # Try to extract user_id from JWT token
    user_id = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = verify_token(token)
        if payload:
            user_id = payload.get("sub")

    # Use user_id if available, otherwise use client IP
    identifier = user_id if user_id else request.client.host if request.client else "unknown"

    # Create minute bucket for time window
    minute_bucket = int(time.time() // 60)

    return f"rate_limit:{identifier}:{minute_bucket}"


async def check_rate_limit_redis(key: str, limit: int) -> tuple[bool, int, int]:
    """Check rate limit using Redis.

    Args:
        key: The rate limit key.
        limit: Maximum requests per minute.

    Returns:
        Tuple of (is_allowed, current_count, seconds_until_reset)
    """
    import redis.asyncio as redis

    settings = get_settings()

    try:
        client = redis.from_url(settings.REDIS_URL)
        try:
            # Get current count
            current = await client.get(key)
            count = int(current) if current else 0

            if count >= limit:
                # Calculate time until reset
                ttl = await client.ttl(key)
                seconds_until_reset = max(ttl, 0) if ttl > 0 else 60
                return False, count, seconds_until_reset

            # Increment counter
            pipe = client.pipeline()
            pipe.incr(key)
            pipe.expire(key, 60)  # TTL: 60 seconds
            await pipe.execute()

            return True, count + 1, 60 - (int(time.time()) % 60)
        finally:
            await client.close()
    except Exception as e:
        # Fail open - if Redis is unavailable, allow the request
        logger.warning(f"Rate limiting unavailable (Redis error): {e}")
        return True, 0, 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests.

    Uses Redis for distributed rate limiting with per-user/IP tracking.
    Fails open (allows requests) when Redis is unavailable.

    Rate limit: 10 requests per minute (configurable via RATE_LIMIT_PER_MINUTE).
    """

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the rate limit middleware.

        Args:
            app: The ASGI application.
        """
        super().__init__(app)
        self.settings = get_settings()

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process the request with rate limiting.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware/handler in the chain.

        Returns:
            Response from the handler or 429 if rate limited.
        """
        # Skip rate limiting for health checks and docs
        if request.url.path in [
            "/api/health",
            "/api/health/live",
            "/api/health/ready",
            "/docs",
            "/redoc",
            "/api/v1/openapi.json",
        ]:
            return await call_next(request)

        limit = self.settings.RATE_LIMIT_PER_MINUTE
        key = get_rate_limit_key(request)

        is_allowed, count, seconds_until_reset = await check_rate_limit_redis(key, limit)

        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "detail": f"Rate limit exceeded. Try again in {seconds_until_reset} seconds.",
                    "retry_after": seconds_until_reset,
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + seconds_until_reset),
                    "Retry-After": str(seconds_until_reset),
                },
            )

        # Process request and add rate limit headers to response
        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + seconds_until_reset)

        return response


async def rate_limit_dependency(
    request: Request,
    limit: int = 10,
) -> None:
    """FastAPI dependency for per-route rate limiting.

    Can be used to override the default rate limit for specific endpoints.

    Args:
        request: The incoming HTTP request.
        limit: Maximum requests per minute for this route.

    Raises:
        HTTPException: If rate limit is exceeded (429).

    Example:
        @app.get("/heavy-endpoint")
        async def heavy_endpoint(
            _: None = Depends(lambda r: rate_limit_dependency(r, limit=5))
        ):
            ...
    """
    from fastapi import HTTPException

    key = get_rate_limit_key(request)
    is_allowed, count, seconds_until_reset = await check_rate_limit_redis(key, limit)

    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "detail": f"Rate limit exceeded. Try again in {seconds_until_reset} seconds.",
                "retry_after": seconds_until_reset,
            },
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + seconds_until_reset),
                "Retry-After": str(seconds_until_reset),
            },
        )
