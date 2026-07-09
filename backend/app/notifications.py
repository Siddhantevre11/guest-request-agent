import itertools
from typing import Dict, List, Tuple

Notification = dict

NOTIFICATIONS: Dict[Tuple[str, str], List[Notification]] = {}
_id_counter = itertools.count(1)


def add_notification(guest_id: str, conversation_id: str, text: str) -> Notification:
    """The host's decision is a later, separate follow-up to the guest --
    never part of the turn that created the Approval (ADR-0002, ADR-0012)."""
    notification: Notification = {"id": f"NOTIF-{next(_id_counter)}", "text": text}
    NOTIFICATIONS.setdefault((guest_id, conversation_id), []).append(notification)
    return notification


def pop_notifications(guest_id: str, conversation_id: str) -> List[Notification]:
    """Consume-on-read: delivered once, not re-sent on the next poll."""
    key = (guest_id, conversation_id)
    notifications = NOTIFICATIONS.get(key, [])
    NOTIFICATIONS[key] = []
    return notifications
