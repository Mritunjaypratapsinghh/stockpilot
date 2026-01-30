"""API Request/Response Schemas"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import date
from enum import Enum


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
