import pytest

from app.memory import MEMORY


@pytest.fixture(autouse=True)
def reset_memory():
    MEMORY.clear()
    yield
    MEMORY.clear()
