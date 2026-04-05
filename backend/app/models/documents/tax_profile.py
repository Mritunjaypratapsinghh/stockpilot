"""Tax Profile — Complete tax filing state per user per financial year."""

from datetime import date
from enum import Enum
from typing import Optional

from beanie import Indexed
from pydantic import BaseModel, Field

from .base import BaseDocument


class FilingStatus(str, Enum):
    DRAFT = "draft"
    RECONCILED = "reconciled"
    VALIDATED = "validated"
    EXPORTED = "exported"
    FILED = "filed"


class RegimeChoice(str, Enum):
    OLD = "old"
    NEW = "new"
    AUTO = "auto"


class AgeCategory(str, Enum):
    NORMAL = "normal"  # < 60
    SENIOR = "senior"  # 60-80
    SUPER_SENIOR = "super_senior"  # 80+


class SalaryDetails(BaseModel):
    gross: int = 0
    basic: int = 0
    da: int = 0
    hra_received: int = 0
    lta: int = 0
    special_allowance: int = 0
    employer_pf: int = 0
    employee_pf: int = 0
    professional_tax: int = 0
    employer_nps: int = 0
    form16_count: int = 0


class HRADetails(BaseModel):
    rent_paid: int = 0
    city_name: str = ""
    city_type: str = "non_metro"  # metro / non_metro
    months_stayed: int = 12


class HouseProperty(BaseModel):
    hp_type: str = "self_occupied"  # self_occupied / let_out
    rental_income: int = 0
    municipal_tax: int = 0
    interest_paid: int = 0


class OtherIncome(BaseModel):
    savings_interest: int = 0
    fd_interest: int = 0
    dividend_income_gross: int = 0
    interest_on_it_refund: int = 0
    other: int = 0


class ExemptIncome(BaseModel):
    ppf_maturity: int = 0
    epf_withdrawal: int = 0
    insurance_maturity: int = 0
    gifts_from_relatives: int = 0
    agricultural_income: int = 0


class Deductions(BaseModel):
    sec_80c: int = 0
    sec_80d_self: int = 0
    sec_80d_parents: int = 0
    is_self_senior: bool = False
    is_parents_senior: bool = False
    sec_80ccd_1b: int = 0
    sec_80ccd_2: int = 0
    sec_80e: int = 0
    sec_80g: int = 0
    sec_80tta: int = 0
    sec_80ttb: int = 0


class ReinvestmentExemptions(BaseModel):
    sec_54: int = 0
    sec_54ec: int = 0
    sec_54f: int = 0


class LossCarryForward(BaseModel):
    from_ay: str  # e.g. "2025-26"
    loss_type: str  # STCL / LTCL / house_property
    original: int = 0
    remaining: int = 0
    expires_ay: str = ""
    filed_on_time: bool = True


class TaxPayment(BaseModel):
    payment_date: Optional[date] = None
    amount: int = 0
    challan_no: str = ""


class DocumentsUploaded(BaseModel):
    form16: bool = False
    form16_count: int = 0
    ais: bool = False
    form26as: bool = False


class TaxProfile(BaseDocument):
    financial_year: Indexed(str)
    assessment_year: str = ""
    status: FilingStatus = FilingStatus.DRAFT
    regime_choice: RegimeChoice = RegimeChoice.AUTO
    age_category: AgeCategory = AgeCategory.NORMAL
    residency: str = "resident"  # hard block NRI

    salary: SalaryDetails = Field(default_factory=SalaryDetails)
    hra: HRADetails = Field(default_factory=HRADetails)
    house_property: list[HouseProperty] = Field(default_factory=list)
    other_income: OtherIncome = Field(default_factory=OtherIncome)
    exempt_income: ExemptIncome = Field(default_factory=ExemptIncome)
    deductions: Deductions = Field(default_factory=Deductions)
    reinvestment_exemptions: ReinvestmentExemptions = Field(default_factory=ReinvestmentExemptions)
    loss_carry_forward: list[LossCarryForward] = Field(default_factory=list)
    advance_tax_paid: list[TaxPayment] = Field(default_factory=list)
    self_assessment_tax_paid: list[TaxPayment] = Field(default_factory=list)
    documents_uploaded: DocumentsUploaded = Field(default_factory=DocumentsUploaded)
    raw_data: dict = Field(default_factory=dict)
    computation_result: dict = Field(default_factory=dict)
    filing_date: Optional[date] = None

    class Settings:
        name = "tax_profiles"
        use_state_management = True
        indexes = [
            [("user_id", 1), ("financial_year", 1)],
        ]
