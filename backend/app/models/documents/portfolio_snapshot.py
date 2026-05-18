from datetime import datetime

from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from .base import BaseDocument


class PortfolioSnapshot(BaseDocument):
    date: datetime
    value: float = Field(0, ge=0)
    invested: float = Field(0, ge=0)
    pnl: float = 0
    pnl_pct: float = 0

    class Settings:
        name = "portfolio_snapshots"
        indexes = [
            IndexModel([("user_id", ASCENDING), ("date", DESCENDING)]),
        ]
