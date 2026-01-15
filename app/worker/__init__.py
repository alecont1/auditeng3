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

# Import status tracking utilities
from app.worker.status import (
    JobInfo,
    JobStatus,
    create_job,
    delete_job_status,
    get_job_status,
    set_job_status,
)

# Import task utilities
from app.worker.tasks import base_task, enqueue_task

__all__ = [
    # Broker
    "broker",
    "QUEUES",
    "DEFAULT_QUEUE",
    "HIGH_PRIORITY_QUEUE",
    "LOW_PRIORITY_QUEUE",
    # Status
    "JobStatus",
    "JobInfo",
    "create_job",
    "set_job_status",
    "get_job_status",
    "delete_job_status",
    # Tasks
    "base_task",
    "enqueue_task",
]
