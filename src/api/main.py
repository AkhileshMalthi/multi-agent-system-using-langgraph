"""FastAPI application for the multi-agent system."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket

from src.database.connection import init_db, close_db
from src.api.routes.tasks import router as tasks_router
from src.api.websocket import websocket_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    - Initializes database tables on startup
    - Closes database connections on shutdown
    """
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="Multi-Agent System API",
    description="API for orchestrating collaborative AI agents using LangGraph",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(tasks_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for container orchestration."""
    return {"status": "healthy"}


@app.websocket("/ws/tasks/{task_id}")
async def ws_task_updates(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time task status updates.
    
    Connect to subscribe to updates for a specific task.
    """
    await websocket_endpoint(websocket, task_id)