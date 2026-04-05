"""Tax Audit Trail — Immutable log of every computed value with source and formula."""

from datetime import datetime, timezone

from beanie import Indexed
from pydantic import Field

from .base import BaseDocument


class TaxAuditTrail(BaseDocument):
    financial_year: Indexed(str)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    step: str = ""  # e.g. "step_7_slab_tax", "step_9_rebate"
    field_name: str = ""  # e.g. "tax_on_normal_income"
    computed_value: float = 0
    source: str = ""  # ais / form16 / manual / portfolio / computed
    rule_applied: str = ""  # e.g. "Section 111A STCG @ 20%"
    formula: str = ""  # e.g. "20% × ₹1,50,000 = ₹30,000"
    inputs: dict = Field(default_factory=dict)

    class Settings:
        name = "tax_audit_trail"
        use_state_management = True
        indexes = [
            [("user_id", 1), ("financial_year", 1)],
            [("user_id", 1), ("financial_year", 1), ("step", 1)],
        ]
