"""Unit tests for the sliding-window limiter (no HTTP, no database)."""

import pytest

from app.core import rate_limit
from app.core.rate_limit import RateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> FakeClock:
    fake = FakeClock()
    monkeypatch.setattr(rate_limit.time, "monotonic", fake)
    return fake


def test_blocks_at_the_limit_and_frees_up_after_the_window(clock: FakeClock) -> None:
    limiter = RateLimiter(max_events=2, window_seconds=60)
    assert limiter.try_acquire("k")
    assert limiter.try_acquire("k")
    assert not limiter.try_acquire("k")
    assert limiter.try_acquire("other")  # keys are independent
    clock.now += 61
    assert limiter.try_acquire("k")


def test_checking_a_key_does_not_store_it(clock: FakeClock) -> None:
    limiter = RateLimiter(max_events=5, window_seconds=60)
    for i in range(100):
        assert not limiter.is_blocked(f"stranger-{i}@example.com")
    assert len(limiter) == 0


def test_old_keys_are_forgotten(clock: FakeClock, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rate_limit, "_SWEEP_ABOVE", 10)
    limiter = RateLimiter(max_events=5, window_seconds=60)
    for i in range(10):
        limiter.record(f"ip-{i}")
    clock.now += 61
    limiter.record("new")  # over the threshold: the 10 stale keys are swept
    assert len(limiter) == 1
