from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from threading import Lock


class SendRateLimiter:
    def __init__(self, max_attempts: int = 10, window_hours: int = 1) -> None:
        self.max_attempts = max_attempts
        self.window = timedelta(hours=window_hours)
        self.attempts: dict[str, deque[datetime]] = defaultdict(deque)
        self.lock = Lock()

    def allow(self, identity: str) -> bool:
        now = datetime.now(timezone.utc)
        with self.lock:
            recent = self.attempts[identity]
            while recent and now - recent[0] >= self.window:
                recent.popleft()
            if len(recent) >= self.max_attempts:
                return False
            recent.append(now)
            return True
