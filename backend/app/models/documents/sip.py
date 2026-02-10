from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from .base import BaseDocument


class Installment(BaseModel):
    amount: float
    nav: float
    units: float
    date: str


class SIP(BaseDocument):
    symbol: str
    amount: float = Field(..., gt=0)
    frequency: Literal["monthly", "weekly", "quarterly"] = "monthly"
    sip_date: int = Field(1, ge=1, le=28)
    start_date: str
    end_date: Optional[str] = None
    is_active: bool = True
    last_nav: Optional[float] = None
    installments: List[Installment] = []

    class Settings:
        name = "sips"
