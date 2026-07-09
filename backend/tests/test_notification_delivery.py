from app.bookings import BookingLookup
from app.main import create_app
from app.models import IntentResult
from fastapi.testclient import TestClient
from tests.doubles import FakeLLMClient


def make_client():
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
    return TestClient(create_app(llm, booking_lookup=BookingLookup(failure_rate=0.0)))


def test_host_approval_delivers_a_notification_the_guest_can_fetch_once():
    client = make_client()
    client.post(
        "/message",
        json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "can I check out late?"},
    )
    approval_id = client.get("/host/approvals").json()[0]["id"]
    client.post("/host/decision", json={"approval_id": approval_id, "decision": "approve"})

    notifications = client.get(
        "/notifications", params={"guest_id": "guest-1", "conversation_id": "conv-1"}
    ).json()

    assert len(notifications) == 1
    assert "13:00" in notifications[0]["text"]

    # delivered once -- consumed on read, not re-delivered on a second poll
    again = client.get("/notifications", params={"guest_id": "guest-1", "conversation_id": "conv-1"}).json()
    assert again == []


def test_notifications_are_isolated_per_conversation():
    client = make_client()
    client.post(
        "/message",
        json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "can I check out late?"},
    )
    approval_id = client.get("/host/approvals").json()[0]["id"]
    client.post("/host/decision", json={"approval_id": approval_id, "decision": "approve"})

    other_guest_notifications = client.get(
        "/notifications", params={"guest_id": "guest-2", "conversation_id": "conv-2a"}
    ).json()

    assert other_guest_notifications == []
