"""CRUD operations for Task model."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Task, TaskStatus


async def create_task(db: AsyncSession, prompt: str) -> Task:
    """
    Create a new task with the given prompt.
    
    Args:
        db: Database session
        prompt: The user's prompt for the agent workflow
        
    Returns:
        The created Task instance with PENDING status
    """
    task = Task(
        prompt=prompt,
        status=TaskStatus.PENDING.value,
        agent_logs=[],
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def get_task(db: AsyncSession, task_id: uuid.UUID) -> Task | None:
    """
    Retrieve a task by its ID.
    
    Args:
        db: Database session
        task_id: UUID of the task
        
    Returns:
        Task instance if found, None otherwise
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def update_task_status(
    db: AsyncSession,
    task_id: uuid.UUID,
    status: TaskStatus,
) -> Task | None:
    """
    Update the status of a task.
    
    Args:
        db: Database session
        task_id: UUID of the task
        status: New TaskStatus value
        
    Returns:
        Updated Task instance if found, None otherwise
    """
    task = await get_task(db, task_id)
    if task is None:
        return None
    
    task.status = status.value
    task.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(task)
    return task


async def update_task_result(
    db: AsyncSession,
    task_id: uuid.UUID,
    result: str,
    status: TaskStatus = TaskStatus.COMPLETED,
) -> Task | None:
    """
    Update the result of a task and set its status.
    
    Args:
        db: Database session
        task_id: UUID of the task
        result: The final result text
        status: New status (defaults to COMPLETED)
        
    Returns:
        Updated Task instance if found, None otherwise
    """
    task = await get_task(db, task_id)
    if task is None:
        return None
    
    task.result = result
    task.status = status.value
    task.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(task)
    return task


async def append_agent_log(
    db: AsyncSession,
    task_id: uuid.UUID,
    agent: str,
    action: str,
) -> Task | None:
    """
    Append an entry to the task's agent_logs.
    
    Args:
        db: Database session
        task_id: UUID of the task
        agent: Name of the agent (e.g., "ResearchAgent")
        action: Description of the action taken
        
    Returns:
        Updated Task instance if found, None otherwise
    """
    task = await get_task(db, task_id)
    if task is None:
        return None
    
    log_entry: dict[str, Any] = {
        "agent": agent,
        "action": action,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    # Ensure agent_logs is a list
    if task.agent_logs is None:
        task.agent_logs = []
    
    # Create new list to trigger SQLAlchemy change detection
    task.agent_logs = [*task.agent_logs, log_entry]
    task.updated_at = datetime.now(timezone.utc)
    
    await db.flush()
    await db.refresh(task)
    return task
