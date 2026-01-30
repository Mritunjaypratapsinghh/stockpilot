from fastapi import APIRouter, HTTPException, Depends
from datetime import date
from beanie import PydanticObjectId
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal

from ..models.documents import Holding
from ..models.documents.holding import EmbeddedTransaction
from ..api.auth import get_current_user

router = APIRouter()


class TransactionCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=30)
    type: Literal["BUY", "SELL"]
    quantity: Optional[float] = Field(None, gt=0)
    price: float = Field(..., gt=0)
    date: date
    amount: Optional[float] = Field(None, gt=0)
    holding_type: Literal["EQUITY", "MF", "ETF"] = "EQUITY"
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator('symbol')
    @classmethod
    def clean_symbol(cls, v: str) -> str:
        return v.strip().upper()


@router.get("/")
async def get_transactions(current_user: dict = Depends(get_current_user)):
    holdings = await Holding.find(Holding.user_id == PydanticObjectId(current_user["_id"])).to_list()
    txns = []
    for h in holdings:
        for i, t in enumerate(h.transactions):
            txns.append({"symbol": h.symbol, "holding_id": str(h.id), "index": i, **t.model_dump()})
    return sorted(txns, key=lambda x: x.get("date", ""), reverse=True)


@router.post("/")
async def add_transaction(txn: TransactionCreate, current_user: dict = Depends(get_current_user)):
    user_id = PydanticObjectId(current_user["_id"])
    
    quantity = txn.quantity
    if txn.amount and not txn.quantity:
        quantity = round(txn.amount / txn.price, 4)
    if not quantity:
        raise HTTPException(status_code=400, detail="Provide quantity or amount")

    holding = await Holding.find_one(Holding.user_id == user_id, Holding.symbol == txn.symbol)

    txn_doc = EmbeddedTransaction(type=txn.type, quantity=quantity, price=txn.price, date=txn.date.isoformat(), notes=txn.notes)

    if not holding:
        if txn.type == "SELL":
            raise HTTPException(status_code=400, detail="Cannot sell - no holding found")
        holding = Holding(
            user_id=user_id,
            symbol=txn.symbol,
            name=txn.symbol,
            exchange="NSE",
            holding_type=txn.holding_type,
            quantity=quantity,
            avg_price=txn.price,
            transactions=[txn_doc]
        )
        await holding.insert()
        return {"message": "Holding created", "holding_id": str(holding.id)}

    old_qty, old_avg = holding.quantity, holding.avg_price

    if txn.type == "BUY":
        new_qty = old_qty + quantity
        new_avg = ((old_qty * old_avg) + (quantity * txn.price)) / new_qty
    else:
        if quantity > old_qty:
            raise HTTPException(status_code=400, detail="Cannot sell more than held")
        new_qty = old_qty - quantity
        new_avg = old_avg

    if new_qty == 0:
        await holding.delete()
        return {"message": "Holding sold completely"}

    holding.quantity = new_qty
    holding.avg_price = round(new_avg, 2)
    holding.transactions.append(txn_doc)
    await holding.save()
    return {"message": "Transaction added", "new_quantity": new_qty, "new_avg_price": round(new_avg, 2)}


@router.delete("/{holding_id}/{index}")
async def delete_transaction(holding_id: str, index: int, current_user: dict = Depends(get_current_user)):
    if not PydanticObjectId.is_valid(holding_id):
        raise HTTPException(status_code=400, detail="Invalid holding ID")
    if index < 0:
        raise HTTPException(status_code=400, detail="Invalid index")

    holding = await Holding.find_one(
        Holding.id == PydanticObjectId(holding_id),
        Holding.user_id == PydanticObjectId(current_user["_id"])
    )
    if not holding or index >= len(holding.transactions):
        raise HTTPException(status_code=404, detail="Transaction not found")

    holding.transactions.pop(index)

    if not holding.transactions:
        await holding.save()
        return {"message": "Deleted"}

    # Recalculate from remaining transactions
    qty, cost = 0, 0
    for t in holding.transactions:
        if t.type == "BUY":
            cost += t.quantity * t.price
            qty += t.quantity
        else:
            qty -= t.quantity

    holding.avg_price = round(cost / qty, 2) if qty > 0 else holding.avg_price
    holding.quantity = qty if qty > 0 else holding.quantity
    await holding.save()
    return {"message": "Deleted"}
