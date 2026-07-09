from typing import List

from app.llm import LLMClient


class FakeLLMClient(LLMClient):
    """Stub LLM: canned classify/draft output, no real model call.

    `intents` may be a single list of IntentResult (returned every call) or a
    list of such lists (one per successive call, repeating the last). Records
    each classify() call's (message, memory) for assertions at the LLM-wrapper
    seam.
    """

    def __init__(self, intents, draft_template: str = "{{fact:0}}"):
        if intents and isinstance(intents[0], list):
            self._intents_sequence = list(intents)
        else:
            self._intents_sequence = [intents]
        self._draft_template = draft_template
        self.classify_calls: List[tuple] = []

    def classify(self, message: str, memory: dict):
        call_index = min(len(self.classify_calls), len(self._intents_sequence) - 1)
        self.classify_calls.append((message, dict(memory)))
        return self._intents_sequence[call_index]

    def draft(self, facts: List[str]) -> str:
        return self._draft_template
