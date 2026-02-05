"""Tests for the LangGraph workflow and tools."""

import pytest
from unittest.mock import patch, MagicMock

from src.agents.tools import (
    search_langgraph_features,
    search_crewai_features,
    search_general,
    reset_flaky_counts,
)
from src.agents.state import WorkflowState, WorkflowStatus


class TestSearchTools:
    """Tests for the search tools."""
    
    def test_search_langgraph_features(self):
        """Test LangGraph search tool returns relevant content."""
        result = search_langgraph_features.invoke("features")
        
        assert result is not None
        assert "LangGraph" in result
        assert "Stateful" in result or "graph" in result.lower()
    
    def test_search_crewai_features(self):
        """Test CrewAI search tool returns relevant content."""
        result = search_crewai_features.invoke("features")
        
        assert result is not None
        assert "CrewAI" in result
        assert "Agent" in result or "role" in result.lower()
    
    def test_search_general(self):
        """Test general search tool returns results."""
        result = search_general.invoke("test query")
        
        assert result is not None
        assert "test query" in result


class TestFlakyTool:
    """Tests for the flaky tool retry behavior."""
    
    def setup_method(self):
        """Reset flaky counter before each test."""
        reset_flaky_counts()
    
    def test_flaky_tool_fails_first_call(self):
        """Test that flaky tool fails on first call."""
        with pytest.raises(RuntimeError) as exc_info:
            search_general.invoke("__FLAKY_TEST__")
        
        assert "Simulated transient failure" in str(exc_info.value)
    
    def test_flaky_tool_succeeds_on_retry(self):
        """Test that flaky tool succeeds on second call."""
        # First call fails
        try:
            search_general.invoke("__FLAKY_TEST__")
        except RuntimeError:
            pass
        
        # Second call succeeds
        result = search_general.invoke("__FLAKY_TEST__")
        
        assert result is not None
        assert "succeeded" in result.lower()
        assert "attempt 2" in result
    
    def test_flaky_tool_multiple_retries(self):
        """Test multiple retry cycles with flaky tool."""
        reset_flaky_counts()
        
        # Should fail first time
        with pytest.raises(RuntimeError):
            search_general.invoke("__FLAKY_TEST__ query1")
        
        # Should succeed second time
        result = search_general.invoke("__FLAKY_TEST__ query1")
        assert "succeeded" in result.lower()
        
        # Different query should fail first time
        reset_flaky_counts()
        with pytest.raises(RuntimeError):
            search_general.invoke("__FLAKY_TEST__ query2")


class TestWorkflowState:
    """Tests for workflow state management."""
    
    def test_workflow_state_creation(self):
        """Test creating a workflow state."""
        state: WorkflowState = {
            "task_id": "test-123",
            "prompt": "Test prompt",
            "status": WorkflowStatus.PENDING,
        }
        
        assert state["task_id"] == "test-123"
        assert state["prompt"] == "Test prompt"
        assert state["status"] == WorkflowStatus.PENDING
    
    def test_workflow_status_constants(self):
        """Test workflow status constants are defined."""
        assert WorkflowStatus.PENDING == "PENDING"
        assert WorkflowStatus.RUNNING == "RUNNING"
        assert WorkflowStatus.RESEARCHING == "RESEARCHING"
        assert WorkflowStatus.WRITING == "WRITING"
        assert WorkflowStatus.AWAITING_APPROVAL == "AWAITING_APPROVAL"
        assert WorkflowStatus.RESUMED == "RESUMED"
        assert WorkflowStatus.COMPLETED == "COMPLETED"
        assert WorkflowStatus.FAILED == "FAILED"


class TestResearchAgent:
    """Tests for the research agent node."""
    
    @patch("src.agents.research_agent.save_to_workspace")
    def test_research_node_returns_research(self, mock_save):
        """Test research node returns research findings."""
        from src.agents.research_agent import research_node
        
        state: WorkflowState = {
            "task_id": "test-123",
            "prompt": "Compare LangGraph and CrewAI",
            "status": WorkflowStatus.RUNNING,
        }
        
        result = research_node(state)
        
        assert "research_langgraph" in result
        assert "research_crewai" in result
        assert result["status"] == WorkflowStatus.RESEARCHING
        mock_save.assert_called_once()


class TestWritingAgent:
    """Tests for the writing agent node."""
    
    @patch("src.agents.writing_agent.get_llm")
    @patch("src.agents.writing_agent.get_from_workspace")
    def test_writing_node_generates_draft(self, mock_workspace, mock_llm):
        """Test writing node generates draft from research."""
        from src.agents.writing_agent import writing_node
        
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.content = "This is a comparison summary..."
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance
        
        # Mock workspace data
        mock_workspace.return_value = {
            "research_langgraph": "LangGraph info...",
            "research_crewai": "CrewAI info...",
        }
        
        state: WorkflowState = {
            "task_id": "test-123",
            "prompt": "Compare LangGraph and CrewAI",
            "status": WorkflowStatus.RESEARCHING,
        }
        
        result = writing_node(state)
        
        assert "draft" in result
        assert result["draft"] == "This is a comparison summary..."
        assert result["status"] == WorkflowStatus.WRITING
