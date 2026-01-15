"""
Worker module for background job processing with Dramatiq.

This module provides:
- Redis broker configuration
- Custom middleware for retry and status tracking
- Job status tracking utilities
- Base task decorators
"""

# Import broker to ensure it's configured on module load
from app.worker.broker import (
    DEFAULT_QUEUE,
    HIGH_PRIORITY_QUEUE,
    LOW_PRIORITY_QUEUE,
    QUEUES,
    broker,
)

__all__ = [
    "broker",
    "QUEUES",
    "DEFAULT_QUEUE",
    "HIGH_PRIORITY_QUEUE",
    "LOW_PRIORITY_QUEUE",
]
