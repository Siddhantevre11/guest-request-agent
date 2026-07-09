from app.main import create_app
from app.models import IntentResult
from fastapi.testclient import TestClient
from tests.doubles import FakeLLMClient


def test_low_confidence_property_question_clarifies_once_without_escalating():
    llm = FakeLLMClient(
        intents=[IntentResult(type="property_question", confidence=0.2, query="towels")],
        draft_template="{{fact:0}}",
    )
    client = TestClient(create_app(llm))

    response = client.post(
        "/message",
        json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "towels?"},
    )

    assert "?" in response.json()["reply"]  # a clarifying question, not an answer
    assert client.get("/host/escalations").json() == []


def test_still_ambiguous_after_clarify_round_trip_escalates():
    llm = FakeLLMClient(
        intents=[IntentResult(type="property_question", confidence=0.2, query="towels")],
        draft_template="{{fact:0}}",
    )
    client = TestClient(create_app(llm))

    # first turn: clarify
    client.post("/message", json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "towels?"})
    # second turn: still ambiguous on the same topic -> escalate rather than clarify again
    response = client.post(
        "/message",
        json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "towels? (still unclear)"},
    )

    reply = response.json()["reply"]
    assert "flagged this for your host" in reply
    escalations = client.get("/host/escalations").json()
    assert len(escalations) == 1
    assert escalations[0]["guest_id"] == "guest-1"


def test_low_confidence_booking_change_escalates_immediately_no_clarify():
    llm = FakeLLMClient(
        intents=[IntentResult(type="booking_change", confidence=0.3, query="move my dates")],
        draft_template="{{fact:0}}",
    )
    client = TestClient(create_app(llm))

    response = client.post(
        "/message",
        json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "can you move my dates?"},
    )

    reply = response.json()["reply"]
    assert "flagged this for your host" in reply
    escalations = client.get("/host/escalations").json()
    assert len(escalations) == 1
    assert "confidence" in escalations[0]["reason"].lower()
