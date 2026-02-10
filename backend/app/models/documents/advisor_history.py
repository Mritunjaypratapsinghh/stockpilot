from pydantic import Field

from .base import BaseDocument


class AdvisorHistory(BaseDocument):
    symbol: str
    name: str
    recommendation: str = Field(..., max_length=2000)

    class Settings:
        name = "advisor_history"
