# from beanie import Indexed
from pydantic import Field
from typing import Optional, Literal
from .base import BaseDocument

class Holding(BaseDocument):
    symbol: str
    name: str
    quantity: float = Field(..., gt=0)
    avg_price: float = Field(..., ge=0)
    current_price: Optional[float] = None
    holding_type: Literal["STOCK", "MF"] = "STOCK"
    sector: Optional[str] = None
    
    class Settings:
        name = "holdings"
