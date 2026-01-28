from pydantic import Field
from typing import Optional
from .base import BaseDocument

class Asset(BaseDocument):
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=50)
    value: float = Field(..., ge=0)
    
    class Settings:
        name = "assets"
