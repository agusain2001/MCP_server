import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import HTTPException, Request
from .config import get_settings


class RateLimiter:
    """
    Token bucket rate limiter for API endpoints.
    Not thread-safe, but sufficient for async FastAPI.
    """
    
    def __init__(self, requests: int, period: int):
        """
        Initialize rate limiter.
        
        :param requests: Number of requests allowed
        :param period: Time period in seconds
        """
        self.requests = requests
        self.period = period
        self._buckets: Dict[str, Tuple[int, float]] = defaultdict(
            lambda: (requests, time.time())
        )
    
    async def check_rate_limit(self, request: Request) -> None:
        """
        Check if request should be rate limited.
        
        :param request: FastAPI request object
        :raises HTTPException: If rate limit exceeded
        """
        # Use client IP as identifier
        client_id = request.client.host if request.client else "unknown"
        
        current_time = time.time()
        tokens, last_update = self._buckets[client_id]
        
        # Refill tokens based on time passed
        time_passed = current_time - last_update
        new_tokens = min(
            self.requests,
            tokens + (time_passed / self.period) * self.requests
        )
        
        if new_tokens < 1:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": str(int(self.period))}
            )
        
        # Consume one token
        self._buckets[client_id] = (new_tokens - 1, current_time)
    
    def reset(self, client_id: str = None) -> None:
        """Reset rate limit for a client or all clients."""
        if client_id:
            self._buckets.pop(client_id, None)
        else:
            self._buckets.clear()


# Create global rate limiter instance
settings = get_settings()
rate_limiter = RateLimiter(
    requests=settings.rate_limit_requests,
    period=settings.rate_limit_period
)
