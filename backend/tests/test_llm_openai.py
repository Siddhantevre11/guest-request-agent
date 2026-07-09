from types import SimpleNamespace

from app.models import IntentResult


class FakeStructuredModel:
    def __init__(self, result):
        self._result = result
        self.invoked_with = None

    def invoke(self, prompt):
        self.invoked_with = prompt
        return self._result


class FakeChatModel:
    """Stub for the LangChain chat-model boundary: no real API call."""

    def __init__(self, structured_result=None, content=None):
        self._structured_result = structured_result
        self._content = content
        self.invoked_with = None
        self.structured_schema = None
        self.last_structured_model = None

    def with_structured_output(self, schema):
        self.structured_schema = schema
        self.last_structured_model = FakeStructuredModel(self._structured_result)
        return self.last_structured_model

    def invoke(self, prompt):
        self.invoked_with = prompt
        return SimpleNamespace(content=self._content)


def test_classify_returns_intents_from_the_structured_model_and_includes_message_and_memory_in_the_prompt():
    from app.llm_openai import ClassifyOutput, OpenAILLMClient

    intents = [IntentResult(type="property_question", confidence=0.9, query="wifi password")]
    fake_model = FakeChatModel(structured_result=ClassifyOutput(intents=intents))
    client = OpenAILLMClient(model=fake_model)

    result = client.classify("what's the wifi password?", {"answered_topics": ["checkin"]})

    assert result == intents
    assert fake_model.structured_schema is ClassifyOutput
    assert "what's the wifi password?" in fake_model.last_structured_model.invoked_with
    assert "checkin" in fake_model.last_structured_model.invoked_with


def test_draft_returns_the_models_text_and_includes_facts_in_the_prompt():
    from app.llm_openai import OpenAILLMClient

    fake_model = FakeChatModel(content="Sure thing! {{fact:0}}")
    client = OpenAILLMClient(model=fake_model)

    result = client.draft(["The wifi password is SunnyDays2024!."])

    assert result == "Sure thing! {{fact:0}}"
    assert "The wifi password is SunnyDays2024!." in fake_model.invoked_with
