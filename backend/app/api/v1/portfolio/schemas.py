"""Portfolio schemas"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List
from datetime import date


# Request schemas
class HoldingCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=30)
    name: str
    exchange: str = "NSE"
    holding_type: Literal["EQUITY", "MF", "ETF"] = "EQUITY"
    quantity: float = Field(..., gt=0)
    avg_price: float = Field(..., gt=0)

    @field_validator('symbol')
    @classmethod
    def clean_symbol(cls, v: str) -> str:
        return v.strip().upper()


class HoldingUpdate(BaseModel):
    quantity: Optional[float] = Field(None, gt=0)
    avg_price: Optional[float] = Field(None, gt=0)


class TransactionCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=30)
    type: Literal["BUY", "SELL"]
    quantity: Optional[float] = Field(None, gt=0)
    price: float = Field(..., gt=0)
    date: date
    amount: Optional[float] = Field(None, gt=0)
    holding_type: Literal["EQUITY", "MF", "ETF"] = "EQUITY"
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator('symbol')
    @classmethod
    def clean_symbol(cls, v: str) -> str:
        return v.strip().upper()


# Response schemas
class HoldingResponse(BaseModel):
    id: str = Field(alias="_id")
    symbol: str
    name: str
    holding_type: str
    quantity: float
    avg_price: float
    current_price: float
    day_change_pct: float = 0
    current_value: float
    total_investment: float
    pnl: float
    pnl_pct: float


class PortfolioSummary(BaseModel):
    total_investment: float
    current_value: float
    total_pnl: float
    total_pnl_pct: float
    day_pnl: float
    day_pnl_pct: float
    holdings_count: int


class SectorAllocation(BaseModel):
    sector: str
    value: float
    percentage: float


class TransactionResponse(BaseModel):
    symbol: str
    holding_id: str
    index: int
    type: str
    quantity: float
    price: float
    date: str
    notes: Optional[str] = None


class ImportResult(BaseModel):
    broker: str
    imported: int
    skipped: int
