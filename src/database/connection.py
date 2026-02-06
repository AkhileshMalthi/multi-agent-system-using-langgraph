"""Database connection and session management."""

import os
from collections.abc import AsyncGenerator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .models import Base

# Get database URL from environment, convert to async driver
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://user:password@db:5432/agent_db"
)

# Convert postgresql:// to postgresql+asyncpg:// for async support
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://", 1
    )
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# Create async engine for API
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,  # Verify connections before use
)

# Async session factory for API
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create sync engine for Celery workers (to avoid event loop issues)
sync_engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# Sync session factory for Celery workers
sync_session_maker = sessionmaker(
    sync_engine,
    class_=Session,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    
    Usage with FastAPI:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@contextmanager
def get_sync_db():
    """
    Context manager for sync database sessions (for Celery workers).
    
    Usage:
        with get_sync_db() as db:
            task = db.query(Task).filter_by(id=task_id).first()
    """
    session = sync_session_maker()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def init_db() -> None:
    """
    Initialize database tables.
    
    Creates all tables defined in the models if they don't exist.
    Call this on application startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections. Call on application shutdown."""
    await engine.dispose()
