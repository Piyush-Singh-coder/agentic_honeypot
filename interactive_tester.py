import requests
import json
import time

def run_tester():
    print("--- Honeypot Endpoint Tester ---")
    print("This tool verifies your Honeypot API deployment.")
    
    # 1. Ask for URL
    default_url = "http://127.0.0.1:8000/analyze"
    url = input(f"Enter Honeypot Endpoint URL [default: {default_url}]: ").strip()
    if not url:
        url = default_url

    # 2. Ask for API Key
    api_key = input("Enter API Key (x-api-key): ").strip()
    if not api_key:
        print("Error: API Key is required!")
        return

    print(f"\nTesting Endpoint: {url}")
    print(f"Using Key: {api_key[:3]}...{api_key[-3:] if len(api_key)>6 else ''}")
    print("Sending Request...")

    # Payload
    payload = {
        "sessionId": f"valid-session-{int(time.time())}",
        "message": {
            "sender": "scammer",
            "text": "Your account is blocked. Visit http://evil.com",
            "timestamp": "2026-02-01T12:00:00Z"
        },
        "conversationHistory": []
    }
    
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Endpoint is reachable and authenticated.")
            print("Response Body:")
            print(json.dumps(response.json(), indent=2))
        elif response.status_code == 403:
            print("❌ FAILED: Authentication failed (403 Forbidden). Check your API Key.")
        elif response.status_code == 404:
            print("❌ FAILED: Endpoint not found (404). Check your URL.")
        elif response.status_code == 405:
            print("❌ FAILED: Method Not Allowed (405). Ensure you are using POST.")
        else:
            print(f"⚠️  WARNING: Unexpected status code {response.status_code}")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("❌ FAILED: Could not connect to server. Is it running?")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    run_tester()
