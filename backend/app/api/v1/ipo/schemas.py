"""IPO schemas"""

from typing import Optional

from pydantic import BaseModel


class IPOResponse(BaseModel):
    name: str
    type: str
    price: float
    lot_size: int
    min_investment: float
    gmp: float
    gmp_pct: float
    estimated_listing: float
    dates: str
    action: str
    status: str
    review: Optional[str] = None


class IPOListResponse(BaseModel):
    mainboard: list
    sme: list
    all: list
    count: int
    updated_at: str
