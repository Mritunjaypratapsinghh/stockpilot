from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import BaseDocumentNoUser


class PriceCache(BaseDocumentNoUser):
    symbol: str
    price: float = Field(..., ge=0)
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    last_updated: datetime

    class Settings:
        name = "price_cache"
