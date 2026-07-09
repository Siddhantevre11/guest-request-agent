from abc import ABC, abstractmethod
from typing import List

from .models import IntentResult


class LLMClient(ABC):
    """LLM boundary: classify proposes intents, draft proposes wording.

    Deterministic code decides everything downstream of these two calls
    (routing, thresholds, tool dispatch, fact substitution). draft() must
    reference facts via `{{fact:i}}` tokens rather than typing them out —
    deterministic code substitutes the real values afterward (ADR-0009).
    """

    @abstractmethod
    def classify(self, message: str, memory: dict) -> List[IntentResult]: ...

    @abstractmethod
    def draft(self, facts: List[str]) -> str: ...
