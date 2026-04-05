"""
Validation Engine — Hard blocks prevent filing, soft warnings advise.

Also includes ITR form recommendation (ITR-1 vs ITR-2).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .tax_rules import TaxRules, get_rules


@dataclass
class ValidationIssue:
    severity: str  # "hard_block" or "warning"
    category: str
    message: str
    guidance: str = ""


@dataclass
class ValidationResult:
    can_proceed: bool = True
    hard_blocks: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    itr_form: str = ""  # "ITR-1" or "ITR-2"
    itr_form_reasons: list[str] = field(default_factory=list)


def _block(result: ValidationResult, cat: str, msg: str, guidance: str = "") -> None:
    result.hard_blocks.append(ValidationIssue("hard_block", cat, msg, guidance))
    result.can_proceed = False


def _warn(result: ValidationResult, cat: str, msg: str, guidance: str = "") -> None:
    result.warnings.append(ValidationIssue("warning", cat, msg, guidance))


def validate(
    profile: dict,
    cg_summary: dict | None = None,
    pending_ais_count: int = 0,
    tds_claimed: int = 0,
    tds_in_26as: int = 0,
    rules: TaxRules | None = None,
) -> ValidationResult:
    """
    Run all validations. Profile is a dict matching TaxProfile fields.
    Returns hard blocks + warnings + ITR form recommendation.
    """
    rules = rules or get_rules()
    r = ValidationResult()
    regime = profile.get("regime_choice", "new")
    ded = profile.get("deductions", {})
    salary = profile.get("salary", {})
    other = profile.get("other_income", {})
    cg = cg_summary or {}

    # ── Deduction Limits ──
    if ded.get("sec_80c", 0) > rules.sec_80c_limit:
        _block(r, "deduction", f"80C exceeds ₹{rules.sec_80c_limit:,}")
    if ded.get("sec_80ccd_1b", 0) > rules.sec_80ccd_1b_limit:
        _block(r, "deduction", f"80CCD(1B) exceeds ₹{rules.sec_80ccd_1b_limit:,}")
    if ded.get("sec_80tta", 0) > rules.sec_80tta_limit:
        _block(r, "deduction", f"80TTA exceeds ₹{rules.sec_80tta_limit:,}")
    if ded.get("sec_80ttb", 0) > rules.sec_80ttb_limit:
        _block(r, "deduction", f"80TTB exceeds ₹{rules.sec_80ttb_limit:,}")
    if ded.get("sec_80tta", 0) > 0 and ded.get("sec_80ttb", 0) > 0:
        _block(r, "deduction", "80TTA and 80TTB are mutually exclusive. Claim only one.")

    # 80D limits
    age = profile.get("age_category", "normal")
    d_self_limit = rules.sec_80d_self_senior if age != "normal" else rules.sec_80d_self_normal
    if ded.get("sec_80d_self", 0) > d_self_limit:
        _block(r, "deduction", f"80D (self) exceeds ₹{d_self_limit:,}")
    total_80d = ded.get("sec_80d_self", 0) + ded.get("sec_80d_parents", 0)
    if total_80d > rules.sec_80d_max:
        _block(r, "deduction", f"Total 80D exceeds ₹{rules.sec_80d_max:,}")

    # New regime deduction violations
    if regime == "new":
        old_only = [
            "sec_80c",
            "sec_80ccd_1b",
            "sec_80d_self",
            "sec_80d_parents",
            "sec_80e",
            "sec_80g",
            "sec_80tta",
            "sec_80ttb",
        ]
        for key in old_only:
            if ded.get(key, 0) > 0:
                _block(r, "regime", f"{key} not allowed in new regime.", "Switch to old regime or remove deduction.")

    # ── Income Completeness ──
    if pending_ais_count > 0:
        _block(
            r,
            "reconciliation",
            f"{pending_ais_count} AIS items still pending.",
            "Resolve all AIS items before proceeding.",
        )

    if tds_claimed > tds_in_26as:
        _block(
            r,
            "tds",
            f"TDS claimed (₹{tds_claimed:,}) exceeds 26AS (₹{tds_in_26as:,}).",
            "You can only claim TDS that appears in Form 26AS.",
        )

    # ── Capital Gains ──
    stcg_equity = cg.get("stcg_111a", 0)
    ltcg_112a = cg.get("ltcg_112a_gross", 0)

    # ── HP ──
    hp_list = profile.get("house_property", [])
    hp_self_occ = [h for h in hp_list if h.get("hp_type") == "self_occupied"]
    if hp_self_occ:
        for h in hp_self_occ:
            if h.get("interest_paid", 0) > rules.sec_24b_self_occupied:
                _block(r, "hp", f"Self-occupied HP interest exceeds ₹{rules.sec_24b_self_occupied:,}")

    # ── Loss carry forward ──
    for loss in profile.get("loss_carry_forward", []):
        if not loss.get("filed_on_time", True):
            _block(
                r, "loss", f"Loss from AY {loss.get('from_ay')} cannot be carried forward — ITR was not filed on time."
            )

    # ── Soft Warnings ──
    if other.get("savings_interest", 0) == 0:
        _warn(r, "income", "No savings interest declared. Check AIS for bank interest.")

    hra = profile.get("hra", {})
    if hra.get("rent_paid", 0) > 100_000:
        _warn(r, "hra", "Rent > ₹1L/year — landlord PAN is mandatory for HRA claim.")

    if tds_in_26as > 0 and tds_claimed > tds_in_26as * 0.5:
        _warn(r, "refund", "High TDS refund (>50%). Ensure all income is declared to avoid scrutiny.")

    # ── ITR Form Recommendation ──
    total_income = (
        salary.get("gross", 0)
        + sum(h.get("rental_income", 0) for h in hp_list)
        + other.get("savings_interest", 0)
        + other.get("fd_interest", 0)
        + other.get("dividend_income_gross", 0)
    )

    itr1_eligible = True
    reasons = []

    if total_income > rules.itr1_income_limit:
        itr1_eligible = False
        reasons.append(f"Income > ₹{rules.itr1_income_limit:,}")
    if stcg_equity != 0:
        itr1_eligible = False
        reasons.append("Has STCG on equity (Section 111A)")
    if ltcg_112a > rules.itr1_ltcg_112a_limit:
        itr1_eligible = False
        reasons.append(f"LTCG 112A > ₹{rules.itr1_ltcg_112a_limit:,}")
    if cg.get("ltcg_other", 0) != 0 or cg.get("stcg_other", 0) != 0:
        itr1_eligible = False
        reasons.append("Has non-equity capital gains")
    if len(hp_list) > 1:
        itr1_eligible = False
        reasons.append("Multiple house properties")
    if any(x.get("remaining", 0) > 0 for x in profile.get("loss_carry_forward", [])):
        itr1_eligible = False
        reasons.append("Has carry forward losses")
    agri = profile.get("exempt_income", {}).get("agricultural_income", 0)
    if agri > rules.itr1_agri_income_limit:
        itr1_eligible = False
        reasons.append(f"Agricultural income > ₹{rules.itr1_agri_income_limit:,}")

    r.itr_form = "ITR-1" if itr1_eligible else "ITR-2"
    r.itr_form_reasons = reasons if reasons else ["Eligible for simpler ITR-1"]

    return r
