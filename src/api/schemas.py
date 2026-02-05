"""Pydantic schemas for API request/response models."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# --- Request Schemas ---

class TaskCreate(BaseModel):
    """Request body for creating a new task."""
    prompt: str = Field(..., description="The user prompt for the agent workflow")


class TaskApprove(BaseModel):
    """Request body for approving a task."""
    approved: bool = Field(..., description="Whether the task is approved")
    feedback: str | None = Field(None, description="Optional feedback for the task")


# --- Response Schemas ---

class TaskCreateResponse(BaseModel):
    """Response after creating a task (202 Accepted)."""
    task_id: UUID
    status: str


class TaskApproveResponse(BaseModel):
    """Response after approving a task."""
    task_id: UUID
    status: str


class TaskResponse(BaseModel):
    """Full task details response."""
    id: UUID
    prompt: str
    status: str
    result: str | None
    agent_logs: list[dict[str, Any]] | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
