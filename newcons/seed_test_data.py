import requests
import os

API_BASE = "http://localhost:8000"

def seed():
    # Create a small dummy text file
    with open("dummy_base.txt", "w") as f:
        f.write("Welcome to the Honkai Agent Platform. This is the base knowledge.\n")
        f.write("Payment issues should be handled by the Commercial Specialist.\n")
        f.write("Technical bugs should be handled by Tech Support.\n")
    
    files = {'file': open("dummy_base.txt", 'rb')}
    try:
        r = requests.post(f"{API_BASE}/upload_memory", files=files)
        print(f"Seed Status: {r.status_code}")
        print(f"Response: {r.json()}")
    except Exception as e:
        print(f"Seed Error: {e}")

if __name__ == "__main__":
    seed()
