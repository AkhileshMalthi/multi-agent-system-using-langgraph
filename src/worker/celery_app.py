"""Celery worker for background task processing."""

import os
import asyncio
from typing import Any

from celery import Celery

from src.agents.workflow import run_workflow, get_interrupt_info
from src.agents.state import WorkflowStatus
from src.shared.logger import log_agent_action
from src.database.connection import async_session_maker
from src.database.crud import (
    get_task,
    update_task_status,
    update_task_result,
    append_agent_log,
)
from src.database.models import TaskStatus


# Create Celery app
celery_app = Celery(
    "agent_worker",
    broker=os.environ.get("CELERY_BROKER_URL"),
    backend=os.environ.get("CELERY_RESULT_BACKEND"),
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)


def run_async(coro):
    """Helper to run async functions in sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _update_task_db(task_id: str, status: TaskStatus, result: str | None = None):
    """Update task in database."""
    async with async_session_maker() as session:
        if result is not None:
            await update_task_result(session, task_id, result, status)
        else:
            await update_task_status(session, task_id, status)
        await session.commit()


async def _append_log(task_id: str, agent: str, action: str):
    """Append log entry to task."""
    async with async_session_maker() as session:
        await append_agent_log(session, task_id, agent, action)
        await session.commit()


@celery_app.task(bind=True, max_retries=3)
def execute_workflow(self, task_id: str, prompt: str) -> dict[str, Any]:
    """
    Execute the multi-agent workflow for a task.
    
    This Celery task:
    1. Updates task status to RUNNING
    2. Executes the LangGraph workflow
    3. Handles interrupt (AWAITING_APPROVAL) or completion
    4. Updates the database with results
    
    Args:
        task_id: UUID of the task
        prompt: User's prompt
        
    Returns:
        Workflow result
    """
    try:
        # Update status to RUNNING
        run_async(_update_task_db(task_id, TaskStatus.RUNNING))
        log_agent_action(task_id, "Orchestrator", "Starting workflow execution")
        run_async(_append_log(task_id, "Orchestrator", "Starting workflow execution"))
        
        # Log research start
        log_agent_action(task_id, "ResearchAgent", "Searching for LangGraph features")
        run_async(_append_log(task_id, "ResearchAgent", "Searching for LangGraph features"))
        
        # Run the workflow
        result = run_workflow(task_id, prompt)
        
        # Log research complete
        log_agent_action(task_id, "ResearchAgent", "Research completed")
        
        # Log writing
        log_agent_action(task_id, "WritingAgent", "Drafting comparison summary")
        run_async(_append_log(task_id, "WritingAgent", "Drafting comparison summary"))
        
        # Check if workflow was interrupted (waiting for approval)
        interrupt_info = get_interrupt_info(result)
        if interrupt_info:
            # Workflow paused for approval
            run_async(_update_task_db(task_id, TaskStatus.AWAITING_APPROVAL))
            log_agent_action(task_id, "Orchestrator", "Workflow paused for approval", "awaiting_approval")
            run_async(_append_log(task_id, "Orchestrator", "Awaiting human approval"))
            return {
                "status": "AWAITING_APPROVAL",
                "task_id": task_id,
                "interrupt": interrupt_info,
            }
        
        # Workflow completed
        final_status = result.get("status", WorkflowStatus.COMPLETED)
        final_result = result.get("result", "")
        
        if final_status == WorkflowStatus.COMPLETED:
            run_async(_update_task_db(task_id, TaskStatus.COMPLETED, final_result))
            log_agent_action(task_id, "Orchestrator", "Workflow completed successfully", "completed")
            run_async(_append_log(task_id, "Orchestrator", "Workflow completed"))
        else:
            run_async(_update_task_db(task_id, TaskStatus.FAILED, result.get("error", "")))
            log_agent_action(task_id, "Orchestrator", f"Workflow failed: {result.get('error', '')}", "failed")
        
        return {
            "status": final_status,
            "task_id": task_id,
            "result": final_result,
        }
        
    except Exception as e:
        # Handle errors
        error_msg = str(e)
        run_async(_update_task_db(task_id, TaskStatus.FAILED))
        log_agent_action(task_id, "Orchestrator", f"Workflow error: {error_msg}", "error")
        
        # Retry on transient errors
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=2 ** self.request.retries)
        
        return {
            "status": "FAILED",
            "task_id": task_id,
            "error": error_msg,
        }


@celery_app.task(bind=True, max_retries=3)
def resume_workflow(self, task_id: str, approved: bool, feedback: str = "") -> dict[str, Any]:
    """
    Resume a paused workflow after human approval.
    
    Args:
        task_id: UUID of the task
        approved: Whether the task was approved
        feedback: Optional feedback from human
        
    Returns:
        Workflow result
    """
    try:
        # Update status to RESUMED
        run_async(_update_task_db(task_id, TaskStatus.RESUMED))
        log_agent_action(task_id, "Orchestrator", f"Resuming workflow (approved={approved})")
        run_async(_append_log(task_id, "Orchestrator", f"Human approval received: {'Approved' if approved else 'Rejected'}"))
        
        # Resume the workflow with approval response
        resume_value = {"approved": approved, "feedback": feedback}
        result = run_workflow(task_id, "", resume=True, resume_value=resume_value)
        
        # Get final status
        final_status = result.get("status", WorkflowStatus.COMPLETED)
        final_result = result.get("result", "")
        
        if final_status == WorkflowStatus.COMPLETED:
            run_async(_update_task_db(task_id, TaskStatus.COMPLETED, final_result))
            log_agent_action(task_id, "Orchestrator", "Workflow completed successfully", "completed")
            run_async(_append_log(task_id, "Orchestrator", "Workflow completed"))
        else:
            error = result.get("error", "Approval rejected")
            run_async(_update_task_db(task_id, TaskStatus.FAILED))
            log_agent_action(task_id, "Orchestrator", f"Workflow ended: {error}", "failed")
        
        return {
            "status": final_status,
            "task_id": task_id,
            "result": final_result,
        }
        
    except Exception as e:
        error_msg = str(e)
        run_async(_update_task_db(task_id, TaskStatus.FAILED))
        log_agent_action(task_id, "Orchestrator", f"Resume error: {error_msg}", "error")
        
        return {
            "status": "FAILED",
            "task_id": task_id,
            "error": error_msg,
        }