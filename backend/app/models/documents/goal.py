from pydantic import Field
from typing import Optional
from datetime import datetime
from .base import BaseDocument

class Goal(BaseDocument):
    name: str = Field(..., min_length=1, max_length=100)
    target_amount: float = Field(..., gt=0)
    current_amount: float = Field(default=0, ge=0)
    
    class Settings:
        name = "goals"
