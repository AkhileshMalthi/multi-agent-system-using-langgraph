"""Writing Agent for creating content based on research."""

from typing import Any

from src.agents.state import WorkflowState, WorkflowStatus
from src.shared.redis_client import get_from_workspace
from src.shared.llm_provider import get_llm
from src.shared.logger import log_agent_action


# Template for comparison tasks
COMPARISON_TEMPLATE = """You are a technical writer creating a comparison.

Based on the following research findings, write a clear comparison for a technical audience.

{research_context}

## Original Request:
{prompt}

Write a professional comparison that:
1. Highlights key differences between the subjects
2. Discusses strengths and weaknesses of each
3. Provides guidance on when to use each
4. Is concise but comprehensive (2-3 paragraphs)

Comparison:"""


# Template for tutorial tasks
TUTORIAL_TEMPLATE = """You are a technical writer creating a tutorial.

Based on the following research findings, write a step-by-step tutorial.

{research_context}

## Original Request:
{prompt}

Write a clear tutorial that:
1. Lists prerequisites if needed
2. Provides numbered, actionable steps
3. Explains what each step accomplishes
4. Includes practical examples
5. Is beginner-friendly but technically accurate

Tutorial:"""


# Template for analysis tasks
ANALYSIS_TEMPLATE = """You are a technical analyst creating an in-depth analysis.

Based on the following research findings, provide a comprehensive technical analysis.

{research_context}

## Original Request:
{prompt}

Write a detailed analysis that:
1. Examines key aspects in depth
2. Discusses trade-offs and considerations
3. Provides technical insights and recommendations
4. Is thorough and well-structured

Analysis:"""


# Template for summary tasks
SUMMARY_TEMPLATE = """You are a technical writer creating an informative summary.

Based on the following research findings, write a clear summary.

{research_context}

## Original Request:
{prompt}

Write a concise summary that:
1. Covers the main points from the research
2. Is well-organized and easy to understand
3. Provides actionable information
4. Is appropriate for a technical audience

Summary:"""


def select_template(task_type: str) -> str:
    """
    Select the appropriate template based on task type.
    
    Args:
        task_type: The type of task (comparison, tutorial, analysis, summary)
        
    Returns:
        Template string
    """
    templates = {
        "comparison": COMPARISON_TEMPLATE,
        "tutorial": TUTORIAL_TEMPLATE,
        "analysis": ANALYSIS_TEMPLATE,
        "summary": SUMMARY_TEMPLATE,
    }
    
    return templates.get(task_type, SUMMARY_TEMPLATE)


def format_research_context(research_results: dict[str, str]) -> str:
    """
    Format research results into context for the LLM prompt.
    
    Args:
        research_results: Dict mapping topics to research findings
        
    Returns:
        Formatted string with all research
    """
    if not research_results:
        return "No research available."
    
    sections = []
    for topic, findings in research_results.items():
        sections.append(f"## {topic}\n{findings}")
    
    return "\n\n".join(sections)


def writing_node(state: WorkflowState) -> dict[str, Any]:
    """
    Writing node that creates content based on research and task type.
    
    Now fully dynamic - adapts to any task type and research topics.
    
    This node:
    1. Reads research from state (or Redis workspace)
    2. Selects appropriate template based on task_type
    3. Uses LLM to generate output
    4. Returns draft for approval
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with draft
    """
    task_id = state.get("task_id", "")
    prompt = state.get("prompt", "")
    task_type = state.get("task_type", "summary")
    
    log_agent_action(task_id, "WritingAgent", f"Starting {task_type} generation")
    
    # Get research results from state (new flexible format)
    research_results = state.get("research_results", {})
    
    if not research_results:
        # Fall back to Redis workspace
        log_agent_action(task_id, "WritingAgent", "Loading research from Redis workspace")
        workspace_data = get_from_workspace(task_id)
        if workspace_data:
            research_results = workspace_data.get("research_results", {})
            task_type = workspace_data.get("task_type", task_type)
    
    if not research_results:
        log_agent_action(task_id, "WritingAgent", "No research results available")
        return {
            "draft": "Error: No research results available to generate content.",
            "status": WorkflowStatus.WRITING,
        }
    
    log_agent_action(
        task_id,
        "WritingAgent",
        f"Found research for {len(research_results)} topics, using {task_type} template"
    )
    
    # Select template based on task type
    template = select_template(task_type)
    
    # Format research context
    research_context = format_research_context(research_results)
    
    # Generate content using LLM
    llm = get_llm(temperature=0.7)  # Higher temp for more creative writing
    
    formatted_prompt = template.format(
        research_context=research_context,
        prompt=prompt,
    )
    
    log_agent_action(task_id, "WritingAgent", "Generating content with LLM")
    response = llm.invoke(formatted_prompt)
    draft = response.content
    
    log_agent_action(
        task_id,
        "WritingAgent",
        f"Generated {len(draft)} character draft for approval"
    )
    
    return {
        "draft": draft,
        "status": WorkflowStatus.WRITING,
    }
