from app.main import create_app
from app.models import IntentResult
from fastapi.testclient import TestClient
from tests.doubles import FakeLLMClient

WIFI_INTENT = [IntentResult(type="property_question", confidence=0.9, query="wifi password")]


def test_memory_is_loaded_into_classify_and_updated_after_each_turn():
    llm = FakeLLMClient(intents=[WIFI_INTENT, WIFI_INTENT], draft_template="{{fact:0}}")
    client = TestClient(create_app(llm))

    client.post("/message", json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "wifi password?"})
    client.post(
        "/message", json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "wifi password again?"}
    )

    assert len(llm.classify_calls) == 2
    # first turn: classify sees empty memory (nothing resolved yet)
    assert llm.classify_calls[0][1]["answered_topics"] == []
    # second turn: classify sees memory reflecting what turn 1 resolved
    assert "wifi password" in llm.classify_calls[1][1]["answered_topics"]


def test_memory_is_isolated_per_conversation():
    llm = FakeLLMClient(intents=[WIFI_INTENT, WIFI_INTENT], draft_template="{{fact:0}}")
    client = TestClient(create_app(llm))

    client.post("/message", json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "wifi password?"})
    client.post("/message", json={"guest_id": "guest-2", "conversation_id": "conv-2a", "message": "wifi password?"})

    # a different guest/conversation never sees guest-1's resolved history
    assert llm.classify_calls[1][1]["answered_topics"] == []
