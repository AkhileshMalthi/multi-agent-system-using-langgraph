"""Search tools for the research agent."""

import os
from typing import Any

from langchain_core.tools import tool

# Track flaky tool call attempts for testing retry behavior
_flaky_call_counts: dict[str, int] = {}


def reset_flaky_counts() -> None:
    """Reset the flaky call counter (for testing)."""
    global _flaky_call_counts
    _flaky_call_counts = {}


@tool
def search_langgraph_features(query: str) -> str:
    """
    Search for information about LangGraph features.
    
    Args:
        query: The search query about LangGraph
        
    Returns:
        Information about LangGraph features
    """
    # Simulated search results for LangGraph
    return """
    LangGraph Key Features:
    
    1. **Stateful Graph Architecture**: LangGraph uses a graph-based approach where nodes
       represent agents or processing steps, and edges define the flow between them.
       State is passed and updated as execution flows through the graph.
    
    2. **Built-in Persistence**: Supports checkpointers for saving and restoring workflow
       state, enabling durable execution that can survive failures.
    
    3. **Human-in-the-Loop**: Native support for interrupts that pause execution and wait
       for human input before continuing. Uses the `interrupt()` function and `Command(resume=...)`
       pattern.
    
    4. **Conditional Routing**: Edges can be conditional, allowing dynamic routing based on
       state. Supports `add_conditional_edges()` for complex branching logic.
    
    5. **Integration with LangChain**: Seamlessly integrates with LangChain tools, models,
       and memory components.
    
    6. **Streaming Support**: Real-time streaming of intermediate results as the workflow
       progresses.
    
    7. **Multi-Agent Coordination**: Built specifically for orchestrating multiple agents
       working together on complex tasks.
    """


@tool  
def search_crewai_features(query: str) -> str:
    """
    Search for information about CrewAI features.
    
    Args:
        query: The search query about CrewAI
        
    Returns:
        Information about CrewAI features
    """
    # Simulated search results for CrewAI
    return """
    CrewAI Key Features:
    
    1. **Role-Based Agents**: Agents are defined with specific roles, goals, and backstories,
       making them specialized for particular tasks. Each agent has a clear purpose.
    
    2. **Task-Oriented Design**: Work is organized as tasks that are assigned to agents.
       Tasks can have dependencies and expected outputs.
    
    3. **Crew Orchestration**: A "Crew" coordinates multiple agents, managing task delegation
       and execution order automatically.
    
    4. **Sequential and Hierarchical Processes**: Supports different execution patterns -
       sequential (one after another) or hierarchical (manager delegates to workers).
    
    5. **Tool Integration**: Agents can use tools to interact with external systems,
       APIs, and data sources.
    
    6. **Memory Systems**: Supports short-term, long-term, and entity memory for agents
       to remember context across interactions.
    
    7. **Easy Agent Definition**: Simple, declarative syntax for defining agents and their
       capabilities using Python classes.
    """


@tool
def search_general(query: str) -> str:
    """
    General web search tool with built-in flaky behavior for testing retries.
    
    For the query "__FLAKY_TEST__", this tool will fail on the first call
    but succeed on subsequent calls, demonstrating retry resilience.
    
    Args:
        query: The search query
        
    Returns:
        Search results or error
        
    Raises:
        RuntimeError: On first call with "__FLAKY_TEST__" query
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
    
    # Default behavior for other queries
    return f"General search results for: {query}"


# List of all available tools
RESEARCH_TOOLS = [
    search_langgraph_features,
    search_crewai_features,
    search_general,
]
