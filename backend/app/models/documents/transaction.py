from datetime import datetime
from typing import Literal, Optional

from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from .base import BaseDocument


class Transaction(BaseDocument):
    symbol: str
    name: str
    transaction_type: Literal["BUY", "SELL"]
    quantity: float = Field(..., gt=0)
    price: float = Field(..., ge=0)
    amount: Optional[float] = None
    holding_type: Literal["STOCK", "MF"] = "STOCK"
    date: datetime
    notes: Optional[str] = Field(None, max_length=500)

    class Settings:
        name = "transactions"
        indexes = [
            IndexModel([("user_id", ASCENDING), ("date", DESCENDING)]),
            IndexModel([("user_id", ASCENDING), ("symbol", ASCENDING)]),
        ]
