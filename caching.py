import time
from typing import Any, Optional, Dict, Tuple


class SimpleTTLCache:
    """
    A simple in-memory cache with Time-To-Live (TTL) support.
    
    This is not thread-safe, but for an async-based application like FastAPI,
    where it's accessed by a single provider instance in a single-threaded
    event loop, it's sufficient.
    """
    
    def __init__(self, ttl_seconds: int = 60, max_size: int = 1000):
        """
        Initialize cache with TTL and size limits.
        
        :param ttl_seconds: The default time-to-live for cache items
        :param max_size: Maximum number of items to store
        """
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._hits = 0
        self._misses = 0

    def set(self, key: str, value: Any) -> None:
        """
        Add an item to the cache with a timestamp.
        
        :param key: Cache key
        :param value: Value to cache
        """
        # Implement LRU eviction if cache is full
        if len(self._cache) >= self.max_size:
            self._evict_oldest()
        
        self._cache[key] = (value, time.time())

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve an item from the cache.
        
        :param key: Cache key
        :return: Cached value or None if expired/missing
        """
        if key not in self._cache:
            self._misses += 1
            return None
        
        value, timestamp = self._cache[key]
        
        # Check if the item has expired
        if (time.time() - timestamp) > self.ttl:
            del self._cache[key]
            self._misses += 1
            return None
        
        self._hits += 1
        return value
    
    def _evict_oldest(self) -> None:
        """Remove the oldest item from cache."""
        if not self._cache:
            return
        
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
        del self._cache[oldest_key]

    def delete(self, key: str) -> bool:
        """
        Delete a specific key from cache.
        
        :param key: Cache key to delete
        :return: True if key existed and was deleted
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "ttl": self.ttl
        }
