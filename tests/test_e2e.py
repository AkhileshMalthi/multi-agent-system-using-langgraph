"""End-to-end tests for the complete multi-agent workflow.

These tests verify the generalized system capabilities (handling diverse prompts like 
comparisons, tutorials, analysis) while ensuring backward compatibility and 
robust error handling.

Run with: docker-compose up -d && pytest tests/test_e2e.py -v
"""

import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app


# Test configuration
API_BASE_URL = "http://test"
MAX_POLL_ATTEMPTS = 30
POLL_INTERVAL = 2  # seconds


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_different_comparison_redis_vs_postgresql():
    """
    Test with a completely different comparison topic.
    Verifies the system is not hardcoded for LangGraph vs CrewAI.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=API_BASE_URL) as client:
        
        prompt = "Compare Redis and PostgreSQL for caching use cases. What are the pros and cons of each?"
        print(f"\nExample 1: Testing different comparison: {prompt}")
        
        create_response = await client.post(
            "/api/v1/tasks",
            json={"prompt": prompt}
        )
        assert create_response.status_code == 202
        task_id = create_response.json()["task_id"]
        
        # Wait for approval
        for _ in range(MAX_POLL_ATTEMPTS):
            await asyncio.sleep(POLL_INTERVAL)
            status_response = await client.get(f"/api/v1/tasks/{task_id}")
            if status_response.json()["status"] == "AWAITING_APPROVAL":
                break
        
        # Approve
        await client.post(
            f"/api/v1/tasks/{task_id}/approve",
            json={"approved": True, "feedback": "Test approval"}
        )
        
        # Wait for completion
        completed = False
        for _ in range(MAX_POLL_ATTEMPTS):
            await asyncio.sleep(POLL_INTERVAL)
            status_response = await client.get(f"/api/v1/tasks/{task_id}")
            task_status = status_response.json()
            
            if task_status["status"] == "COMPLETED":
                completed = True
                result = task_status.get("result", "")
                
                # Verify result mentions the correct topics (not LangGraph/CrewAI!)
                assert "Redis" in result or "redis" in result.lower(), "Result should mention Redis"
                assert "PostgreSQL" in result or "postgres" in result.lower(), "Result should mention PostgreSQL"
                assert "LangGraph" not in result, "Result should NOT mention LangGraph (old hardcoded topic)"
                
                print(f"Result discusses Redis and PostgreSQL: {result[:200]}...")
                break
        
        assert completed, "Task did not complete"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_single_topic_research():
    """
    Test researching a single topic (not a comparison).
    Verifies the system handles non-comparison tasks.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=API_BASE_URL) as client:
        
        prompt = "Research the key features of Kubernetes and explain its main use cases."
        print(f"\nExample 2: Testing single-topic research: {prompt}")
        
        create_response = await client.post(
            "/api/v1/tasks",
            json={"prompt": prompt}
        )
        task_id = create_response.json()["task_id"]
        
        # Wait for approval
        for _ in range(MAX_POLL_ATTEMPTS):
            await asyncio.sleep(POLL_INTERVAL)
            status_response = await client.get(f"/api/v1/tasks/{task_id}")
            if status_response.json()["status"] == "AWAITING_APPROVAL":
                break
        
        # Approve
        await client.post(
            f"/api/v1/tasks/{task_id}/approve",
            json={"approved": True}
        )
        
        # Wait for completion
        for _ in range(MAX_POLL_ATTEMPTS):
            await asyncio.sleep(POLL_INTERVAL)
            status_response = await client.get(f"/api/v1/tasks/{task_id}")
            task_status = status_response.json()
            
            if task_status["status"] == "COMPLETED":
                result = task_status.get("result", "")
                assert "Kubernetes" in result or "kubernetes" in result.lower() or "K8s" in result
                assert len(result) > 100
                print(f"Single-topic research successful: {result[:200]}...")
                break


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_tutorial_request():
    """
    Test generating a tutorial (different task type).
    Verifies the system handles tutorial-style requests.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=API_BASE_URL) as client:
        
        prompt = "Create a beginner's tutorial for setting up Docker on a new machine."
        print(f"\nExample 3: Testing tutorial generation: {prompt}")
        
        create_response = await client.post(
            "/api/v1/tasks",
            json={"prompt": prompt}
        )
        task_id = create_response.json()["task_id"]
        
        # Wait for approval
        for _ in range(MAX_POLL_ATTEMPTS):
            await asyncio.sleep(POLL_INTERVAL)
            status_response = await client.get(f"/api/v1/tasks/{task_id}")
            if status_response.json()["status"] == "AWAITING_APPROVAL":
                break
        
        # Approve
        await client.post(
            f"/api/v1/tasks/{task_id}/approve",
            json={"approved": True}
        )
        
        # Wait for completion
        for _ in range(MAX_POLL_ATTEMPTS):
            await asyncio.sleep(POLL_INTERVAL)
            status_response = await client.get(f"/api/v1/tasks/{task_id}")
            task_status = status_response.json()
            
            if task_status["status"] == "COMPLETED":
                result = task_status.get("result", "")
                assert "Docker" in result or "docker" in result.lower()
                # Tutorial should have step-like language
                tutorial_indicators = ["step", "first", "install", "setup", "how to"]
                has_tutorial_language = any(indicator in result.lower() for indicator in tutorial_indicators)
                assert has_tutorial_language, "Result should read like a tutorial"
                print(f"Tutorial generation successful: {result[:200]}...")
                break


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_analysis_request():
    """
    Test generating an analysis (different task type).
    Verifies the system handles analysis-style requests.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=API_BASE_URL) as client:
        
        prompt = "Analyze the trade-offs between microservices and monolithic architectures."
        print(f"\nExample 4: Testing analysis generation: {prompt}")
        
        create_response = await client.post(
            "/api/v1/tasks",
            json={"prompt": prompt}
        )
        task_id = create_response.json()["task_id"]
        
        # Wait for approval
        for _ in range(MAX_POLL_ATTEMPTS):
            await asyncio.sleep(POLL_INTERVAL)
            status_response = await client.get(f"/api/v1/tasks/{task_id}")
            if status_response.json()["status"] == "AWAITING_APPROVAL":
                break
        
        # Approve
        await client.post(
            f"/api/v1/tasks/{task_id}/approve",
            json={"approved": True}
        )
        
        # Wait for completion
        for _ in range(MAX_POLL_ATTEMPTS):
            await asyncio.sleep(POLL_INTERVAL)
            status_response = await client.get(f"/api/v1/tasks/{task_id}")
            task_status = status_response.json()
            
            if task_status["status"] == "COMPLETED":
                result = task_status.get("result", "")
                assert "microservices" in result.lower() or "monolithic" in result.lower()
                analysis_indicators = ["trade-off", "advantage", "disadvantage", "consider", "however"]
                has_analysis_language = any(indicator in result.lower() for indicator in analysis_indicators)
                assert has_analysis_language, "Result should read like an analysis"
                print(f"Analysis generation successful: {result[:200]}...")
                break


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_original_backward_compatibility():
    """
    Test the complete multi-agent workflow with the original hardcoded task.
    
    This ensures backward compatibility for the original LangGraph vs CrewAI test case
    and verifies detailed log info and status transitions.
    """
    TEST_PROMPT = "Research the key features of LangGraph and CrewAI. Write a short comparison summary for a technical audience."
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=API_BASE_URL) as client:
        
        print(f"\nExample 5: Testing backward compatibility: {TEST_PROMPT}")
        create_response = await client.post(
            "/api/v1/tasks",
            json={"prompt": TEST_PROMPT}
        )
        assert create_response.status_code == 202
        task_id = create_response.json()["task_id"]
        print(f"Task created: {task_id}")
        
        # Wait for AWAITING_APPROVAL
        approval_reached = False
        for attempt in range(MAX_POLL_ATTEMPTS):
            await asyncio.sleep(POLL_INTERVAL)
            
            status_response = await client.get(f"/api/v1/tasks/{task_id}")
            task_status = status_response.json()
            current_status = task_status["status"]
            
            if current_status == "AWAITING_APPROVAL":
                approval_reached = True
                
                # Check detailed logs (feature from original test)
                agent_logs = task_status.get("agent_logs", [])
                assert len(agent_logs) >= 3, f"Expected logs, got {len(agent_logs)}"
                agent_names = [log["agent"] for log in agent_logs]
                assert "ResearchAgent" in agent_names
                assert "WritingAgent" in agent_names
                
                print("Reached AWAITING_APPROVAL with correct logs")
                break
            elif current_status == "FAILED":
                pytest.fail(f"Task failed: {task_status.get('result')}")
        
        assert approval_reached, "Task did not reach AWAITING_APPROVAL"
        
        # Approve
        approval_response = await client.post(
            f"/api/v1/tasks/{task_id}/approve",
            json={"approved": True, "feedback": "Automated test approval"}
        )
        assert approval_response.status_code == 200
        
        # Wait for completion
        completed = False
        for attempt in range(MAX_POLL_ATTEMPTS):
            await asyncio.sleep(POLL_INTERVAL)
            
            status_response = await client.get(f"/api/v1/tasks/{task_id}")
            task_status = status_response.json()
            current_status = task_status["status"]
            
            if current_status == "COMPLETED":
                completed = True
                result = task_status.get("result", "")
                
                # Verify result content (original requirements)
                assert "LangGraph" in result or "langgraph" in result.lower()
                assert "CrewAI" in result or "crewai" in result.lower()
                assert len(result) > 50
                
                # Verify final logs
                agent_logs = task_status.get("agent_logs", [])
                assert len(agent_logs) >= 5, "Expected more logs in final state"
                
                print(f"Backward compatibility verified! Result matches original requirements.")
                break
        
        assert completed, "Task did not complete"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_task_rejection():
    """
    Test that rejecting a task properly updates the status to FAILED.
    """
    TEST_PROMPT = "Research something for rejection test."
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=API_BASE_URL) as client:
        
        create_response = await client.post(
            "/api/v1/tasks",
            json={"prompt": TEST_PROMPT}
        )
        task_id = create_response.json()["task_id"]
        
        # Wait for approval
        for _ in range(MAX_POLL_ATTEMPTS):
            await asyncio.sleep(POLL_INTERVAL)
            status_response = await client.get(f"/api/v1/tasks/{task_id}")
            if status_response.json()["status"] == "AWAITING_APPROVAL":
                break
        
        # Reject
        approval_response = await client.post(
            f"/api/v1/tasks/{task_id}/approve",
            json={"approved": False, "feedback": "Test rejection"}
        )
        assert approval_response.status_code == 200
        
        # Check final status
        final_status = await client.get(f"/api/v1/tasks/{task_id}")
        assert final_status.json()["status"] in ["FAILED", "REJECTED"]
        print("Task rejection handled correctly")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_invalid_approval_on_non_pending_task():
    """
    Test that approving a task not in AWAITING_APPROVAL state returns error.
    """
    TEST_PROMPT = "Assume strict state checks."
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=API_BASE_URL) as client:
        
        create_response = await client.post(
            "/api/v1/tasks",
            json={"prompt": TEST_PROMPT}
        )
        task_id = create_response.json()["task_id"]
        
        # Try to approve immediately (task is PENDING/RUNNING)
        approval_response = await client.post(
            f"/api/v1/tasks/{task_id}/approve",
            json={"approved": True}
        )
        
        assert approval_response.status_code == 400
        assert "not awaiting approval" in approval_response.json()["detail"].lower()
        print("Invalid approval state check passed")
