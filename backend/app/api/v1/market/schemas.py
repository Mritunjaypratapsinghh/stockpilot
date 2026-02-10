"""Market schemas"""

from typing import Optional

from pydantic import BaseModel


# Response schemas
class QuoteResponse(BaseModel):
    symbol: str
    current_price: float
    previous_close: Optional[float] = None
    day_change: Optional[float] = None
    day_change_pct: Optional[float] = None
    volume: Optional[int] = None


class IndexData(BaseModel):
    price: float
    change: float
    change_pct: float


class SearchResult(BaseModel):
    symbol: str
    name: str
    exchange: str


class ChartCandle(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: int


class CorporateAction(BaseModel):
    type: str
    symbol: str
    date: str
    value: float
