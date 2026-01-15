"""
Dramatiq task definitions and base task decorator.

This module provides:
- base_task: A decorator that wraps dramatiq.actor with default retry options
- Example placeholder tasks for testing
"""

from functools import wraps
from typing import Any, Callable, TypeVar

import dramatiq

from app.worker.broker import DEFAULT_QUEUE, broker
from app.worker.status import JobStatus, create_job, set_job_status

# Type variable for function return type
T = TypeVar("T")

# Default retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_MIN_BACKOFF = 1000  # 1 second in ms
DEFAULT_MAX_BACKOFF = 300000  # 5 minutes in ms


def base_task(
    queue_name: str = DEFAULT_QUEUE,
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    min_backoff: int = DEFAULT_MIN_BACKOFF,
    max_backoff: int = DEFAULT_MAX_BACKOFF,
    **actor_options: Any,
) -> Callable[[Callable[..., T]], dramatiq.Actor]:
    """
    Decorator that creates a Dramatiq actor with default retry options.

    This decorator wraps dramatiq.actor and configures default retry behavior
    with exponential backoff.

    Args:
        queue_name: The queue to use for this task (default: "default")
        max_retries: Maximum number of retry attempts (default: 3)
        min_backoff: Minimum backoff time in ms (default: 1000)
        max_backoff: Maximum backoff time in ms (default: 300000)
        **actor_options: Additional options passed to dramatiq.actor

    Returns:
        A decorator that creates a Dramatiq actor

    Example:
        @base_task(queue_name="high")
        def process_document(task_id: str) -> None:
            # Process the document
            pass

        # Enqueue the task
        process_document.send("doc-123")
    """

    def decorator(func: Callable[..., T]) -> dramatiq.Actor:
        @dramatiq.actor(
            queue_name=queue_name,
            max_retries=max_retries,
            min_backoff=min_backoff,
            max_backoff=max_backoff,
            broker=broker,
            **actor_options,
        )
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return func(*args, **kwargs)

        return wrapper

    return decorator


def enqueue_task(
    actor: dramatiq.Actor,
    *args: Any,
    job_id: str | None = None,
    **kwargs: Any,
) -> str:
    """
    Enqueue a task and initialize its status tracking.

    This helper function sends a message to the queue and creates
    the initial job status record.

    Args:
        actor: The Dramatiq actor to invoke
        *args: Positional arguments for the task
        job_id: Optional custom job ID (auto-generated if not provided)
        **kwargs: Keyword arguments for the task

    Returns:
        The message ID (job ID) for tracking

    Example:
        job_id = enqueue_task(process_document, "doc-123")
        status = get_job_status(job_id)
    """
    message = actor.send(*args, **kwargs)
    message_id = message.message_id

    # Create initial status record
    create_job(message_id)

    return message_id


# ============================================================================
# Example Placeholder Tasks
# ============================================================================


@base_task(queue_name="default")
def process_document(task_id: str) -> dict[str, Any]:
    """
    Process a document for analysis.

    This is a placeholder task that will be implemented in Phase 2.
    It demonstrates the basic task structure with status tracking.

    Args:
        task_id: The unique identifier for the document task

    Returns:
        A dict containing processing results
    """
    # Placeholder implementation
    # Will be replaced with actual document processing in Phase 2
    return {
        "task_id": task_id,
        "status": "processed",
        "message": "Placeholder - to be implemented in Phase 2",
    }


@base_task(queue_name="high", max_retries=5)
def high_priority_task(data: dict[str, Any]) -> dict[str, Any]:
    """
    High-priority task with more retry attempts.

    This demonstrates using a different queue and custom retry settings.

    Args:
        data: Input data for the task

    Returns:
        Processing result
    """
    # Placeholder implementation
    return {
        "data": data,
        "priority": "high",
        "message": "Placeholder high-priority task",
    }


@base_task(queue_name="low", max_retries=1)
def batch_processing_task(batch_id: str, items: list[str]) -> dict[str, Any]:
    """
    Low-priority batch processing task.

    This demonstrates batch processing with minimal retries.

    Args:
        batch_id: Identifier for the batch
        items: List of item IDs to process

    Returns:
        Batch processing result
    """
    # Placeholder implementation
    return {
        "batch_id": batch_id,
        "items_count": len(items),
        "priority": "low",
        "message": "Placeholder batch processing",
    }
