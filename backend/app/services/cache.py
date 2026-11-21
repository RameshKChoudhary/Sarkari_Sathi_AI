"""Tiny in-process TTL + LRU cache (per worker)."""
from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any, Hashable, Optional


class TTLCache:
    def __init__(self, ttl_s: int = 600, max_items: int = 512) -> None:
        self.ttl, self.max = ttl_s, max_items
        self._d: OrderedDict[Hashable, tuple[float, Any]] = OrderedDict()
        self.hits = self.misses = 0

    def get(self, key: Hashable) -> Optional[Any]:
        item = self._d.get(key)
        if item and time.monotonic() - item[0] < self.ttl:
            self._d.move_to_end(key)
            self.hits += 1
            return item[1]
        self._d.pop(key, None)
        self.misses += 1
        return None

    def set(self, key: Hashable, value: Any) -> None:
        self._d[key] = (time.monotonic(), value)
        self._d.move_to_end(key)
        while len(self._d) > self.max:
            self._d.popitem(last=False)

    def stats(self) -> dict[str, int]:
        return {"size": len(self._d), "hits": self.hits, "misses": self.misses}
