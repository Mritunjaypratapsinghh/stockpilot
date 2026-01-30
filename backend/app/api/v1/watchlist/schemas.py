"""Watchlist schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


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
