from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional
from ..database import get_db
from ..api.auth import get_current_user
from ..services.price_service import get_bulk_prices

router = APIRouter()

def validate_object_id(id_str: str) -> ObjectId:
    if not ObjectId.is_valid(id_str):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    return ObjectId(id_str)

class WatchlistAdd(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=30)
    notes: Optional[str] = Field(None, max_length=500)

@router.get("")
@router.get("/")
async def get_watchlist(current_user: dict = Depends(get_current_user)):
    db = get_db()
    items = await db.watchlist.find({"user_id": ObjectId(current_user["_id"])}).to_list(50)
    symbols = [w["symbol"] for w in items]
    prices = await get_bulk_prices(symbols) if symbols else {}
    
    result = []
    for w in items:
        p = prices.get(w["symbol"], {})
        result.append({
            "_id": str(w["_id"]),
            "symbol": w["symbol"],
            "notes": w.get("notes"),
            "current_price": p.get("current_price"),
            "day_change_pct": p.get("day_change_pct", 0),
            "added_at": w.get("added_at")
        })
    return result

@router.post("/")
async def add_to_watchlist(item: WatchlistAdd, current_user: dict = Depends(get_current_user)):
    db = get_db()
    symbol = item.symbol.strip().upper()
    existing = await db.watchlist.find_one({"user_id": ObjectId(current_user["_id"]), "symbol": symbol})
    if existing:
        raise HTTPException(status_code=400, detail="Already in watchlist")
    
    doc = {"user_id": ObjectId(current_user["_id"]), "symbol": symbol, "notes": item.notes, "added_at": datetime.now(timezone.utc)}
    result = await db.watchlist.insert_one(doc)
    return {"_id": str(result.inserted_id), "symbol": symbol}

@router.delete("/{item_id}")
async def remove_from_watchlist(item_id: str, current_user: dict = Depends(get_current_user)):
    oid = validate_object_id(item_id)
    db = get_db()
    result = await db.watchlist.delete_one({"_id": oid, "user_id": ObjectId(current_user["_id"])})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"message": "Removed"}
