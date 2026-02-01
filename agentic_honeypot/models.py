from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class Message(BaseModel):
    sender: str  # "scammer" or "user"
    text: str
    timestamp: str

class IncomingMessage(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: List[Message] = []
    metadata: Optional[Dict[str, str]] = None

class AgentResponse(BaseModel):
    status: str = "success"
    reply: str

class IntelligenceData(BaseModel):
    bankAccounts: List[str] = []
    upiIds: List[str] = []
    phishingLinks: List[str] = []
    phoneNumbers: List[str] = []
    suspiciousKeywords: List[str] = []

class CallbackPayload(BaseModel):
    sessionId: str
    scamDetected: bool
    totalMessagesExchanged: int
    extractedIntelligence: IntelligenceData
    agentNotes: str
