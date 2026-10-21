import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


def rate_limit(max_calls: int, window_seconds: int):
    """Returns a FastAPI dependency: max_calls per window per client IP (in memory)."""
    hits: dict[str, deque] = defaultdict(deque)

    def dependency(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        q = hits[ip]
        while q and now - q[0] > window_seconds:
            q.popleft()
        if len(q) >= max_calls:
            raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")
        q.append(now)

    return dependency
