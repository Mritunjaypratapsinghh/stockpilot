from typing import Optional
from datetime import datetime
from .base import BaseDocument


class WatchlistItem(BaseDocument):
    symbol: str
    notes: Optional[str] = None
    added_at: Optional[datetime] = None

    class Settings:
        name = "watchlist"
