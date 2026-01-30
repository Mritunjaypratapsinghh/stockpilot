from pydantic import Field
from typing import Optional
from .base import BaseDocument


class Dividend(BaseDocument):
    symbol: str
    amount: float = Field(..., gt=0)
    quantity: float = 0
    total: float = 0
    ex_date: str
    record_date: Optional[str] = None
    payment_date: Optional[str] = None

    class Settings:
        name = "dividends"
