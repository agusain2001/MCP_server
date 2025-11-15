import time

class SimpleTTLCache:
    """
    A simple in-memory cache with Time-To-Live (TTL) support.
    
    This is not thread-safe, but for an async-based application like FastAPI,
    where it's accessed by a single provider instance in a single-threaded
    event loop, it's sufficient.
    """
    
    def __init__(self, ttl_seconds: int = 60):
        """
        :param ttl_seconds: The default time-to-live for cache items.
        """
        self._cache = {}
        self.ttl = ttl_seconds

    def set(self, key: str, value: any):
        """
        Adds an item to the cache with a timestamp.
        """
        self._cache[key] = (value, time.time())

    def get(self, key: str) -> any | None:
        """
        Retrieves an item from the cache.
        Returns None if the item doesn't exist or has expired.
        """
        if key not in self._cache:
            return None
        
        value, timestamp = self._cache[key]
        
        # Check if the item has expired
        if (time.time() - timestamp) > self.ttl:
            # Expired, delete and return None
            del self._cache[key]
            return None
        
        # Not expired, return the value
        return value

    def clear(self):
        """
        Clears the entire cache.
        """
        self._cache.clear()