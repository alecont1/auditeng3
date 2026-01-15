"""
Custom Dramatiq middleware for retry handling and status tracking.

This module provides:
- RetryMiddleware: Configures exponential backoff for failed jobs
- StatusTrackingMiddleware: Tracks job status in Redis
"""

import logging
import time
from typing import Any

from dramatiq import Middleware

logger = logging.getLogger(__name__)


class RetryMiddleware(Middleware):
    """
    Middleware for enhanced error handling with exponential backoff.

    Default retry settings:
    - max_retries: 3 attempts
    - min_backoff: 1000ms (1 second)
    - max_backoff: 300000ms (5 minutes)
    - backoff_factor: 2 (exponential)
    """

    # Default retry configuration
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_MIN_BACKOFF = 1000  # 1 second in ms
    DEFAULT_MAX_BACKOFF = 300000  # 5 minutes in ms
    DEFAULT_BACKOFF_FACTOR = 2

    def __init__(
        self,
        *,
        max_retries: int = DEFAULT_MAX_RETRIES,
        min_backoff: int = DEFAULT_MIN_BACKOFF,
        max_backoff: int = DEFAULT_MAX_BACKOFF,
        backoff_factor: int = DEFAULT_BACKOFF_FACTOR,
    ) -> None:
        """
        Initialize the retry middleware.

        Args:
            max_retries: Maximum number of retry attempts
            min_backoff: Minimum backoff time in milliseconds
            max_backoff: Maximum backoff time in milliseconds
            backoff_factor: Multiplier for exponential backoff
        """
        self.max_retries = max_retries
        self.min_backoff = min_backoff
        self.max_backoff = max_backoff
        self.backoff_factor = backoff_factor

    def calculate_backoff(self, retries: int) -> int:
        """
        Calculate backoff time using exponential backoff algorithm.

        Args:
            retries: Current retry attempt number

        Returns:
            Backoff time in milliseconds
        """
        backoff = self.min_backoff * (self.backoff_factor**retries)
        return min(backoff, self.max_backoff)

    def after_process_message(
        self,
        broker: Any,
        message: Any,
        *,
        result: Any = None,
        exception: BaseException | None = None,
    ) -> None:
        """
        Handle post-processing of messages, logging failures.

        Args:
            broker: The Dramatiq broker
            message: The processed message
            result: Result of successful processing (if any)
            exception: Exception raised during processing (if any)
        """
        if exception is not None:
            retries = message.options.get("retries", 0)
            actor_name = message.actor_name
            message_id = message.message_id

            if retries < self.max_retries:
                backoff = self.calculate_backoff(retries)
                next_retry_time = time.time() + (backoff / 1000)
                logger.warning(
                    f"Job {message_id} ({actor_name}) failed on attempt {retries + 1}. "
                    f"Retrying in {backoff}ms (next attempt at {time.ctime(next_retry_time)}). "
                    f"Error: {exception}"
                )
            else:
                logger.error(
                    f"Job {message_id} ({actor_name}) failed after {retries + 1} attempts. "
                    f"Max retries ({self.max_retries}) exceeded. Error: {exception}"
                )


class StatusTrackingMiddleware(Middleware):
    """
    Middleware for tracking job status in Redis.

    Tracks the lifecycle of jobs:
    - PROCESSING: When job execution starts
    - COMPLETED: When job completes successfully
    - FAILED: When job fails (after all retries exhausted)
    """

    def __init__(self) -> None:
        """Initialize the status tracking middleware."""
        # Import here to avoid circular imports
        # Status functions will be available after status.py is created
        self._status_module_loaded = False

    def _ensure_status_module(self) -> bool:
        """Lazily load status module to avoid circular imports."""
        if not self._status_module_loaded:
            try:
                from app.worker.status import JobStatus, set_job_status

                self._set_job_status = set_job_status
                self._JobStatus = JobStatus
                self._status_module_loaded = True
            except ImportError:
                logger.warning("Status module not yet available")
                return False
        return True

    def before_process_message(
        self,
        broker: Any,
        message: Any,
    ) -> None:
        """
        Set job status to PROCESSING before execution.

        Args:
            broker: The Dramatiq broker
            message: The message being processed
        """
        if not self._ensure_status_module():
            return

        message_id = message.message_id
        try:
            self._set_job_status(
                job_id=message_id,
                status=self._JobStatus.PROCESSING,
            )
            logger.debug(f"Job {message_id} status set to PROCESSING")
        except Exception as e:
            logger.error(f"Failed to update job {message_id} status to PROCESSING: {e}")

    def after_process_message(
        self,
        broker: Any,
        message: Any,
        *,
        result: Any = None,
        exception: BaseException | None = None,
    ) -> None:
        """
        Update job status after processing completes.

        Args:
            broker: The Dramatiq broker
            message: The processed message
            result: Result of successful processing (if any)
            exception: Exception raised during processing (if any)
        """
        if not self._ensure_status_module():
            return

        message_id = message.message_id
        retries = message.options.get("retries", 0)
        max_retries = message.options.get("max_retries", 3)

        try:
            if exception is None:
                # Job completed successfully
                self._set_job_status(
                    job_id=message_id,
                    status=self._JobStatus.COMPLETED,
                    result=result,
                )
                logger.debug(f"Job {message_id} status set to COMPLETED")
            elif retries >= max_retries:
                # Job failed after all retries
                self._set_job_status(
                    job_id=message_id,
                    status=self._JobStatus.FAILED,
                    error=str(exception),
                )
                logger.debug(f"Job {message_id} status set to FAILED")
            # If exception but retries remaining, status stays PROCESSING
        except Exception as e:
            logger.error(f"Failed to update job {message_id} status: {e}")
