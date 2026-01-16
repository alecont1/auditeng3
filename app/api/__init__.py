"""API routers package.

Exports:
    - auth_router: Authentication endpoints
    - health_router: Health check endpoints
    - upload_router: File upload endpoints
"""

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.upload import router as upload_router

__all__ = ["auth_router", "health_router", "upload_router"]
