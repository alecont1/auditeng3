"""
Job status tracking system using Redis.

This module provides utilities for tracking job status throughout their lifecycle.
Status information is stored in Redis with automatic TTL expiration.
"""

import json
import os
from datetime import datetime
from enum import Enum
from typing import Any, TypedDict

import redis

# Redis connection URL from environment or default
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# TTL for job status records (7 days in seconds)
JOB_STATUS_TTL = 7 * 24 * 60 * 60  # 604800 seconds

# Redis key prefix for job status
JOB_KEY_PREFIX = "job:"


class JobStatus(str, Enum):
    """Enumeration of possible job states."""

    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobInfo(TypedDict, total=False):
    """Type definition for job information stored in Redis."""

    status: str  # JobStatus value
    queued_at: str  # ISO format datetime
    started_at: str | None  # ISO format datetime
    completed_at: str | None  # ISO format datetime
    error: str | None  # Error message if failed
    result: Any | None  # Result data if completed


# Lazy Redis client initialization
_redis_client: redis.Redis | None = None


def _get_redis_client() -> redis.Redis:
    """
    Get or create the Redis client instance.

    Returns:
        Redis client connected to the configured Redis URL
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


def _get_job_key(job_id: str) -> str:
    """
    Generate Redis key for a job.

    Args:
        job_id: The unique job identifier

    Returns:
        Redis key in format "job:{job_id}"
    """
    return f"{JOB_KEY_PREFIX}{job_id}"


def create_job(job_id: str) -> None:
    """
    Initialize a new job with QUEUED status.

    Args:
        job_id: The unique job identifier
    """
    client = _get_redis_client()
    job_info: JobInfo = {
        "status": JobStatus.QUEUED.value,
        "queued_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "completed_at": None,
        "error": None,
        "result": None,
    }
    key = _get_job_key(job_id)
    client.setex(key, JOB_STATUS_TTL, json.dumps(job_info))


def set_job_status(
    job_id: str,
    status: JobStatus,
    *,
    error: str | None = None,
    result: Any | None = None,
) -> None:
    """
    Update the status of a job.

    Args:
        job_id: The unique job identifier
        status: The new status for the job
        error: Error message (optional, for FAILED status)
        result: Result data (optional, for COMPLETED status)
    """
    client = _get_redis_client()
    key = _get_job_key(job_id)

    # Get existing job info or create new
    existing_data = client.get(key)
    if existing_data:
        job_info: JobInfo = json.loads(existing_data)
    else:
        job_info = {
            "status": JobStatus.QUEUED.value,
            "queued_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None,
            "error": None,
            "result": None,
        }

    # Update status
    job_info["status"] = status.value

    # Update timestamps based on status
    now = datetime.utcnow().isoformat()
    if status == JobStatus.PROCESSING:
        job_info["started_at"] = now
    elif status in (JobStatus.COMPLETED, JobStatus.FAILED):
        job_info["completed_at"] = now

    # Update error/result if provided
    if error is not None:
        job_info["error"] = error
    if result is not None:
        # Serialize result to JSON-safe format
        try:
            job_info["result"] = result if isinstance(result, (str, int, float, bool, list, dict, type(None))) else str(result)
        except Exception:
            job_info["result"] = str(result)

    # Store with TTL
    client.setex(key, JOB_STATUS_TTL, json.dumps(job_info))


def get_job_status(job_id: str) -> JobInfo | None:
    """
    Retrieve the status information for a job.

    Args:
        job_id: The unique job identifier

    Returns:
        JobInfo dict with status details, or None if not found
    """
    client = _get_redis_client()
    key = _get_job_key(job_id)
    data = client.get(key)

    if data is None:
        return None

    return json.loads(data)


def delete_job_status(job_id: str) -> bool:
    """
    Delete the status record for a job.

    Args:
        job_id: The unique job identifier

    Returns:
        True if the job was deleted, False if not found
    """
    client = _get_redis_client()
    key = _get_job_key(job_id)
    return client.delete(key) > 0
