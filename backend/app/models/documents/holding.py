from pydantic import Field, BaseModel
from typing import Optional, Literal, List
from .base import BaseDocument


class EmbeddedTransaction(BaseModel):
    """Embedded transaction within a holding"""
    type: Literal["BUY", "SELL"]
    quantity: float
    price: float
    date: str
    notes: Optional[str] = None

    class Config:
        extra = "allow"


class Holding(BaseDocument):
    symbol: str
    name: str
    exchange: str = "NSE"
    holding_type: Literal["EQUITY", "MF", "ETF"] = "EQUITY"
    quantity: float = Field(..., ge=0)
    avg_price: float = Field(..., ge=0)
    current_price: Optional[float] = None
    sector: Optional[str] = None
    transactions: List[EmbeddedTransaction] = []

    class Settings:
        name = "holdings"
