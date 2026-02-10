from typing import List, Literal

from pydantic import BaseModel, Field

from .base import BaseDocument


class Contribution(BaseModel):
    amount: float
    date: str


class Goal(BaseDocument):
    name: str = Field(..., min_length=1, max_length=100)
    category: Literal["retirement", "house", "education", "emergency", "general"] = "general"
    target_amount: float = Field(..., gt=0)
    target_date: str
    current_value: float = 0
    monthly_sip: float = 0
    contributions: List[Contribution] = []

    class Settings:
        name = "goals"
