"""Workflow state definition for the multi-agent system."""

from typing import Annotated, TypedDict
from operator import add


class WorkflowState(TypedDict, total=False):
    """
    State shared across all nodes in the LangGraph workflow.
    
    Attributes:
        task_id: UUID of the task being processed
        prompt: The original user prompt
        status: Current workflow status
        research_langgraph: Research findings about LangGraph
        research_crewai: Research findings about CrewAI
        draft: The draft comparison summary
        result: The final approved result
        approved: Whether the draft was approved
        feedback: Human feedback if provided
        error: Error message if workflow failed
    """
    task_id: str
    prompt: str
    status: str
    research_langgraph: str
    research_crewai: str
    draft: str
    result: str
    approved: bool
    feedback: str
    error: str


# Status constants for workflow phases
class WorkflowStatus:
    """Constants for workflow status values."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    RESEARCHING = "RESEARCHING"
    WRITING = "WRITING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    RESUMED = "RESUMED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
