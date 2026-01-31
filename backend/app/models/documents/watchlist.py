from typing import Optional
from .base import BaseDocument


class WatchlistItem(BaseDocument):
    symbol: str
    notes: Optional[str] = None

    class Settings:
        name = "watchlist"
