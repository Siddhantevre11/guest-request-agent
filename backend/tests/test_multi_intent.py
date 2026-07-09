from fastapi.testclient import TestClient

from app.main import create_app
from app.models import IntentResult
from tests.doubles import FakeLLMClient


def test_clear_intent_proceeds_while_ambiguous_intent_is_held_back():
    # property_question threshold is low (~0.4) -> 0.9 clears it.
    # booking_change threshold is high (~0.7) -> 0.3 does not clear it.
    llm = FakeLLMClient(
        intents=[
            IntentResult(type="property_question", confidence=0.9, query="wifi password"),
            IntentResult(type="booking_change", confidence=0.3, query="check out late"),
        ],
        draft_template="Sure thing! {{fact:0}}",
    )
    client = TestClient(create_app(llm))

    response = client.post(
        "/message",
        json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "wifi password + check out late?"},
    )

    assert response.status_code == 200
    reply = response.json()["reply"]
    # the clear intent's fact is answered, verbatim from the notes store
    assert "SunnyDays2024!" in reply
    # the ambiguous intent gets the fixed held-back status line, not an invented answer
    assert "I'll check with the host about your requested change and get back to you shortly." in reply


def test_both_intents_clear_produces_no_held_back_text():
    llm = FakeLLMClient(
        intents=[
            IntentResult(type="property_question", confidence=0.9, query="wifi password"),
        ],
        draft_template="Sure thing! {{fact:0}}",
    )
    client = TestClient(create_app(llm))

    response = client.post(
        "/message",
        json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "wifi password?"},
    )

    reply = response.json()["reply"]
    assert "SunnyDays2024!" in reply
    assert "check with the host" not in reply
