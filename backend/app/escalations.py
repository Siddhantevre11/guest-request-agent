import itertools
from typing import Dict

Escalation = dict

ESCALATIONS: Dict[str, Escalation] = {}
_id_counter = itertools.count(1)


def create_escalation(guest_id: str, conversation_id: str, reason: str) -> Escalation:
    """A concise, host-facing item for a genuine problem -- what's happening
    and what the host needs to do, not a verbose dump (ADR-0008)."""
    escalation_id = f"ESC-{next(_id_counter)}"
    escalation: Escalation = {
        "id": escalation_id,
        "guest_id": guest_id,
        "conversation_id": conversation_id,
        "reason": reason,
    }
    ESCALATIONS[escalation_id] = escalation
    return escalation


def list_escalations() -> list[Escalation]:
    return list(ESCALATIONS.values())
