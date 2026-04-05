"""Pydantic schemas for ITR API requests/responses."""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel


# ── Request Schemas ──
class TaxProfileCreate(BaseModel):
    financial_year: str = "2025-26"
    regime_choice: str = "auto"
    age_category: str = "normal"
    residency: str = "resident"


class SalaryInput(BaseModel):
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


class HRAInput(BaseModel):
    rent_paid: int = 0
    city_name: str = ""
    months_stayed: int = 12


class HousePropertyInput(BaseModel):
    hp_type: str = "self_occupied"
    rental_income: int = 0
    municipal_tax: int = 0
    interest_paid: int = 0


class OtherIncomeInput(BaseModel):
    savings_interest: int = 0
    fd_interest: int = 0
    dividend_income_gross: int = 0
    interest_on_it_refund: int = 0
    other: int = 0


class DeductionsInput(BaseModel):
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


class LossCarryForwardInput(BaseModel):
    from_ay: str
    loss_type: str
    original: int = 0
    remaining: int = 0
    expires_ay: str = ""
    filed_on_time: bool = True


class TaxProfileUpdate(BaseModel):
    regime_choice: Optional[str] = None
    age_category: Optional[str] = None
    salary: Optional[SalaryInput] = None
    hra: Optional[HRAInput] = None
    house_property: Optional[list[HousePropertyInput]] = None
    other_income: Optional[OtherIncomeInput] = None
    deductions: Optional[DeductionsInput] = None
    loss_carry_forward: Optional[list[LossCarryForwardInput]] = None
    filing_date: Optional[date] = None


class AISItemResolve(BaseModel):
    status: str  # accepted / corrected / disputed
    user_value: Optional[int] = None
    dispute_reason: str = ""
    is_exempt: bool = False


# ── Response Schemas ──
class ScopeCheckResponse(BaseModel):
    supported: bool
    blockers: list[dict] = []


class ReconciliationResponse(BaseModel):
    tds_items: list[dict] = []
    income_items: list[dict] = []
    total_claimable_tds: int = 0
    has_mismatches: bool = False
    pending_ais_count: int = 0
    can_proceed: bool = False


class ComputationResponse(BaseModel):
    regime: str = ""
    gross_total_income: int = 0
    total_deductions: int = 0
    taxable_normal_income: int = 0
    tax_on_normal: int = 0
    tax_stcg_111a: int = 0
    tax_ltcg_112a: int = 0
    rebate_87a: int = 0
    surcharge_normal: int = 0
    surcharge_cg: int = 0
    cess: int = 0
    gross_tax: int = 0
    total_tax_paid: int = 0
    net_tax_payable: int = 0
    audit_trail: list[dict] = []


class RegimeComparisonResponse(BaseModel):
    recommended: str = ""
    savings: int = 0
    explanation: str = ""
    old_result: dict = {}
    new_result: dict = {}


class ValidationResponse(BaseModel):
    can_proceed: bool = True
    hard_blocks: list[dict] = []
    warnings: list[dict] = []
    itr_form: str = ""
    itr_form_reasons: list[str] = []


class TaxCalendarEntry(BaseModel):
    date: str
    description: str
    category: str


class TaxCalendarResponse(BaseModel):
    deadlines: list[TaxCalendarEntry] = []
    financial_year: str = "2025-26"
