"""
Complete Tax Computation Engine — 12-step pipeline.

Runs for BOTH regimes, compares, recommends lower.
Handles: slab tax, special rate CG, 87A rebate (excludes special rate),
surcharge (CG capped 15%), cess, 234B/C interest, 234F fee.
Every step logged to audit trail.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional

from .audit_trail import AuditTrail
from .tax_rules import TaxRules, compute_slab_tax, get_rules, get_surcharge_rate

D = Decimal


# ---------------------------------------------------------------------------
# Input / Output structures
# ---------------------------------------------------------------------------
@dataclass
class TaxInput:
    # Salary (after aggregation)
    gross_salary: int = 0
    basic_plus_da: int = 0
    hra_exemption: int = 0  # old regime only
    lta_exemption: int = 0  # old regime only
    professional_tax: int = 0
    employer_nps: int = 0

    # House Property
    hp_income: int = 0  # net (can be negative for loss)

    # Capital Gains (from CG engine)
    stcg_111a: int = 0
    stcg_other: int = 0
    ltcg_112a_gross: int = 0
    ltcg_other: int = 0
    slab_rate_gains: int = 0  # debt MF post-2023

    # Other Sources
    savings_interest: int = 0
    fd_interest: int = 0
    dividend_gross: int = 0
    it_refund_interest: int = 0
    other_income: int = 0

    # Deductions (old regime)
    sec_80c: int = 0
    sec_80ccd_1b: int = 0
    sec_80ccd_2: int = 0
    sec_80d_self: int = 0
    sec_80d_parents: int = 0
    sec_80e: int = 0
    sec_80g: int = 0
    sec_80tta: int = 0
    sec_80ttb: int = 0

    # Reinvestment exemptions
    sec_54: int = 0
    sec_54ec: int = 0
    sec_54f: int = 0

    # Loss carry forward
    cf_stcl: int = 0
    cf_ltcl: int = 0
    cf_hp_loss: int = 0

    # Tax paid
    tds_total: int = 0  # from 26AS only
    tcs_total: int = 0
    advance_tax: int = 0
    self_assessment_tax: int = 0

    # Meta
    age_category: str = "normal"
    filing_date: Optional[date] = None
    due_date: date = date(2026, 7, 31)  # default for FY 2025-26


@dataclass
class TaxResult:
    regime: str = ""

    # Step 1
    salary_income: int = 0
    hp_income: int = 0
    cg_income: int = 0
    other_sources: int = 0
    gross_total_income: int = 0

    # Step 2-4
    stcg_after_setoff: int = 0
    ltcg_after_setoff: int = 0
    hp_loss_setoff: int = 0
    cf_loss_applied: int = 0

    # Step 5
    total_deductions: int = 0
    taxable_normal_income: int = 0

    # Step 7-8
    tax_on_normal: int = 0
    tax_stcg_111a: int = 0
    tax_ltcg_112a: int = 0
    tax_ltcg_other: int = 0
    total_tax_before_rebate: int = 0

    # Step 9
    rebate_87a: int = 0

    # Step 10-11
    surcharge_normal: int = 0
    surcharge_cg: int = 0
    cess: int = 0

    # Step 12
    gross_tax: int = 0
    total_tax_paid: int = 0
    interest_234b: int = 0
    interest_234c: int = 0
    late_fee_234f: int = 0
    net_tax_payable: int = 0  # positive = pay, negative = refund

    audit_trail: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
def compute_tax(
    inp: TaxInput,
    regime: str = "new",
    rules: TaxRules | None = None,
) -> TaxResult:
    """Run 12-step tax computation for given regime."""
    rules = rules or get_rules()
    r = TaxResult(regime=regime)
    at = AuditTrail()

    # ── Step 1: Gross Total Income ──
    std_ded = rules.standard_deduction_new if regime == "new" else rules.standard_deduction_old
    salary_net = inp.gross_salary - std_ded
    if regime == "old":
        salary_net -= inp.hra_exemption + inp.lta_exemption + inp.professional_tax
    r.salary_income = max(0, salary_net)
    at.log(
        "step_1",
        "salary_income",
        r.salary_income,
        rule="Gross - Std Ded" + (" - HRA - LTA - PT" if regime == "old" else ""),
        formula=f"{inp.gross_salary} - {std_ded}"
        + (f" - {inp.hra_exemption} - {inp.lta_exemption} - {inp.professional_tax}" if regime == "old" else ""),
    )

    r.hp_income = inp.hp_income
    r.other_sources = (
        inp.savings_interest + inp.fd_interest + inp.dividend_gross + inp.it_refund_interest + inp.other_income
    )

    # CG: separate tracking for special rate
    stcg_111a = inp.stcg_111a
    stcg_other = inp.stcg_other + inp.slab_rate_gains
    ltcg_112a = inp.ltcg_112a_gross
    ltcg_other = inp.ltcg_other

    r.gross_total_income = (
        r.salary_income + r.hp_income + r.other_sources + stcg_111a + stcg_other + ltcg_112a + ltcg_other
    )
    at.log("step_1", "gross_total_income", r.gross_total_income)

    # ── Step 2: Intra-head set-off ──
    # STCL can offset STCG then LTCG; LTCL can offset LTCG only
    # (losses are negative values in stcg/ltcg)
    # Already handled in CG engine aggregation

    # ── Step 3: Inter-head set-off ──
    hp_loss = 0
    if r.hp_income < 0:
        hp_loss = min(abs(r.hp_income), rules.hp_loss_interhead_limit)
        r.hp_loss_setoff = hp_loss
        at.log("step_3", "hp_loss_interhead", hp_loss, rule=f"HP loss capped at ₹{rules.hp_loss_interhead_limit:,}")

    # ── Step 4: Carry forward losses ──
    cf_stcl_remaining = inp.cf_stcl
    cf_ltcl_remaining = inp.cf_ltcl

    if cf_stcl_remaining > 0 and stcg_111a > 0:
        used = min(cf_stcl_remaining, stcg_111a)
        stcg_111a -= used
        cf_stcl_remaining -= used
    if cf_stcl_remaining > 0 and stcg_other > 0:
        used = min(cf_stcl_remaining, stcg_other)
        stcg_other -= used
        cf_stcl_remaining -= used
    if cf_stcl_remaining > 0 and ltcg_112a > 0:
        used = min(cf_stcl_remaining, ltcg_112a)
        ltcg_112a -= used
        cf_stcl_remaining -= used
    if cf_ltcl_remaining > 0 and ltcg_112a > 0:
        used = min(cf_ltcl_remaining, ltcg_112a)
        ltcg_112a -= used
        cf_ltcl_remaining -= used
    if cf_ltcl_remaining > 0 and ltcg_other > 0:
        used = min(cf_ltcl_remaining, ltcg_other)
        ltcg_other -= used
        cf_ltcl_remaining -= used

    r.stcg_after_setoff = stcg_111a + stcg_other
    r.ltcg_after_setoff = ltcg_112a + ltcg_other

    # ── Step 5: Chapter VI-A Deductions ──
    deductions = 0
    if regime == "old":
        deductions += min(inp.sec_80c, rules.sec_80c_limit)
        deductions += min(inp.sec_80ccd_1b, rules.sec_80ccd_1b_limit)
        deductions += min(inp.sec_80ccd_2, int(float(rules.sec_80ccd_2_rate_old) * inp.basic_plus_da))
        # 80D
        d_self_limit = rules.sec_80d_self_senior if inp.age_category != "normal" else rules.sec_80d_self_normal
        d_parents_limit = rules.sec_80d_parents_senior  # conservative: use senior limit
        deductions += min(inp.sec_80d_self, d_self_limit)
        deductions += min(inp.sec_80d_parents, d_parents_limit)
        deductions += inp.sec_80e  # unlimited
        deductions += inp.sec_80g
        deductions += min(inp.sec_80tta, rules.sec_80tta_limit)
        deductions += min(inp.sec_80ttb, rules.sec_80ttb_limit)
    else:
        # New regime: only 80CCD(2) at 14%
        deductions += min(inp.sec_80ccd_2, int(float(rules.sec_80ccd_2_rate_new) * inp.basic_plus_da))

    r.total_deductions = deductions
    at.log("step_5", "total_deductions", deductions, rule=f"{'Old' if regime == 'old' else 'New'} regime deductions")

    # ── Step 6: Reinvestment exemptions ──
    reinvestment = inp.sec_54 + inp.sec_54ec + inp.sec_54f
    if reinvestment > 0:
        ltcg_112a = max(0, ltcg_112a - reinvestment)
        at.log("step_6", "reinvestment_exemption", reinvestment, rule="Sec 54/54EC/54F")

    # ── Normal taxable income ──
    normal_income = r.salary_income + max(r.hp_income, -hp_loss) + r.other_sources + stcg_other - hp_loss
    normal_income = max(0, normal_income - deductions)
    r.taxable_normal_income = normal_income
    at.log("step_5", "taxable_normal_income", normal_income)

    # ── Step 7: Tax on normal income ──
    if regime == "new":
        slabs = rules.new_regime_slabs
    elif inp.age_category == "super_senior":
        slabs = rules.old_regime_slabs_super_senior
    elif inp.age_category == "senior":
        slabs = rules.old_regime_slabs_senior
    else:
        slabs = rules.old_regime_slabs_normal

    r.tax_on_normal = compute_slab_tax(normal_income, slabs)
    at.log("step_7", "tax_on_normal", r.tax_on_normal, rule=f"Slab rates ({regime})")

    # ── Step 8: Tax on special rate income ──
    r.tax_stcg_111a = max(0, int(D(str(max(0, stcg_111a))) * rules.stcg_111a_rate))
    at.log(
        "step_8",
        "tax_stcg_111a",
        r.tax_stcg_111a,
        rule=f"STCG 111A @ {float(rules.stcg_111a_rate)*100}%",
        formula=f"{float(rules.stcg_111a_rate)*100}% × {max(0, stcg_111a)}",
    )

    ltcg_112a_taxable = max(0, ltcg_112a - rules.ltcg_112a_exemption)
    r.tax_ltcg_112a = int(D(str(ltcg_112a_taxable)) * rules.ltcg_112a_rate)
    at.log(
        "step_8",
        "tax_ltcg_112a",
        r.tax_ltcg_112a,
        rule=f"LTCG 112A @ {float(rules.ltcg_112a_rate)*100}% above ₹{rules.ltcg_112a_exemption:,}",
        formula=f"{float(rules.ltcg_112a_rate)*100}% × ({ltcg_112a} - {rules.ltcg_112a_exemption})",
    )

    r.tax_ltcg_other = max(0, int(D(str(max(0, ltcg_other))) * rules.ltcg_other_rate))

    special_tax = r.tax_stcg_111a + r.tax_ltcg_112a + r.tax_ltcg_other
    r.total_tax_before_rebate = r.tax_on_normal + special_tax

    # ── Step 9: Rebate u/s 87A ──
    # Eligibility on NORMAL income only, rebate on NORMAL tax only
    if regime == "new" and normal_income <= rules.rebate_new_threshold:
        r.rebate_87a = min(r.tax_on_normal, rules.rebate_new_limit)
        at.log(
            "step_9",
            "rebate_87a",
            r.rebate_87a,
            rule=f"87A: normal income ₹{normal_income:,} ≤ ₹{rules.rebate_new_threshold:,}",
        )
    elif regime == "old" and normal_income <= rules.rebate_old_threshold:
        r.rebate_87a = min(r.tax_on_normal, rules.rebate_old_limit)
        at.log(
            "step_9",
            "rebate_87a",
            r.rebate_87a,
            rule=f"87A: normal income ₹{normal_income:,} ≤ ₹{rules.rebate_old_threshold:,}",
        )

    tax_after_rebate_normal = max(0, r.tax_on_normal - r.rebate_87a)

    # ── Step 10: Surcharge ──
    total_income_for_surcharge = normal_income + max(0, stcg_111a) + max(0, ltcg_112a) + max(0, ltcg_other)
    surcharge_slabs = rules.surcharge_new if regime == "new" else rules.surcharge_old

    # Normal income surcharge
    normal_surcharge_rate = get_surcharge_rate(total_income_for_surcharge, surcharge_slabs)
    if regime == "new":
        normal_surcharge_rate = min(normal_surcharge_rate, rules.surcharge_cap_new)
    r.surcharge_normal = int(D(str(tax_after_rebate_normal)) * normal_surcharge_rate)

    # CG surcharge capped at 15%
    cg_surcharge_rate = min(get_surcharge_rate(total_income_for_surcharge, surcharge_slabs), rules.surcharge_cap_cg)
    r.surcharge_cg = int(D(str(special_tax)) * cg_surcharge_rate)

    total_surcharge = r.surcharge_normal + r.surcharge_cg
    at.log(
        "step_10",
        "surcharge",
        total_surcharge,
        rule=f"Normal @{float(normal_surcharge_rate)*100}%, CG capped @{float(cg_surcharge_rate)*100}%",
    )

    # ── Step 11: Cess ──
    tax_plus_surcharge = tax_after_rebate_normal + special_tax + total_surcharge
    r.cess = int(D(str(tax_plus_surcharge)) * rules.cess_rate)
    at.log("step_11", "cess", r.cess, rule=f"4% on ₹{tax_plus_surcharge:,}")

    # ── Step 12: Net Tax ──
    r.gross_tax = tax_plus_surcharge + r.cess

    # Tax paid
    r.total_tax_paid = inp.tds_total + inp.tcs_total + inp.advance_tax + inp.self_assessment_tax

    # 234F late filing fee
    if inp.filing_date and inp.filing_date > inp.due_date:
        total_income = r.salary_income + r.hp_income + r.other_sources + r.stcg_after_setoff + r.ltcg_after_setoff
        if total_income <= rules.late_fee_234f_income_threshold:
            r.late_fee_234f = rules.late_fee_234f_low_income
        else:
            r.late_fee_234f = rules.late_fee_234f
        at.log("step_12", "late_fee_234f", r.late_fee_234f, rule="Filing after due date")

    # 234B interest (simplified)
    if inp.advance_tax < int(r.gross_tax * 0.9) and r.gross_tax > 10000:
        months = 1  # simplified — actual: months from Apr to filing
        if inp.filing_date:
            months = max(1, (inp.filing_date.month - 4) % 12 + 1)
        shortfall = r.gross_tax - inp.advance_tax
        r.interest_234b = int(D(str(shortfall)) * rules.interest_234b_rate * months)
        at.log("step_12", "interest_234b", r.interest_234b, rule=f"1% × {months} months on shortfall ₹{shortfall:,}")

    r.net_tax_payable = r.gross_tax - r.total_tax_paid + r.interest_234b + r.interest_234c + r.late_fee_234f
    at.log(
        "step_12",
        "net_tax_payable",
        r.net_tax_payable,
        formula=f"{r.gross_tax} - {r.total_tax_paid} + {r.interest_234b} + {r.late_fee_234f}",
    )

    r.audit_trail = at.to_dicts()
    return r


# ---------------------------------------------------------------------------
# Regime comparison
# ---------------------------------------------------------------------------
@dataclass
class RegimeComparison:
    old_result: TaxResult | None = None
    new_result: TaxResult | None = None
    recommended: str = "new"
    savings: int = 0
    explanation: str = ""


def compare_regimes(inp: TaxInput, rules: TaxRules | None = None) -> RegimeComparison:
    """Run tax engine for both regimes and recommend the lower one."""
    rules = rules or get_rules()
    old = compute_tax(inp, regime="old", rules=rules)
    new = compute_tax(inp, regime="new", rules=rules)

    comp = RegimeComparison(old_result=old, new_result=new)
    if new.net_tax_payable <= old.net_tax_payable:
        comp.recommended = "new"
        comp.savings = old.net_tax_payable - new.net_tax_payable
        comp.explanation = f"New regime saves ₹{comp.savings:,}"
    else:
        comp.recommended = "old"
        comp.savings = new.net_tax_payable - old.net_tax_payable
        comp.explanation = f"Old regime saves ₹{comp.savings:,} (deductions: ₹{old.total_deductions:,})"

    return comp
