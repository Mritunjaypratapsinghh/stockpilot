from pydantic import BaseModel, Field
from datetime import datetime
from datetime import date as date_type
from enum import Enum


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
    description: str | None = None
    date: date_type | None = None
    due_date: date_type | None = None
    # Recurring payment fields
    is_recurring: bool = False
    recurring_amount: float | None = None  # EMI amount
    recurring_day: int | None = None  # Day of month (1-31)
    end_date: date_type | None = None  # When recurring ends


class SettlementCreate(BaseModel):
    amount: float = Field(..., gt=0)
    note: str | None = None


class SettlementResponse(BaseModel):
    amount: float
    date: datetime
    note: str | None = None


class LedgerResponse(BaseModel):
    id: str
    type: str
    person_name: str
    amount: float
    description: str | None
    date: datetime
    due_date: datetime | None
    status: str
    settlements: list[SettlementResponse]
    remaining: float
    created_at: datetime
    # Recurring fields
    is_recurring: bool = False
    recurring_amount: float | None = None
    recurring_day: int | None = None
    end_date: datetime | None = None
    total_paid: float = 0
    emis_remaining: int | None = None


class LedgerSummary(BaseModel):
    total_lent: float
    total_borrowed: float
    net_balance: float
    pending_entries: int
    monthly_outgoing: float = 0  # Total recurring EMIs you pay
