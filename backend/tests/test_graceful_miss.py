from app.main import create_app
from app.models import IntentResult
from fastapi.testclient import TestClient
from tests.doubles import FakeLLMClient


def test_uncovered_property_question_gets_graceful_miss_not_escalation():
    llm = FakeLLMClient(
        intents=[IntentResult(type="property_question", confidence=0.9, query="is there a hair dryer?")],
        draft_template="{{fact:0}}",
    )
    client = TestClient(create_app(llm))

    response = client.post(
        "/message",
        json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "is there a hair dryer?"},
    )

    reply = response.json()["reply"]
    # truthful negative
    assert "don't have specific info" in reply
    # grounded alternatives -- real topics from the notes store, not invented
    assert "wifi" in reply and "checkin" in reply and "parking" in reply
    # never escalated for a mere FAQ miss (ADR-0010)
    assert "host" not in reply.lower()
