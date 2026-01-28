# from beanie import Indexed
from pydantic import Field
from typing import Optional
from .base import BaseDocument

class WatchlistItem(BaseDocument):
    symbol: str
    name: str
    
    class Settings:
        name = "watchlist"
