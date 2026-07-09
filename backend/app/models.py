from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

IntentType = Literal["property_question", "booking_change", "upsell", "affirmation", "other"]
Sentiment = Literal["neutral", "positive", "negative"]


class ProposedChange(BaseModel):
    """Fields the LLM may propose for a booking_change intent -- deterministic
    code (check_availability, create_approval) still decides what happens with
    them. `extra="forbid"` keeps the JSON schema OpenAI-strict-mode compatible
    (every object node must set additionalProperties: false).

    No `date` field: classify() is never given the guest's actual booking, so
    any date it produced would be a guess. The date is always resolved
    deterministically from the resolved Booking, never proposed by the LLM."""

    model_config = ConfigDict(extra="forbid")

    new_checkout_time: Optional[str] = None
    fee: Optional[float] = None


class IntentResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: IntentType
    confidence: float
    sentiment: Sentiment = "neutral"
    query: Optional[str] = None
    proposed_change: Optional[ProposedChange] = None


class MessageRequest(BaseModel):
    guest_id: str
    conversation_id: str
    message: str


class MessageResponse(BaseModel):
    reply: str
