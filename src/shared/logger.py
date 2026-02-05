"""Structured JSON logger for agent activity."""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Log file path
LOG_DIR = Path("/app/logs")
LOG_FILE = LOG_DIR / "agent_activity.log"


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON line."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, "task_id"):
            log_data["task_id"] = record.task_id
        if hasattr(record, "agent_name"):
            log_data["agent_name"] = record.agent_name
        if hasattr(record, "action_details"):
            log_data["action_details"] = record.action_details
        if hasattr(record, "status"):
            log_data["status"] = record.status
            
        return json.dumps(log_data)


def setup_agent_logger() -> logging.Logger:
    """
    Set up the structured agent activity logger.
    
    Returns:
        Configured logger instance
    """
    # Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("agent_activity")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        # File handler with JSON formatter
        file_handler = logging.FileHandler(LOG_FILE, mode="a")
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
        
        # Also log to console for debugging
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(JSONFormatter())
        logger.addHandler(console_handler)
    
    return logger


# Global logger instance
agent_logger = setup_agent_logger()


def log_agent_action(
    task_id: str,
    agent_name: str,
    action_details: str,
    status: str = "running",
) -> None:
    """
    Log an agent action to the structured log file.
    
    Args:
        task_id: UUID of the task
        agent_name: Name of the agent (e.g., "ResearchAgent")
        action_details: Description of what the agent is doing
        status: Current status (default: "running")
    """
    agent_logger.info(
        action_details,
        extra={
            "task_id": task_id,
            "agent_name": agent_name,
            "action_details": action_details,
            "status": status,
        }
    )


def log_tool_error(
    task_id: str,
    agent_name: str,
    tool_name: str,
    error: str,
) -> None:
    """
    Log a tool execution error.
    
    Args:
        task_id: UUID of the task
        agent_name: Name of the agent
        tool_name: Name of the tool that failed
        error: Error message
    """
    agent_logger.error(
        f"Tool error in {tool_name}: {error}",
        extra={
            "task_id": task_id,
            "agent_name": agent_name,
            "action_details": f"Tool '{tool_name}' failed: {error}",
            "status": "tool_error",
        }
    )


def log_retry(
    task_id: str,
    agent_name: str,
    tool_name: str,
    attempt: int,
) -> None:
    """
    Log a retry attempt.
    
    Args:
        task_id: UUID of the task
        agent_name: Name of the agent
        tool_name: Name of the tool being retried
        attempt: Retry attempt number
    """
    agent_logger.info(
        f"Retrying {tool_name} (attempt {attempt})",
        extra={
            "task_id": task_id,
            "agent_name": agent_name,
            "action_details": f"Retrying {tool_name}... (attempt {attempt})",
            "status": "retrying",
        }
    )
