from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class HoldingType(str, Enum):
    EQUITY = "EQUITY"
    ETF = "ETF"
    MF = "MF"

class TransactionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class Transaction(BaseModel):
    type: TransactionType
    quantity: float
    price: float
    date: date
    notes: Optional[str] = None

class HoldingCreate(BaseModel):
    symbol: str
    name: Optional[str] = None
    exchange: str = "NSE"
    holding_type: HoldingType = HoldingType.EQUITY
    quantity: float
    avg_price: float

class HoldingUpdate(BaseModel):
    quantity: Optional[float] = None
    avg_price: Optional[float] = None

class Holding(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    symbol: str
    name: Optional[str] = None
    exchange: str = "NSE"
    holding_type: HoldingType = HoldingType.EQUITY
    quantity: float
    avg_price: float
    transactions: List[Transaction] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True

class HoldingWithPrice(Holding):
    current_price: Optional[float] = None
    day_change: Optional[float] = None
    day_change_pct: Optional[float] = None
    current_value: Optional[float] = None
    total_investment: Optional[float] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
