from typing import Optional

from pydantic import Field

from .base import BaseDocument


class Asset(BaseDocument):
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=50)
    value: float = Field(..., ge=0)
    invested: Optional[float] = None
    interest_rate: Optional[float] = None
    maturity_date: Optional[str] = None
    notes: Optional[str] = None

    class Settings:
        name = "assets"
