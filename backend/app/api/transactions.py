from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, date, timezone
from bson import ObjectId
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from ..database import get_db
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
    db = get_db()
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    txns = []
    for h in holdings:
        for t in h.get("transactions", []):
            txns.append({"symbol": h["symbol"], "holding_id": str(h["_id"]), **t})
    return sorted(txns, key=lambda x: x.get("date", ""), reverse=True)

@router.post("/")
async def add_transaction(txn: TransactionCreate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    
    quantity = txn.quantity
    if txn.amount and not txn.quantity:
        quantity = round(txn.amount / txn.price, 4)
    if not quantity:
        raise HTTPException(status_code=400, detail="Provide quantity or amount")
    
    holding = await db.holdings.find_one({"user_id": ObjectId(current_user["_id"]), "symbol": txn.symbol})
    
    if not holding:
        if txn.type == "SELL":
            raise HTTPException(status_code=400, detail="Cannot sell - no holding found")
        doc = {
            "user_id": ObjectId(current_user["_id"]),
            "symbol": txn.symbol,
            "name": txn.symbol,
            "exchange": "NSE",
            "holding_type": txn.holding_type,
            "quantity": quantity,
            "avg_price": txn.price,
            "transactions": [{"type": txn.type, "quantity": quantity, "price": txn.price, "date": txn.date.isoformat(), "notes": txn.notes}],
            "created_at": datetime.now(timezone.utc)
        }
        result = await db.holdings.insert_one(doc)
        return {"message": "Holding created", "holding_id": str(result.inserted_id)}
    
    old_qty = holding["quantity"]
    old_avg = holding["avg_price"]
    
    if txn.type == "BUY":
        new_qty = old_qty + quantity
        new_avg = ((old_qty * old_avg) + (quantity * txn.price)) / new_qty
    else:
        if quantity > old_qty:
            raise HTTPException(status_code=400, detail="Cannot sell more than held")
        new_qty = old_qty - quantity
        new_avg = old_avg
    
    txn_doc = {"type": txn.type, "quantity": quantity, "price": txn.price, "date": txn.date.isoformat(), "notes": txn.notes}
    
    if new_qty == 0:
        await db.holdings.delete_one({"_id": holding["_id"]})
        return {"message": "Holding sold completely"}
    
    await db.holdings.update_one(
        {"_id": holding["_id"]},
        {"$set": {"quantity": new_qty, "avg_price": round(new_avg, 2), "updated_at": datetime.now(timezone.utc)}, "$push": {"transactions": txn_doc}}
    )
    return {"message": "Transaction added", "new_quantity": new_qty, "new_avg_price": round(new_avg, 2)}

@router.delete("/{holding_id}/{index}")
async def delete_transaction(holding_id: str, index: int, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(holding_id):
        raise HTTPException(status_code=400, detail="Invalid holding ID")
    if index < 0:
        raise HTTPException(status_code=400, detail="Invalid index")
    
    db = get_db()
    holding = await db.holdings.find_one({"_id": ObjectId(holding_id), "user_id": ObjectId(current_user["_id"])})
    if not holding or index >= len(holding.get("transactions", [])):
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    txns = holding["transactions"]
    txns.pop(index)
    await db.holdings.update_one({"_id": ObjectId(holding_id)}, {"$set": {"transactions": txns}})
    return {"message": "Deleted"}
