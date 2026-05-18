from datetime import datetime, timezone
from typing import Optional

from beanie import Document, PydanticObjectId
from pydantic import Field


class BaseDocument(Document):
    user_id: PydanticObjectId
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

    class Settings:
        use_state_management = True

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    async def soft_delete(self):
        """Mark as deleted without removing from DB."""
        self.deleted_at = datetime.now(timezone.utc)
        await self.save()

    async def restore(self):
        """Undo soft delete."""
        self.deleted_at = None
        await self.save()

    async def save(self, *args, **kwargs):
        self.updated_at = datetime.now(timezone.utc)
        return await super().save(*args, **kwargs)


class BaseDocumentNoUser(Document):
    """For collections without user_id (e.g., IPO, price_cache)"""

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    async def save(self, *args, **kwargs):
        self.updated_at = datetime.now(timezone.utc)
        return await super().save(*args, **kwargs)
