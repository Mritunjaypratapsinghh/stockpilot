"""
Three-Way Reconciliation Engine + Mandatory Checklist.

Cross-verifies AIS vs 26AS vs Form 16. Flags every mismatch.
Hard-blocks filing if ANY AIS line item is still "pending".
26AS is source of truth for TDS claims.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class MatchStatus(str, Enum):
    MATCHED = "matched"
    AMOUNT_MISMATCH = "amount_mismatch"
    MISSING_IN_26AS = "missing_in_26as"
    MISSING_IN_AIS = "missing_in_ais"
    EXTRA_IN_AIS = "extra_in_ais"


@dataclass
class ReconciliationItem:
    match_group_id: str = ""
    tan: str = ""
    section: str = ""
    deductor: str = ""
    form16_amount: int = 0
    ais_amount: int = 0
    form26as_amount: int = 0
    status: MatchStatus = MatchStatus.EXTRA_IN_AIS
    recommended_amount: int = 0  # always use 26AS
    action: str = ""


@dataclass
class IncomeReconciliationItem:
    income_type: str = ""
    form16_amount: int = 0
    ais_amount: int = 0
    declared_amount: int = 0
    status: str = "ok"
    action: str = ""


@dataclass
class ReconciliationReport:
    tds_items: list[ReconciliationItem] = field(default_factory=list)
    income_items: list[IncomeReconciliationItem] = field(default_factory=list)
    total_claimable_tds: int = 0
    total_tds_form16: int = 0
    total_tds_ais: int = 0
    total_tds_26as: int = 0
    has_mismatches: bool = False
    pending_ais_count: int = 0
    can_proceed: bool = False  # False if pending_ais_count > 0


# Tolerance for rounding differences
_TOLERANCE = 100


def _match_key(tan: str, section: str) -> str:
    return f"{tan.upper().strip()}|{section.strip()}"


def reconcile_tds(
    form16_entries: list[dict],
    ais_entries: list[dict],
    form26as_entries: list[dict],
) -> list[ReconciliationItem]:
    """
    Match TDS across three sources by TAN + section.
    form16_entries: [{tan, section, amount, deductor_name}]
    ais_entries: [{tan, section, amount, source_name}]
    form26as_entries: [{tan, section, amount, deductor_name}]
    """
    # Index by TAN+section
    f16 = {}
    for e in form16_entries:
        key = _match_key(e.get("tan", ""), e.get("section", ""))
        f16[key] = e

    ais = {}
    for e in ais_entries:
        key = _match_key(e.get("tan", ""), e.get("section", ""))
        ais[key] = e

    f26 = {}
    for e in form26as_entries:
        key = _match_key(e.get("tan", ""), e.get("section", ""))
        f26[key] = e

    all_keys = set(f16.keys()) | set(ais.keys()) | set(f26.keys())
    items = []

    for key in sorted(all_keys):
        parts = key.split("|")
        tan = parts[0] if parts else ""
        section = parts[1] if len(parts) > 1 else ""

        f16_amt = f16.get(key, {}).get("amount", 0)
        ais_amt = ais.get(key, {}).get("amount", 0)
        f26_amt = f26.get(key, {}).get("amount", 0)
        deductor = (
            f16.get(key, {}).get("deductor_name", "")
            or ais.get(key, {}).get("source_name", "")
            or f26.get(key, {}).get("deductor_name", "")
        )

        item = ReconciliationItem(
            match_group_id=str(uuid4())[:8],
            tan=tan,
            section=section,
            deductor=deductor,
            form16_amount=f16_amt,
            ais_amount=ais_amt,
            form26as_amount=f26_amt,
            recommended_amount=f26_amt,  # 26AS is truth
        )

        if key not in f26:
            item.status = MatchStatus.MISSING_IN_26AS
            item.recommended_amount = 0
            item.action = "CANNOT claim this TDS — not in Form 26AS. Contact deductor."
        elif key not in ais:
            item.status = MatchStatus.MISSING_IN_AIS
            item.action = "TDS in 26AS but not AIS. Still claimable (26AS is truth)."
        elif abs(f26_amt - ais_amt) <= _TOLERANCE and (not f16_amt or abs(f26_amt - f16_amt) <= _TOLERANCE):
            item.status = MatchStatus.MATCHED
            item.action = "All sources match."
        else:
            item.status = MatchStatus.AMOUNT_MISMATCH
            item.action = f"Amount mismatch. Using 26AS amount (₹{f26_amt:,}). Verify with deductor."

        items.append(item)

    return items


def reconcile_income(
    form16_salary: int = 0,
    ais_salary: int = 0,
    declared_salary: int = 0,
    ais_interest: int = 0,
    declared_interest: int = 0,
    ais_dividend_gross: int = 0,
    declared_dividend: int = 0,
) -> list[IncomeReconciliationItem]:
    """Reconcile income amounts across sources."""
    items = []

    # Salary
    if form16_salary or ais_salary:
        status = "ok"
        action = ""
        if form16_salary and ais_salary and abs(form16_salary - ais_salary) > 1000:
            status = "mismatch"
            action = f"Salary mismatch: Form16=₹{form16_salary:,} vs AIS=₹{ais_salary:,}. Use Form 16 amount."
        if declared_salary and form16_salary and abs(declared_salary - form16_salary) > 1000:
            status = "mismatch"
            action = f"Declared salary (₹{declared_salary:,}) differs from Form 16 (₹{form16_salary:,})."
        items.append(
            IncomeReconciliationItem(
                income_type="Salary",
                form16_amount=form16_salary,
                ais_amount=ais_salary,
                declared_amount=declared_salary,
                status=status,
                action=action,
            )
        )

    # Interest
    if ais_interest or declared_interest:
        status = "ok"
        action = ""
        if ais_interest > declared_interest + 1000:
            status = "under_reported"
            action = (
                f"AIS shows ₹{ais_interest:,} interest but you declared ₹{declared_interest:,}. Update to avoid notice."
            )
        items.append(
            IncomeReconciliationItem(
                income_type="Interest",
                ais_amount=ais_interest,
                declared_amount=declared_interest,
                status=status,
                action=action,
            )
        )

    # Dividends (must be GROSS)
    if ais_dividend_gross or declared_dividend:
        status = "ok"
        action = ""
        if ais_dividend_gross > declared_dividend + 1000:
            status = "under_reported"
            action = f"AIS shows ₹{ais_dividend_gross:,} gross dividend. Ensure you report GROSS amount, not net."
        items.append(
            IncomeReconciliationItem(
                income_type="Dividend (Gross)",
                ais_amount=ais_dividend_gross,
                declared_amount=declared_dividend,
                status=status,
                action=action,
            )
        )

    return items


def generate_report(
    tds_items: list[ReconciliationItem],
    income_items: list[IncomeReconciliationItem],
    pending_ais_count: int = 0,
) -> ReconciliationReport:
    """Generate full reconciliation report. Blocks if pending AIS items exist."""
    report = ReconciliationReport(
        tds_items=tds_items,
        income_items=income_items,
        total_claimable_tds=sum(i.recommended_amount for i in tds_items),
        total_tds_form16=sum(i.form16_amount for i in tds_items),
        total_tds_ais=sum(i.ais_amount for i in tds_items),
        total_tds_26as=sum(i.form26as_amount for i in tds_items),
        has_mismatches=any(i.status != MatchStatus.MATCHED for i in tds_items)
        or any(i.status != "ok" for i in income_items),
        pending_ais_count=pending_ais_count,
        can_proceed=pending_ais_count == 0,
    )
    return report
