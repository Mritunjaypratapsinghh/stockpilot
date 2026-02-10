from datetime import datetime, timezone

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException

from ....core.response_handler import StandardResponse
from ....core.security import get_current_user
from ....models.documents import WatchlistItem
from ....services.market.price_service import get_bulk_prices
from .schemas import WatchlistAdd, WatchlistItemResponse

router = APIRouter()


@router.get("", summary="Get watchlist", description="List all watchlist items with prices")
async def get_watchlist(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get watchlist items."""
    items = await WatchlistItem.find(WatchlistItem.user_id == PydanticObjectId(current_user["_id"])).to_list()
    symbols = [w.symbol for w in items]
    prices = await get_bulk_prices(symbols) if symbols else {}

    return StandardResponse.ok(
        [
            WatchlistItemResponse(
                _id=str(w.id),
                symbol=w.symbol,
                notes=w.notes,
                current_price=prices.get(w.symbol, {}).get("current_price"),
                day_change_pct=prices.get(w.symbol, {}).get("day_change_pct", 0),
                added_at=w.added_at,
            )
            for w in items
        ]
    )


@router.post("/", summary="Add to watchlist", description="Add a stock to watchlist")
async def add_to_watchlist(item: WatchlistAdd, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Add stock to watchlist."""
    user_id = PydanticObjectId(current_user["_id"])
    symbol = item.symbol.strip().upper()

    existing = await WatchlistItem.find_one(WatchlistItem.user_id == user_id, WatchlistItem.symbol == symbol)
    if existing:
        raise HTTPException(status_code=400, detail="Already in watchlist")

    doc = WatchlistItem(user_id=user_id, symbol=symbol, notes=item.notes, added_at=datetime.now(timezone.utc))
    await doc.insert()
    return StandardResponse.ok({"id": str(doc.id), "symbol": symbol}, "Added to watchlist")


@router.delete("/{item_id}", summary="Remove from watchlist", description="Remove a stock from watchlist")
async def remove_from_watchlist(item_id: str, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Remove from watchlist."""
    if not PydanticObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    item = await WatchlistItem.find_one(
        WatchlistItem.id == PydanticObjectId(item_id), WatchlistItem.user_id == PydanticObjectId(current_user["_id"])
    )
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    await item.delete()
    return StandardResponse.ok(message="Removed from watchlist")
