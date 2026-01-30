from pydantic import Field
from datetime import datetime
from typing import Dict
from .base import BaseDocument


class NetworthHistory(BaseDocument):
    date: datetime
    value: float = Field(0, ge=0)
    breakdown: Dict[str, float] = {}

    class Settings:
        name = "networth_history"
