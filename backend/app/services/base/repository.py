"""
Base Repository — Tenant-scoped data access layer.

All DB queries go through repositories to enforce:
1. Automatic user_id scoping (tenant isolation)
2. Consistent pagination
3. Projection support
4. Audit-friendly query patterns
"""

from typing import Any, Generic, Optional, TypeVar

from beanie import Document, PydanticObjectId

T = TypeVar("T", bound=Document)


class BaseRepository(Generic[T]):
    """Base repository with tenant-scoped queries."""

    def __init__(self, model: type[T], user_id: PydanticObjectId):
        self.model = model
        self.user_id = user_id

    def _scoped(self, **extra_filters) -> dict:
        """Build query dict scoped to current user."""
        return {"user_id": self.user_id, **extra_filters}

    async def find_all(self, skip: int = 0, limit: int = 100, sort: str = "-created_at", **filters) -> list[T]:
        query = self._scoped(**filters)
        return await self.model.find(query).sort(sort).skip(skip).limit(limit).to_list()

    async def find_one(self, **filters) -> Optional[T]:
        return await self.model.find_one(self._scoped(**filters))

    async def get_by_id(self, doc_id: PydanticObjectId) -> Optional[T]:
        """Get by ID with ownership check."""
        doc = await self.model.get(doc_id)
        if doc and getattr(doc, "user_id", None) == self.user_id:
            return doc
        return None

    async def count(self, **filters) -> int:
        return await self.model.find(self._scoped(**filters)).count()

    async def create(self, doc: T) -> T:
        doc.user_id = self.user_id
        await doc.insert()
        return doc

    async def delete_by_id(self, doc_id: PydanticObjectId) -> bool:
        doc = await self.get_by_id(doc_id)
        if doc:
            await doc.delete()
            return True
        return False
