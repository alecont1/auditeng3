"""
Dramatiq broker configuration with Redis backend.

This module configures the Dramatiq broker using Redis as the message broker.
It supports priority queues for different job types.
"""

import os

import dramatiq
from dramatiq.brokers.redis import RedisBroker

# Redis connection URL from environment or default
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Create the Redis broker
broker = RedisBroker(url=REDIS_URL)

# Set as the default broker for Dramatiq
dramatiq.set_broker(broker)

# Queue configuration
# - "default": Normal priority tasks
# - "high": High priority tasks (retries, urgent work)
# - "low": Low priority tasks (batch processing)
QUEUES = {
    "default": "default",
    "high": "high",
    "low": "low",
}

# Export queue names for use in other modules
DEFAULT_QUEUE = QUEUES["default"]
HIGH_PRIORITY_QUEUE = QUEUES["high"]
LOW_PRIORITY_QUEUE = QUEUES["low"]
