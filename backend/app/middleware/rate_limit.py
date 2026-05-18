from fastapi import HTTPException, Request

from ..services.cache import get_redis
from ..utils.logger import logger


class RateLimiter:
    """Redis-based rate limiter using sliding window."""

    def get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed using Redis INCR + EXPIRE."""
        try:
            r = await get_redis()
            if not r:
                return True  # Fail open if Redis unavailable
            current = await r.incr(key)
            if current == 1:
                await r.expire(key, window)
            return current <= limit
        except Exception as e:
            logger.debug(f"Rate limit check error: {e}")
            return True  # Fail open


limiter = RateLimiter()

# Rate limit configurations
LIMITS = {
    "auth": (5, 60),  # 5 requests per minute for auth endpoints
    "api": (60, 60),  # 60 requests per minute for general API
    "search": (20, 60),  # 20 searches per minute
}


def rate_limit(limit_type: str = "api"):
    """Dependency for rate limiting."""

    async def check_rate_limit(request: Request):
        ip = limiter.get_client_ip(request)
        limit, window = LIMITS.get(limit_type, (60, 60))
        key = f"rl:{limit_type}:{ip}"

        if not await limiter.is_allowed(key, limit, window):
            raise HTTPException(status_code=429, detail=f"Too many requests. Limit: {limit} per {window}s")

    return check_rate_limit
