from pydantic import Field
from datetime import datetime
from typing import Dict, Any, List
from .base import BaseDocument

class PortfolioSnapshot(BaseDocument):
    date: datetime
    total_value: float = Field(..., ge=0)
    total_invested: float = Field(..., ge=0)
    pnl: float = 0
    pnl_percent: float = 0
    
    class Settings:
        name = "portfolio_snapshots"
