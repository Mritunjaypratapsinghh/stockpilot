from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from beanie import PydanticObjectId
from pydantic import BaseModel, Field
from typing import Optional

from ..models.documents import WatchlistItem
from ..api.auth import get_current_user
from ..services.price_service import get_bulk_prices

router = APIRouter()


class WatchlistAdd(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=30)
    notes: Optional[str] = Field(None, max_length=500)


@router.get("")
@router.get("/")
async def get_watchlist(current_user: dict = Depends(get_current_user)):
    items = await WatchlistItem.find(WatchlistItem.user_id == PydanticObjectId(current_user["_id"])).to_list()
    symbols = [w.symbol for w in items]
    prices = await get_bulk_prices(symbols) if symbols else {}

    return [{
        "_id": str(w.id),
        "symbol": w.symbol,
        "notes": w.notes,
        "current_price": prices.get(w.symbol, {}).get("current_price"),
        "day_change_pct": prices.get(w.symbol, {}).get("day_change_pct", 0),
        "added_at": w.added_at
    } for w in items]


@router.post("/")
async def add_to_watchlist(item: WatchlistAdd, current_user: dict = Depends(get_current_user)):
    user_id = PydanticObjectId(current_user["_id"])
    symbol = item.symbol.strip().upper()
    
    existing = await WatchlistItem.find_one(WatchlistItem.user_id == user_id, WatchlistItem.symbol == symbol)
    if existing:
        raise HTTPException(status_code=400, detail="Already in watchlist")

    doc = WatchlistItem(user_id=user_id, symbol=symbol, notes=item.notes, added_at=datetime.now(timezone.utc))
    await doc.insert()
    return {"_id": str(doc.id), "symbol": symbol}


@router.delete("/{item_id}")
async def remove_from_watchlist(item_id: str, current_user: dict = Depends(get_current_user)):
    if not PydanticObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    item = await WatchlistItem.find_one(WatchlistItem.id == PydanticObjectId(item_id), WatchlistItem.user_id == PydanticObjectId(current_user["_id"]))
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    await item.delete()
    return {"message": "Removed"}
