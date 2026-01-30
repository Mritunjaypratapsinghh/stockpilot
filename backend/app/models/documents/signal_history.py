# from beanie import Indexed
from pydantic import Field
from .base import BaseDocument

class SignalHistory(BaseDocument):
    symbol: str
    name: str
    reason: str = Field(..., max_length=1000)
    price_at_signal: float = Field(..., ge=0)
    
    class Settings:
        name = "signal_history"
