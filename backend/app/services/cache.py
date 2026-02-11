import json
from typing import Any, Optional

import redis.asyncio as redis

from ..core.config import settings
from ..utils.logger import logger

_redis: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get Redis connection (lazy initialization)."""
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
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
