"""In-process token-bucket rate limiter for expensive endpoints."""

from __future__ import annotations

import threading
import time


class TokenBucket:
    def __init__(self, rate_per_minute: int, burst: int | None = None,
                 clock=time.monotonic) -> None:
        self.rate = rate_per_minute / 60.0
        self.capacity = float(burst or rate_per_minute)
        self.clock = clock
        self._buckets: dict[str, tuple[float, float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = self.clock()
        with self._lock:
            tokens, last = self._buckets.get(key, (self.capacity, now))
            tokens = min(self.capacity, tokens + (now - last) * self.rate)
            if tokens < 1:
                self._buckets[key] = (tokens, now)
                return False
            self._buckets[key] = (tokens - 1, now)
            return True

