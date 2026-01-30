"""Analytics schemas"""
from pydantic import BaseModel
from typing import List, Dict


class SectorAllocation(BaseModel):
    sector: str
    value: float
    percentage: float


class AnalyticsSummary(BaseModel):
    total_value: float
    sectors: List[SectorAllocation]
    holdings_count: int


class PnLCalendarEntry(BaseModel):
    date: str
    buy: float
    sell: float


class RebalanceSuggestion(BaseModel):
    sector: str
    current_pct: float
    target_pct: float
    action: str
