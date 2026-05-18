"""
Base Service — Business logic layer with common patterns.

Services encapsulate business logic and orchestrate repositories + external calls.
"""

from beanie import PydanticObjectId

from ...services.cache import cache_delete, cache_get, cache_set, market_ttl


class BaseService:
    """Base service with caching and user context."""

    def __init__(self, user_id: PydanticObjectId):
        self.user_id = user_id

    def _cache_key(self, prefix: str) -> str:
        return f"{prefix}:{self.user_id}"

    async def _cached(self, prefix: str, loader, ttl: int | None = None):
        """Get from cache or compute + store."""
        key = self._cache_key(prefix)
        cached = await cache_get(key)
        if cached is not None:
            return cached
        result = await loader()
        await cache_set(key, result, ttl=ttl or market_ttl())
        return result

    async def _invalidate(self, *prefixes: str):
        """Invalidate cache keys for this user."""
        for prefix in prefixes:
            await cache_delete(self._cache_key(prefix))
