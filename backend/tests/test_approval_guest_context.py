from app.bookings import BookingLookup
from app.main import create_app
from app.models import IntentResult
from fastapi.testclient import TestClient
from tests.doubles import FakeLLMClient


def test_approval_carries_the_guests_actual_message_for_host_context():
    llm = FakeLLMClient(
        intents=[
            IntentResult(
                type="booking_change",
                confidence=0.9,
                query="check out late",
                proposed_change={"new_checkout_time": "13:00", "fee": 25},
            )
        ],
        draft_template="{{fact:0}}",
    )
    client = TestClient(create_app(llm, booking_lookup=BookingLookup(failure_rate=0.0)))

    guest_message = "can I check out at 1pm instead of 11am on my last day?"
    client.post(
        "/message",
        json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": guest_message},
    )

    approvals = client.get("/host/approvals").json()
    assert approvals[0]["guest_message"] == guest_message
