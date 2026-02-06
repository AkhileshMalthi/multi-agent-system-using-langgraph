"""Prompt Analyzer for extracting research requirements from user prompts."""

import json
from typing import Any
from src.shared.llm_provider import get_llm


class PromptAnalyzer:
    """
    Analyzes user prompts to extract research requirements and task type.
    
    Uses LLM to intelligently parse prompts and determine:
    - What topics need to be researched
    - What type of task is being requested
    - What output format is expected
    """
    
    def __init__(self, llm=None):
        """
        Initialize the analyzer.
        
        Args:
            llm: Optional LLM instance. If not provided, uses default from get_llm()
        """
        self.llm = llm or get_llm(temperature=0.1)  # Low temp for consistent parsing
    
    def analyze(self, prompt: str) -> dict[str, Any]:
        """
        Analyze a user prompt to extract research requirements.
        
        Args:
            prompt: The user's request/prompt
            
        Returns:
            Dictionary containing:
                - topics: List of topics to research
                - task_type: Type of task (comparison, tutorial, analysis, summary)
                - context: Additional context or requirements
        """
        analysis_prompt = f"""You are a prompt analysis assistant. Analyze the following user request and extract structured information.

User Request:
"{prompt}"

Analyze this request and provide a JSON response with the following structure:
{{
    "topics": ["topic1", "topic2", ...],
    "task_type": "comparison" | "tutorial" | "analysis" | "summary",
    "context": "any additional context or requirements"
}}

Guidelines:
- **topics**: Extract all subjects, frameworks, technologies, or concepts that need to be researched
- **task_type**:
  - "comparison": When comparing multiple things (e.g., "compare X and Y", "X vs Y")
  - "tutorial": When asking for how-to guides, step-by-step instructions
  - "analysis": When asking for in-depth examination or evaluation
  - "summary": When asking for general information or overview
- **context**: Capture any specific requirements like "for technical audience", "beginner-friendly", etc.

Respond ONLY with valid JSON, no other text.

JSON:"""

        try:
            response = self.llm.invoke(analysis_prompt)
            content = response.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
                content = content.replace("```json", "").replace("```", "").strip()
            
            # Parse JSON
            analysis = json.loads(content)
            
            # Validate required fields
            if "topics" not in analysis or "task_type" not in analysis:
                raise ValueError("Missing required fields in analysis")
            
            # Ensure topics is a list
            if isinstance(analysis["topics"], str):
                analysis["topics"] = [analysis["topics"]]
            
            # Validate task_type
            valid_types = ["comparison", "tutorial", "analysis", "summary"]
            if analysis["task_type"] not in valid_types:
                # Default to summary if invalid
                analysis["task_type"] = "summary"
            
            return analysis
            
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback: Simple keyword-based extraction
            return self._fallback_analysis(prompt)
    
    def _fallback_analysis(self, prompt: str) -> dict[str, Any]:
        """
        Fallback analysis using simple keyword matching.
        
        Used when LLM-based analysis fails.
        
        Args:
            prompt: The user prompt
            
        Returns:
            Basic analysis dict
        """
        prompt_lower = prompt.lower()
        
        # Extract topics using simple heuristics
        topics = []
        
        # Look for common patterns
        if "langgraph" in prompt_lower:
            topics.append("LangGraph")
        if "crewai" in prompt_lower:
            topics.append("CrewAI")
        if "redis" in prompt_lower:
            topics.append("Redis")
        if "postgresql" in prompt_lower or "postgres" in prompt_lower:
            topics.append("PostgreSQL")
        if "docker" in prompt_lower:
            topics.append("Docker")
        if "kubernetes" in prompt_lower or "k8s" in prompt_lower:
            topics.append("Kubernetes")
        
        # Default if no topics found
        if not topics:
            topics = ["general topic"]
        
        # Determine task type
        task_type = "summary"  # Default
        if any(word in prompt_lower for word in ["compare", "vs", "versus", "difference"]):
            task_type = "comparison"
        elif any(word in prompt_lower for word in ["tutorial", "how to", "guide", "step"]):
            task_type = "tutorial"
        elif any(word in prompt_lower for word in ["analyze", "analysis", "evaluate", "examine"]):
            task_type = "analysis"
        
        return {
            "topics": topics,
            "task_type": task_type,
            "context": ""
        }
