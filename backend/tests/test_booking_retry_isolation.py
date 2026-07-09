from app.bookings import BookingLookupError
from app.main import create_app
from app.models import IntentResult
from fastapi.testclient import TestClient
from tests.doubles import FakeLLMClient


class ScriptedBookingLookup:
    """Test double: replays a fixed sequence of outcomes, repeating the last."""

    def __init__(self, outcomes):
        self._outcomes = list(outcomes)
        self.call_count = 0

    def __call__(self, guest_id, conversation_id):
        self.call_count += 1
        outcome = self._outcomes.pop(0) if len(self._outcomes) > 1 else self._outcomes[0]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


BOOKING = {"booking_id": "BK-1001", "checkin": "2026-08-01", "checkout": "2026-08-05"}


def make_client(booking_lookup, intents):
    llm = FakeLLMClient(intents=intents, draft_template="Sure thing! {{fact:0}}")
    return TestClient(create_app(llm, booking_lookup=booking_lookup))


def test_booking_lookup_retried_and_succeeds_within_attempt_budget():
    lookup = ScriptedBookingLookup([BookingLookupError("transient"), BookingLookupError("transient"), BOOKING])
    client = make_client(
        lookup,
        intents=[IntentResult(type="booking_change", confidence=0.9, query="check out late")],
    )

    response = client.post(
        "/message",
        json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "can I check out late?"},
    )

    assert response.status_code == 200
    assert lookup.call_count == 3
    assert "BK-1001" in response.json()["reply"]


def test_booking_lookup_exhausted_escalates_only_booking_dependent_intent():
    lookup = ScriptedBookingLookup([BookingLookupError("down")] * 5)
    client = make_client(
        lookup,
        intents=[
            IntentResult(type="property_question", confidence=0.9, query="wifi password"),
            IntentResult(type="booking_change", confidence=0.9, query="check out late"),
        ],
    )

    response = client.post(
        "/message",
        json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "wifi password + check out late?"},
    )

    reply = response.json()["reply"]
    # independent FAQ intent still answers even though booking lookup failed
    assert "SunnyDays2024!" in reply
    # booking-dependent intent is flagged, not silently dropped or guessed
    assert "I'm having trouble pulling up your reservation right now" in reply
    # never more than 3 attempts (retry budget, not infinite retry)
    assert lookup.call_count == 3
