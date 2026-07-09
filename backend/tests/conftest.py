import copy

import pytest

from app.approvals import APPROVALS
from app.bookings import BOOKINGS
from app.escalations import ESCALATIONS
from app.memory import MEMORY

_BOOKINGS_SNAPSHOT = copy.deepcopy(BOOKINGS)


@pytest.fixture(autouse=True)
def reset_state():
    MEMORY.clear()
    APPROVALS.clear()
    ESCALATIONS.clear()
    BOOKINGS.clear()
    BOOKINGS.update(copy.deepcopy(_BOOKINGS_SNAPSHOT))
    yield
    MEMORY.clear()
    APPROVALS.clear()
    ESCALATIONS.clear()
    BOOKINGS.clear()
    BOOKINGS.update(copy.deepcopy(_BOOKINGS_SNAPSHOT))
