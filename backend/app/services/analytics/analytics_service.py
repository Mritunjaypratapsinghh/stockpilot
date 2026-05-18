"""
Analytics Service — portfolio metrics, PnL, returns, drawdown, health score.

Extracted from analytics/routes.py to separate business logic from HTTP concerns.
"""

from beanie import PydanticObjectId

from ...core.constants import SECTOR_MAP
from ..base import BaseService
from ..cache import cache_get, cache_set, market_ttl
from ..portfolio import get_prices_for_holdings, get_user_holdings


class AnalyticsService(BaseService):
    """Analytics business logic."""

    def __init__(self, user_id: str):
        super().__init__(PydanticObjectId(user_id))

    async def _get_holdings_with_prices(self):
        """Common pattern: fetch holdings + prices."""
        holdings = await get_user_holdings(str(self.user_id))
        prices = await get_prices_for_holdings(holdings) or {} if holdings else {}
        return holdings, prices

    async def get_sector_analytics(self) -> dict:
        """Sector breakdown with caching."""
        ck = self._cache_key("analytics")
        cached = await cache_get(ck)
        if cached:
            return cached

        holdings, prices = await self._get_holdings_with_prices()
        if not holdings:
            return {"total_value": 0, "sectors": [], "holdings_count": 0}

        sector_values = {}
        total_value = 0
        for h in holdings:
            curr = prices.get(h.symbol, {}).get("current_price") or h.current_price or h.avg_price
            value = h.quantity * curr
            total_value += value
            sector = SECTOR_MAP.get(h.symbol, "Others")
            sector_values[sector] = sector_values.get(sector, 0) + value

        sectors = [
            {"sector": s, "value": round(v, 2), "percentage": round(v / total_value * 100, 1)}
            for s, v in sorted(sector_values.items(), key=lambda x: x[1], reverse=True)
        ]
        result = {"total_value": round(total_value, 2), "sectors": sectors, "holdings_count": len(holdings)}
        await cache_set(ck, result, ttl=market_ttl())
        return result

    async def get_pnl_calendar(self) -> dict:
        """Daily buy/sell activity calendar."""
        holdings, _ = await self._get_holdings_with_prices()
        if not holdings:
            return {"calendar": {}}

        calendar = {}
        for h in holdings:
            for t in h.transactions:
                date = t.date[:10] if isinstance(t.date, str) else t.date.strftime("%Y-%m-%d")
                if date not in calendar:
                    calendar[date] = {"date": date, "pnl": 0, "buy": 0, "sell": 0, "transactions": []}
                amount = t.quantity * t.price
                if t.type == "BUY":
                    calendar[date]["buy"] += amount
                    calendar[date]["pnl"] -= amount
                else:
                    calendar[date]["sell"] += amount
                    calendar[date]["pnl"] += amount
                calendar[date]["transactions"].append({"symbol": h.symbol, "type": t.type, "amount": round(amount, 2)})
        return {"calendar": calendar}

    async def get_metrics(self) -> dict:
        """Key portfolio metrics: total value, day change, winners/losers."""
        holdings, prices = await self._get_holdings_with_prices()
        if not holdings:
            return {
                "total_value": 0,
                "day_change": 0,
                "day_change_pct": 0,
                "total_pnl": 0,
                "total_pnl_pct": 0,
                "winners": 0,
                "losers": 0,
                "best_performer": None,
                "worst_performer": None,
            }

        total_val = total_inv = day_change = 0.0
        winners = losers = 0
        best = worst = None

        for h in holdings:
            p = prices.get(h.symbol, {})
            curr = p.get("current_price") or h.current_price or h.avg_price
            prev = p.get("previous_close") or curr
            inv = h.quantity * h.avg_price
            val = h.quantity * curr
            total_inv += inv
            total_val += val
            day_change += (curr - prev) * h.quantity
            pnl_pct = ((val - inv) / inv * 100) if inv > 0 else 0

            if val > inv:
                winners += 1
            elif val < inv:
                losers += 1

            entry = {"symbol": h.symbol, "name": h.name, "pnl_pct": round(pnl_pct, 2)}
            if best is None or pnl_pct > best["pnl_pct"]:
                best = entry
            if worst is None or pnl_pct < worst["pnl_pct"]:
                worst = entry

        total_pnl = total_val - total_inv
        return {
            "total_value": round(total_val, 2),
            "day_change": round(day_change, 2),
            "day_change_pct": round(
                (day_change / (total_val - day_change) * 100) if (total_val - day_change) > 0 else 0, 2
            ),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round((total_pnl / total_inv * 100) if total_inv > 0 else 0, 2),
            "winners": winners,
            "losers": losers,
            "best_performer": best,
            "worst_performer": worst,
        }

    async def get_returns(self) -> list[dict]:
        """Returns breakdown by holding."""
        holdings, prices = await self._get_holdings_with_prices()
        result = []
        for h in holdings:
            p = prices.get(h.symbol, {})
            curr = p.get("current_price") or h.current_price or h.avg_price
            inv = h.quantity * h.avg_price
            val = h.quantity * curr
            pnl = val - inv
            result.append(
                {
                    "symbol": h.symbol,
                    "name": h.name,
                    "holding_type": h.holding_type,
                    "quantity": h.quantity,
                    "avg_price": h.avg_price,
                    "current_price": round(curr, 2),
                    "invested": round(inv, 2),
                    "current_value": round(val, 2),
                    "pnl": round(pnl, 2),
                    "pnl_pct": round((pnl / inv * 100) if inv > 0 else 0, 2),
                }
            )
        result.sort(key=lambda x: x["pnl"], reverse=True)
        return result

    async def get_sector_risk(self) -> dict:
        """Sector concentration risk analysis."""
        holdings, prices = await self._get_holdings_with_prices()
        if not holdings:
            return {"sectors": [], "risk_level": "none", "concentration_warning": False}

        sector_values = {}
        total = 0.0
        for h in holdings:
            curr = prices.get(h.symbol, {}).get("current_price") or h.current_price or h.avg_price
            val = h.quantity * curr
            total += val
            sector = SECTOR_MAP.get(h.symbol, "Others")
            sector_values[sector] = sector_values.get(sector, 0) + val

        sectors = []
        max_pct = 0
        for s, v in sorted(sector_values.items(), key=lambda x: x[1], reverse=True):
            pct = round(v / total * 100, 1) if total > 0 else 0
            max_pct = max(max_pct, pct)
            risk = "high" if pct > 40 else "medium" if pct > 25 else "low"
            sectors.append({"sector": s, "value": round(v, 2), "percentage": pct, "risk": risk})

        overall_risk = "high" if max_pct > 40 else "medium" if max_pct > 25 else "low"
        return {
            "sectors": sectors,
            "risk_level": overall_risk,
            "concentration_warning": max_pct > 35,
            "max_sector_pct": max_pct,
        }
