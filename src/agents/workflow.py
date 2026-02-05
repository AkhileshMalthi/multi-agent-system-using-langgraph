"""LangGraph workflow definition for the multi-agent system."""

from typing import Any, Literal

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

from src.agents.state import WorkflowState, WorkflowStatus
from src.agents.research_agent import research_node
from src.agents.writing_agent import writing_node
from src.shared.redis_client import delete_workspace


# Create a global checkpointer for state persistence
_checkpointer = MemorySaver()


def approval_node(state: WorkflowState) -> Command[Literal["finalize", "failed"]]:
    """
    Approval node that pauses for human review.
    
    This node uses LangGraph's interrupt() to pause execution and wait
    for human approval via the API.
    
    Args:
        state: Current workflow state with draft
        
    Returns:
        Command to route to finalize or failed based on approval
    """
    draft = state.get("draft", "")
    task_id = state.get("task_id", "")
    
    # Pause and wait for human approval
    # The value passed to interrupt() is returned under __interrupt__ to the caller
    approval_response = interrupt({
        "question": "Do you approve this draft?",
        "task_id": task_id,
        "draft": draft,
    })
    
    # approval_response is the value passed to Command(resume=...) when resuming
    if isinstance(approval_response, dict):
        approved = approval_response.get("approved", False)
        feedback = approval_response.get("feedback", "")
    else:
        approved = bool(approval_response)
        feedback = ""
    
    if approved:
        return Command(goto="finalize", update={"approved": True, "feedback": feedback})
    else:
        return Command(goto="failed", update={"approved": False, "feedback": feedback})


def finalize_node(state: WorkflowState) -> dict[str, Any]:
    """
    Finalize node that completes the workflow.
    
    Args:
        state: Current workflow state
        
    Returns:
        Final state with result
    """
    task_id = state.get("task_id", "")
    draft = state.get("draft", "")
    
    # Clean up Redis workspace
    delete_workspace(task_id)
    
    return {
        "result": draft,
        "status": WorkflowStatus.COMPLETED,
    }


def failed_node(state: WorkflowState) -> dict[str, Any]:
    """
    Failed node for when approval is rejected.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with failed status
    """
    task_id = state.get("task_id", "")
    feedback = state.get("feedback", "Draft was rejected")
    
    # Clean up Redis workspace
    delete_workspace(task_id)
    
    return {
        "error": feedback,
        "status": WorkflowStatus.FAILED,
    }


def create_workflow() -> StateGraph:
    """
    Create the LangGraph workflow for the multi-agent system.
    
    Workflow:
    START -> research -> writing -> approval -> finalize -> END
                                        |
                                        +-> failed -> END
    
    Returns:
        Compiled StateGraph ready for execution
    """
    builder = StateGraph(WorkflowState)
    
    # Add nodes
    builder.add_node("research", research_node)
    builder.add_node("writing", writing_node)
    builder.add_node("approval", approval_node)
    builder.add_node("finalize", finalize_node)
    builder.add_node("failed", failed_node)
    
    # Add edges
    builder.add_edge(START, "research")
    builder.add_edge("research", "writing")
    builder.add_edge("writing", "approval")
    # approval node uses Command(goto=...) for routing, no explicit edges needed
    builder.add_edge("finalize", END)
    builder.add_edge("failed", END)
    
    # Compile with checkpointer for interrupt/resume support
    return builder.compile(checkpointer=_checkpointer)


def run_workflow(
    task_id: str,
    prompt: str,
    resume: bool = False,
    resume_value: Any = None,
) -> dict[str, Any]:
    """
    Run the workflow for a task.
    
    Args:
        task_id: UUID of the task (used as thread_id for persistence)
        prompt: The user's prompt
        resume: Whether this is a resume operation
        resume_value: Value to pass when resuming (e.g., approval response)
        
    Returns:
        Workflow result state
    """
    graph = create_workflow()
    config = {"configurable": {"thread_id": task_id}}
    
    if resume:
        # Resume from interrupt with the provided value
        result = graph.invoke(Command(resume=resume_value), config=config)
    else:
        # Start new workflow
        initial_state: WorkflowState = {
            "task_id": task_id,
            "prompt": prompt,
            "status": WorkflowStatus.RUNNING,
        }
        result = graph.invoke(initial_state, config=config)
    
    return result


def get_interrupt_info(result: dict[str, Any]) -> dict[str, Any] | None:
    """
    Extract interrupt information from a workflow result.
    
    Args:
        result: Workflow execution result
        
    Returns:
        Interrupt info dict or None if not interrupted
    """
    interrupt_data = result.get("__interrupt__")
    if interrupt_data and len(interrupt_data) > 0:
        return interrupt_data[0].value
    return None
