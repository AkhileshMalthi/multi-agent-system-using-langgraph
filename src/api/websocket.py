"""WebSocket connection manager for real-time task updates."""

import asyncio
import json
from typing import Any
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState


class ConnectionManager:
    """
    Manages WebSocket connections for real-time task status updates.
    
    Each task can have multiple connected clients that receive updates
    when the task status changes.
    """
    
    def __init__(self):
        # Map of task_id -> list of connected WebSockets
        self.active_connections: dict[str, list[WebSocket]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, task_id: str) -> None:
        """
        Accept and register a new WebSocket connection for a task.
        
        Args:
            websocket: The WebSocket connection
            task_id: UUID of the task to subscribe to
        """
        await websocket.accept()
        
        async with self._lock:
            if task_id not in self.active_connections:
                self.active_connections[task_id] = []
            self.active_connections[task_id].append(websocket)
    
    async def disconnect(self, websocket: WebSocket, task_id: str) -> None:
        """
        Remove a WebSocket connection from the task's subscribers.
        
        Args:
            websocket: The WebSocket connection to remove
            task_id: UUID of the task
        """
        async with self._lock:
            if task_id in self.active_connections:
                if websocket in self.active_connections[task_id]:
                    self.active_connections[task_id].remove(websocket)
                # Clean up empty lists
                if not self.active_connections[task_id]:
                    del self.active_connections[task_id]
    
    async def broadcast_to_task(self, task_id: str, message: dict[str, Any]) -> None:
        """
        Broadcast a message to all clients subscribed to a task.
        
        Args:
            task_id: UUID of the task
            message: Dictionary to send as JSON
        """
        async with self._lock:
            connections = self.active_connections.get(task_id, []).copy()
        
        # Send to all connected clients
        disconnected = []
        for websocket in connections:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected:
            await self.disconnect(websocket, task_id)
    
    async def send_status_update(
        self,
        task_id: str,
        status: str,
        result: str | None = None,
        agent_name: str | None = None,
        action: str | None = None,
    ) -> None:
        """
        Send a status update to all clients subscribed to a task.
        
        Args:
            task_id: UUID of the task
            status: Current task status
            result: Task result (if completed)
            agent_name: Name of the agent taking action
            action: Description of the action
        """
        message = {
            "task_id": task_id,
            "status": status,
        }
        
        if result is not None:
            message["result"] = result
        if agent_name is not None:
            message["agent_name"] = agent_name
        if action is not None:
            message["action"] = action
        
        await self.broadcast_to_task(task_id, message)
    
    def get_connection_count(self, task_id: str) -> int:
        """Get the number of active connections for a task."""
        return len(self.active_connections.get(task_id, []))


# Global connection manager instance
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, task_id: str) -> None:
    """
    WebSocket endpoint handler for task status updates.
    
    Clients connect to /ws/tasks/{task_id} to receive real-time updates
    about task status changes and agent actions.
    
    Args:
        websocket: The WebSocket connection
        task_id: UUID of the task to subscribe to
    """
    await manager.connect(websocket, task_id)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "task_id": task_id,
            "message": "Subscribed to task updates",
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for any client messages (ping/pong, disconnect, etc.)
                data = await websocket.receive_text()
                
                # Handle ping
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                break
                
    finally:
        await manager.disconnect(websocket, task_id)
