from pydantic import Field
from datetime import datetime
from .base import BaseDocument


class PortfolioSnapshot(BaseDocument):
    date: datetime
    value: float = Field(0, ge=0)
    invested: float = Field(0, ge=0)
    pnl: float = 0
    pnl_pct: float = 0

    class Settings:
        name = "portfolio_snapshots"
