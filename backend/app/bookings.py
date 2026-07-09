import random
from typing import Dict, Tuple

Booking = dict

# Keyed by (guest_id, conversation_id) -- the platform binds each Conversation
# to exactly one Booking before a message reaches the agent (ADR-0005). A
# returning guest with multiple bookings has one entry per conversation_id.
BOOKINGS: Dict[Tuple[str, str], Booking] = {
    ("guest-1", "conv-1"): {
        "booking_id": "BK-1001",
        "checkin": "2026-08-01",
        "checkout": "2026-08-05",
        "checkout_time": "11:00",
    },
    ("guest-2", "conv-2a"): {
        "booking_id": "BK-2001",
        "checkin": "2026-09-01",
        "checkout": "2026-09-04",
        "checkout_time": "11:00",
    },
    ("guest-2", "conv-2b"): {
        "booking_id": "BK-2002",
        "checkin": "2026-10-10",
        "checkout": "2026-10-12",
        "checkout_time": "11:00",
    },
    # Dedicated to identity-resolution tests: both checkouts are available in
    # the calendar fixture, so those tests aren't coupled to availability.
    ("guest-4", "conv-4a"): {
        "booking_id": "BK-4001",
        "checkin": "2026-11-01",
        "checkout": "2026-11-05",
        "checkout_time": "11:00",
    },
    ("guest-4", "conv-4b"): {
        "booking_id": "BK-4002",
        "checkin": "2026-11-10",
        "checkout": "2026-11-14",
        "checkout_time": "11:00",
    },
}


class BookingLookupError(Exception):
    pass


class BookingLookup:
    """Deliberately flaky (per the brief) so callers must retry (ADR-0003)."""

    def __init__(
        self,
        bookings: Dict[Tuple[str, str], Booking] = BOOKINGS,
        failure_rate: float = 0.3,
        rng: random.Random | None = None,
    ):
        self._bookings = bookings
        self._failure_rate = failure_rate
        self._rng = rng or random.Random()

    def __call__(self, guest_id: str, conversation_id: str) -> Booking:
        if self._rng.random() < self._failure_rate:
            raise BookingLookupError("transient lookup failure")
        key = (guest_id, conversation_id)
        if key not in self._bookings:
            raise BookingLookupError(f"no booking found for {key}")
        return self._bookings[key]
