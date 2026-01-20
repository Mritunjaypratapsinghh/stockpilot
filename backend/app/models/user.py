from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from bson import ObjectId

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v, info):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserSettings(BaseModel):
    alerts_enabled: bool = True
    daily_digest: bool = True
    digest_time: str = "18:00"

class User(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    email: EmailStr
    telegram_chat_id: Optional[str] = None
    settings: UserSettings = UserSettings()
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
