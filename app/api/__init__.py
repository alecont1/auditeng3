"""API routers package.

Exports:
    - health_router: Health check endpoints
    - upload_router: File upload endpoints
"""

from app.api.health import router as health_router
from app.api.upload import router as upload_router

__all__ = ["health_router", "upload_router"]
