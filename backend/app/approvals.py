import itertools
from typing import Dict, Optional

Approval = dict

APPROVALS: Dict[str, Approval] = {}
_id_counter = itertools.count(1)


def create_approval(guest_id: str, conversation_id: str, booking_id: str, change: dict) -> Approval:
    """A fully-specified proposed booking change, routed to the host for a
    one-click yes/no -- the agent never mutates a booking itself (ADR-0007)."""
    approval_id = f"APR-{next(_id_counter)}"
    approval: Approval = {
        "id": approval_id,
        "guest_id": guest_id,
        "conversation_id": conversation_id,
        "booking_id": booking_id,
        "change": change,
        "status": "pending",
    }
    APPROVALS[approval_id] = approval
    return approval


def list_pending_approvals() -> list[Approval]:
    return [a for a in APPROVALS.values() if a["status"] == "pending"]


def get_approval(approval_id: str) -> Optional[Approval]:
    return APPROVALS.get(approval_id)
