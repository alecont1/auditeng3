"""API routers package.

Exports:
    - health_router: Health check endpoints
"""

from app.api.health import router as health_router

__all__ = ["health_router"]
