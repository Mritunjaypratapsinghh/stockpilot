"""Watchlist schemas"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# Request schemas
class WatchlistAdd(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=30)
    notes: Optional[str] = Field(None, max_length=500)


# Response schemas
class WatchlistItemResponse(BaseModel):
    id: str = Field(alias="_id")
    symbol: str
    notes: Optional[str] = None
    current_price: Optional[float] = None
    day_change_pct: float = 0
    added_at: datetime
