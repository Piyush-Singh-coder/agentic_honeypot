import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict
from .models import Message, IntelligenceData

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class HoneyPotAgent:
    def __init__(self):
        self.system_prompt = """You are Ramu Kaka, a 38-year-old construction laborer from a small village near Patna, Bihar.
        You work on daily wages and recently got a new smartphone from your son who works in the city.
        You don't understand English well and prefer speaking in Hinglish (Hindi-English mix).
        You are very trusting of anyone who sounds official or uses English words.

        Try to make the scammer reveal as much information as possible. Make him/her reveal its phone number, bank account number, UPI ID, phishing links, etc.
        Example: Me apko paise bej deta hu aap kuch kar dijiye na. Aapka account number kya hai?
        Me apka bej dunga. Aapka UPI ID kya hai?
        
        IMPORTANT RULES:
        - NEVER reveal that you suspect a scam. Act completely naive and trusting.
        - Match the scammer's language. If they use Hinglish, reply in Hinglish.
        - If they speak in English, reply in simple Hinglish like: "Haan sahab, samajh nahi aaya, thoda Hindi mein batao na"
        - Express fear and worry about losing money. You don't have much savings.
        - Ask clarifying questions: "Kaunsa bank?", "Account number kya hai?", "UPI ID kya hota hai?"
        - If they ask for money, seem willing but confused: "Kitna paisa bhejoon? Kahan bhejoon?"
        - Keep responses short (1-2 sentences) in simple Hinglish.
        """

    def detect_scam(self, message: str) -> bool:
        """
        Analyzes the initial message to determine if it's a scam.
        """
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a scam detection expert. Analyze the following message. If it looks like a scam (phishing, financial fraud, urgency, suspicious links), reply with TRUE. Otherwise FALSE. Reply ONLY with the boolean."},
                    {"role": "user", "content": message}
                ],
                temperature=0.0
            )
            result = response.choices[0].message.content.strip().upper()
            return "TRUE" in result
        except Exception as e:
            print(f"Error in scam detection: {e}")
            # Fail safe: treat as potential scam if unsure? Or false to be safe. 
            # Given the context, we should probably log and return False if API fails.
            return False

    def generate_reply(self, history: List[Message]) -> str:
        """
        Generates a reply based on conversation history.
        """
        messages = [{"role": "system", "content": self.system_prompt}]
        for msg in history:
            role = "assistant" if msg.sender == "user" else "user" # Our agent acts as 'user' in the chat, but to the LLM it is the assistant role? 
            # Wait, the history from the API has 'sender': 'scammer' and 'sender': 'user' (agent).
            # So 'scammer' -> 'user' (for LLM), 'user' (agent) -> 'assistant' (for LLM).
            
            check_sender = "user" if msg.sender == "scammer" else "assistant"
            messages.append({"role": check_sender, "content": msg.text})

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.8
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating reply: {e}")
            return "I am a bit confused, could you explain that again?"

    def extract_intelligence(self, history: List[Message]) -> IntelligenceData:
        """
        Extracts structured intelligence from the conversation.
        """
        # Combine all scammer messages
        scammer_text = "\n".join([msg.text for msg in history if msg.sender == "scammer"])
        
        prompt = f"""
        Analyze the following text sent by a suspected scammer.
        Extract the following fields in JSON format:
        - bankAccounts: list of strings (account numbers, IBANs)
        - upiIds: list of strings (e.g. name@upi)
        - phishingLinks: list of strings (URLs)
        - phoneNumbers: list of strings
        - suspiciousKeywords: list of strings (urgency words, threats, etc.)
        
        Text:
        {scammer_text}
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an intelligence analyst. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            content = response.choices[0].message.content
            data = json.loads(content)
            return IntelligenceData(**data)
        except Exception as e:
            print(f"Error extracting intelligence: {e}")
            return IntelligenceData()
