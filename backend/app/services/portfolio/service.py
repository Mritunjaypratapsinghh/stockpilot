"""Portfolio service - shared functions for portfolio operations"""

from typing import Any, Dict, List

from beanie import PydanticObjectId

from ...models.documents import Holding
from ..market.price_service import get_bulk_prices


async def get_user_holdings(user_id: str) -> List[Holding]:
    """Get all holdings for a user."""
    return await Holding.find(Holding.user_id == PydanticObjectId(user_id)).to_list()


async def get_prices_for_holdings(holdings: List[Holding]) -> Dict[str, Any]:
    """Get current prices for holdings (excludes MF)."""
    symbols = [h.symbol for h in holdings if h.holding_type != "MF"]
    return await get_bulk_prices(symbols) if symbols else {}
