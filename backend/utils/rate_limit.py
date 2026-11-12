"""Sliding-window rate limiter dependency for sensitive FastAPI endpoints."""

from collections import deque
import threading
import time
from typing import Callable

from fastapi import HTTPException, Request, status


class SlidingWindowRateLimiter:
    """Thread-safe per-IP + route sliding window rate limiter."""

    def __init__(self):
        self._buckets: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str, max_requests: int, window_seconds: int) -> None:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            bucket = self._buckets.setdefault(key, deque())
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= max_requests:
                retry_after = max(1, int(window_seconds - (now - bucket[0])))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please wait before trying again.",
                    headers={"Retry-After": str(retry_after)},
                )
            bucket.append(now)

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()


rate_limiter = SlidingWindowRateLimiter()


def rate_limit(max_requests: int = 30, window_seconds: int = 60) -> Callable[[Request], None]:
    """Return a FastAPI dependency enforcing max_requests per window_seconds per IP+path."""

    def _dependency(request: Request) -> None:
        client_host = request.client.host if request.client else "unknown"
        key = f"{client_host}:{request.url.path}"
        rate_limiter.check(key, max_requests=max_requests, window_seconds=window_seconds)

    return _dependency
