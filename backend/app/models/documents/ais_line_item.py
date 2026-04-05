"""AIS Line Item — Individual income/transaction entry from Annual Information Statement."""

from enum import Enum
from typing import Optional

from beanie import Indexed

from .base import BaseDocument


class AISCategory(str, Enum):
    TDS = "TDS"
    TCS = "TCS"
    SFT = "SFT"
    TAX_PAYMENT = "tax_payment"
    DEMAND_REFUND = "demand_refund"
    OTHER = "other"


class AISStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    CORRECTED = "corrected"
    DISPUTED = "disputed"


class AISMatchSource(str, Enum):
    FORM16 = "form16"
    FORM26AS = "form26as"
    PORTFOLIO = "portfolio"
    MANUAL = "manual"


class AISLineItem(BaseDocument):
    financial_year: Indexed(str)
    category: AISCategory = AISCategory.OTHER
    info_code: str = ""
    description: str = ""
    source_name: str = ""
    source_tan: str = ""
    reported_value: int = 0
    modified_value: int = 0
    status: AISStatus = AISStatus.PENDING
    user_value: Optional[int] = None
    dispute_reason: str = ""
    matched_with: Optional[AISMatchSource] = None
    is_exempt: bool = False

    class Settings:
        name = "ais_line_items"
        use_state_management = True
        indexes = [
            [("user_id", 1), ("financial_year", 1)],
            [("user_id", 1), ("financial_year", 1), ("status", 1)],
        ]
