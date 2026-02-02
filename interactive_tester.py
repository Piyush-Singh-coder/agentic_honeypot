import requests
import json
import re
from datetime import datetime

def extract_intelligence_locally(conversation_history):
    """
    Extract intelligence from conversation history locally.
    This mirrors what the server does with GPT, but uses regex for quick local analysis.
    """
    all_scammer_text = " ".join([
        msg["text"] for msg in conversation_history if msg["sender"] == "scammer"
    ])
    
    # Extract patterns
    phone_pattern = r'(?:\+91[\s-]?)?[6-9]\d{9}'
    upi_pattern = r'[a-zA-Z0-9._-]+@[a-zA-Z]+'
    bank_account_pattern = r'\d{9,18}'
    url_pattern = r'https?://[^\s]+'
    
    # Suspicious keywords
    suspicious_keywords = []
    keyword_list = ["urgent", "block", "verify", "suspend", "otp", "kyc", "immediately", 
                    "blocked", "closed", "update", "link", "click", "account", "bank",
                    "upi", "payment", "transfer", "send", "money", "paisa", "rupees"]
    
    for word in keyword_list:
        if word.lower() in all_scammer_text.lower():
            suspicious_keywords.append(word)
    
    return {
        "phoneNumbers": list(set(re.findall(phone_pattern, all_scammer_text))),
        "upiIds": list(set(re.findall(upi_pattern, all_scammer_text))),
        "bankAccounts": list(set(re.findall(bank_account_pattern, all_scammer_text))),
        "phishingLinks": list(set(re.findall(url_pattern, all_scammer_text))),
        "suspiciousKeywords": list(set(suspicious_keywords))
    }

def run_interactive_tester():
    print("\n" + "="*60)
    print("🕵️  AGENTIC HONEYPOT - INTERACTIVE TESTER")
    print("="*60)
    print("Commands: 'quit' to exit, 'reset' to new session, 'intel' to see collected data\n")
    
    # 1. Get endpoint and API key
    default_url = "http://127.0.0.1:8000/analyze"
    url = input(f"Enter API Endpoint URL [default: {default_url}]: ").strip()
    if not url:
        url = default_url
    
    # Auto-append /analyze if not present
    if not url.endswith("/analyze"):
        if url.endswith("/"):
            url = url + "analyze"
        else:
            url = url + "/analyze"
        print(f"📌 Auto-corrected URL to: {url}")
    
    api_key = input("Enter API Key (x-api-key): ").strip()
    if not api_key:
        print("❌ API Key is required!")
        return
    
    print(f"\n✅ Connected to: {url}")
    print(f"🔑 Using Key: {api_key[:3]}...{api_key[-3:]}")
    print("-"*60)
    
    # Session state
    session_id = f"test-session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    conversation_history = []
    
    print(f"\n📝 Session ID: {session_id}")
    print("💬 Type scam messages to test. Type 'intel' to see extracted data.\n")
    
    while True:
        user_input = input("🔴 SCAMMER: ").strip()
        
        if user_input.lower() == 'quit':
            print("\n👋 Exiting tester. Goodbye!")
            break
        
        if user_input.lower() == 'reset':
            session_id = f"test-session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            conversation_history = []
            print(f"\n🔄 Session reset! New Session ID: {session_id}\n")
            continue
        
        if user_input.lower() == 'intel':
            # Show collected intelligence
            intel = extract_intelligence_locally(conversation_history)
            print("\n" + "="*60)
            print("🔍 EXTRACTED INTELLIGENCE (from this session)")
            print("="*60)
            print(f"📱 Phone Numbers: {intel['phoneNumbers'] or 'None found'}")
            print(f"💳 UPI IDs: {intel['upiIds'] or 'None found'}")
            print(f"🏦 Bank Accounts: {intel['bankAccounts'] or 'None found'}")
            print(f"🔗 Phishing Links: {intel['phishingLinks'] or 'None found'}")
            print(f"⚠️  Suspicious Keywords: {intel['suspiciousKeywords'] or 'None found'}")
            print("="*60 + "\n")
            continue
        
        if not user_input:
            continue
        
        # Build payload
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": user_input,
                "timestamp": timestamp
            },
            "conversationHistory": conversation_history.copy(),
            "metadata": {
                "channel": "SMS",
                "language": "Hinglish",
                "locale": "IN"
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get("reply", "No reply")
                status = data.get("status", "unknown")
                
                print(f"🟢 RAMU KAKA: {reply}")
                print(f"   [Status: {status}]\n")
                
                # Update conversation history
                conversation_history.append({
                    "sender": "scammer",
                    "text": user_input,
                    "timestamp": timestamp
                })
                conversation_history.append({
                    "sender": "user",
                    "text": reply,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
                
            elif response.status_code == 403:
                print("❌ ERROR: Invalid API Key (403 Forbidden)\n")
            elif response.status_code == 404:
                print("❌ ERROR: Endpoint not found (404). Check your URL.\n")
            else:
                print(f"❌ ERROR: HTTP {response.status_code}: {response.text[:200]}\n")
                
        except requests.exceptions.Timeout:
            print("❌ ERROR: Request timed out. Server might be sleeping.\n")
        except requests.exceptions.ConnectionError:
            print("❌ ERROR: Could not connect. Is the server running?\n")
        except Exception as e:
            print(f"❌ ERROR: {e}\n")
    
    # Final Summary
    intel = extract_intelligence_locally(conversation_history)
    print("\n" + "="*60)
    print("📊 FINAL SESSION SUMMARY")
    print("="*60)
    print(f"Session ID: {session_id}")
    print(f"Total Messages: {len(conversation_history)}")
    print("\n🔍 COLLECTED INTELLIGENCE:")
    print(f"  📱 Phone Numbers: {intel['phoneNumbers'] or 'None'}")
    print(f"  💳 UPI IDs: {intel['upiIds'] or 'None'}")
    print(f"  🏦 Bank Accounts: {intel['bankAccounts'] or 'None'}")
    print(f"  🔗 Phishing Links: {intel['phishingLinks'] or 'None'}")
    print(f"  ⚠️  Keywords: {intel['suspiciousKeywords'] or 'None'}")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_interactive_tester()
