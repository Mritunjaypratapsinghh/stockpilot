"""TDS Entry — Normalized TDS record from Form 16, AIS, or Form 26AS."""

from enum import Enum
from typing import Optional

from beanie import Indexed

from .base import BaseDocument


class TDSSource(str, Enum):
    FORM16 = "form16"
    AIS = "ais"
    FORM26AS = "form26as"


class ReconciliationStatus(str, Enum):
    MATCHED = "matched"
    MISMATCH = "mismatch"
    MISSING_IN_26AS = "missing_in_26as"
    EXTRA = "extra"


class TDSEntry(BaseDocument):
    financial_year: Indexed(str)
    source: TDSSource
    tan: str = ""
    deductor_name: str = ""
    section: str = ""  # e.g. "192", "194A", "194"
    amount: int = 0
    quarter: str = ""  # Q1/Q2/Q3/Q4
    reconciliation_status: ReconciliationStatus = ReconciliationStatus.EXTRA
    match_group_id: Optional[str] = None

    class Settings:
        name = "tds_entries"
        use_state_management = True
        indexes = [
            [("user_id", 1), ("financial_year", 1)],
            [("user_id", 1), ("financial_year", 1), ("tan", 1)],
        ]
