"""Pytest fixtures for the multi-agent system test suite."""

import asyncio
import os
import uuid
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from src.database.models import Base
from src.api.main import app


# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a test database engine with in-memory SQLite."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing."""
    session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """Create a synchronous test client for FastAPI."""
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_prompt() -> str:
    """Sample prompt for testing."""
    return "Research the key features of LangGraph and CrewAI. Write a short comparison summary for a technical audience."


@pytest.fixture
def sample_task_id() -> str:
    """Generate a sample UUID for testing."""
    return str(uuid.uuid4())


@pytest.fixture
def flaky_test_prompt() -> str:
    """Prompt that triggers flaky tool behavior."""
    return "__FLAKY_TEST__"
