import time
from typing import Callable, TypeVar

T = TypeVar("T")


def retry(fn: Callable[[], T], max_attempts: int = 3, delay_seconds: float = 0.01) -> T:
    """Fixed small delay between attempts (ADR-0003). This is a single
    in-memory lookup with injected failure, not a rate-limited API, so
    exponential backoff has no target to protect here -- it's a noted
    production upgrade, not built.
    """
    last_error: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - any tool failure here is retryable
            last_error = exc
            if attempt < max_attempts - 1:
                time.sleep(delay_seconds)
    assert last_error is not None
    raise last_error
