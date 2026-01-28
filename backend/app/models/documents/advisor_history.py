# from beanie import Indexed
from pydantic import Field
from typing import Optional
from .base import BaseDocument

class AdvisorHistory(BaseDocument):
    symbol: str
    name: str
    recommendation: str = Field(..., max_length=2000)
    
    class Settings:
        name = "advisor_history"
