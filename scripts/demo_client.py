import requests
import time
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def print_step(step, msg):
    print(f"\n🚀 {step}: {msg}")

def print_json(data):
    print(json.dumps(data, indent=2))

def main():
    print("🔎 Starting Manual Verification Demo...")
    
    # 1. Health Check
    print_step("Step 1", "Checking API Health...")
    try:
        pass 
    except Exception as e:
        print(f"❌ API might be down: {e}")
        return

    # 2. Create Task
    PROMPT = "Compare Redis and Memcached for caching. keep it brief."
    print_step("Step 2", f"Creating Task with prompt: '{PROMPT}'")
    
    try:
        resp = requests.post(f"{BASE_URL}/tasks", json={"prompt": PROMPT})
        if resp.status_code != 202:
            print(f"❌ Failed to create task: {resp.text}")
            return
            
        task_data = resp.json()
        task_id = task_data["task_id"]
        print(f"✅ Task Created! ID: {task_id}")
        print(f"   Initial Status: {task_data['status']}")
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return

    # 3. Poll for Approval
    print_step("Step 3", "Waiting for Agent Research (Awaiting Approval)...")
    
    status = "PENDING"
    for i in range(20):
        time.sleep(2)
        resp = requests.get(f"{BASE_URL}/tasks/{task_id}")
        data = resp.json()
        status = data["status"]
        print(f"   Poll {i+1}: Task Status = {status}")
        
        if status == "AWAITING_APPROVAL":
            print("✅ Task is ready for review!")
            # Show what the agents did so far
            logs = data.get("agent_logs", [])
            print(f"   Agent Logs so far: {len(logs)} entries")
            break
        elif status == "FAILED":
            print(f"❌ Task Failed: {data.get('result')}")
            return
            
    if status != "AWAITING_APPROVAL":
        print("❌ Timed out waiting for approval")
        return

    # 4. Approve Task
    print_step("Step 4", "Approving Task...")
    resp = requests.post(f"{BASE_URL}/tasks/{task_id}/approve", json={"approved": True, "feedback": "Looks good, proceed!"})
    if resp.status_code == 200:
        print("✅ Task Approved & Resumed")
    else:
        print(f"❌ Approval failed: {resp.text}")
        return

    # 5. Poll for Completion
    print_step("Step 5", "Waiting for Final Output...")
    
    for i in range(20):
        time.sleep(2)
        resp = requests.get(f"{BASE_URL}/tasks/{task_id}")
        data = resp.json()
        status = data["status"]
        print(f"   Poll {i+1}: Task Status = {status}")
        
        if status == "COMPLETED":
            print("✅ Task Completed Successfully!")
            print("-" * 50)
            print("📜 FINAL RESULT:")
            print("-" * 50)
            print(data.get("result", "No result found"))
            print("-" * 50)
            break
        elif status == "FAILED":
            print(f"❌ Task Failed: {data.get('result')}")
            return

if __name__ == "__main__":
    main()
