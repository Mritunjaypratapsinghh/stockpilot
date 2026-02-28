"""Calculator schemas"""

from typing import Literal

from pydantic import BaseModel, Field


class AssetAllocationInput(BaseModel):
    age: int = Field(30, ge=18, le=80)
    risk_appetite: Literal["very_low", "low", "moderate", "high", "very_high"] = "moderate"
    horizon: int = Field(10, ge=1, le=40)


class SIPStepupInput(BaseModel):
    monthly_amount: float = Field(10000, gt=0)
    expected_return: float = Field(12, ge=1, le=30)
    years: int = Field(10, ge=1, le=40)
    annual_stepup: float = Field(10, ge=0, le=50)


class RetirementInput(BaseModel):
    current_age: int = Field(30, ge=18, le=70)
    retirement_age: int = Field(60, ge=40, le=80)
    monthly_expenses: float = Field(50000, gt=0)
    current_savings: float = Field(0, ge=0)
    inflation: float = Field(6, ge=0, le=15)
    expected_return: float = Field(10, ge=1, le=20)


class SWPInput(BaseModel):
    corpus: float = Field(5000000, gt=0)
    monthly_withdrawal: float = Field(30000, gt=0)
    annual_stepup: float = Field(0, ge=0, le=20)
    expected_return: float = Field(10, ge=1, le=20)
    years: int = Field(20, ge=1, le=50)


class LoanInput(BaseModel):
    principal: float = Field(5000000, gt=0)
    interest_rate: float = Field(8.5, ge=1, le=20)
    tenure_years: int = Field(25, ge=1, le=40)
    stepup_pct: float = Field(7.5, ge=0, le=30)
    extra_emis: int = Field(1, ge=0, le=12)


class SalaryTaxInput(BaseModel):
    annual_ctc: float = Field(1200000, gt=0)
    pf_type: Literal["capped", "full"] = "capped"
    regime: Literal["new", "old"] = "new"
    vpf: float = Field(0, ge=0)


class CashflowInput(BaseModel):
    inflows: list[dict] = Field(default_factory=lambda: [{"name": "Salary", "amount": 80000}])
    outflows: list[dict] = Field(default_factory=lambda: [{"name": "Rent", "amount": 25000}])
