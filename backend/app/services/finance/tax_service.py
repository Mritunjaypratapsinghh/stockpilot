"""
Finance Service — tax summary, networth, goals, SIP calculations.

Extracted from finance/routes.py.
"""

from datetime import datetime, timedelta

from beanie import PydanticObjectId

from ..base import BaseService
from ..cache import cache_get, cache_set
from ..portfolio import get_prices_for_holdings, get_user_holdings


class TaxService(BaseService):
    """Tax computation for portfolio holdings."""

    def __init__(self, user_id: str):
        super().__init__(PydanticObjectId(user_id))

    async def get_tax_summary(self) -> dict:
        """Calculate STCG/LTCG tax liability based on holding period."""
        cache_key = self._cache_key("tax_summary")
        cached = await cache_get(cache_key)
        if cached:
            return cached

        holdings = await get_user_holdings(str(self.user_id))
        now = datetime.now()
        fy_start = datetime(now.year if now.month >= 4 else now.year - 1, 4, 1)
        fy = f"{fy_start.year}-{fy_start.year + 1}"
        one_year_ago = now - timedelta(days=365)

        if not holdings:
            return {
                "financial_year": fy,
                "realized": {"stcg": 0, "ltcg": 0},
                "unrealized": {"total": 0, "stcg": 0, "ltcg": 0},
                "tax_liability": {"stcg_tax": 0, "ltcg_tax": 0, "total_tax": 0},
            }

        prices = await get_prices_for_holdings(holdings) or {}
        unrealized_ltcg = unrealized_stcg = 0

        for h in holdings:
            curr_price = prices.get(h.symbol, {}).get("current_price") or h.current_price or h.avg_price
            pnl = (curr_price - h.avg_price) * h.quantity

            first_buy = None
            for t in h.transactions:
                if t.type == "BUY":
                    t_date = datetime.fromisoformat(t.date) if isinstance(t.date, str) else t.date
                    if first_buy is None or t_date < first_buy:
                        first_buy = t_date

            if first_buy and first_buy < one_year_ago:
                unrealized_ltcg += pnl
            else:
                unrealized_stcg += pnl

        ltcg_exemption = 125000
        ltcg_taxable = max(0, unrealized_ltcg - ltcg_exemption)
        ltcg_tax = ltcg_taxable * 0.125
        stcg_tax = max(0, unrealized_stcg) * 0.20

        result = {
            "financial_year": fy,
            "realized": {"stcg": 0, "ltcg": 0, "total": 0},
            "unrealized": {
                "stcg": round(unrealized_stcg, 2),
                "ltcg": round(unrealized_ltcg, 2),
                "total": round(unrealized_ltcg + unrealized_stcg, 2),
            },
            "tax_liability": {
                "ltcg_exemption": ltcg_exemption,
                "taxable_ltcg": round(ltcg_taxable, 2),
                "ltcg_tax": round(ltcg_tax, 2),
                "stcg_tax": round(stcg_tax, 2),
                "total_tax": round(ltcg_tax + stcg_tax, 2),
            },
            "transactions": [],
        }
        await cache_set(cache_key, result, ttl=300)
        return result
