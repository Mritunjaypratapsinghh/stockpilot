from fastapi import APIRouter, HTTPException, Depends, Query
from beanie import PydanticObjectId
from datetime import datetime, timezone
from typing import Optional
from dateutil.relativedelta import relativedelta

from ....models.documents import Ledger, LedgerType, LedgerStatus
from ....core.security import get_current_user
from ....core.response_handler import StandardResponse
from ....services.ledger import get_user_ledger, get_ledger_summary, add_settlement
from .schemas import LedgerCreate, LedgerResponse, SettlementCreate, SettlementResponse, LedgerSummary

router = APIRouter()


def calc_emis_remaining(entry: Ledger) -> int | None:
    if not entry.is_recurring or not entry.end_date:
        return None
    now = datetime.now(timezone.utc)
    end = entry.end_date if entry.end_date.tzinfo else entry.end_date.replace(tzinfo=timezone.utc)
    if now >= end:
        return 0
    months = (end.year - now.year) * 12 + (end.month - now.month)
    return max(0, months + 1)


def to_response(entry: Ledger) -> LedgerResponse:
    settled = sum(s.amount for s in entry.settlements)
    emis_remaining = calc_emis_remaining(entry)
    total_paid = settled
    
    return LedgerResponse(
        id=str(entry.id),
        type=entry.type,
        person_name=entry.person_name,
        amount=entry.amount,
        description=entry.description,
        date=entry.date,
        due_date=entry.due_date,
        status=entry.status,
        settlements=[SettlementResponse(amount=s.amount, date=s.date, note=s.note) for s in entry.settlements],
        remaining=entry.amount - settled,
        created_at=entry.created_at,
        is_recurring=entry.is_recurring,
        recurring_amount=entry.recurring_amount,
        recurring_day=entry.recurring_day,
        end_date=entry.end_date,
        total_paid=total_paid,
        emis_remaining=emis_remaining
    )


@router.get("", summary="Get ledger entries")
async def get_ledger(
    type: Optional[str] = Query(None, description="Filter by lent/borrowed"),
    status: Optional[str] = Query(None, description="Filter by status"),
    person: Optional[str] = Query(None, description="Search by person name"),
    recurring: Optional[bool] = Query(None, description="Filter recurring only"),
    current_user: dict = Depends(get_current_user)
) -> StandardResponse:
    entries = await get_user_ledger(PydanticObjectId(current_user["_id"]), type, status, person, recurring)
    return StandardResponse.ok([to_response(e) for e in entries])


@router.get("/summary", summary="Get ledger summary")
async def ledger_summary(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    summary = await get_ledger_summary(PydanticObjectId(current_user["_id"]))
    return StandardResponse.ok(LedgerSummary(**summary))


@router.post("", summary="Add ledger entry")
async def create_entry(data: LedgerCreate, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    entry = Ledger(
        user_id=PydanticObjectId(current_user["_id"]),
        type=LedgerType(data.type),
        person_name=data.person_name,
        amount=data.amount,
        description=data.description,
        date=datetime.combine(data.date, datetime.min.time()).replace(tzinfo=timezone.utc) if data.date else datetime.now(timezone.utc),
        due_date=datetime.combine(data.due_date, datetime.min.time()).replace(tzinfo=timezone.utc) if data.due_date else None,
        is_recurring=data.is_recurring,
        recurring_amount=data.recurring_amount,
        recurring_day=data.recurring_day,
        end_date=datetime.combine(data.end_date, datetime.min.time()).replace(tzinfo=timezone.utc) if data.end_date else None
    )
    await entry.insert()
    return StandardResponse.ok(to_response(entry), "Entry added")


@router.post("/{entry_id}/settle", summary="Add settlement")
async def settle_entry(entry_id: str, data: SettlementCreate, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    if not PydanticObjectId.is_valid(entry_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    
    entry = await add_settlement(PydanticObjectId(entry_id), PydanticObjectId(current_user["_id"]), data.amount, data.note)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return StandardResponse.ok(to_response(entry), "Settlement recorded")


@router.put("/{entry_id}", summary="Update entry")
async def update_entry(entry_id: str, data: LedgerCreate, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    if not PydanticObjectId.is_valid(entry_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    
    entry = await Ledger.find_one({"_id": PydanticObjectId(entry_id), "user_id": PydanticObjectId(current_user["_id"])})
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    entry.type = LedgerType(data.type)
    entry.person_name = data.person_name
    entry.amount = data.amount
    entry.description = data.description
    entry.due_date = datetime.combine(data.due_date, datetime.min.time()).replace(tzinfo=timezone.utc) if data.due_date else None
    entry.is_recurring = data.is_recurring
    entry.recurring_amount = data.recurring_amount
    entry.recurring_day = data.recurring_day
    entry.end_date = datetime.combine(data.end_date, datetime.min.time()).replace(tzinfo=timezone.utc) if data.end_date else None
    await entry.save()
    return StandardResponse.ok(to_response(entry), "Entry updated")


@router.delete("/{entry_id}", summary="Delete entry")
async def delete_entry(entry_id: str, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    if not PydanticObjectId.is_valid(entry_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    
    entry = await Ledger.find_one({"_id": PydanticObjectId(entry_id), "user_id": PydanticObjectId(current_user["_id"])})
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    await entry.delete()
    return StandardResponse.ok(message="Entry deleted")
