"""Tools available to agents for performing research and actions."""

import os
from typing import Any
from langchain_core.tools import tool
from src.shared.llm_provider import get_llm


# Global counter for tracking flaky tool behavior (for testing)
_flaky_call_counts = {}


@tool
def llm_research(query: str) -> str:
    """
    Use LLM's knowledge to research a topic and provide comprehensive information.
    
    This is a real research tool that uses the LLM to generate detailed, accurate
    information about any topic based on its training data.
    
    Args:
        query: The research query or topic to investigate
        
    Returns:
        Comprehensive information about the topic
    """
    llm = get_llm(temperature=0.7)
    
    research_prompt = f"""You are a technical research assistant. Provide comprehensive, accurate information about the following topic:

{query}

Your response should include:
1. **Overview**: Brief introduction and context
2. **Key Features**: Main characteristics and capabilities
3. **Use Cases**: Common applications and scenarios
4. **Technical Details**: Important technical aspects
5. **Strengths**: Main advantages and benefits

Be specific, technical, and comprehensive. Focus on factual information."""

    response = llm.invoke(research_prompt)
    return response.content


@tool
def search_general(query: str) -> str:
    """
    General web search tool with built-in flaky behavior for testing retries.
    
    For the query "__FLAKY_TEST__", this tool will fail on the first call
    but succeed on subsequent calls, demonstrating retry resilience.
    
    For other queries, uses LLM-based research.
    
    Args:
        query: The search query
        
    Returns:
        Search results or research findings
    """
    global _flaky_call_counts
    
    # Handle flaky test case
    if "__FLAKY_TEST__" in query:
        call_key = f"flaky_{query}"
        current_count = _flaky_call_counts.get(call_key, 0)
        _flaky_call_counts[call_key] = current_count + 1
        
        if current_count == 0:
            # First call fails
            raise RuntimeError(
                "Simulated transient failure for flaky test. "
                "This should trigger a retry."
            )
        else:
            # Subsequent calls succeed
            return f"Flaky search succeeded on attempt {current_count + 1}: Results for '{query}'"
    
    # For normal queries, use LLM research
    return llm_research.invoke(query)


# Tool registry for dynamic selection
AVAILABLE_TOOLS = [
    llm_research,
    search_general,
]


def get_tool_by_name(name: str) -> Any:
    """
    Get a tool by name from the registry.
    
    Args:
        name: Tool name
        
    Returns:
        Tool function
        
    Raises:
        ValueError: If tool not found
    """
    for tool in AVAILABLE_TOOLS:
        if tool.name == name:
            return tool
    raise ValueError(f"Tool '{name}' not found in registry")


def list_available_tools() -> list[str]:
    """
    List all available tool names.
    
    Returns:
        List of tool names
    """
    return [tool.name for tool in AVAILABLE_TOOLS]
