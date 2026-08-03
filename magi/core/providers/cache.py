"""
Caché acotada (Plan MAGI 9.0 §1.1).

En v5.0.28 `self._cache[key] = value` (cloud.py:161) crecía sin límite y no se
purgaba nunca: fuga de memoria proporcional al uso de la sesión.

LRU + TTL, sin dependencias externas.
"""
from __future__ import annotations

import hashlib
import time
from collections import OrderedDict
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    def __init__(self, maxsize: int = 500, ttl_s: float = 3600.0):
        self.maxsize = maxsize
        self.ttl_s = ttl_s
        self._d: OrderedDict[str, tuple[float, T]] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def _now(self) -> float:
        return time.monotonic()

    def get(self, key: str) -> T | None:
        item = self._d.get(key)
        if item is None:
            self.misses += 1
            return None
        ts, value = item
        if self._now() - ts > self.ttl_s:
            del self._d[key]
            self.misses += 1
            return None
        self._d.move_to_end(key)
        self.hits += 1
        return value

    def set(self, key: str, value: T) -> None:
        if key in self._d:
            self._d.move_to_end(key)
        self._d[key] = (self._now(), value)
        while len(self._d) > self.maxsize:
            self._d.popitem(last=False)  # expulsa el menos usado

    def clear(self) -> None:
        self._d.clear()

    def __len__(self) -> int:
        return len(self._d)

    def stats(self) -> dict[str, Any]:
        total = self.hits + self.misses
        return {
            "size": len(self._d),
            "maxsize": self.maxsize,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total, 3) if total else 0.0,
        }


def make_key(*parts: Any) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(repr(p).encode("utf-8", errors="replace"))
        h.update(b"\x00")
    return h.hexdigest()
