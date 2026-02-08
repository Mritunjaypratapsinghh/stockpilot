from fastapi import Request, HTTPException
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self, max_keys: int = 10000):
        self.requests = defaultdict(list)
        self.max_keys = max_keys
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed. limit requests per window seconds."""
        now = time.time()
        # Clean old requests
        self.requests[key] = [t for t in self.requests[key] if now - t < window]
        
        # Prevent unbounded growth - remove oldest keys if limit exceeded
        if len(self.requests) > self.max_keys:
            oldest_keys = sorted(self.requests.keys(), 
                               key=lambda k: self.requests[k][-1] if self.requests[k] else 0)[:len(self.requests) - self.max_keys]
            for old_key in oldest_keys:
                del self.requests[old_key]
        
        if len(self.requests[key]) >= limit:
            return False
        
        self.requests[key].append(now)
        return True
    
    def get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

limiter = RateLimiter()

# Rate limit configurations
LIMITS = {
    "auth": (5, 60),       # 5 requests per minute for auth endpoints
    "api": (60, 60),       # 60 requests per minute for general API
    "search": (20, 60),    # 20 searches per minute
}

def rate_limit(limit_type: str = "api"):
    """Dependency for rate limiting"""
    async def check_rate_limit(request: Request):
        ip = limiter.get_client_ip(request)
        limit, window = LIMITS.get(limit_type, (60, 60))
        key = f"{limit_type}:{ip}"
        
        if not limiter.is_allowed(key, limit, window):
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests. Limit: {limit} per {window}s"
            )
    return check_rate_limit
