from typing import Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


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
    credential: str
