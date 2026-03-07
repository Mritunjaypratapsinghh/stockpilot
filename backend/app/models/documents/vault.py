from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import EmailStr, Field

from .base import BaseDocument


class VaultCategory(str, Enum):
    BANK = "bank"
    INSURANCE = "insurance"
    INVESTMENT = "investment"
    PROPERTY = "property"
    LEGAL = "legal"
    DIGITAL = "digital"
    CONTACT = "contact"


class VaultEntry(BaseDocument):
    category: VaultCategory
    title: str
    details: dict = Field(default_factory=dict)  # Flexible key-value for category-specific fields
    notes: Optional[str] = None
    nominee_visible: bool = True

    class Settings:
        name = "vault_entries"


class VaultNominee(BaseDocument):
    nominee_email: EmailStr
    nominee_name: str
    relation: Optional[str] = None
    accepted: bool = False
    accepted_at: Optional[datetime] = None
    invite_token: Optional[str] = None

    class Settings:
        name = "vault_nominees"
