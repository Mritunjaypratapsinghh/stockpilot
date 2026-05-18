from typing import Optional

from pymongo import ASCENDING, IndexModel

from .base import BaseDocument


class WatchlistItem(BaseDocument):
    symbol: str
    notes: Optional[str] = None

    class Settings:
        name = "watchlist"
        indexes = [
            IndexModel([("user_id", ASCENDING), ("symbol", ASCENDING)], unique=True),
        ]
