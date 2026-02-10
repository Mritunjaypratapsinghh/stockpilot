from datetime import datetime, timezone

from ..models.documents import Holding, PriceCache
from ..services.market.price_service import get_bulk_prices


async def update_all_prices():
    holdings = await Holding.find().to_list()
    symbols = list(set(h.symbol for h in holdings))

    if not symbols:
        return

    prices = await get_bulk_prices(symbols)

    for symbol, data in prices.items():
        if data.get("current_price"):
            cache = await PriceCache.find_one(PriceCache.symbol == symbol)
            if cache:
                for k, v in data.items():
                    setattr(cache, k, v)
                cache.updated_at = datetime.now(timezone.utc)
                await cache.save()
            else:
                await PriceCache(symbol=symbol, **data, updated_at=datetime.now(timezone.utc)).insert()
