"""Thread-safe in-memory TTL cache for external API responses."""

import threading
import time
from typing import Any, Optional


class TTLCache:
    """Simple bounded TTL cache with per-key expiry."""

    def __init__(self, max_items: int = 512):
        self._max_items = max_items
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        now = time.monotonic()
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            expires_at, value = entry
            if now >= expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        if ttl_seconds <= 0:
            return
        expires_at = time.monotonic() + ttl_seconds
        with self._lock:
            if len(self._store) >= self._max_items:
                # Evict oldest entry
                oldest_key = next(iter(self._store))
                del self._store[oldest_key]
            self._store[key] = (expires_at, value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


shared_cache = TTLCache(max_items=1024)
