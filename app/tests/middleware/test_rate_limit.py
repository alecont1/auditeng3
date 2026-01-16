"""Tests for rate limiting middleware."""

from unittest.mock import AsyncMock, MagicMock, patch
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.middleware import (
    RateLimitMiddleware,
    check_rate_limit_redis,
    get_rate_limit_key,
)


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client with in-memory storage."""
    storage = {}

    async def mock_get(key):
        return storage.get(key)

    async def mock_incr(key):
        storage[key] = storage.get(key, 0) + 1
        return storage[key]

    async def mock_expire(key, ttl):
        pass  # We don't track TTL in mock

    async def mock_ttl(key):
        return 60 if key in storage else -1

    async def mock_close():
        pass

    client = AsyncMock()
    client.get = mock_get
    client.incr = mock_incr
    client.expire = mock_expire
    client.ttl = mock_ttl
    client.close = mock_close

    # Mock pipeline
    async def mock_execute():
        return [None, None]

    pipe = MagicMock()
    pipe.incr = MagicMock()
    pipe.expire = MagicMock()
    pipe.execute = mock_execute
    client.pipeline = MagicMock(return_value=pipe)

    return client, storage


@pytest.fixture
def test_app():
    """Create a test FastAPI app with rate limiting."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}

    @app.get("/api/health")
    async def health_endpoint():
        return {"status": "healthy"}

    app.add_middleware(RateLimitMiddleware)

    return app


class TestGetRateLimitKey:
    """Tests for rate limit key generation."""

    def test_key_from_ip_no_auth(self):
        """Generate key from client IP when no auth token present."""
        request = MagicMock()
        request.headers.get.return_value = None
        request.client.host = "192.168.1.100"

        key = get_rate_limit_key(request)

        assert "rate_limit:" in key
        assert "192.168.1.100" in key

    def test_key_from_user_id_with_auth(self):
        """Generate key from user_id when JWT token is valid."""
        with patch("app.core.middleware.verify_token") as mock_verify:
            mock_verify.return_value = {"sub": "user-123"}

            request = MagicMock()
            request.headers.get.return_value = "Bearer valid.jwt.token"
            request.client.host = "192.168.1.100"

            key = get_rate_limit_key(request)

            assert "rate_limit:" in key
            assert "user-123" in key
            assert "192.168.1.100" not in key

    def test_key_falls_back_to_ip_on_invalid_token(self):
        """Fall back to IP when JWT token is invalid."""
        with patch("app.core.middleware.verify_token") as mock_verify:
            mock_verify.return_value = None

            request = MagicMock()
            request.headers.get.return_value = "Bearer invalid.token"
            request.client.host = "192.168.1.100"

            key = get_rate_limit_key(request)

            assert "192.168.1.100" in key

    def test_key_includes_minute_bucket(self):
        """Key includes time bucket for rate limiting window."""
        request = MagicMock()
        request.headers.get.return_value = None
        request.client.host = "192.168.1.100"

        key = get_rate_limit_key(request)

        # Key should have format: rate_limit:{identifier}:{minute_bucket}
        parts = key.split(":")
        assert len(parts) == 3
        assert parts[0] == "rate_limit"
        # Third part should be a timestamp (numeric)
        assert parts[2].isdigit()


class TestCheckRateLimitRedis:
    """Tests for Redis rate limit checking."""

    @pytest.mark.asyncio
    async def test_allows_under_limit(self):
        """Allow requests when under the limit."""
        with patch("redis.asyncio.from_url") as mock_redis:
            client = AsyncMock()
            client.get = AsyncMock(return_value=b"5")  # 5 requests made
            client.ttl = AsyncMock(return_value=30)

            pipe = AsyncMock()
            pipe.execute = AsyncMock(return_value=[6, True])
            client.pipeline = MagicMock(return_value=pipe)
            client.close = AsyncMock()

            mock_redis.return_value = client

            is_allowed, count, reset = await check_rate_limit_redis("test_key", 10)

            assert is_allowed is True
            assert count == 6

    @pytest.mark.asyncio
    async def test_blocks_at_limit(self):
        """Block requests when at or over the limit."""
        with patch("redis.asyncio.from_url") as mock_redis:
            client = AsyncMock()
            client.get = AsyncMock(return_value=b"10")  # 10 requests (at limit)
            client.ttl = AsyncMock(return_value=45)
            client.close = AsyncMock()

            mock_redis.return_value = client

            is_allowed, count, reset = await check_rate_limit_redis("test_key", 10)

            assert is_allowed is False
            assert count == 10
            assert reset == 45

    @pytest.mark.asyncio
    async def test_fails_open_on_redis_error(self):
        """Allow requests when Redis is unavailable (fail open)."""
        with patch("redis.asyncio.from_url") as mock_redis:
            mock_redis.side_effect = Exception("Connection refused")

            is_allowed, count, reset = await check_rate_limit_redis("test_key", 10)

            assert is_allowed is True
            assert count == 0


class TestRateLimitMiddleware:
    """Tests for the rate limiting middleware."""

    def test_allows_under_limit(self):
        """Allow requests when under rate limit."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        # Mock Redis to track request count
        request_count = {"count": 0}

        async def mock_check(key, limit):
            request_count["count"] += 1
            return True, request_count["count"], 60

        with patch("app.core.middleware.check_rate_limit_redis", side_effect=mock_check):
            app.add_middleware(RateLimitMiddleware)
            client = TestClient(app)

            # Make 9 requests (all should succeed)
            for i in range(9):
                response = client.get("/test")
                assert response.status_code == 200
                assert "X-RateLimit-Limit" in response.headers
                assert "X-RateLimit-Remaining" in response.headers

    def test_blocks_over_limit(self):
        """Return 429 when rate limit is exceeded."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        request_count = {"count": 0}

        async def mock_check(key, limit):
            request_count["count"] += 1
            if request_count["count"] > 10:
                return False, 11, 45
            return True, request_count["count"], 60

        with patch("app.core.middleware.check_rate_limit_redis", side_effect=mock_check):
            app.add_middleware(RateLimitMiddleware)
            client = TestClient(app)

            # Make 10 successful requests
            for i in range(10):
                response = client.get("/test")
                assert response.status_code == 200

            # 11th request should be blocked
            response = client.get("/test")
            assert response.status_code == 429

            data = response.json()
            assert data["error"] == "rate_limit_exceeded"
            assert "retry_after" in data
            assert response.headers["Retry-After"] == "45"

    def test_rate_limit_per_user_isolation(self):
        """Different users have independent rate limits."""
        with patch("app.core.middleware.verify_token") as mock_verify:
            # Track requests per user
            user_requests = {"user-a": 0, "user-b": 0}

            async def mock_check(key, limit):
                user = "user-a" if "user-a" in key else "user-b"
                user_requests[user] += 1
                if user_requests[user] > 10:
                    return False, 11, 45
                return True, user_requests[user], 60

            with patch("app.core.middleware.check_rate_limit_redis", side_effect=mock_check):
                app = FastAPI()

                @app.get("/test")
                async def test_endpoint():
                    return {"message": "success"}

                app.add_middleware(RateLimitMiddleware)
                client = TestClient(app)

                # User A makes 10 requests (hits limit)
                mock_verify.return_value = {"sub": "user-a"}
                for i in range(10):
                    response = client.get(
                        "/test", headers={"Authorization": "Bearer token-a"}
                    )
                    assert response.status_code == 200

                # User A is blocked
                response = client.get(
                    "/test", headers={"Authorization": "Bearer token-a"}
                )
                assert response.status_code == 429

                # User B can still make requests
                mock_verify.return_value = {"sub": "user-b"}
                response = client.get(
                    "/test", headers={"Authorization": "Bearer token-b"}
                )
                assert response.status_code == 200

    def test_health_check_bypasses_rate_limit(self):
        """Health check endpoints are not rate limited."""
        app = FastAPI()

        @app.get("/api/health")
        async def health_endpoint():
            return {"status": "healthy"}

        # Make mock_check raise an exception to prove it's not called
        async def mock_check(key, limit):
            raise AssertionError("Rate limit should not be checked for health endpoints")

        with patch("app.core.middleware.check_rate_limit_redis", side_effect=mock_check):
            app.add_middleware(RateLimitMiddleware)
            client = TestClient(app)

            # Health check should succeed without calling rate limit
            response = client.get("/api/health")
            assert response.status_code == 200

    def test_graceful_redis_failure(self):
        """API continues to work when Redis fails (fail open)."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        async def mock_check(key, limit):
            # Simulate fail open behavior (Redis down)
            return True, 0, 60

        with patch("app.core.middleware.check_rate_limit_redis", side_effect=mock_check):
            app.add_middleware(RateLimitMiddleware)
            client = TestClient(app)

            # Request should succeed even when Redis is "down"
            response = client.get("/test")
            assert response.status_code == 200


class TestRateLimitHeaders:
    """Tests for rate limit response headers."""

    def test_headers_present_on_success(self):
        """Rate limit headers are present on successful requests."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        async def mock_check(key, limit):
            return True, 5, 30

        with patch("app.core.middleware.check_rate_limit_redis", side_effect=mock_check):
            app.add_middleware(RateLimitMiddleware)
            client = TestClient(app)

            response = client.get("/test")

            assert "X-RateLimit-Limit" in response.headers
            assert response.headers["X-RateLimit-Limit"] == "10"
            assert "X-RateLimit-Remaining" in response.headers
            assert response.headers["X-RateLimit-Remaining"] == "5"
            assert "X-RateLimit-Reset" in response.headers

    def test_headers_on_rate_limited_response(self):
        """Rate limit headers are present on 429 responses."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        async def mock_check(key, limit):
            return False, 10, 30

        with patch("app.core.middleware.check_rate_limit_redis", side_effect=mock_check):
            app.add_middleware(RateLimitMiddleware)
            client = TestClient(app)

            response = client.get("/test")

            assert response.status_code == 429
            assert "X-RateLimit-Limit" in response.headers
            assert response.headers["X-RateLimit-Remaining"] == "0"
            assert "Retry-After" in response.headers
