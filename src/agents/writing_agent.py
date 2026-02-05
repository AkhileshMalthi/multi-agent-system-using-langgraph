"""Writing Agent for creating content based on research."""

from typing import Any

from src.agents.state import WorkflowState, WorkflowStatus
from src.shared.redis_client import get_from_workspace
from src.shared.llm_provider import get_llm


COMPARISON_PROMPT = """You are a technical writer creating a comparison summary.

Based on the following research about LangGraph and CrewAI, write a short, clear 
comparison summary for a technical audience.

## LangGraph Research:
{langgraph_research}

## CrewAI Research:
{crewai_research}

## Original Request:
{prompt}

Write a professional comparison summary that:
1. Highlights key differences between the two frameworks
2. Discusses strengths of each approach
3. Provides guidance on when to use each
4. Is concise but comprehensive (2-3 paragraphs)

Comparison Summary:"""


def writing_node(state: WorkflowState) -> dict[str, Any]:
    """
    Writing node that creates a comparison summary based on research.
    
    This node:
    1. Reads research from state (or Redis workspace)
    2. Uses LLM to generate a comparison summary
    3. Returns draft for approval
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with draft summary
    """
    task_id = state.get("task_id", "")
    prompt = state.get("prompt", "")
    
    # Try to get research from state first, fall back to Redis
    langgraph_research = state.get("research_langgraph", "")
    crewai_research = state.get("research_crewai", "")
    
    if not langgraph_research or not crewai_research:
        # Fall back to Redis workspace
        workspace_data = get_from_workspace(task_id)
        if workspace_data:
            langgraph_research = workspace_data.get("research_langgraph", "")
            crewai_research = workspace_data.get("research_crewai", "")
    
    # Generate comparison using LLM
    llm = get_llm()
    
    formatted_prompt = COMPARISON_PROMPT.format(
        langgraph_research=langgraph_research,
        crewai_research=crewai_research,
        prompt=prompt,
    )
    
    response = llm.invoke(formatted_prompt)
    draft = response.content
    
    return {
        "draft": draft,
        "status": WorkflowStatus.WRITING,
    }
