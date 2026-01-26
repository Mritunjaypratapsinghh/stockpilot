from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, date
from bson import ObjectId
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..api.auth import get_current_user

router = APIRouter()

class TransactionCreate(BaseModel):
    symbol: str
    type: str  # BUY or SELL
    quantity: Optional[float] = None
    price: float
    date: date
    amount: Optional[float] = None  # For MF: invest by amount
    holding_type: str = "EQUITY"  # EQUITY or MF
    notes: Optional[str] = None

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
    
    # Calculate quantity from amount if provided (for MF)
    quantity = txn.quantity
    if txn.amount and not txn.quantity:
        quantity = round(txn.amount / txn.price, 4)
    if not quantity:
        raise HTTPException(status_code=400, detail="Provide quantity or amount")
    
    holding = await db.holdings.find_one({"user_id": ObjectId(current_user["_id"]), "symbol": txn.symbol.upper()})
    
    if not holding:
        if txn.type == "SELL":
            raise HTTPException(status_code=400, detail="Cannot sell - no holding found")
        # Create new holding for BUY
        doc = {
            "user_id": ObjectId(current_user["_id"]),
            "symbol": txn.symbol.upper(),
            "name": txn.symbol.upper(),
            "exchange": "NSE",
            "holding_type": txn.holding_type,
            "quantity": quantity,
            "avg_price": txn.price,
            "transactions": [{"type": txn.type, "quantity": quantity, "price": txn.price, "date": txn.date.isoformat(), "notes": txn.notes}],
            "created_at": datetime.utcnow()
        }
        result = await db.holdings.insert_one(doc)
        return {"message": "Holding created", "holding_id": str(result.inserted_id)}
    
    # Update existing holding
    old_qty = holding["quantity"]
    old_avg = holding["avg_price"]
    
    if txn.type == "BUY":
        new_qty = old_qty + quantity
        new_avg = ((old_qty * old_avg) + (quantity * txn.price)) / new_qty
    else:  # SELL
        if quantity > old_qty:
            raise HTTPException(status_code=400, detail="Cannot sell more than held")
        new_qty = old_qty - quantity
        new_avg = old_avg  # Avg price unchanged on sell
    
    txn_doc = {"type": txn.type, "quantity": quantity, "price": txn.price, "date": txn.date.isoformat(), "notes": txn.notes}
    
    if new_qty == 0:
        await db.holdings.delete_one({"_id": holding["_id"]})
        return {"message": "Holding sold completely"}
    
    await db.holdings.update_one(
        {"_id": holding["_id"]},
        {"$set": {"quantity": new_qty, "avg_price": round(new_avg, 2), "updated_at": datetime.utcnow()}, "$push": {"transactions": txn_doc}}
    )
    return {"message": "Transaction added", "new_quantity": new_qty, "new_avg_price": round(new_avg, 2)}

@router.delete("/{holding_id}/{index}")
async def delete_transaction(holding_id: str, index: int, current_user: dict = Depends(get_current_user)):
    db = get_db()
    holding = await db.holdings.find_one({"_id": ObjectId(holding_id), "user_id": ObjectId(current_user["_id"])})
    if not holding or index >= len(holding.get("transactions", [])):
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    txns = holding["transactions"]
    txns.pop(index)
    await db.holdings.update_one({"_id": ObjectId(holding_id)}, {"$set": {"transactions": txns}})
    return {"message": "Deleted"}
