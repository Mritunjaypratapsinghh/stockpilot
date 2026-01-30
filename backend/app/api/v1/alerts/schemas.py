"""Alerts schemas"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


# Request schemas
class AlertCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=30)
    alert_type: Literal["PRICE_ABOVE", "PRICE_BELOW"] = "PRICE_ABOVE"
    target_value: float = Field(..., gt=0)


class PushSubscription(BaseModel):
    endpoint: str
    keys: dict


# Response schemas
class AlertResponse(BaseModel):
    id: str = Field(alias="_id")
    symbol: str
    alert_type: str
    target_value: float
    is_active: bool


class NotificationResponse(BaseModel):
    id: str = Field(alias="_id")
    title: str
    message: str
    created_at: datetime
