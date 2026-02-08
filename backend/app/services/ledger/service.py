from beanie import PydanticObjectId
from datetime import datetime, timezone

from ...models.documents import Ledger, LedgerStatus, Settlement


async def get_user_ledger(user_id: PydanticObjectId, type_filter: str = None, status: str = None, person: str = None, recurring: bool = None):
    query = {"user_id": user_id}
    if type_filter:
        query["type"] = type_filter
    if status:
        query["status"] = status
    if person:
        query["person_name"] = {"$regex": person, "$options": "i"}
    if recurring is not None:
        query["is_recurring"] = recurring
    return await Ledger.find(query).sort("-created_at").to_list()


async def get_ledger_summary(user_id: PydanticObjectId):
    entries = await Ledger.find({"user_id": user_id, "status": {"$ne": "settled"}}).to_list()
    
    total_lent = sum(e.amount - sum(s.amount for s in e.settlements) for e in entries if e.type == "lent")
    total_borrowed = sum(e.amount - sum(s.amount for s in e.settlements) for e in entries if e.type == "borrowed")
    
    # Monthly outgoing = sum of recurring EMIs you're paying (lent type)
    monthly_outgoing = sum(e.recurring_amount or 0 for e in entries if e.type == "lent" and e.is_recurring)
    
    return {
        "total_lent": total_lent,
        "total_borrowed": total_borrowed,
        "net_balance": total_lent - total_borrowed,
        "pending_entries": len(entries),
        "monthly_outgoing": monthly_outgoing
    }


async def add_settlement(ledger_id: PydanticObjectId, user_id: PydanticObjectId, amount: float, note: str = None):
    entry = await Ledger.find_one({"_id": ledger_id, "user_id": user_id})
    if not entry:
        return None
    
    settlement = Settlement(
        user_id=user_id,
        amount=amount,
        date=datetime.now(timezone.utc),
        note=note
    )
    entry.settlements.append(settlement)
    
    total_settled = sum(s.amount for s in entry.settlements)
    if total_settled >= entry.amount:
        entry.status = LedgerStatus.SETTLED
    else:
        entry.status = LedgerStatus.PARTIAL
    
    await entry.save()
    return entry
