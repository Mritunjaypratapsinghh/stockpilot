import re
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    settings: dict
    telegram_chat_id: str = ""
    is_pro: bool = False


class SettingsUpdate(BaseModel):
    telegram_chat_id: Optional[str] = None
    email: Optional[EmailStr] = None
    daily_digest: Optional[bool] = None
    alerts_enabled: Optional[bool] = None
    email_alerts: Optional[bool] = None
    hourly_alerts: Optional[bool] = None
    privacy_mode: Optional[bool] = None


class GoogleAuth(BaseModel):
    credential: str = Field(..., max_length=4096)
