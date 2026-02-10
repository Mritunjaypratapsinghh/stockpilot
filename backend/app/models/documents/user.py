from datetime import datetime, timezone
from typing import Any, Dict, Optional

from beanie import Document
from pydantic import EmailStr, Field
from pymongo import ASCENDING, IndexModel


class User(Document):
    email: EmailStr
    password_hash: Optional[str] = None
    google_id: Optional[str] = None
    name: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    push_subscription: Optional[Dict[str, Any]] = None
    settings: Dict[str, Any] = Field(default_factory=lambda: {"alerts_enabled": True, "daily_digest": True})
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
        indexes = [
            IndexModel([("email", ASCENDING)], unique=True),
        ]
