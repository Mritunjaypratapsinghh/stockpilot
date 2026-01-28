from beanie import Document
from pydantic import Field, EmailStr
from datetime import datetime, timezone
from typing import Optional

class User(Document):
    email: EmailStr
    password: str
    name: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "users"
