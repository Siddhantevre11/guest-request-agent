import re

from .store import SOP_NOTES

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "do", "does", "did",
    "there", "here", "i", "my", "me", "you", "your", "it", "to", "of",
    "in", "on", "at", "for", "and", "with", "can", "what", "s",
}


def _keywords(text: str) -> set[str]:
    return {w for w in re.findall(r"\w+", text.lower()) if w not in STOPWORDS}


def answer_from_notes(question: str, notes: dict[str, str] = SOP_NOTES) -> list[str]:
    """Retrieve matching SOP passages; an empty list means a miss (ADR-0010).

    Returns retrieved passage text, not a finished answer, so deterministic
    code — not the LLM — decides whether the question was actually covered.
    """
    question_words = _keywords(question)
    scored: list[tuple[int, str]] = []
    for key, text in notes.items():
        note_words = _keywords(f"{key} {text}")
        overlap = len(question_words & note_words)
        if overlap:
            scored.append((overlap, text))
    scored.sort(key=lambda pair: -pair[0])
    return [text for _, text in scored]


def graceful_miss_message(notes: dict[str, str] = SOP_NOTES) -> str:
    """Truthful negative + real, retrieved topic list -- never a fabricated
    alternative (ADR-0010)."""
    topics = ", ".join(sorted(notes.keys()))
    return f"I don't have specific info on that, but I can help with: {topics}."
