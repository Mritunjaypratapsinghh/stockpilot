"""WebSocket price broadcaster - pushes real-time updates to subscribed clients."""

from ..services.market.price_service import get_bulk_prices
from ..services.websocket import ws_manager
from ..utils.logger import logger


async def broadcast_prices():
    """Fetch prices for subscribed symbols and broadcast to WebSocket clients."""
    symbols = ws_manager.get_subscribed_symbols()
    if not symbols:
        return

    prices = await get_bulk_prices(symbols)
    for symbol, data in prices.items():
        await ws_manager.broadcast_price(symbol, data)

    if prices:
        logger.debug(f"Broadcast {len(prices)} prices to {ws_manager.get_connection_count()} clients")
