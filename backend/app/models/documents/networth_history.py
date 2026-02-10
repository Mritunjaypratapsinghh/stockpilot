from datetime import datetime
from typing import Any, Dict

from pydantic import Field, model_validator

from .base import BaseDocument


class NetworthHistory(BaseDocument):
    date: datetime
    value: float = Field(0, ge=0)
    breakdown: Dict[str, float] = {}

    @model_validator(mode="before")
    @classmethod
    def migrate_total_to_value(cls, data: Any) -> Any:
        """Handle old records that have 'total' instead of 'value'."""
        if isinstance(data, dict) and "total" in data:
            if not data.get("value"):
                data["value"] = data["total"]
            del data["total"]
        return data

    class Settings:
        name = "networth_history"
