"""
ITR API Routes — All endpoints for the ITR filing system.
"""

from __future__ import annotations

import tempfile
from dataclasses import asdict
from typing import Optional

from app.models.documents import (
    AISLineItem,
    AISStatus,
    TaxAuditTrail,
    TaxProfile,
    TDSEntry,
)
from app.services.itr.capital_gains import compute_capital_gains
from app.services.itr.hra_calculator import compute_hra
from app.services.itr.itr_json_generator import export_json, generate_itr_json
from app.services.itr.optimizer import optimize
from app.services.itr.parsers.ais_parser import parse_ais
from app.services.itr.parsers.form16_parser import parse_form16
from app.services.itr.parsers.form26as_parser import parse_form26as
from app.services.itr.reconciliation import generate_report, reconcile_tds
from app.services.itr.scope_checker import check_scope
from app.services.itr.tax_engine import TaxInput, compare_regimes, compute_tax
from app.services.itr.tax_rules import get_rules
from app.services.itr.validator import validate
from beanie import PydanticObjectId
from fastapi import APIRouter, File, HTTPException, UploadFile

from .schemas import (
    AISItemResolve,
    ComputationResponse,
    ReconciliationResponse,
    RegimeComparisonResponse,
    ScopeCheckRequest,
    ScopeCheckResponse,
    TaxCalendarResponse,
    TaxProfileCreate,
    TaxProfileUpdate,
    ValidationResponse,
)

router = APIRouter()


async def _get_profile(user_id: str, fy: str) -> TaxProfile:
    profile = await TaxProfile.find_one(
        TaxProfile.user_id == PydanticObjectId(user_id),
        TaxProfile.financial_year == fy,
    )
    if not profile:
        raise HTTPException(404, f"Tax profile not found for FY {fy}")
    return profile


# ── Profile ──
@router.post("/profile")
async def create_or_update_profile(user_id: str, data: TaxProfileCreate):
    existing = await TaxProfile.find_one(
        TaxProfile.user_id == PydanticObjectId(user_id),
        TaxProfile.financial_year == data.financial_year,
    )
    if existing:
        existing.regime_choice = data.regime_choice
        existing.age_category = data.age_category
        existing.residency = data.residency
        await existing.save()
        return existing.dict()

    profile = TaxProfile(
        user_id=PydanticObjectId(user_id),
        financial_year=data.financial_year,
        assessment_year=(
            data.financial_year.split("-")[0] + "-" + str(int(data.financial_year.split("-")[0]) + 1)[-2:]
            if "-" in data.financial_year
            else ""
        ),
        regime_choice=data.regime_choice,
        age_category=data.age_category,
        residency=data.residency,
    )
    await profile.insert()
    return profile.dict()


@router.get("/profile/{fy}")
async def get_profile(user_id: str, fy: str):
    return (await _get_profile(user_id, fy)).dict()


@router.put("/profile/{fy}")
async def update_profile(user_id: str, fy: str, data: TaxProfileUpdate):
    profile = await _get_profile(user_id, fy)
    update_data = data.dict(exclude_none=True)
    for key, value in update_data.items():
        if isinstance(value, dict):
            existing = getattr(profile, key, None)
            if existing and hasattr(existing, "__dict__"):
                for k, v in value.items():
                    setattr(existing, k, v)
            else:
                setattr(profile, key, value)
        else:
            setattr(profile, key, value)
    await profile.save()
    return profile.dict()


# ── Document Upload ──
async def _save_upload(upload: UploadFile) -> str:
    suffix = "." + (upload.filename or "file").split(".")[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(await upload.read())
        return f.name


@router.post("/upload/form16")
async def upload_form16(user_id: str, fy: str, file: UploadFile = File(...), password: Optional[str] = None):
    path = await _save_upload(file)
    result = parse_form16(path, password)
    return asdict(result)


@router.post("/upload/ais")
async def upload_ais(user_id: str, fy: str, file: UploadFile = File(...), password: Optional[str] = None):
    path = await _save_upload(file)
    result = parse_ais(path, password)

    # Create AISLineItem documents
    for entry in result.entries:
        item = AISLineItem(
            user_id=PydanticObjectId(user_id),
            financial_year=fy,
            category=entry.category,
            info_code=entry.info_code,
            description=entry.description,
            source_name=entry.source_name,
            source_tan=entry.source_tan,
            reported_value=entry.reported_value,
            modified_value=entry.modified_value,
            is_exempt=entry.is_exempt,
        )
        await item.insert()

    return asdict(result)


@router.post("/upload/form26as")
async def upload_form26as(user_id: str, fy: str, file: UploadFile = File(...), password: Optional[str] = None):
    path = await _save_upload(file)
    result = parse_form26as(path, password)

    # Create TDSEntry documents
    for entry in result.tds_entries:
        tds = TDSEntry(
            user_id=PydanticObjectId(user_id),
            financial_year=fy,
            source="form26as",
            tan=entry.tan,
            deductor_name=entry.deductor_name,
            section=entry.section,
            amount=entry.amount,
        )
        await tds.insert()

    return asdict(result)


# ── Scope Check ──
@router.post("/scope-check", response_model=ScopeCheckResponse)
async def scope_check(data: ScopeCheckRequest, user_id: str = "me"):
    result = check_scope(
        transactions=data.transactions,
        residency=data.residency,
        ais_entries=data.ais_entries,
        has_foreign_income=data.has_foreign_income,
        has_foreign_assets=data.has_foreign_assets,
    )
    return {"supported": result.supported, "blockers": [asdict(b) for b in result.blockers]}


# ── Reconciliation ──
@router.get("/reconciliation/{fy}", response_model=ReconciliationResponse)
async def get_reconciliation(user_id: str, fy: str):
    uid = PydanticObjectId(user_id)
    ais_items = await AISLineItem.find(AISLineItem.user_id == uid, AISLineItem.financial_year == fy).to_list()
    tds_entries = await TDSEntry.find(TDSEntry.user_id == uid, TDSEntry.financial_year == fy).to_list()

    ais_tds = [
        {"tan": i.source_tan, "section": i.info_code, "amount": i.reported_value, "source_name": i.source_name}
        for i in ais_items
        if i.category == "TDS"
    ]
    f26_tds = [
        {"tan": t.tan, "section": t.section, "amount": t.amount, "deductor_name": t.deductor_name}
        for t in tds_entries
        if t.source == "form26as"
    ]

    tds_items = reconcile_tds([], ais_tds, f26_tds)
    pending = sum(1 for i in ais_items if i.status == AISStatus.PENDING)
    report = generate_report(tds_items, [], pending)

    return {
        "tds_items": [asdict(i) for i in report.tds_items],
        "income_items": [asdict(i) for i in report.income_items],
        "total_claimable_tds": report.total_claimable_tds,
        "has_mismatches": report.has_mismatches,
        "pending_ais_count": report.pending_ais_count,
        "can_proceed": report.can_proceed,
    }


# ── AIS Checklist ──
@router.get("/checklist/{fy}")
async def get_checklist(user_id: str, fy: str):
    items = await AISLineItem.find(
        AISLineItem.user_id == PydanticObjectId(user_id),
        AISLineItem.financial_year == fy,
    ).to_list()
    total = len(items)
    resolved = sum(1 for i in items if i.status != AISStatus.PENDING)
    return {
        "items": [i.dict() for i in items],
        "total": total,
        "resolved": resolved,
        "pending": total - resolved,
        "progress": resolved / total if total else 1.0,
        "can_proceed": total == resolved,
    }


@router.put("/ais-item/{item_id}")
async def resolve_ais_item(item_id: str, data: AISItemResolve):
    item = await AISLineItem.get(PydanticObjectId(item_id))
    if not item:
        raise HTTPException(404, "AIS item not found")
    item.status = data.status
    item.user_value = data.user_value
    item.dispute_reason = data.dispute_reason
    item.is_exempt = data.is_exempt
    await item.save()
    return item.dict()


# ── Capital Gains ──
@router.get("/capital-gains/{fy}")
async def get_capital_gains(user_id: str, fy: str):
    # In production, fetch lots/sells from portfolio transactions
    # For now return empty summary
    summary = compute_capital_gains([], [])
    return asdict(summary)


# ── HRA ──
@router.get("/hra/{fy}")
async def get_hra(user_id: str, fy: str):
    profile = await _get_profile(user_id, fy)
    result = compute_hra(
        basic_plus_da=profile.salary.basic + profile.salary.da,
        hra_received=profile.salary.hra_received,
        rent_paid=profile.hra.rent_paid,
        city_name=profile.hra.city_name,
        months=profile.hra.months_stayed,
        regime=profile.regime_choice,
    )
    return asdict(result)


# ── Tax Computation ──
@router.post("/compute/{fy}", response_model=ComputationResponse)
async def compute(user_id: str, fy: str, regime: str = "new"):
    profile = await _get_profile(user_id, fy)
    inp = _build_tax_input(profile)
    result = compute_tax(inp, regime=regime)
    # Cache result
    profile.computation_result = asdict(result)
    await profile.save()
    return asdict(result)


# ── Regime Comparison ──
@router.get("/comparison/{fy}", response_model=RegimeComparisonResponse)
async def get_comparison(user_id: str, fy: str):
    profile = await _get_profile(user_id, fy)
    inp = _build_tax_input(profile)
    comp = compare_regimes(inp)
    return {
        "recommended": comp.recommended,
        "savings": comp.savings,
        "explanation": comp.explanation,
        "old_result": asdict(comp.old_result) if comp.old_result else {},
        "new_result": asdict(comp.new_result) if comp.new_result else {},
    }


# ── Validation ──
@router.post("/validate/{fy}", response_model=ValidationResponse)
async def validate_profile(user_id: str, fy: str):
    profile = await _get_profile(user_id, fy)
    uid = PydanticObjectId(user_id)
    pending = await AISLineItem.find(
        AISLineItem.user_id == uid,
        AISLineItem.financial_year == fy,
        AISLineItem.status == AISStatus.PENDING,
    ).count()
    tds_26as = await TDSEntry.find(
        TDSEntry.user_id == uid,
        TDSEntry.financial_year == fy,
        TDSEntry.source == "form26as",
    ).to_list()
    tds_total = sum(t.amount for t in tds_26as)

    result = validate(
        profile=profile.dict(),
        pending_ais_count=pending,
        tds_in_26as=tds_total,
    )
    return {
        "can_proceed": result.can_proceed,
        "hard_blocks": [asdict(b) for b in result.hard_blocks],
        "warnings": [asdict(w) for w in result.warnings],
        "itr_form": result.itr_form,
        "itr_form_reasons": result.itr_form_reasons,
    }


# ── Form Recommendation ──
@router.get("/form-recommendation/{fy}")
async def form_recommendation(user_id: str, fy: str):
    profile = await _get_profile(user_id, fy)
    result = validate(profile=profile.dict())
    return {"itr_form": result.itr_form, "reasons": result.itr_form_reasons}


# ── Schedule 112A ──
@router.get("/schedule-112a/{fy}")
async def schedule_112a(user_id: str, fy: str):
    summary = compute_capital_gains([], [])
    return {"entries": [asdict(e) for e in summary.schedule_112a]}


# ── Export ITR JSON ──
@router.post("/export/{fy}")
async def export_itr(user_id: str, fy: str):
    profile = await _get_profile(user_id, fy)
    # Run validation first
    uid = PydanticObjectId(user_id)
    pending = await AISLineItem.find(
        AISLineItem.user_id == uid,
        AISLineItem.financial_year == fy,
        AISLineItem.status == AISStatus.PENDING,
    ).count()
    if pending > 0:
        raise HTTPException(400, f"{pending} AIS items still pending. Resolve all before exporting.")

    val = validate(profile=profile.dict(), pending_ais_count=pending)
    if not val.can_proceed:
        blocks = [b.message for b in val.hard_blocks]
        raise HTTPException(400, f"Validation failed: {'; '.join(blocks)}")

    computation = profile.computation_result or {}
    itr_data = generate_itr_json(profile.dict(), computation, itr_form=val.itr_form)
    return {"json": itr_data, "json_string": export_json(itr_data)}


# ── Audit Trail ──
@router.get("/audit-trail/{fy}")
async def get_audit_trail(user_id: str, fy: str):
    entries = (
        await TaxAuditTrail.find(
            TaxAuditTrail.user_id == PydanticObjectId(user_id),
            TaxAuditTrail.financial_year == fy,
        )
        .sort("+timestamp")
        .to_list()
    )
    return [e.dict() for e in entries]


# ── Optimization ──
@router.get("/optimize/{fy}")
async def get_optimization(user_id: str, fy: str):
    profile = await _get_profile(user_id, fy)
    inp = _build_tax_input(profile)
    result = optimize(inp)
    return {
        "recommended_regime": result.comparison.recommended if result.comparison else "new",
        "savings": result.comparison.savings if result.comparison else 0,
        "suggestions": [asdict(s) for s in result.suggestions],
        "total_potential_saving": result.total_potential_saving,
    }


# ── Advance Tax ──
@router.get("/advance-tax/{fy}")
async def advance_tax(user_id: str, fy: str):
    profile = await _get_profile(user_id, fy)
    rules = get_rules(fy)
    inp = _build_tax_input(profile)
    result = compute_tax(inp, regime=profile.regime_choice or "new")

    if result.gross_tax <= rules.advance_tax_threshold:
        return {
            "applicable": False,
            "message": f"Tax liability ≤ ₹{rules.advance_tax_threshold:,}. No advance tax needed.",
        }

    schedule = []
    for label, pct in rules.advance_tax_schedule:
        due = int(result.gross_tax * float(pct))
        schedule.append({"due_date": label, "cumulative_pct": float(pct) * 100, "amount_due": due})

    return {
        "applicable": True,
        "total_liability": result.gross_tax,
        "tds_credit": inp.tds_total,
        "net_payable": result.gross_tax - inp.tds_total,
        "schedule": schedule,
    }


# ── Tax Calendar ──
@router.get("/tax-calendar", response_model=TaxCalendarResponse)
async def tax_calendar(fy: str = "2025-26"):
    return {
        "financial_year": fy,
        "deadlines": [
            {"date": "2025-06-15", "description": "Advance Tax Q1 (15%)", "category": "advance_tax"},
            {"date": "2025-09-15", "description": "Advance Tax Q2 (45%)", "category": "advance_tax"},
            {"date": "2025-12-15", "description": "Advance Tax Q3 (75%)", "category": "advance_tax"},
            {"date": "2026-03-15", "description": "Advance Tax Q4 (100%)", "category": "advance_tax"},
            {"date": "2026-07-31", "description": "ITR Filing Deadline (non-audit)", "category": "filing"},
            {"date": "2026-12-31", "description": "Belated/Revised Return Deadline", "category": "filing"},
            {"date": "2027-03-31", "description": "Updated Return (ITR-U) Deadline", "category": "filing"},
        ],
    }


# ── Helper ──
def _build_tax_input(profile: TaxProfile) -> TaxInput:
    """Convert TaxProfile to TaxInput for computation."""
    sal = profile.salary
    ded = profile.deductions
    oth = profile.other_income
    hp_income = 0
    for hp in profile.house_property:
        if hp.hp_type == "let_out":
            net = hp.rental_income - hp.municipal_tax
            net = int(net * 0.7) - hp.interest_paid  # 30% standard deduction
            hp_income += net
        else:
            hp_income -= min(hp.interest_paid, 200_000)

    return TaxInput(
        gross_salary=sal.gross,
        basic_plus_da=sal.basic + sal.da,
        professional_tax=sal.professional_tax,
        employer_nps=sal.employer_nps,
        hp_income=hp_income,
        savings_interest=oth.savings_interest,
        fd_interest=oth.fd_interest,
        dividend_gross=oth.dividend_income_gross,
        it_refund_interest=oth.interest_on_it_refund,
        other_income=oth.other,
        sec_80c=ded.sec_80c,
        sec_80ccd_1b=ded.sec_80ccd_1b,
        sec_80ccd_2=ded.sec_80ccd_2,
        sec_80d_self=ded.sec_80d_self,
        sec_80d_parents=ded.sec_80d_parents,
        sec_80e=ded.sec_80e,
        sec_80g=ded.sec_80g,
        sec_80tta=ded.sec_80tta,
        sec_80ttb=ded.sec_80ttb,
        age_category=profile.age_category,
        filing_date=profile.filing_date,
        tds_total=sum(p.amount for p in profile.advance_tax_paid),  # will be replaced by 26AS
        advance_tax=sum(p.amount for p in profile.advance_tax_paid),
        self_assessment_tax=sum(p.amount for p in profile.self_assessment_tax_paid),
    )
