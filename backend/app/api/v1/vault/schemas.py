from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class VaultCategoryEnum(str, Enum):
    BANK = "bank"
    INSURANCE = "insurance"
    INVESTMENT = "investment"
    PROPERTY = "property"
    LEGAL = "legal"
    DIGITAL = "digital"
    CONTACT = "contact"


class VaultEntryCreate(BaseModel):
    category: VaultCategoryEnum
    title: str = Field(..., min_length=1, max_length=200)
    details: dict = Field(default_factory=dict)
    notes: str | None = None
    nominee_visible: bool = True


class VaultEntryResponse(BaseModel):
    id: str
    category: str
    title: str
    details: dict
    notes: str | None
    nominee_visible: bool
    created_at: str
    updated_at: str


class NomineeCreate(BaseModel):
    nominee_email: EmailStr
    nominee_name: str = Field(..., min_length=1, max_length=100)
    relation: str | None = None


class NomineeResponse(BaseModel):
    id: str
    nominee_email: str
    nominee_name: str
    relation: str | None
    accepted: bool
    created_at: str
