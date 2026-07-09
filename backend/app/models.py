from typing import Literal, Optional

from pydantic import BaseModel

IntentType = Literal["property_question", "booking_change", "upsell", "affirmation", "other"]
Sentiment = Literal["neutral", "positive", "negative"]


class IntentResult(BaseModel):
    type: IntentType
    confidence: float
    sentiment: Sentiment = "neutral"
    query: Optional[str] = None
    proposed_change: Optional[dict] = None


class MessageRequest(BaseModel):
    guest_id: str
    conversation_id: str
    message: str


class MessageResponse(BaseModel):
    reply: str
