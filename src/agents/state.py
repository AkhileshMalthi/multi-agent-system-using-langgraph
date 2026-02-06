"""Workflow state definition for the multi-agent system."""

from typing import Annotated, TypedDict, Any
from operator import add


class WorkflowState(TypedDict, total=False):
    """
    State shared across all nodes in the LangGraph workflow.
    
    This state schema is now flexible and can handle any research topics,
    not just LangGraph and CrewAI.
    
    Attributes:
        task_id: UUID of the task being processed
        prompt: The original user prompt
        status: Current workflow status
        research_results: Generic dict mapping topic names to research findings
        research_queries: List of topics extracted from the prompt
        task_type: Type of task (comparison, tutorial, analysis, summary)
        draft: The draft output
        result: The final approved result
        approved: Whether the draft was approved
        feedback: Human feedback if provided
        error: Error message if workflow failed
    """
    task_id: str
    prompt: str
    status: str
    
    # Generic research storage - replaces hardcoded fields
    research_results: dict[str, Any]  # {"topic_name": "findings"}
    research_queries: list[str]       # ["topic1", "topic2"]
    task_type: str                    # "comparison", "tutorial", "analysis", "summary"
    
    # Output fields
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
