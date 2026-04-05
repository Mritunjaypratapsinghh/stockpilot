"""
Versioned Tax Rules Engine — Single source of truth for ALL Indian tax rules.

Every other module MUST import constants from here. No magic numbers anywhere else.
Supports multiple financial years for forward compatibility.

Reference: Income Tax Act 1961, Finance Act 2024 (Budget 2024), CBDT notifications.
FY 2025-26 = AY 2026-27.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

D = Decimal


# ---------------------------------------------------------------------------
# Slab definition
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Slab:
    """Single tax slab: income FROM (inclusive) to TO (exclusive), rate as decimal."""

    lower: int
    upper: Optional[int]  # None = no cap
    rate: Decimal


@dataclass(frozen=True)
class SurchargeSlabDef:
    lower: int
    upper: Optional[int]
    rate: Decimal


# ---------------------------------------------------------------------------
# Main rules container
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TaxRules:
    """Immutable tax rules for a given financial year."""

    financial_year: str  # e.g. "2025-26"
    assessment_year: str  # e.g. "2026-27"

    # --- Income Tax Slabs ---
    new_regime_slabs: tuple[Slab, ...]
    old_regime_slabs_normal: tuple[Slab, ...]  # age < 60
    old_regime_slabs_senior: tuple[Slab, ...]  # 60 <= age < 80
    old_regime_slabs_super_senior: tuple[Slab, ...]  # age >= 80

    # --- Standard Deduction (applied ONCE regardless of employers) ---
    standard_deduction_new: int
    standard_deduction_old: int

    # --- Capital Gains ---
    stcg_111a_rate: Decimal  # listed equity, STT paid
    ltcg_112a_rate: Decimal  # listed equity, STT paid
    ltcg_112a_exemption: int  # aggregate across all holdings
    ltcg_other_rate: Decimal  # unlisted, debt MF pre-2023 etc.
    debt_mf_no_ltcg_cutoff: date  # purchases ON or AFTER this → slab rate always

    # --- Holding Periods (months) ---
    holding_period_listed_equity: int
    holding_period_debt_mf: int  # pre-Apr-2023 only
    holding_period_unlisted: int
    holding_period_immovable: int

    # --- Grandfathering ---
    grandfathering_date: date  # 31-Jan-2018

    # --- Deduction Limits ---
    sec_80c_limit: int
    sec_80ccd_1b_limit: int
    sec_80ccd_2_rate_old: Decimal  # % of basic
    sec_80ccd_2_rate_new: Decimal  # % of basic
    sec_80d_self_normal: int
    sec_80d_self_senior: int
    sec_80d_parents_normal: int
    sec_80d_parents_senior: int
    sec_80d_max: int
    sec_80tta_limit: int  # non-senior, old regime only
    sec_80ttb_limit: int  # senior, old regime only
    sec_80e_limit: Optional[int]  # None = unlimited
    sec_24b_self_occupied: int
    sec_24b_let_out: Optional[int]  # None = unlimited
    sec_80gg_monthly: int  # when no HRA component
    family_pension_deduction: int  # new regime

    # Deductions allowed in new regime (whitelist)
    new_regime_allowed_deductions: frozenset[str]

    # --- Rebate u/s 87A ---
    rebate_new_limit: int  # max rebate amount
    rebate_new_threshold: int  # normal taxable income threshold
    rebate_old_limit: int
    rebate_old_threshold: int

    # --- Surcharge ---
    surcharge_old: tuple[SurchargeSlabDef, ...]
    surcharge_new: tuple[SurchargeSlabDef, ...]
    surcharge_cap_new: Decimal  # max surcharge rate for new regime
    surcharge_cap_cg: Decimal  # max surcharge rate on capital gains

    # --- Cess ---
    cess_rate: Decimal

    # --- Advance Tax ---
    advance_tax_threshold: int  # after TDS
    advance_tax_schedule: tuple[tuple[str, Decimal], ...]  # (date_label, cumulative %)
    interest_234b_rate: Decimal  # per month
    interest_234c_rate: Decimal  # per month
    interest_234c_months_q1_q3: int
    interest_234c_months_q4: int
    late_fee_234f: int
    late_fee_234f_low_income: int
    late_fee_234f_income_threshold: int

    # --- HRA ---
    hra_metro_cities: frozenset[str]
    hra_metro_rate: Decimal
    hra_non_metro_rate: Decimal
    hra_basic_rate: Decimal  # 10% of basic+DA

    # --- ITR-1 Eligibility ---
    itr1_income_limit: int
    itr1_ltcg_112a_limit: int
    itr1_agri_income_limit: int

    # --- Loss Set-off ---
    hp_loss_interhead_limit: int  # max ₹2L
    loss_carry_forward_years: int  # 8 AY

    # --- Interest on IT Refund ---
    interest_on_refund_section: str  # "244A"


# ---------------------------------------------------------------------------
# FY 2025-26 Rules (AY 2026-27)
# ---------------------------------------------------------------------------
_FY_2025_26 = TaxRules(
    financial_year="2025-26",
    assessment_year="2026-27",
    # ── New Regime 115BAC ──
    new_regime_slabs=(
        Slab(0, 400_000, D("0")),
        Slab(400_000, 800_000, D("0.05")),
        Slab(800_000, 1_200_000, D("0.10")),
        Slab(1_200_000, 1_600_000, D("0.15")),
        Slab(1_600_000, 2_000_000, D("0.20")),
        Slab(2_000_000, 2_400_000, D("0.25")),
        Slab(2_400_000, None, D("0.30")),
    ),
    # ── Old Regime — Normal (age < 60) ──
    old_regime_slabs_normal=(
        Slab(0, 250_000, D("0")),
        Slab(250_000, 500_000, D("0.05")),
        Slab(500_000, 1_000_000, D("0.20")),
        Slab(1_000_000, None, D("0.30")),
    ),
    # ── Old Regime — Senior (60-80) ──
    old_regime_slabs_senior=(
        Slab(0, 300_000, D("0")),
        Slab(300_000, 500_000, D("0.05")),
        Slab(500_000, 1_000_000, D("0.20")),
        Slab(1_000_000, None, D("0.30")),
    ),
    # ── Old Regime — Super Senior (80+) ──
    old_regime_slabs_super_senior=(
        Slab(0, 500_000, D("0")),
        Slab(500_000, 1_000_000, D("0.20")),
        Slab(1_000_000, None, D("0.30")),
    ),
    # ── Standard Deduction ──
    standard_deduction_new=75_000,
    standard_deduction_old=50_000,
    # ── Capital Gains ──
    stcg_111a_rate=D("0.20"),  # 20% (Budget 2024, up from 15%)
    ltcg_112a_rate=D("0.125"),  # 12.5% (Budget 2024, up from 10%)
    ltcg_112a_exemption=125_000,  # ₹1.25L aggregate
    ltcg_other_rate=D("0.125"),  # 12.5%, no indexation
    debt_mf_no_ltcg_cutoff=date(2023, 4, 1),  # ON or AFTER → slab rate always
    # ── Holding Periods (months) ──
    holding_period_listed_equity=12,
    holding_period_debt_mf=24,  # pre-Apr-2023 only
    holding_period_unlisted=24,
    holding_period_immovable=24,
    # ── Grandfathering ──
    grandfathering_date=date(2018, 1, 31),
    # ── Deduction Limits ──
    sec_80c_limit=150_000,
    sec_80ccd_1b_limit=50_000,
    sec_80ccd_2_rate_old=D("0.10"),  # 10% of basic (old)
    sec_80ccd_2_rate_new=D("0.14"),  # 14% of basic (new)
    sec_80d_self_normal=25_000,
    sec_80d_self_senior=50_000,
    sec_80d_parents_normal=25_000,
    sec_80d_parents_senior=50_000,
    sec_80d_max=100_000,
    sec_80tta_limit=10_000,
    sec_80ttb_limit=50_000,
    sec_80e_limit=None,  # unlimited
    sec_24b_self_occupied=200_000,
    sec_24b_let_out=None,  # unlimited
    sec_80gg_monthly=5_000,
    family_pension_deduction=25_000,
    new_regime_allowed_deductions=frozenset(
        {
            "standard_deduction",
            "sec_80ccd_2",
            "sec_80cch",
            "family_pension",
            "sec_24b_let_out",
        }
    ),
    # ── Rebate 87A ──
    rebate_new_limit=60_000,
    rebate_new_threshold=1_200_000,  # normal taxable income ≤ ₹12L
    rebate_old_limit=12_500,
    rebate_old_threshold=500_000,  # taxable income ≤ ₹5L
    # ── Surcharge ──
    surcharge_old=(
        SurchargeSlabDef(0, 5_000_000, D("0")),
        SurchargeSlabDef(5_000_000, 10_000_000, D("0.10")),
        SurchargeSlabDef(10_000_000, 20_000_000, D("0.15")),
        SurchargeSlabDef(20_000_000, 50_000_000, D("0.25")),
        SurchargeSlabDef(50_000_000, None, D("0.37")),
    ),
    surcharge_new=(
        SurchargeSlabDef(0, 5_000_000, D("0")),
        SurchargeSlabDef(5_000_000, 10_000_000, D("0.10")),
        SurchargeSlabDef(10_000_000, 20_000_000, D("0.15")),
        SurchargeSlabDef(20_000_000, None, D("0.25")),
    ),
    surcharge_cap_new=D("0.25"),
    surcharge_cap_cg=D("0.15"),
    # ── Cess ──
    cess_rate=D("0.04"),
    # ── Advance Tax ──
    advance_tax_threshold=10_000,
    advance_tax_schedule=(
        ("Jun 15", D("0.15")),
        ("Sep 15", D("0.45")),
        ("Dec 15", D("0.75")),
        ("Mar 15", D("1.00")),
    ),
    interest_234b_rate=D("0.01"),  # 1% per month
    interest_234c_rate=D("0.01"),  # 1% per month
    interest_234c_months_q1_q3=3,
    interest_234c_months_q4=1,
    late_fee_234f=5_000,
    late_fee_234f_low_income=1_000,
    late_fee_234f_income_threshold=500_000,
    # ── HRA ──
    hra_metro_cities=frozenset(
        {
            "delhi",
            "mumbai",
            "kolkata",
            "chennai",
            "bengaluru",
            "hyderabad",
            "pune",
            "ahmedabad",
            # Common aliases
            "bangalore",
            "calcutta",
            "bombay",
            "madras",
            "new delhi",
        }
    ),
    hra_metro_rate=D("0.50"),
    hra_non_metro_rate=D("0.40"),
    hra_basic_rate=D("0.10"),  # 10% of basic+DA
    # ── ITR-1 Eligibility ──
    itr1_income_limit=5_000_000,
    itr1_ltcg_112a_limit=125_000,
    itr1_agri_income_limit=5_000,
    # ── Loss Set-off ──
    hp_loss_interhead_limit=200_000,
    loss_carry_forward_years=8,
    # ── Other ──
    interest_on_refund_section="244A",
)

# ---------------------------------------------------------------------------
# Registry — add future FYs here
# ---------------------------------------------------------------------------
_RULES_REGISTRY: dict[str, TaxRules] = {
    "2025-26": _FY_2025_26,
}


def get_rules(financial_year: str = "2025-26") -> TaxRules:
    """Get tax rules for a financial year. Raises ValueError if unsupported."""
    rules = _RULES_REGISTRY.get(financial_year)
    if rules is None:
        supported = ", ".join(sorted(_RULES_REGISTRY.keys()))
        raise ValueError(f"Unsupported financial year: {financial_year}. Supported: {supported}")
    return rules


# ---------------------------------------------------------------------------
# Helper: compute tax from slabs
# ---------------------------------------------------------------------------
def compute_slab_tax(income: int, slabs: tuple[Slab, ...]) -> int:
    """Compute tax on income using given slab structure. Returns rounded int."""
    if income <= 0:
        return 0
    tax = D("0")
    for slab in slabs:
        if income <= slab.lower:
            break
        upper = slab.upper if slab.upper is not None else income
        taxable_in_slab = min(income, upper) - slab.lower
        tax += D(str(taxable_in_slab)) * slab.rate
    return int(tax)


def get_surcharge_rate(
    total_income: int,
    slabs: tuple[SurchargeSlabDef, ...],
) -> Decimal:
    """Get applicable surcharge rate for given total income."""
    rate = D("0")
    for s in slabs:
        upper = s.upper if s.upper is not None else total_income + 1
        if s.lower <= total_income < upper:
            rate = s.rate
            break
        if s.upper is None and total_income >= s.lower:
            rate = s.rate
    return rate


def compute_surcharge_with_marginal_relief(
    tax: int,
    total_income: int,
    slabs: tuple[SurchargeSlabDef, ...],
) -> int:
    """Compute surcharge with marginal relief at threshold boundaries."""
    if tax <= 0 or total_income <= 0:
        return 0

    rate = get_surcharge_rate(total_income, slabs)
    if rate == D("0"):
        return 0

    surcharge = int(D(str(tax)) * rate)

    # Marginal relief: find the threshold we just crossed
    for s in slabs:
        if s.rate == rate and s.lower > 0:
            threshold = s.lower
            prev_rate = D("0")
            for ps in slabs:
                if ps.upper == threshold:
                    prev_rate = ps.rate
                    break
            # Surcharge should not make total exceed income above threshold
            income_above = total_income - threshold
            surcharge_at_prev = int(D(str(tax)) * prev_rate)
            max_surcharge = surcharge_at_prev + income_above
            if surcharge > max_surcharge:
                surcharge = max_surcharge
            break

    return max(surcharge, 0)
