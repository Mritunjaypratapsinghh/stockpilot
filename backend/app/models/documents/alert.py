from pydantic import Field
from typing import Optional, Literal
from datetime import datetime
from pymongo import IndexModel, ASCENDING
from .base import BaseDocument


class Alert(BaseDocument):
    symbol: str
    alert_type: Literal["PRICE_ABOVE", "PRICE_BELOW"] = "PRICE_ABOVE"
    target_value: float = Field(..., gt=0)
    is_active: bool = True
    triggered_at: Optional[datetime] = None
    notification_sent: bool = False

    class Settings:
        name = "alerts"
        indexes = [
            IndexModel([("user_id", ASCENDING), ("is_active", ASCENDING)]),
            IndexModel([("symbol", ASCENDING)]),
        ]
