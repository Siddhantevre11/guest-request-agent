from app.bookings import BookingLookup
from app.main import create_app
from app.models import IntentResult
from fastapi.testclient import TestClient
from tests.doubles import FakeLLMClient


def test_guest_with_multiple_bookings_resolves_the_right_one_per_conversation():
    lookup = BookingLookup(failure_rate=0.0)
    # No date in proposed_change -- the date is always resolved from each
    # conversation's own booking, never proposed by the LLM. Both BK-4001 and
    # BK-4002's checkouts are available in the calendar fixture, so this test
    # is purely about identity resolution, not availability.
    proposed_change = {"new_checkout_time": "13:00"}
    llm = FakeLLMClient(
        intents=[IntentResult(type="booking_change", confidence=0.9, query="check out late", proposed_change=proposed_change)],
        draft_template="Sure thing! {{fact:0}}",
    )
    client = TestClient(create_app(llm, booking_lookup=lookup))

    client.post(
        "/message",
        json={"guest_id": "guest-4", "conversation_id": "conv-4a", "message": "can I check out late?"},
    )
    client.post(
        "/message",
        json={"guest_id": "guest-4", "conversation_id": "conv-4b", "message": "can I check out late?"},
    )

    approvals = client.get("/host/approvals").json()
    booking_ids = {a["booking_id"] for a in approvals}
    assert booking_ids == {"BK-4001", "BK-4002"}
