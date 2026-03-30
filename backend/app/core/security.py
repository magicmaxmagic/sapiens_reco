from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import monotonic


class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = monotonic()
        with self._lock:
            queue = self._events[key]
            threshold = now - self.window_seconds
            while queue and queue[0] < threshold:
                queue.popleft()

            if len(queue) >= self.max_requests:
                return False

            queue.append(now)
            return True
