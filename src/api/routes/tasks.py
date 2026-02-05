"""Task management API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import (
    TaskCreate,
    TaskCreateResponse,
    TaskApprove,
    TaskApproveResponse,
    TaskResponse,
)
from src.database.connection import get_db
from src.database.crud import (
    create_task,
    get_task,
    update_task_status,
)
from src.database.models import TaskStatus
from src.worker.celery_app import execute_workflow, resume_workflow

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.post(
    "",
    response_model=TaskCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start a new agent task",
    description="Creates a new task and queues it for background processing.",
)
async def start_task(
    request: TaskCreate,
    db: AsyncSession = Depends(get_db),
) -> TaskCreateResponse:
    """
    Create a new collaborative agent task.
    
    - Accepts a prompt and immediately returns a task ID
    - Queues the actual work to be done in the background via Celery
    - Returns 202 Accepted as the task is being processed asynchronously
    """
    # Create task in database with PENDING status
    task = await create_task(db, request.prompt)
    
    # Queue Celery task for background processing
    execute_workflow.delay(str(task.id), request.prompt)
    
    return TaskCreateResponse(
        task_id=task.id,
        status=task.status,
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task status and details",
    description="Retrieves the current status and details of a specific task.",
)
async def get_task_status(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """
    Retrieve a task by its ID.
    
    Returns the full task details including:
    - Current status
    - Result (if completed)
    - Agent logs for auditability
    """
    task = await get_task(db, task_id)
    
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )
    
    return TaskResponse.model_validate(task)


@router.post(
    "/{task_id}/approve",
    response_model=TaskApproveResponse,
    summary="Approve or reject a task",
    description="Provides human approval for a task paused at a decision point.",
)
async def approve_task(
    task_id: UUID,
    request: TaskApprove,
    db: AsyncSession = Depends(get_db),
) -> TaskApproveResponse:
    """
    Provide human-in-the-loop approval for a task.
    
    - Only works when task is in AWAITING_APPROVAL status
    - If approved, resumes the workflow
    - If rejected, marks the task as FAILED
    """
    task = await get_task(db, task_id)
    
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )
    
    if task.status != TaskStatus.AWAITING_APPROVAL.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task is not awaiting approval (current status: {task.status})",
        )
    
    if request.approved:
        # Resume the workflow via Celery
        new_status = TaskStatus.RESUMED
        resume_workflow.delay(str(task_id), request.approved, request.feedback or "")
    else:
        # Mark as failed
        new_status = TaskStatus.FAILED
    
    await update_task_status(db, task_id, new_status)
    
    return TaskApproveResponse(
        task_id=task_id,
        status=new_status.value,
    )
