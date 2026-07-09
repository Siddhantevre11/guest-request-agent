from app.bookings import BookingLookup
from app.main import create_app
from app.models import IntentResult
from fastapi.testclient import TestClient
from tests.doubles import FakeLLMClient

UPSELL_INTENT = IntentResult(type="upsell", confidence=0.9, query="gap night")


def create_test_client(llm):
    # failure_rate=0.0: these tests aren't exercising retry, so the lookup
    # must be deterministic rather than intermittently flaky.
    return TestClient(create_app(llm, booking_lookup=BookingLookup(failure_rate=0.0)))


def test_real_gap_offered_when_not_previously_offered_and_no_complaint():
    llm = FakeLLMClient(intents=[UPSELL_INTENT], draft_template="{{fact:0}}")
    client = create_test_client(llm)

    response = client.post(
        "/message",
        json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "just checking in soon!"},
    )

    reply = response.json()["reply"]
    assert "2026-07-31" in reply
    assert "120" in reply


def test_no_gap_produces_no_offer():
    # guest-2/conv-2a's booking checks in 2026-09-01 -> gap date 2026-08-31,
    # not marked available in the calendar fixture.
    llm = FakeLLMClient(intents=[UPSELL_INTENT], draft_template="{{fact:0}}")
    client = create_test_client(llm)

    response = client.post(
        "/message",
        json={"guest_id": "guest-2", "conversation_id": "conv-2a", "message": "hi!"},
    )

    assert response.json()["reply"].strip() == ""


def test_already_offered_upsell_is_not_repeated():
    llm = FakeLLMClient(intents=[[UPSELL_INTENT], [UPSELL_INTENT]], draft_template="{{fact:0}}")
    client = create_test_client(llm)

    first = client.post(
        "/message", json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "hi!"}
    ).json()["reply"]
    second = client.post(
        "/message", json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "hi again!"}
    ).json()["reply"]

    assert "2026-07-31" in first
    assert second.strip() == ""


def test_complaint_in_message_suppresses_upsell():
    llm = FakeLLMClient(
        intents=[
            UPSELL_INTENT,
            IntentResult(type="property_question", confidence=0.9, query="ac broken", sentiment="negative"),
        ],
        draft_template="{{fact:0}}",
    )
    client = create_test_client(llm)

    response = client.post(
        "/message",
        json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "the AC is broken!"},
    )

    reply = response.json()["reply"]
    assert "2026-07-31" not in reply
