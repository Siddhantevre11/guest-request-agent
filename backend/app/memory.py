from typing import Dict, Tuple

# Structured summary per conversation, not a raw transcript (ADR-0004). Fed
# into classify each turn so the agent doesn't re-ask/re-offer something
# already settled. In-memory dict for the build; Postgres/Redis in production.
ConversationMemory = dict

MEMORY: Dict[Tuple[str, str], ConversationMemory] = {}


def get_memory(guest_id: str, conversation_id: str) -> ConversationMemory:
    return MEMORY.setdefault((guest_id, conversation_id), {"answered_topics": []})
