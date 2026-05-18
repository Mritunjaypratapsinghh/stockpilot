import json
from datetime import datetime
from typing import Any, Optional

import pytz
import redis.asyncio as redis

from ..core.config import settings
from ..utils.logger import logger

_redis: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get Redis connection with connection pool (lazy initialization)."""
    global _redis
    if _redis is None:
        _redis = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=20,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
    return _redis


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


async def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    try:
        r = await get_redis()
        data = await r.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        logger.debug(f"Cache get error: {e}")
        return None


async def cache_set(key: str, value: Any, ttl: int = 60) -> bool:
    """Set value in cache with TTL."""
    try:
        r = await get_redis()
        await r.setex(key, ttl, json.dumps(value))
        return True
    except Exception as e:
        logger.debug(f"Cache set error: {e}")
        return False


async def cache_delete(key: str) -> bool:
    """Delete key from cache."""
    try:
        r = await get_redis()
        await r.delete(key)
        return True
    except Exception as e:
        logger.debug(f"Cache delete error: {e}")
        return False


_IST = pytz.timezone("Asia/Kolkata")

# NSE holidays 2026 (update annually — check NSE circular each December)
_NSE_HOLIDAYS = {
    (1, 26), (3, 10), (3, 31), (4, 1), (4, 14), (4, 18),
    (5, 1), (6, 26), (7, 17), (8, 15), (8, 27), (10, 2),
    (10, 20), (10, 21), (11, 5), (11, 26), (12, 25),
}


def market_open() -> bool:
    """Check if Indian stock market is currently open (accounts for holidays)."""
    now = datetime.now(_IST)
    if now.weekday() >= 5:
        return False
    if (now.month, now.day) in _NSE_HOLIDAYS:
        return False
    return 915 <= now.hour * 100 + now.minute <= 1530


def market_ttl(active: int = 120, closed: int = 3600) -> int:
    """Return TTL based on market hours."""
    return active if market_open() else closed


async def cache_mget(keys: list[str]) -> dict[str, Any]:
    """Get multiple values from cache."""
    if not keys:
        return {}
    try:
        r = await get_redis()
        values = await r.mget(keys)
        return {k: json.loads(v) if v else None for k, v in zip(keys, values)}
    except Exception as e:
        logger.debug(f"Cache mget error: {e}")
        return {}


async def cache_mset(data: dict[str, Any], ttl: int = 60) -> bool:
    """Set multiple values in cache with TTL."""
    if not data:
        return True
    try:
        r = await get_redis()
        pipe = r.pipeline()
        for key, value in data.items():
            pipe.setex(key, ttl, json.dumps(value))
        await pipe.execute()
        return True
    except Exception as e:
        logger.debug(f"Cache mset error: {e}")
        return False
