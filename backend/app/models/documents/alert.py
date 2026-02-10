from datetime import datetime
from typing import Literal, Optional

from pydantic import Field
from pymongo import ASCENDING, IndexModel

from .base import BaseDocument

AlertType = Literal[
    "PRICE_ABOVE",
    "PRICE_BELOW",
    "PERCENT_CHANGE",
    "PERCENT_UP",
    "PERCENT_DOWN",
    "WEEK_52_HIGH",
    "WEEK_52_LOW",
    "VOLUME_SPIKE",
    "EARNINGS",
]


class Alert(BaseDocument):
    symbol: str
    alert_type: AlertType = "PRICE_ABOVE"
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
