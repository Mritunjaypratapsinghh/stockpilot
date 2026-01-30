from pydantic import Field
from datetime import datetime
from .base import BaseDocument

class DailyDigest(BaseDocument):
    date: datetime
    summary: str = Field(..., max_length=5000)
    portfolio_value: float = Field(..., ge=0)
    pnl: float = 0
    
    class Settings:
        name = "daily_digest"
