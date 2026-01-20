from ..database import get_db
from ..services.price_service import get_bulk_prices
from datetime import datetime

async def update_all_prices():
    db = get_db()
    holdings = await db.holdings.find({}, {"symbol": 1}).to_list(500)
    symbols = list(set(h["symbol"] for h in holdings))
    
    if not symbols:
        return
    
    prices = await get_bulk_prices(symbols)
    
    for symbol, data in prices.items():
        if data.get("current_price"):
            await db.price_cache.update_one(
                {"_id": symbol},
                {"$set": {**data, "symbol": symbol, "updated_at": datetime.utcnow()}},
                upsert=True
            )
