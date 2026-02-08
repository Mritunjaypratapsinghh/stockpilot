from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TimestampMixin(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserContext(BaseModel):
    user_id: str
    email: str


# Re-export from response_handler for convenience
from .response_handler import StandardResponse

__all__ = ["TimestampMixin", "UserContext", "StandardResponse"]
