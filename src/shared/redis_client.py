"""Redis client for shared workspace state between agents."""

import json
import os
from typing import Any

import redis


# Get Redis URL from environment
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

# Create Redis client
_redis_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    """Get or create the Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


def get_workspace_key(task_id: str) -> str:
    """
    Get the Redis key for a task's workspace.
    
    Pattern: task:<task_id>:workspace
    """
    return f"task:{task_id}:workspace"


def save_to_workspace(task_id: str, data: dict[str, Any]) -> None:
    """
    Save data to the task's Redis workspace.
    
    Args:
        task_id: UUID of the task
        data: Dictionary of data to save
    """
    client = get_redis_client()
    key = get_workspace_key(task_id)
    
    # Get existing data and merge
    existing = get_from_workspace(task_id) or {}
    existing.update(data)
    
    # Save as JSON string
    client.set(key, json.dumps(existing))
    # Set TTL of 24 hours
    client.expire(key, 86400)


def get_from_workspace(task_id: str) -> dict[str, Any] | None:
    """
    Get data from the task's Redis workspace.
    
    Args:
        task_id: UUID of the task
        
    Returns:
        Workspace data dictionary or None if not found
    """
    client = get_redis_client()
    key = get_workspace_key(task_id)
    
    data = client.get(key)
    if data is None:
        return None
    
    return json.loads(data)


def delete_workspace(task_id: str) -> None:
    """
    Delete the task's Redis workspace.
    
    Args:
        task_id: UUID of the task
    """
    client = get_redis_client()
    key = get_workspace_key(task_id)
    client.delete(key)


def workspace_exists(task_id: str) -> bool:
    """
    Check if a workspace exists for the given task.
    
    Args:
        task_id: UUID of the task
        
    Returns:
        True if workspace exists, False otherwise
    """
    client = get_redis_client()
    key = get_workspace_key(task_id)
    return client.exists(key) > 0
