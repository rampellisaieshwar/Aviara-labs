import os
import json
import logging
from typing import Dict, Any, Tuple
from groq import Groq

from app.config import settings

logger = logging.getLogger(__name__)

# List of allowed intents
ALLOWED_INTENTS = {"sales_enquiry", "support", "job_application", "partnership", "spam", "other"}

CLASSIFICATION_SYSTEM_PROMPT = """You are a highly accurate AI lead classifier. Your job is to classify the intent of a message sent by a potential customer or user.
You must analyze the incoming message and categorize it into exactly ONE of the following intents:
- 'sales_enquiry': Lead is interested in buying, pricing, services, booking a demo, or working together.
- 'support': User is asking for help with an existing account, tool issues, bug reports, or general customer support.
- 'job_application': Sender is applying for a job, sending a resume, or asking about open positions.
- 'partnership': Sender is proposing a business partnership, marketing collaboration, or vendor pitch.
- 'spam': Unsolicited ads, promotional blasts, phishing, gibberish, or completely irrelevant noise.
- 'other': Valid messages that do not fit the above (e.g. general feedback, friendly greetings with no specific request).

Handle noisy or ambiguous inputs:
- If the message is completely ambiguous, short, or gibberish (e.g. "hi", "asdf", "test"), classify it as 'other' or 'spam' with a lower confidence.
- Be objective and assess the text message details carefully.

You MUST respond with a valid JSON object only. Do not include markdown formatting (like ```json ... ```) or conversational fluff. The JSON structure must match this:
{
  "intent": "string (one of the listed intents)",
  "confidence": float (between 0.0 and 1.0 representing your confidence in this classification)
}"""

class GroqClassificationService:
    @classmethod
    def _fallback_classify(cls, message: str) -> Dict[str, Any]:
        """
        A rule-based heuristic classifier used if the Groq API key is not configured,
        or if the API call fails. Ensures system runs end-to-end.
        """
        logger.warning("Using rule-based fallback classifier for lead intent classification")
        text = message.lower().strip()
        
        # Simple keyword checks
        if not text or len(text) < 4:
            return {"intent": "other", "confidence": 0.50}
            
        sales_keywords = ["buy", "price", "pricing", "cost", "demo", "quote", "interested in your services", "hire", "consultation", "services", "sales"]
        support_keywords = ["help", "support", "error", "bug", "broken", "issue", "login", "password", "reset", "failed", "ticket"]
        job_keywords = ["job", "career", "resume", "cv", "hiring", "apply", "position", "internship"]
        partnership_keywords = ["partner", "partnership", "collab", "collaboration", "integrate", "vendor", "synergy"]
        spam_keywords = ["seo", "backlink", "crypto", "bitcoin", "rich", "viagra", "make money", "winner", "congratulations"]

        if any(kw in text for kw in spam_keywords):
            return {"intent": "spam", "confidence": 0.90}
        if any(kw in text for kw in sales_keywords):
            return {"intent": "sales_enquiry", "confidence": 0.85}
        if any(kw in text for kw in support_keywords):
            return {"intent": "support", "confidence": 0.88}
        if any(kw in text for kw in job_keywords):
            return {"intent": "job_application", "confidence": 0.90}
        if any(kw in text for kw in partnership_keywords):
            return {"intent": "partnership", "confidence": 0.82}
            
        return {"intent": "other", "confidence": 0.60}

    @classmethod
    async def classify_message(cls, message: str) -> Dict[str, Any]:
        """
        Classifies lead message using Groq API and LLM.
        Falls back to rule-based classification on failure or missing API key.
        """
        # Validate input message
        if not message or not message.strip():
            return {"intent": "other", "confidence": 0.0}

        # Check if the API key is set properly
        api_key = settings.GROQ_API_KEY
        if not api_key or api_key.startswith("gsk_mock") or "your_actual" in api_key:
            return cls._fallback_classify(message)

        try:
            # Initialize Groq client
            client = Groq(api_key=api_key)
            
            logger.info(f"Calling Groq API (Model: {settings.GROQ_MODEL}) to classify: '{message[:50]}...'")
            
            # Request classification from Groq LLM
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Message to classify: {message}"}
                ],
                model=settings.GROQ_MODEL,
                temperature=0.0,
                response_format={"type": "json_object"}  # Request JSON response format
            )
            
            # Parse response content
            response_content = chat_completion.choices[0].message.content
            logger.debug(f"Groq API raw response: {response_content}")
            
            data = json.loads(response_content)
            
            # Validate output keys & intent type
            intent = data.get("intent", "other").lower().strip()
            confidence = float(data.get("confidence", 0.50))
            
            if intent not in ALLOWED_INTENTS:
                intent = "other"
                
            return {
                "intent": intent,
                "confidence": min(max(confidence, 0.0), 1.0)
            }
            
        except Exception as e:
            logger.error(f"Groq API classification failed: {str(e)}. Falling back to rule-based classification.")
            return cls._fallback_classify(message)
