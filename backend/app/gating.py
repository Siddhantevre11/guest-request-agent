from typing import List, Tuple

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

# Fixed status line per intent type for held-back (below-threshold) intents.
# Deterministic and never invented — a real queue/escalation lands in a later
# slice; for now this proves independent per-intent handling within one reply.
HELD_BACK_MESSAGES: dict[str, str] = {
    "property_question": "I'll double check that and get back to you shortly.",
    "booking_change": "I'll check with the host about your requested change and get back to you shortly.",
    "upsell": "I'll check on that offer and get back to you shortly.",
    "affirmation": "Let me confirm what you're referring to before I proceed.",
    "other": "I'll look into that and get back to you shortly.",
}


# Intent types whose handling requires a resolved Booking.
BOOKING_DEPENDENT_TYPES = {"booking_change", "upsell"}

# Fixed status line when the booking lookup fails after the retry budget is
# exhausted -- only booking-dependent intents are affected; independent
# intents (e.g. answered from notes) still resolve in the same reply (ADR-0003).
BOOKING_FAILURE_MESSAGE = (
    "I'm having trouble pulling up your reservation right now — I've flagged this for your host to confirm."
)


def passes_threshold(intent: IntentResult) -> bool:
    return intent.confidence >= THRESHOLDS.get(intent.type, 0.5)


def partition_intents(intents: List[IntentResult]) -> Tuple[List[IntentResult], List[IntentResult]]:
    """Split intents into those that clear their risk-tiered threshold and
    those held back — independently, so one ambiguous intent never blocks
    a clear one in the same message (ADR-0001)."""
    proceeding = [i for i in intents if passes_threshold(i)]
    held_back = [i for i in intents if not passes_threshold(i)]
    return proceeding, held_back
