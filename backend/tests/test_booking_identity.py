from app.bookings import BookingLookup
from app.main import create_app
from app.models import IntentResult
from fastapi.testclient import TestClient
from tests.doubles import FakeLLMClient


def test_guest_with_multiple_bookings_resolves_the_right_one_per_conversation():
    lookup = BookingLookup(failure_rate=0.0)
    # date is available in the calendar fixture regardless of the booking's
    # own checkout date -- this test is about identity resolution, not
    # availability, so it uses a date already known to clear check_availability.
    proposed_change = {"date": "2026-08-05", "new_checkout_time": "13:00"}
    llm = FakeLLMClient(
        intents=[IntentResult(type="booking_change", confidence=0.9, query="check out late", proposed_change=proposed_change)],
        draft_template="Sure thing! {{fact:0}}",
    )
    client = TestClient(create_app(llm, booking_lookup=lookup))

    client.post(
        "/message",
        json={"guest_id": "guest-2", "conversation_id": "conv-2a", "message": "can I check out late?"},
    )
    client.post(
        "/message",
        json={"guest_id": "guest-2", "conversation_id": "conv-2b", "message": "can I check out late?"},
    )

    approvals = client.get("/host/approvals").json()
    booking_ids = {a["booking_id"] for a in approvals}
    assert booking_ids == {"BK-2001", "BK-2002"}
