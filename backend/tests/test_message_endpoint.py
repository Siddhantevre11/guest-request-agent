from fastapi.testclient import TestClient

from app.main import create_app
from app.models import IntentResult
from tests.doubles import FakeLLMClient


def test_property_question_answered_from_notes():
    llm = FakeLLMClient(
        intents=[IntentResult(type="property_question", confidence=0.95, query="what's the wifi password?")],
        draft_template="Sure thing! {{fact:0}}",
    )
    client = TestClient(create_app(llm))

    response = client.post(
        "/message",
        json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "what's the wifi password?"},
    )

    assert response.status_code == 200
    assert "SunnyDays2024!" in response.json()["reply"]
