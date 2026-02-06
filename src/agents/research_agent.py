"""Research Agent for gathering information."""

from typing import Any
import os

from tenacity import retry, stop_after_attempt, wait_exponential

from src.agents.state import WorkflowState, WorkflowStatus
from src.agents.tools import llm_research, get_tool_by_name
from src.agents.prompt_analyzer import PromptAnalyzer
from src.shared.redis_client import save_to_workspace
from src.shared.logger import log_agent_action
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


def get_research_tool():
    """
    Get the configured research tool.
    
    Returns tool based on RESEARCH_TOOL environment variable.
    Defaults to llm_research if not configured.
    """
    tool_name = os.getenv("RESEARCH_TOOL", "llm_research")
    
    try:
        return get_tool_by_name(tool_name)
    except ValueError:
        # Fallback to llm_research if configured tool not found
        return llm_research


def research_node(state: WorkflowState) -> dict[str, Any]:
    """
    Research node that dynamically gathers information based on prompt analysis.
    
    This node is now fully dynamic:
    1. Uses PromptAnalyzer to extract topics from ANY prompt
    2. Researches each topic using real LLM-based tools
    3. Saves findings to Redis workspace
    4. Returns updated state with research results
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with research findings
    """
    task_id = state.get("task_id", "")
    prompt = state.get("prompt", "")
    
    log_agent_action(task_id, "ResearchAgent", "Analyzing prompt to extract research topics")
    
    # Use PromptAnalyzer to dynamically extract topics and task type
    analyzer = PromptAnalyzer(llm=get_llm())
    analysis = analyzer.analyze(prompt)
    
    topics = analysis.get("topics", [])
    task_type = analysis.get("task_type", "summary")
    context = analysis.get("context", "")
    
    log_agent_action(
        task_id,
        "ResearchAgent",
        f"Identified {len(topics)} topics: {', '.join(topics)} | Task type: {task_type}"
    )
    
    # Get the research tool to use
    research_tool = get_research_tool()
    
    # Research each topic dynamically
    research_results = {}
    
    for topic in topics:
        log_agent_action(task_id, "ResearchAgent", f"Researching: {topic}")
        
        # Create detailed query incorporating context
        query = f"{topic} - {prompt}"
        if context:
            query += f" | Context: {context}"
        
        try:
            result = research_with_retry(research_tool, query)
            research_results[topic] = result
            log_agent_action(task_id, "ResearchAgent", f"Completed research for: {topic}")
        except Exception as e:
            log_agent_action(
                task_id,
                "ResearchAgent",
                f"Failed to research {topic}: {str(e)}"
            )
            research_results[topic] = f"Research failed: {str(e)}"
    
    log_agent_action(
        task_id,
        "ResearchAgent",
        f"Research completed for all {len(topics)} topics"
    )
    
    # Save to Redis workspace for the writing agent
    save_to_workspace(task_id, {
        "research_results": research_results,
        "topics": topics,
        "task_type": task_type,
        "context": context,
    })
    
    return {
        "research_results": research_results,
        "research_queries": topics,
        "task_type": task_type,
        "status": WorkflowStatus.RESEARCHING,
    }
