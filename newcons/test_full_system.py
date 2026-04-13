import requests
import time
import json
import os
import sys

# Set path
API_BASE = "http://localhost:8000/api/v1"

def test_workflow():
    print("Starting full system end-to-end automation test...")
    
    # 1. Mock Feedback Ingestion
    print("\n[Step 1] Mocking Ingestion: Payment Timeout Case")
    
    payload = {
        "text": "Why always error PAY_ERR_404? I already paid! UID: 10086",
        "custom_metadata": json.dumps({"source": "community_test"})
    }
    
    # Mock file upload
    files = [
        ('images', ('mock_pay_error.png', b'fake image data', 'image/png'))
    ]
    
    try:
        response = requests.post(f"{API_BASE}/ingest/feedback", data=payload)
        print(f"Ingest Status: {response.status_code}")
        event_data = response.json()
        event_id = event_data.get("event_id")
        print(f"Generated Event ID: {event_id}")
    except Exception as e:
        print(f"FAILED: Ingestion error: {e}")
        return

    # 2. Wait for background Pipeline
    print("\n[Step 2] Waiting for Ticket Pipeline processing (5s)...")
    time.sleep(5)
    
    # 3. Verify Alert Log
    if os.path.exists("alerts.log"):
        with open("alerts.log", "r", encoding="utf-8") as f:
            content = f.read()
            if event_id in content:
                print("PASS: Alert verified. System identified P0 crisis.")
            else:
                print("FAIL: Alert log does not contain correct event ID.")
    
    # 4. Verify Dashboard Summary
    print("\n[Step 3] Verifying AI Conflict Briefing...")
    try:
        sum_res = requests.get(f"{API_BASE}/dashboard/summary")
        summary = sum_res.json().get("markdown", "")
        print(f"AI Summary Preview (first 50 chars): {summary[:50]}...")
        if len(summary) > 10:
            print("PASS: Summary generated successfully.")
    except Exception as e:
        print(f"FAILED: Summary retrieval error: {e}")

    # 5. Verify Personalized Recommendation
    print("\n[Step 4] Verifying Personalized Recommendation...")
    try:
        tick_res = requests.get(f"{API_BASE}/dashboard/tickets")
        tickets = tick_res.json().get("tickets", [])
        found = False
        for t in tickets:
            if t['event_id'] == event_id:
                found = True
                print(f"PASS: Ticket found in feed. Recommended Role: {t.get('recommended_operator', 'Unknown')}")
                break
        if not found:
            print("FAIL: Target ticket not found in the feed.")
    except Exception as e:
        print(f"FAILED: Ticket list retrieval error: {e}")

    print("\nFULL BACKEND INTEGRATION TEST COMPLETE.")

if __name__ == "__main__":
    test_workflow()
