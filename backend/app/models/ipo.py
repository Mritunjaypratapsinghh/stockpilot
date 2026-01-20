from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class IPODates(BaseModel):
    open: str
    close: str
    allotment: Optional[str] = None
    listing: Optional[str] = None

class IPO(BaseModel):
    name: str
    symbol: Optional[str] = None
    ipo_type: str = "MAINBOARD"
    price_band: dict
    lot_size: int
    issue_size_cr: Optional[float] = None
    dates: IPODates
    gmp: Optional[float] = None
    gmp_percent: Optional[float] = None
    subscription: Optional[dict] = None
    status: str = "UPCOMING"
