from datetime import datetime, timezone

from ..models.documents import Holding, PriceCache
from ..services.market.price_service import get_bulk_prices


async def update_all_prices():
    holdings = await Holding.find().to_list()
    # Skip MF symbols - they don't have Yahoo prices
    symbols = list(set(h.symbol for h in holdings if h.holding_type != "MF"))

    if not symbols:
        return

    prices = await get_bulk_prices(symbols)
    now = datetime.now(timezone.utc)

    for symbol, data in prices.items():
        if not data.get("current_price"):
            continue

        # Map API response to PriceCache fields
        cache_data = {
            "price": data.get("current_price"),
            "change": data.get("day_change"),
            "change_percent": data.get("day_change_pct"),
            "volume": data.get("volume"),
            "last_updated": now,
        }

        cache = await PriceCache.find_one(PriceCache.symbol == symbol)
        if cache:
            for k, v in cache_data.items():
                setattr(cache, k, v)
            await cache.save()
        else:
            await PriceCache(symbol=symbol, **cache_data).insert()
