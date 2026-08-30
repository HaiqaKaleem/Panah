"""
In-Memory Cache — TTL-based caching for expensive calculations.

Provides:
  - Generic key-value cache with TTL
  - Decorator for automatic caching of function results
  - Cache statistics and invalidation
  - Per-namespace scoping

In production, replace with Redis or Memcached.
"""
from __future__ import annotations

import hashlib
import json
import time
from functools import wraps
from typing import Any, Callable


class CacheEntry:
    """A single cache entry with TTL."""
    __slots__ = ("key", "value", "created_at", "ttl_seconds", "hit_count")

    def __init__(self, key: str, value: Any, ttl_seconds: int = 300):
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds
        self.hit_count = 0

    @property
    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at


class Cache:
    """TTL-based in-memory cache."""

    def __init__(self, default_ttl: int = 300, max_size: int = 10000):
        self._store: dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        entry = self._store.get(key)
        if entry is None:
            self._misses += 1
            return None
        if entry.is_expired:
            del self._store[key]
            self._misses += 1
            return None
        entry.hit_count += 1
        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in cache."""
        # Evict if at capacity
        if len(self._store) >= self._max_size:
            self._evict_lru()

        self._store[key] = CacheEntry(
            key=key,
            value=value,
            ttl_seconds=ttl or self._default_ttl,
        )

    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        return self._store.pop(key, None) is not None

    def clear(self, namespace: str | None = None) -> int:
        """Clear cache entries. If namespace given, only clear matching keys."""
        if namespace:
            keys = [k for k in self._store if k.startswith(f"{namespace}:")]
            for k in keys:
                del self._store[k]
            return len(keys)
        count = len(self._store)
        self._store.clear()
        return count

    def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if not self._store:
            return
        # Evict oldest entry
        oldest_key = min(self._store.keys(), key=lambda k: self._store[k].created_at)
        del self._store[oldest_key]

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        return {
            "size": len(self._store),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / max(total_requests, 1) * 100, 1),
            "total_requests": total_requests,
        }

    def cleanup(self) -> int:
        """Remove all expired entries. Returns count removed."""
        expired = [k for k, v in self._store.items() if v.is_expired]
        for k in expired:
            del self._store[k]
        return len(expired)


# Global cache instance
_global_cache = Cache(default_ttl=300, max_size=10000)


def get_cache() -> Cache:
    """Get the global cache instance."""
    return _global_cache


def cached(ttl: int = 300, namespace: str = ""):
    """
    Decorator to cache function results.

    Usage:
        @cached(ttl=60, namespace="wind")
        def calculate_wind_load(params):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key from function name + args
            key_parts = [func.__module__, func.__qualname__]
            key_parts.extend(str(a) for a in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            raw_key = ":".join(key_parts)
            cache_key = f"{namespace}:{hashlib.md5(raw_key.encode()).hexdigest()}" if namespace else hashlib.md5(raw_key.encode()).hexdigest()

            # Check cache
            result = _global_cache.get(cache_key)
            if result is not None:
                return result

            # Compute and cache
            result = func(*args, **kwargs)
            _global_cache.set(cache_key, result, ttl=ttl)
            return result
        return wrapper
    return decorator
