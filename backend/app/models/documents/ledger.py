from beanie import PydanticObjectId
from pydantic import Field
from datetime import datetime, timezone
from typing import Optional
from enum import Enum

from .base import BaseDocument


class LedgerType(str, Enum):
    LENT = "lent"
    BORROWED = "borrowed"


class LedgerStatus(str, Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    SETTLED = "settled"


class Settlement(BaseDocument):
    amount: float
    date: datetime
    note: Optional[str] = None


class Ledger(BaseDocument):
    type: LedgerType
    person_name: str
    amount: float
    description: Optional[str] = None
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    due_date: Optional[datetime] = None
    status: LedgerStatus = LedgerStatus.PENDING
    settlements: list[Settlement] = []
    # Recurring payment fields
    is_recurring: bool = False
    recurring_amount: Optional[float] = None  # EMI per month
    recurring_day: Optional[int] = None  # Day of month
    end_date: Optional[datetime] = None  # When EMIs end

    class Settings:
        name = "ledger"
