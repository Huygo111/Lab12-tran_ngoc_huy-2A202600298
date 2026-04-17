import time
from collections import defaultdict, deque
from fastapi import HTTPException
from app.config import settings

_windows: dict[str, deque] = defaultdict(deque)
WINDOW_SECONDS = 60


def check_rate_limit(user_id: str) -> None:
    now = time.time()
    window = _windows[user_id]

    while window and window[0] < now - WINDOW_SECONDS:
        window.popleft()

    if len(window) >= settings.rate_limit_per_minute:
        retry_after = int(window[0] + WINDOW_SECONDS - now) + 1
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": settings.rate_limit_per_minute,
                "retry_after_seconds": retry_after,
            },
        )

    window.append(now)
