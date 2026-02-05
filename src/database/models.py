"""SQLAlchemy models for the multi-agent system."""

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Text, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class TaskStatus(str, enum.Enum):
    """Possible states for a task in the workflow."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    RESEARCHING = "RESEARCHING"
    WRITING = "WRITING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    RESUMED = "RESUMED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class Task(Base):
    """
    Task model representing an agent workflow session.
    
    Matches the required schema from project requirements:
    - id: UUID PRIMARY KEY
    - prompt: TEXT NOT NULL
    - status: VARCHAR(50) NOT NULL
    - result: TEXT NULL
    - agent_logs: JSONB NULL
    - created_at: TIMESTAMP WITH TIME ZONE NOT NULL
    - updated_at: TIMESTAMP WITH TIME ZONE NOT NULL
    """
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        nullable=False,
        default=TaskStatus.PENDING.value,
    )
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_logs: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB, nullable=True, default=list
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("NOW()"),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, status={self.status})>"
