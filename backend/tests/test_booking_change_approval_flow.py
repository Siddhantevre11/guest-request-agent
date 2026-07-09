from app.bookings import BookingLookup
from app.main import create_app
from app.models import IntentResult
from fastapi.testclient import TestClient
from tests.doubles import FakeLLMClient


def create_test_client(llm):
    # failure_rate=0.0: these tests aren't exercising retry (see
    # test_booking_retry_isolation.py for that), so the lookup must be
    # deterministic here rather than intermittently flaky.
    return TestClient(create_app(llm, booking_lookup=BookingLookup(failure_rate=0.0)))


def test_available_booking_change_creates_pending_approval_and_tells_guest_checking_with_host():
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
    client = create_test_client(llm)

    response = client.post(
        "/message",
        json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "can I check out late?"},
    )
    reply = response.json()["reply"]

    # honest, fast, non-committal reply -- no mutation happened yet
    assert "checking with your host" in reply.lower()

    approvals = client.get("/host/approvals").json()
    assert len(approvals) == 1
    assert approvals[0]["booking_id"] == "BK-1001"
    assert approvals[0]["change"] == {"date": "2026-08-05", "new_checkout_time": "13:00", "fee": 25}
    assert approvals[0]["status"] == "pending"


def test_unavailable_booking_change_declines_without_creating_an_approval():
    llm = FakeLLMClient(
        intents=[
            IntentResult(
                type="booking_change",
                confidence=0.9,
                query="check out late",
                proposed_change={"new_checkout_time": "13:00"},
            )
        ],
        draft_template="{{fact:0}}",
    )
    client = create_test_client(llm)

    response = client.post(
        "/message",
        json={"guest_id": "guest-2", "conversation_id": "conv-2a", "message": "can I check out late?"},
    )
    reply = response.json()["reply"]

    assert "isn't available" in reply.lower()
    assert client.get("/host/approvals").json() == []


def test_host_approval_executes_prespecified_diff_and_notifies_guest():
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
    client = create_test_client(llm)
    client.post(
        "/message",
        json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "can I check out late?"},
    )
    approval_id = client.get("/host/approvals").json()[0]["id"]

    response = client.post("/host/decision", json={"approval_id": approval_id, "decision": "approve"})
    body = response.json()

    assert body["status"] == "approved"
    # mutation matches the pre-specified diff exactly -- no LLM re-interpretation
    assert body["booking"]["checkout_time"] == "13:00"
    assert body["booking"]["fee"] == 25
    # guest notification carries the consequential facts via the executed change
    assert "13:00" in body["guest_notification"]
    assert "25" in body["guest_notification"]
    # approval is resolved, no longer pending
    assert client.get("/host/approvals").json() == []


def test_host_denial_does_not_mutate_booking():
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
    client = create_test_client(llm)
    client.post(
        "/message",
        json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "can I check out late?"},
    )
    approval_id = client.get("/host/approvals").json()[0]["id"]

    response = client.post("/host/decision", json={"approval_id": approval_id, "decision": "deny"})
    body = response.json()

    assert body["status"] == "denied"
    assert body["booking"] is None
    assert "couldn't accommodate" in body["guest_notification"].lower()
