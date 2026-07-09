from datetime import date as date_cls
from datetime import timedelta
from typing import Optional

# In-memory calendar: date -> available for a booking-change/upsell request.
# Deterministic, real data -- the LLM never invents availability (ADR-0007).
CALENDAR: dict[str, bool] = {
    "2026-08-05": True,
    "2026-09-04": False,
    "2026-07-31": True,  # the night before BK-1001's checkin -- a real gap
}

GAP_NIGHT_PRICE = 120


def check_availability(date: str, calendar: dict[str, bool] = CALENDAR) -> bool:
    return calendar.get(date, False)


def find_upsell(booking: dict, calendar: dict[str, bool] = CALENDAR) -> Optional[dict]:
    """A real, available gap night the night before check-in -- never invented
    (ADR-0006). Returns None if there's no genuine gap."""
    checkin = date_cls.fromisoformat(booking["checkin"])
    gap_date = (checkin - timedelta(days=1)).isoformat()
    if calendar.get(gap_date):
        return {"date": gap_date, "price": GAP_NIGHT_PRICE}
    return None
