"""Distributed lock using Redis — prevents duplicate job execution across workers."""

import functools

from ..services.cache import get_redis
from ..utils.logger import logger


async def acquire_lock(key: str, ttl: int = 60) -> bool:
    """Try to acquire a Redis lock. Returns True if acquired."""
    try:
        r = await get_redis()
        return await r.set(f"lock:{key}", "1", nx=True, ex=ttl)
    except Exception:
        return True  # Fail open if Redis unavailable


async def release_lock(key: str) -> None:
    """Release a Redis lock."""
    try:
        r = await get_redis()
        await r.delete(f"lock:{key}")
    except Exception:
        pass


def with_lock(lock_name: str, ttl: int = 60):
    """Decorator: only execute if Redis lock is acquired. Prevents duplicate jobs."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not await acquire_lock(lock_name, ttl):
                logger.debug(f"Skipping {lock_name} — another worker holds the lock")
                return
            try:
                return await func(*args, **kwargs)
            finally:
                await release_lock(lock_name)

        return wrapper

    return decorator
