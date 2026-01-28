# from beanie import Indexed
from pydantic import Field
from typing import Optional, Literal
from datetime import datetime
from .base import BaseDocument

class SIP(BaseDocument):
    symbol: str
    name: str
    amount: float = Field(..., gt=0)
    sip_date: int = Field(..., ge=1, le=31)
    active: bool = True
    
    class Settings:
        name = "sips"
