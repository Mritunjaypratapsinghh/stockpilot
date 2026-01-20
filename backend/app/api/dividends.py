from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, date
from bson import ObjectId
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..api.auth import get_current_user

router = APIRouter()

class DividendCreate(BaseModel):
    symbol: str
    amount: float  # Per share
    ex_date: date
    record_date: Optional[date] = None
    payment_date: Optional[date] = None

@router.get("")
@router.get("/")
async def get_dividends(current_user: dict = Depends(get_current_user)):
    """Get all dividend records for user"""
    db = get_db()
    dividends = await db.dividends.find({"user_id": ObjectId(current_user["_id"])}).sort("ex_date", -1).to_list(100)
    return [{"_id": str(d["_id"]), **{k: v for k, v in d.items() if k not in ["_id", "user_id"]}} for d in dividends]

@router.get("/summary")
async def get_dividend_summary(current_user: dict = Depends(get_current_user)):
    """Get dividend summary with total income and yield"""
    db = get_db()
    dividends = await db.dividends.find({"user_id": ObjectId(current_user["_id"])}).to_list(500)
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    
    total_dividend = sum(d["amount"] * d["quantity"] for d in dividends)
    total_investment = sum(h["quantity"] * h["avg_price"] for h in holdings)
    
    # Group by year
    by_year = {}
    for d in dividends:
        year = d["ex_date"][:4] if isinstance(d["ex_date"], str) else d["ex_date"].year
        by_year[year] = by_year.get(year, 0) + d["amount"] * d["quantity"]
    
    # Group by symbol
    by_symbol = {}
    for d in dividends:
        by_symbol[d["symbol"]] = by_symbol.get(d["symbol"], 0) + d["amount"] * d["quantity"]
    
    return {
        "total_dividend": round(total_dividend, 2),
        "dividend_yield": round((total_dividend / total_investment * 100) if total_investment > 0 else 0, 2),
        "by_year": [{"year": y, "amount": round(a, 2)} for y, a in sorted(by_year.items(), reverse=True)],
        "by_symbol": [{"symbol": s, "amount": round(a, 2)} for s, a in sorted(by_symbol.items(), key=lambda x: x[1], reverse=True)[:10]]
    }

@router.post("/")
async def add_dividend(div: DividendCreate, current_user: dict = Depends(get_current_user)):
    """Record a dividend payment"""
    db = get_db()
    holding = await db.holdings.find_one({"user_id": ObjectId(current_user["_id"]), "symbol": div.symbol.upper()})
    quantity = holding["quantity"] if holding else 0
    
    doc = {
        "user_id": ObjectId(current_user["_id"]),
        "symbol": div.symbol.upper(),
        "amount": div.amount,
        "quantity": quantity,
        "total": round(div.amount * quantity, 2),
        "ex_date": div.ex_date.isoformat(),
        "record_date": div.record_date.isoformat() if div.record_date else None,
        "payment_date": div.payment_date.isoformat() if div.payment_date else None,
        "created_at": datetime.utcnow()
    }
    result = await db.dividends.insert_one(doc)
    return {"_id": str(result.inserted_id), "total": doc["total"]}

@router.delete("/{dividend_id}")
async def delete_dividend(dividend_id: str, current_user: dict = Depends(get_current_user)):
    result = await get_db().dividends.delete_one({"_id": ObjectId(dividend_id), "user_id": ObjectId(current_user["_id"])})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"message": "Deleted"}
