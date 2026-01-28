# from beanie import Indexed
from pydantic import Field
from typing import Optional
from datetime import datetime
from .base import BaseDocument

class Dividend(BaseDocument):
    symbol: str
    name: str
    amount: float = Field(..., ge=0)
    
    class Settings:
        name = "dividends"
