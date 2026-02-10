from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .response_handler import StandardResponse


class TimestampMixin(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserContext(BaseModel):
    user_id: str
    email: str


__all__ = ["TimestampMixin", "UserContext", "StandardResponse"]
