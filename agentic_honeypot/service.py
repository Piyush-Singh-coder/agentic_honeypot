import requests
import json
from typing import Dict, List
from .models import IncomingMessage, AgentResponse, Message, CallbackPayload, IntelligenceData
from .agent import HoneyPotAgent

# In-memory session storage
# SessionID -> Data dict
sessions: Dict[str, Dict] = {}

agent_brain = HoneyPotAgent()
CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
MAX_TURNS_BEFORE_CALLBACK = 6 # Heuristic: Report after some exchanges

def process_message(data: IncomingMessage) -> AgentResponse:
    session_id = data.sessionId
    
    # 1. Initialize or Retrieve Session
    if session_id not in sessions:
        # New session
        is_scam = agent_brain.detect_scam(data.message.text)
        sessions[session_id] = {
            "history": [],
            "scamDetected": is_scam,
            "messageCount": 0,
            "callbackSent": False
        }
        # If passed history is empty, start fresh. If passed history exists (e.g. restart), trust it?
        # The prompt says 6.1 First Message has empty history.
    else:
        # Existing session
        # If for some reason we missed the start, we stick to previous detection or re-evaluate?
        # We'll just trust established state.
        pass

    session = sessions[session_id]
    
    # Update local history with the incoming history if provided, or just append the new message
    # The API sends `conversationHistory`. We should probably use that as the source of truth
    # OR maintain our own. The prompt implies we receive the history.
    # Let's rely on the incoming `conversationHistory` + the new `message`.
    
    current_history = list(data.conversationHistory)  # Copy to avoid mutation
    current_history.append(data.message)
    
    # Update our session count
    session["messageCount"] = len(current_history)

    # 2. Logic
    if not session["scamDetected"]:
        # double check if it was not detected initially but now assumes it is?
        # For this PoC, let's assume detection happens at start. 
        # But maybe we check every time if not yet detected?
        is_scam = agent_brain.detect_scam(data.message.text)
        if is_scam:
            session["scamDetected"] = True

    if session["scamDetected"]:
        # Generate Agent Reply
        reply_text = agent_brain.generate_reply(current_history)
        
        # Add our reply to history (conceptually, for the NEXT turn)
        # But we just return the reply here.
        
        # Check if we should send callback
        # We send callback if we have exchanged enough messages.
        # totalMessagesExchanged includes the one we just received + our reply (implied)
        if session["messageCount"] >= MAX_TURNS_BEFORE_CALLBACK and not session["callbackSent"]:
            # Extract Intelligence
            # We include our new reply in the analysis? Maybe.
            full_history = current_history + [Message(sender="user", text=reply_text, timestamp="now")]
            intel = agent_brain.extract_intelligence(full_history)
            
            # Send Callback
            payload = CallbackPayload(
                sessionId=session_id,
                scamDetected=True,
                totalMessagesExchanged=len(full_history),
                extractedIntelligence=intel,
                agentNotes="Scam detected and engaged. Intelligence extracted."
            )
            print("\n==============================================")
            print("🔍 EXTRACTED INTELLIGENCE (READY TO SEND):")
            print(json.dumps(payload.model_dump(), indent=2))
            print("==============================================\n")

            try:
                # Fire and forget? Or wait? Pydantic model to dict
                requests.post(CALLBACK_URL, json=payload.model_dump(), timeout=5)
                # We interpret strict "Mandatory" as "Try to send".
            except Exception as e:
                print(f"Failed to send callback: {e}")
            
            # Mark callback as sent
            session["callbackSent"] = True

        return AgentResponse(status="success", reply=reply_text)
    else:
        # Not a scam, return generic or empty?
        # The prompt implies we engage scammers.
        return AgentResponse(status="success", reply="Thank you for your message. How can I help you today?")
