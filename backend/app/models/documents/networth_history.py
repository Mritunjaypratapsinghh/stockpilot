from pydantic import Field
from datetime import datetime
from typing import Dict, Any
from .base import BaseDocument

class NetworthHistory(BaseDocument):
    date: datetime
    total_networth: float = Field(..., ge=0)
    
    class Settings:
        name = "networth_history"
