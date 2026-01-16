"""Custom exception classes and handlers for AuditEng.

This module defines structured exceptions with error codes and consistent
JSON response formatting.
"""

import logging
import traceback
from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """Structured error response model.

    Attributes:
        error_code: Application-specific error code (e.g., "AUTH_001").
        detail: Human-readable error description.
        timestamp: UTC timestamp of when the error occurred.
    """

    error_code: str
    detail: str
    timestamp: datetime


class AuditEngException(Exception):
    """Base exception for all AuditEng application errors.

    Attributes:
        status_code: HTTP status code for the response.
        detail: Human-readable error message.
        error_code: Application-specific error code.
    """

    def __init__(
        self,
        detail: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_001",
    ) -> None:
        """Initialize the exception.

        Args:
            detail: Human-readable error message.
            status_code: HTTP status code (default: 500).
            error_code: Application error code (default: "INTERNAL_001").
        """
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        super().__init__(detail)


class NotFoundError(AuditEngException):
    """Resource not found exception (404)."""

    def __init__(
        self,
        detail: str = "Resource not found",
        error_code: str = "NOT_FOUND_001",
    ) -> None:
        super().__init__(detail=detail, status_code=404, error_code=error_code)


class ValidationError(AuditEngException):
    """Validation error exception (422)."""

    def __init__(
        self,
        detail: str = "Validation error",
        error_code: str = "VALIDATION_001",
    ) -> None:
        super().__init__(detail=detail, status_code=422, error_code=error_code)


class AuthenticationError(AuditEngException):
    """Authentication error exception (401)."""

    def __init__(
        self,
        detail: str = "Authentication required",
        error_code: str = "AUTH_001",
    ) -> None:
        super().__init__(detail=detail, status_code=401, error_code=error_code)


class AuthorizationError(AuditEngException):
    """Authorization error exception (403)."""

    def __init__(
        self,
        detail: str = "Permission denied",
        error_code: str = "AUTH_002",
    ) -> None:
        super().__init__(detail=detail, status_code=403, error_code=error_code)


class ExternalServiceError(AuditEngException):
    """External service error exception (503)."""

    def __init__(
        self,
        detail: str = "External service unavailable",
        error_code: str = "EXTERNAL_001",
    ) -> None:
        super().__init__(detail=detail, status_code=503, error_code=error_code)


async def audit_eng_exception_handler(
    request: Request,
    exc: AuditEngException,
) -> JSONResponse:
    """Handle AuditEngException and return structured JSON response.

    Args:
        request: The incoming request.
        exc: The raised AuditEngException.

    Returns:
        JSONResponse with ErrorResponse body.
    """
    error_response = ErrorResponse(
        error_code=exc.error_code,
        detail=exc.detail,
        timestamp=datetime.now(timezone.utc),
    )

    logger.warning(
        f"AuditEngException: {exc.error_code} - {exc.detail}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "path": str(request.url.path),
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json"),
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unhandled exceptions with safe error response.

    Logs the full traceback but returns a generic message to avoid
    leaking internal details.

    Args:
        request: The incoming request.
        exc: The unhandled exception.

    Returns:
        JSONResponse with generic 500 error.
    """
    # Log full traceback for debugging
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "path": str(request.url.path),
            "traceback": traceback.format_exc(),
        },
    )

    error_response = ErrorResponse(
        error_code="INTERNAL_500",
        detail="An internal error occurred",
        timestamp=datetime.now(timezone.utc),
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(mode="json"),
    )
