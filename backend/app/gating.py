from typing import List, Optional, Tuple

from .models import IntentResult

# Risk-tiered confidence thresholds (ADR-0001): low bar for low-stakes property
# questions, high bar for consequential booking-change/upsell intents. The LLM
# proposes the confidence number; this threshold check is what decides.
THRESHOLDS: dict[str, float] = {
    "property_question": 0.4,
    "booking_change": 0.7,
    "upsell": 0.7,
    "affirmation": 0.5,
    "other": 0.5,
}

# Intent types whose handling requires a resolved Booking. Affirmation needs
# it too: converting a "yes" into an Approval needs the booking_id.
BOOKING_DEPENDENT_TYPES = {"booking_change", "upsell", "affirmation"}

# Fixed status line when the booking lookup fails after the retry budget is
# exhausted -- only booking-dependent intents are affected; independent
# intents (e.g. answered from notes) still resolve in the same reply (ADR-0003).
BOOKING_FAILURE_MESSAGE = (
    "I'm having trouble pulling up your reservation right now — I've flagged this for your host to confirm."
)

# Booking-change status lines (ADR-0007): the agent proposes, the host
# commits -- so the guest reply is always non-committal on approval, and
# a factually unavailable change is declined immediately without bothering
# the host at all.
BOOKING_CHANGE_PENDING_MESSAGE = "I'm checking with your host on that — they'll confirm shortly."
BOOKING_CHANGE_UNAVAILABLE_MESSAGE = "Unfortunately that time isn't available for your stay."

# Clarify-vs-escalate (ADR-0001): property_question gets one clarify attempt
# before escalating; consequential types (booking_change, upsell, etc.) never
# self-clarify -- they escalate immediately, since a wrong guess there has
# real consequences.
CLARIFY_QUESTION = "Could you tell me a bit more about what you need?"
GUEST_ESCALATED_NOTE = "I've flagged this for your host to help with."

# Ambiguous affirmation (ADR-0011): two pending items + a bare "yes" ->
# clarify once before escalating, rather than guessing which one.
AMBIGUOUS_AFFIRMATION_QUESTION = "Just to confirm — which one are you saying yes to?"

ESCALATION_REASONS: dict[str, str] = {
    "booking_change": "Booking-change intent below confidence threshold — needs manual review.",
    "upsell": "Upsell intent below confidence threshold — needs manual review.",
    "property_question": "Guest's property question remained unclear after a follow-up — needs manual review.",
    "affirmation": "Ambiguous affirmation — needs manual review.",
    "other": "Low-confidence request — needs manual review.",
}


def process_held_back_intent(intent: IntentResult, memory: dict) -> Tuple[str, Optional[str]]:
    """Return (guest-facing note, escalation reason or None if only clarifying).

    property_question gets exactly one clarify attempt per topic, tracked in
    memory; a second miss on the same topic escalates instead of looping.
    """
    if intent.type == "property_question":
        attempted = memory.setdefault("clarify_attempted_topics", [])
        topic = intent.query or ""
        if topic in attempted:
            return GUEST_ESCALATED_NOTE, ESCALATION_REASONS["property_question"]
        attempted.append(topic)
        return CLARIFY_QUESTION, None

    return GUEST_ESCALATED_NOTE, ESCALATION_REASONS.get(intent.type, ESCALATION_REASONS["other"])


def passes_threshold(intent: IntentResult) -> bool:
    return intent.confidence >= THRESHOLDS.get(intent.type, 0.5)


def partition_intents(intents: List[IntentResult]) -> Tuple[List[IntentResult], List[IntentResult]]:
    """Split intents into those that clear their risk-tiered threshold and
    those held back — independently, so one ambiguous intent never blocks
    a clear one in the same message (ADR-0001)."""
    proceeding = [i for i in intents if passes_threshold(i)]
    held_back = [i for i in intents if not passes_threshold(i)]
    return proceeding, held_back
