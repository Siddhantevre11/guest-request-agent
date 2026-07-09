from app.bookings import BookingLookup
from app.main import create_app
from app.models import IntentResult
from fastapi.testclient import TestClient
from tests.doubles import FakeLLMClient


def test_guest_with_multiple_bookings_resolves_the_right_one_per_conversation():
    lookup = BookingLookup(failure_rate=0.0)
    llm = FakeLLMClient(
        intents=[IntentResult(type="booking_change", confidence=0.9, query="check out late")],
        draft_template="Sure thing! {{fact:0}}",
    )
    client = TestClient(create_app(llm, booking_lookup=lookup))

    reply_a = client.post(
        "/message",
        json={"guest_id": "guest-2", "conversation_id": "conv-2a", "message": "can I check out late?"},
    ).json()["reply"]
    reply_b = client.post(
        "/message",
        json={"guest_id": "guest-2", "conversation_id": "conv-2b", "message": "can I check out late?"},
    ).json()["reply"]

    assert "BK-2001" in reply_a
    assert "BK-2002" not in reply_a
    assert "BK-2002" in reply_b
    assert "BK-2001" not in reply_b
