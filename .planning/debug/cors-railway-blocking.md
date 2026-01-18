# CORS Railway Blocking - Debug Investigation

**Date:** 2026-01-18
**Status:** FIXED (v2)
**Environment:** Railway (FastAPI backend, React+Vite frontend)

## Issue Summary

CORS blocking all API requests from frontend (`web-production-a0708.up.railway.app`) to backend (`worker-production-a0a1.up.railway.app`) with error:
```
No 'Access-Control-Allow-Origin' header
```

Additional symptoms:
- 401 on `/api/auth/login`
- 429 rate limiting on `/api/tasks/{id}` due to aggressive polling
- 500 errors on task status endpoint

## Investigation Findings (v2)

### 1. ROOT CAUSE: Exception Handlers Bypass CORS Middleware

**Critical Discovery:** FastAPI exception handlers create `JSONResponse` objects directly, which bypass the CORS middleware entirely.

```
Request Flow (Normal):
  Request -> CORSMiddleware -> RateLimitMiddleware -> Route -> Response
  Response <- CORSMiddleware <- (adds CORS headers) <- RateLimitMiddleware <- Route

Request Flow (Exception):
  Request -> CORSMiddleware -> RateLimitMiddleware -> Route -> EXCEPTION!
  Response <- Exception Handler creates JSONResponse DIRECTLY (no CORS headers!)
```

This means ANY error response (401, 403, 404, 422, 429, 500) was returned WITHOUT CORS headers, causing the browser to block the response entirely.

### 2. Middleware Order Was Correct

The middleware order in `app/main.py` was actually correct:
- RateLimitMiddleware added FIRST (line 185-189)
- CORSMiddleware added SECOND (line 212-219)

In Starlette, middleware executes in reverse order, so:
- CORS middleware runs first on requests
- Rate limiter runs second

This was NOT the issue.

### 3. Rate Limiter Also Bypassed CORS

The rate limiter's 429 response was also created directly:
```python
return JSONResponse(
    status_code=429,
    content={...},
    headers={...},  # Only rate limit headers, NO CORS!
)
```

### 4. Regex Pattern Was Correct

Tested and confirmed:
```python
import re
pattern = r"https://[a-zA-Z0-9-]+\.(?:vercel\.app|railway\.app|up\.railway\.app)"
url = "https://web-production-a0708.up.railway.app"
re.fullmatch(pattern, url)  # Returns match object - WORKS
```

## Changes Applied (v2)

### 1. Exception Handlers with CORS Headers (`app/core/exceptions.py`)

Added `_get_cors_headers()` helper function that:
- Extracts Origin header from request
- Validates against allowed origins list
- Validates against regex pattern for Railway/Vercel deployments
- Returns appropriate CORS headers if origin is allowed

Updated both exception handlers:
- `audit_eng_exception_handler` - handles AuditEngException (401, 403, 404, etc.)
- `generic_exception_handler` - handles unhandled 500 errors

```python
def _get_cors_headers(request: Request) -> dict[str, str]:
    """Generate CORS headers for error responses."""
    origin = request.headers.get("origin")
    if not origin:
        return {}

    settings = get_settings()
    allowed_origins = list(settings.CORS_ORIGINS)
    if settings.FRONTEND_URL:
        allowed_origins.append(settings.FRONTEND_URL.rstrip("/"))

    # Check explicit list
    if origin in allowed_origins:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }

    # Check regex for Railway/Vercel
    cors_origin_regex = r"https://[a-zA-Z0-9-]+\.(?:vercel\.app|railway\.app|up\.railway\.app)"
    if re.fullmatch(cors_origin_regex, origin):
        return {...}

    return {}

async def audit_eng_exception_handler(request, exc):
    ...
    cors_headers = _get_cors_headers(request)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json"),
        headers=cors_headers,  # <-- Now includes CORS headers!
    )
```

### 2. Rate Limiter with CORS Headers (`app/core/middleware.py`)

Added `_get_cors_headers_for_origin()` helper and updated 429 response:

```python
if not is_allowed:
    origin = request.headers.get("origin")
    cors_headers = _get_cors_headers_for_origin(origin)

    return JSONResponse(
        status_code=429,
        content={...},
        headers={
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(int(time.time()) + seconds_until_reset),
            "Retry-After": str(seconds_until_reset),
            **cors_headers,  # <-- Now includes CORS headers!
        },
    )
```

## Previous Changes (v1) - Still Applied

### CORS Configuration (`app/main.py`)

- Added FRONTEND_URL to allowed origins
- Added logging for debugging
- Improved regex pattern (security: no longer allows `.` in subdomain)

### Rate Limit Middleware (`app/core/middleware.py`)

- OPTIONS requests bypass rate limiting

## Railway Configuration Checklist

Ensure these environment variables are set in Railway for the backend service:

```bash
# Required for CORS
FRONTEND_URL=https://web-production-a0708.up.railway.app

# Other required variables
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
JWT_SECRET_KEY=<generate with: openssl rand -hex 32>
ANTHROPIC_API_KEY=sk-ant-...
```

## Verification Steps

1. **Check logs after deploy:**
   ```
   railway logs
   ```
   Look for:
   - `CORS: Added FRONTEND_URL to allowed origins: https://...`
   - `CORS: Configured origins: [...]`

2. **Test CORS preflight:**
   ```bash
   curl -I -X OPTIONS \
     -H "Origin: https://web-production-a0708.up.railway.app" \
     -H "Access-Control-Request-Method: POST" \
     https://worker-production-a0a1.up.railway.app/api/auth/login
   ```

   Expected response headers:
   ```
   Access-Control-Allow-Origin: https://web-production-a0708.up.railway.app
   Access-Control-Allow-Credentials: true
   Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
   ```

3. **Test actual request (normal response):**
   ```bash
   curl -I \
     -H "Origin: https://web-production-a0708.up.railway.app" \
     https://worker-production-a0a1.up.railway.app/api/health
   ```

4. **Test error response (401 - CORS must still be present):**
   ```bash
   curl -I \
     -H "Origin: https://web-production-a0708.up.railway.app" \
     https://worker-production-a0a1.up.railway.app/api/analyses
   ```

   Expected: 401 with `Access-Control-Allow-Origin` header present

## Why This Worked

The key insight is that FastAPI's exception handling system operates independently from the middleware stack. When an exception is raised:

1. The exception bubbles up to the exception handler
2. The handler creates a `JSONResponse` directly
3. This response is returned to the client
4. **It never passes back through the middleware stack**

This is by design in Starlette/FastAPI - exception handlers are meant to be a fast path for error responses. But it means CORS headers (normally added by middleware) are never applied.

The fix ensures CORS headers are explicitly added to all error responses.

## Files Modified

1. `/home/xande/app/core/exceptions.py`
   - Added `_get_cors_headers()` function
   - Added `import re` and `from app.config import get_settings`
   - Updated `audit_eng_exception_handler` to include CORS headers
   - Updated `generic_exception_handler` to include CORS headers

2. `/home/xande/app/core/middleware.py`
   - Added `_get_cors_headers_for_origin()` function
   - Added `import re`
   - Updated 429 response to include CORS headers

## Lessons Learned

1. **CORS headers must be on ALL responses** - not just successful ones
2. **Exception handlers bypass middleware** - they need special handling
3. **Rate limiters that return early also bypass middleware** - same issue
4. **Test error responses explicitly** - not just happy paths
5. **Use `curl -I` with `Origin` header** - the browser's behavior depends on response headers
