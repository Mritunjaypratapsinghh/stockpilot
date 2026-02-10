from pydantic import BaseModel, EmailStr
from typing import Optional


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


class SettingsUpdate(BaseModel):
    telegram_chat_id: Optional[str] = None
    email: Optional[EmailStr] = None
    daily_digest: Optional[bool] = None
    alerts_enabled: Optional[bool] = None
    email_alerts: Optional[bool] = None
    hourly_alerts: Optional[bool] = None


class GoogleAuth(BaseModel):
    credential: str
