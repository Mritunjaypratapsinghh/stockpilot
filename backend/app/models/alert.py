from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum

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

class Alert(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    symbol: str
    alert_type: AlertType
    target_value: float
    is_active: bool = True
    triggered_at: Optional[datetime] = None
    notification_sent: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True
