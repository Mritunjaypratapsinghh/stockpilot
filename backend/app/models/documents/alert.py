# from beanie import Indexed
from pydantic import Field
from typing import Optional, Literal
from .base import BaseDocument

class Alert(BaseDocument):
    symbol: str
    name: str
    target_price: float = Field(..., gt=0)
    triggered: bool = False
    active: bool = True
    
    class Settings:
        name = "alerts"
