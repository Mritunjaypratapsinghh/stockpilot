"""API Request/Response Schemas"""

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# Auth Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Holding Schemas
class HoldingType(str, Enum):
    EQUITY = "EQUITY"
    ETF = "ETF"
    MF = "MF"


class TransactionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class TransactionSchema(BaseModel):
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


# Alert Schemas
class AlertType(str, Enum):
    PRICE_ABOVE = "PRICE_ABOVE"
    PRICE_BELOW = "PRICE_BELOW"
    PERCENT_UP = "PERCENT_UP"
    PERCENT_DOWN = "PERCENT_DOWN"
    PERCENT_CHANGE = "PERCENT_CHANGE"
    WEEK_52_HIGH = "WEEK_52_HIGH"
    WEEK_52_LOW = "WEEK_52_LOW"
    VOLUME_SPIKE = "VOLUME_SPIKE"
    EARNINGS = "EARNINGS"


class AlertCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=30)
    alert_type: AlertType
    target_value: float = Field(..., gt=0)


# Ledger Schemas
class LedgerTypeEnum(str, Enum):
    LENT = "lent"
    BORROWED = "borrowed"


class LedgerStatusEnum(str, Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    SETTLED = "settled"


class LedgerCreate(BaseModel):
    type: LedgerTypeEnum
    person_name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    description: Optional[str] = None
    date: Optional[date] = None
    due_date: Optional[date] = None


class LedgerUpdate(BaseModel):
    person_name: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[LedgerStatusEnum] = None


class SettlementCreate(BaseModel):
    amount: float = Field(..., gt=0)
    note: Optional[str] = None
