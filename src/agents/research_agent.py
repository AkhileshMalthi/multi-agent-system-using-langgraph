"""Research Agent for gathering information."""

from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from src.agents.state import WorkflowState, WorkflowStatus
from src.agents.tools import search_langgraph_features, search_crewai_features
from src.shared.redis_client import save_to_workspace
from src.shared.logger import log_agent_action, log_retry
from src.shared.llm_provider import get_llm


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def research_with_retry(tool_func: Any, query: str) -> str:
    """
    Execute a research tool with retry logic.
    
    Args:
        tool_func: The tool function to call
        query: The search query
        
    Returns:
        Tool result
    """
    return tool_func.invoke(query)


def research_node(state: WorkflowState) -> dict[str, Any]:
    """
    Research node that gathers information about LangGraph and CrewAI.
    
    This node:
    1. Searches for LangGraph features
    2. Searches for CrewAI features  
    3. Saves findings to Redis workspace
    4. Returns updated state with research results
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with research findings
    """
    task_id = state.get("task_id", "")
    prompt = state.get("prompt", "")
    
    # Research LangGraph
    langgraph_research = research_with_retry(
        search_langgraph_features,
        f"LangGraph features for: {prompt}"
    )
    
    # Research CrewAI
    crewai_research = research_with_retry(
        search_crewai_features,
        f"CrewAI features for: {prompt}"
    )
    
    # Save to Redis workspace for the writing agent
    save_to_workspace(task_id, {
        "research_langgraph": langgraph_research,
        "research_crewai": crewai_research,
    })
    
    return {
        "research_langgraph": langgraph_research,
        "research_crewai": crewai_research,
        "status": WorkflowStatus.RESEARCHING,
    }
