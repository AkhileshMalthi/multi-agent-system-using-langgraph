"""Tests for database CRUD operations."""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.crud import (
    create_task,
    get_task,
    update_task_status,
    update_task_result,
    append_agent_log,
)
from src.database.models import TaskStatus


@pytest.mark.asyncio
async def test_create_task(db_session: AsyncSession, sample_prompt: str):
    """Test creating a new task."""
    task = await create_task(db_session, sample_prompt)
    
    assert task is not None
    assert task.id is not None
    assert task.prompt == sample_prompt
    assert task.status == TaskStatus.PENDING.value
    assert task.result is None
    assert task.agent_logs == []
    assert task.created_at is not None
    assert task.updated_at is not None


@pytest.mark.asyncio
async def test_get_task(db_session: AsyncSession, sample_prompt: str):
    """Test retrieving a task by ID."""
    # Create a task first
    created_task = await create_task(db_session, sample_prompt)
    
    # Retrieve it
    retrieved_task = await get_task(db_session, created_task.id)
    
    assert retrieved_task is not None
    assert retrieved_task.id == created_task.id
    assert retrieved_task.prompt == sample_prompt


@pytest.mark.asyncio
async def test_get_task_not_found(db_session: AsyncSession):
    """Test retrieving a non-existent task returns None."""
    fake_id = uuid.uuid4()
    task = await get_task(db_session, fake_id)
    
    assert task is None


@pytest.mark.asyncio
async def test_update_task_status(db_session: AsyncSession, sample_prompt: str):
    """Test updating task status."""
    task = await create_task(db_session, sample_prompt)
    
    # Update status to RUNNING
    updated_task = await update_task_status(db_session, task.id, TaskStatus.RUNNING)
    
    assert updated_task is not None
    assert updated_task.status == TaskStatus.RUNNING.value


@pytest.mark.asyncio
async def test_update_task_result(db_session: AsyncSession, sample_prompt: str):
    """Test updating task result."""
    task = await create_task(db_session, sample_prompt)
    result_text = "This is the final result"
    
    updated_task = await update_task_result(
        db_session,
        task.id,
        result_text,
        TaskStatus.COMPLETED,
    )
    
    assert updated_task is not None
    assert updated_task.result == result_text
    assert updated_task.status == TaskStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_append_agent_log(db_session: AsyncSession, sample_prompt: str):
    """Test appending to agent logs."""
    task = await create_task(db_session, sample_prompt)
    
    # Append first log entry
    updated_task = await append_agent_log(
        db_session,
        task.id,
        "ResearchAgent",
        "Searching for LangGraph features",
    )
    
    assert updated_task is not None
    assert len(updated_task.agent_logs) == 1
    assert updated_task.agent_logs[0]["agent"] == "ResearchAgent"
    assert updated_task.agent_logs[0]["action"] == "Searching for LangGraph features"
    assert "timestamp" in updated_task.agent_logs[0]
    
    # Append second log entry
    updated_task = await append_agent_log(
        db_session,
        task.id,
        "WritingAgent",
        "Drafting summary",
    )
    
    assert len(updated_task.agent_logs) == 2
    assert updated_task.agent_logs[1]["agent"] == "WritingAgent"


@pytest.mark.asyncio
async def test_task_status_transitions(db_session: AsyncSession, sample_prompt: str):
    """Test full task status lifecycle."""
    task = await create_task(db_session, sample_prompt)
    
    # PENDING -> RUNNING
    await update_task_status(db_session, task.id, TaskStatus.RUNNING)
    task = await get_task(db_session, task.id)
    assert task.status == TaskStatus.RUNNING.value
    
    # RUNNING -> AWAITING_APPROVAL
    await update_task_status(db_session, task.id, TaskStatus.AWAITING_APPROVAL)
    task = await get_task(db_session, task.id)
    assert task.status == TaskStatus.AWAITING_APPROVAL.value
    
    # AWAITING_APPROVAL -> RESUMED
    await update_task_status(db_session, task.id, TaskStatus.RESUMED)
    task = await get_task(db_session, task.id)
    assert task.status == TaskStatus.RESUMED.value
    
    # RESUMED -> COMPLETED
    await update_task_result(db_session, task.id, "Final result", TaskStatus.COMPLETED)
    task = await get_task(db_session, task.id)
    assert task.status == TaskStatus.COMPLETED.value
    assert task.result == "Final result"
