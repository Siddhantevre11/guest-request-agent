from typing import Any, List, Optional

from pydantic import BaseModel

from .llm import LLMClient
from .models import IntentResult

CLASSIFY_SYSTEM_PROMPT = (
    "You are the intent classifier for a short-term rental guest-messaging agent. "
    "Read the guest's message and the conversation memory (what's already been "
    "resolved this conversation) and propose the intents present, each with your "
    "confidence and the sentiment of the message. You only propose -- deterministic "
    "code decides thresholds, routing, and anything with consequences."
)

DRAFT_SYSTEM_PROMPT = (
    "You draft the guest-facing reply from the given facts. Reference each fact "
    "by its placeholder token {{fact:i}} -- never type out a fact's content "
    "yourself. Write natural, warm, concise connective language around the tokens."
)


class ClassifyOutput(BaseModel):
    intents: List[IntentResult]


class OpenAILLMClient(LLMClient):
    """LLM boundary backed by OpenAI (ADR-0013): classify() and draft() only
    propose -- deterministic code decides everything with consequences."""

    def __init__(self, model: Optional[Any] = None):
        if model is not None:
            self._model = model
        else:
            from langchain_openai import ChatOpenAI

            self._model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    def classify(self, message: str, memory: dict) -> List[IntentResult]:
        structured_model = self._model.with_structured_output(ClassifyOutput)
        prompt = f"{CLASSIFY_SYSTEM_PROMPT}\n\nConversation memory: {memory}\nGuest message: {message}"
        result = structured_model.invoke(prompt)
        return result.intents

    def draft(self, facts: List[str]) -> str:
        prompt = f"{DRAFT_SYSTEM_PROMPT}\n\nFacts (reference by index):\n" + "\n".join(
            f"{i}: {fact}" for i, fact in enumerate(facts)
        )
        response = self._model.invoke(prompt)
        return response.content
