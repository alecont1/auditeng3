"""Core application utilities.

Exports:
    - Exceptions and exception handlers
    - Dependency injection functions
"""

from app.core.dependencies import get_db, get_settings
from app.core.exceptions import (
    AuditEngException,
    AuthenticationError,
    AuthorizationError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
    audit_eng_exception_handler,
    generic_exception_handler,
)

__all__ = [
    # Exceptions
    "AuditEngException",
    "NotFoundError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "ExternalServiceError",
    # Exception handlers
    "audit_eng_exception_handler",
    "generic_exception_handler",
    # Dependencies
    "get_db",
    "get_settings",
]
