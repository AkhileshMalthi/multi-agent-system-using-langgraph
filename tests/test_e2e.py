"""End-to-end tests for the complete multi-agent workflow.

These tests require Docker services to be running.
Run with: docker-compose up -d && pytest tests/test_e2e.py -v
"""

import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app


# Test configuration
API_BASE_URL = "http://test"
TEST_PROMPT = "Research the key features of LangGraph and CrewAI. Write a short comparison summary for a technical audience."
MAX_POLL_ATTEMPTS = 30
POLL_INTERVAL = 2  # seconds


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_complete_workflow_end_to_end():
    """
    Test the complete multi-agent workflow from start to finish.
    
    This test verifies:
    1. Task creation via POST /api/v1/tasks
    2. Workflow execution with status transitions
    3. Human-in-the-loop approval mechanism
    4. Final completion with result and agent logs
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=API_BASE_URL) as client:
        
        # Step 1: Create a new task
        print("\n📝 Step 1: Creating task...")
        create_response = await client.post(
            "/api/v1/tasks",
            json={"prompt": TEST_PROMPT}
        )
        assert create_response.status_code == 202, f"Expected 202, got {create_response.status_code}"
        
        task_data = create_response.json()
        task_id = task_data["task_id"]
        assert task_data["status"] == "PENDING"
        print(f"✅ Task created: {task_id}")
        
        # Step 2: Poll until task reaches AWAITING_APPROVAL
        print("\n⏳ Step 2: Waiting for AWAITING_APPROVAL status...")
        approval_reached = False
        
        for attempt in range(MAX_POLL_ATTEMPTS):
            await asyncio.sleep(POLL_INTERVAL)
            
            status_response = await client.get(f"/api/v1/tasks/{task_id}")
            assert status_response.status_code == 200
            
            task_status = status_response.json()
            current_status = task_status["status"]
            print(f"  Attempt {attempt + 1}/{MAX_POLL_ATTEMPTS}: Status = {current_status}")
            
            if current_status == "AWAITING_APPROVAL":
                approval_reached = True
                print("✅ Task reached AWAITING_APPROVAL")
                
                # Verify agent logs at this stage
                agent_logs = task_status.get("agent_logs", [])
                assert len(agent_logs) >= 3, f"Expected at least 3 log entries, got {len(agent_logs)}"
                
                # Verify expected agents logged actions
                agent_names = [log["agent"] for log in agent_logs]
                assert "ResearchAgent" in agent_names, "ResearchAgent should have logged"
                assert "WritingAgent" in agent_names, "WritingAgent should have logged"
                assert "Orchestrator" in agent_names, "Orchestrator should have logged"
                
                break
            elif current_status == "FAILED":
                pytest.fail(f"Task failed before approval: {task_status.get('result', 'No error message')}")
        
        assert approval_reached, f"Task did not reach AWAITING_APPROVAL within {MAX_POLL_ATTEMPTS * POLL_INTERVAL}s"
        
        # Step 3: Approve the task
        print("\n✅ Step 3: Approving task...")
        approval_response = await client.post(
            f"/api/v1/tasks/{task_id}/approve",
            json={
                "approved": True,
                "feedback": "Automated test approval"
            }
        )
        assert approval_response.status_code == 200
        
        approval_data = approval_response.json()
        assert approval_data["status"] == "RESUMED"
        print("✅ Task approved and resumed")
        
        # Step 4: Poll until task completes
        print("\n⏳ Step 4: Waiting for COMPLETED status...")
        completed = False
        
        for attempt in range(MAX_POLL_ATTEMPTS):
            await asyncio.sleep(POLL_INTERVAL)
            
            status_response = await client.get(f"/api/v1/tasks/{task_id}")
            assert status_response.status_code == 200
            
            task_status = status_response.json()
            current_status = task_status["status"]
            print(f"  Attempt {attempt + 1}/{MAX_POLL_ATTEMPTS}: Status = {current_status}")
            
            if current_status == "COMPLETED":
                completed = True
                print("✅ Task completed successfully")
                
                # Verify final result
                result = task_status.get("result")
                assert result is not None, "Result should not be None"
                assert len(result) > 50, "Result should contain substantial content"
                assert "LangGraph" in result or "langgraph" in result.lower(), "Result should mention LangGraph"
                assert "CrewAI" in result or "crewai" in result.lower(), "Result should mention CrewAI"
                
                # Verify final agent logs
                agent_logs = task_status.get("agent_logs", [])
                assert len(agent_logs) >= 5, f"Expected at least 5 log entries in final state, got {len(agent_logs)}"
                
                # Check for approval log entry
                approval_logs = [log for log in agent_logs if "approval" in log.get("action", "").lower()]
                assert len(approval_logs) > 0, "Should have approval-related log entry"
                
                print(f"\n📊 Final Statistics:")
                print(f"  - Total agent logs: {len(agent_logs)}")
                print(f"  - Result length: {len(result)} characters")
                print(f"  - Result preview: {result[:100]}...")
                
                break
            elif current_status == "FAILED":
                pytest.fail(f"Task failed after approval: {task_status.get('result', 'No error message')}")
        
        assert completed, f"Task did not complete within {MAX_POLL_ATTEMPTS * POLL_INTERVAL}s"
        
        print("\n🎉 End-to-end test PASSED!")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_task_rejection():
    """
    Test that rejecting a task properly updates the status.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=API_BASE_URL) as client:
        
        # Create task
        create_response = await client.post(
            "/api/v1/tasks",
            json={"prompt": TEST_PROMPT}
        )
        task_id = create_response.json()["task_id"]
        
        # Wait for AWAITING_APPROVAL
        for _ in range(MAX_POLL_ATTEMPTS):
            await asyncio.sleep(POLL_INTERVAL)
            status_response = await client.get(f"/api/v1/tasks/{task_id}")
            if status_response.json()["status"] == "AWAITING_APPROVAL":
                break
        
        # Reject the task
        approval_response = await client.post(
            f"/api/v1/tasks/{task_id}/approve",
            json={
                "approved": False,
                "feedback": "Test rejection"
            }
        )
        
        assert approval_response.status_code == 200
        # Status should be FAILED after rejection
        final_status = await client.get(f"/api/v1/tasks/{task_id}")
        # Note: The current implementation sets status to FAILED on rejection
        # If your implementation differs, adjust this assertion
        assert final_status.json()["status"] in ["FAILED", "REJECTED"]


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_invalid_approval_on_non_pending_task():
    """
    Test that approving a task not in AWAITING_APPROVAL state returns error.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=API_BASE_URL) as client:
        
        # Create task
        create_response = await client.post(
            "/api/v1/tasks",
            json={"prompt": TEST_PROMPT}
        )
        task_id = create_response.json()["task_id"]
        
        # Try to approve immediately (should fail - task is PENDING, not AWAITING_APPROVAL)
        approval_response = await client.post(
            f"/api/v1/tasks/{task_id}/approve",
            json={"approved": True, "feedback": "Should fail"}
        )
        
        # Should return 400 Bad Request
        assert approval_response.status_code == 400
        assert "not awaiting approval" in approval_response.json()["detail"].lower()
