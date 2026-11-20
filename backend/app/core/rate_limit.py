"""Small in-memory rate limiters (sliding window).

Good enough for one server process. With several instances you would keep the counters in
a shared store such as Redis, because each process would otherwise count separately. The
counters also reset when the process restarts (e.g. Render's free plan going to sleep).
"""

import threading
import time
from collections import deque

# Above this many keys, forget the ones whose events are all outside their window, so an
# attacker sending a different email or IP on every request cannot grow memory forever.
_SWEEP_ABOVE = 10_000


class RateLimiter:
    """At most `max_events` per key within the last `window_seconds`."""

    def __init__(self, max_events: int, window_seconds: int) -> None:
        self.max_events = max_events
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()  # sync FastAPI routes run in a thread pool

    def _recent(self, key: str, now: float) -> deque[float]:
        """Events for `key` still inside the window. Never creates an entry."""
        events = self._events.get(key)
        if events is None:
            return deque()
        while events and now - events[0] > self.window_seconds:
            events.popleft()
        if not events:
            del self._events[key]  # empty: drop it, don't keep a key per stranger forever
        return events

    def _record(self, key: str, now: float) -> None:
        if len(self._events) >= _SWEEP_ABOVE:
            for stale in list(self._events):
                self._recent(stale, now)
        self._events.setdefault(key, deque()).append(now)

    def is_blocked(self, key: str) -> bool:
        with self._lock:
            return len(self._recent(key, time.monotonic())) >= self.max_events

    def record(self, key: str) -> None:
        with self._lock:
            self._record(key, time.monotonic())

    def try_acquire(self, key: str) -> bool:
        """Check and record in one step (no race between two requests). False = blocked."""
        with self._lock:
            now = time.monotonic()
            if len(self._recent(key, now)) >= self.max_events:
                return False
            self._record(key, now)
            return True

    def reset(self, key: str) -> None:
        with self._lock:
            self._events.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()

    def __len__(self) -> int:
        return len(self._events)


MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR

# Logins: failures only. Per email stops guessing one account's password; per IP stops one
# machine trying a common password against many accounts.
login_failures_by_email = RateLimiter(max_events=5, window_seconds=15 * MINUTE)
login_failures_by_ip = RateLimiter(max_events=20, window_seconds=15 * MINUTE)

# Sign-ups: every attempt counts (each one costs a slow bcrypt hash).
registrations_by_ip = RateLimiter(max_events=5, window_seconds=HOUR)

# "Send me a test email": each one is a real email paid for from the Brevo quota.
test_email_cooldown = RateLimiter(max_events=1, window_seconds=10 * MINUTE)  # per user
test_emails_per_user = RateLimiter(max_events=5, window_seconds=DAY)
test_emails_global = RateLimiter(max_events=100, window_seconds=DAY)  # whole app; key "all"

ALL_LIMITERS = (
    login_failures_by_email,
    login_failures_by_ip,
    registrations_by_ip,
    test_email_cooldown,
    test_emails_per_user,
    test_emails_global,
)


def clear_all() -> None:
    """Tests start every case with empty counters."""
    for limiter in ALL_LIMITERS:
        limiter.clear()
