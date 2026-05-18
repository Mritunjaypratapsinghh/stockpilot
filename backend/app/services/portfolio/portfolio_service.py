"""
Portfolio Service — Business logic for holdings, transactions, and portfolio metrics.

Extracted from portfolio/routes.py to enforce separation of concerns.
Routes handle HTTP; this handles business logic.
"""

from typing import Any

from beanie import PydanticObjectId

from ...core.constants import SECTOR_MAP
from ...models.documents import Holding
from ...models.documents.holding import EmbeddedTransaction
from ..base import BaseRepository, BaseService


class HoldingRepository(BaseRepository[Holding]):
    """Tenant-scoped holding data access."""

    def __init__(self, user_id: PydanticObjectId):
        super().__init__(Holding, user_id)

    async def find_by_symbol(self, symbol: str) -> Holding | None:
        return await self.find_one(symbol=symbol)

    async def get_all(self) -> list[Holding]:
        return await self.find_all(limit=1000, sort="symbol")


class PortfolioService(BaseService):
    """Portfolio business logic — summary, sectors, transactions."""

    def __init__(self, user_id: PydanticObjectId):
        super().__init__(user_id)
        self.holdings = HoldingRepository(user_id)

    async def get_summary(self) -> dict[str, Any]:
        """Compute portfolio summary with P&L."""

        async def _compute():
            from ..portfolio import get_prices_for_holdings

            holdings = await self.holdings.get_all()
            if not holdings:
                return {"total_investment": 0, "current_value": 0, "total_pnl": 0,
                        "total_pnl_pct": 0, "day_pnl": 0, "day_pnl_pct": 0, "holdings_count": 0}

            prices = await get_prices_for_holdings(holdings) or {}
            total_inv = current_val = day_pnl = 0.0

            for h in holdings:
                inv = h.quantity * h.avg_price
                total_inv += inv
                p = prices.get(h.symbol, {})
                curr = p.get("current_price") or h.current_price or h.avg_price
                prev = p.get("previous_close") or curr
                current_val += h.quantity * curr
                day_pnl += (curr - prev) * h.quantity

            total_pnl = current_val - total_inv
            return {
                "total_investment": round(total_inv, 2),
                "current_value": round(current_val, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_pct": round((total_pnl / total_inv * 100) if total_inv > 0 else 0, 2),
                "day_pnl": round(day_pnl, 2),
                "day_pnl_pct": round((day_pnl / (current_val - day_pnl) * 100) if (current_val - day_pnl) > 0 else 0, 2),
                "holdings_count": len(holdings),
            }

        return await self._cached("portfolio_summary", _compute)

    async def get_sectors(self) -> dict[str, Any]:
        """Compute sector allocation."""

        async def _compute():
            from ..portfolio import get_prices_for_holdings

            holdings = await self.holdings.get_all()
            if not holdings:
                return {"sectors": [], "total_value": 0}

            prices = await get_prices_for_holdings(holdings) or {}
            sector_values: dict[str, float] = {}
            total = 0.0

            for h in holdings:
                curr = prices.get(h.symbol, {}).get("current_price") or h.current_price or h.avg_price
                val = h.quantity * curr
                total += val
                sector = SECTOR_MAP.get(h.symbol, "Others")
                sector_values[sector] = sector_values.get(sector, 0) + val

            sectors = [
                {"sector": s, "value": round(v, 2), "percentage": round(v / total * 100, 1) if total > 0 else 0}
                for s, v in sorted(sector_values.items(), key=lambda x: x[1], reverse=True)
            ]
            return {"sectors": sectors, "total_value": round(total, 2)}

        return await self._cached("sectors", _compute)

    async def add_holding(self, symbol: str, name: str, exchange: str, holding_type: str,
                          quantity: float, avg_price: float) -> str:
        """Add new holding. Returns holding ID."""
        existing = await self.holdings.find_by_symbol(symbol)
        if existing:
            raise ValueError("Holding already exists")

        doc = Holding(
            user_id=self.user_id, symbol=symbol, name=name, exchange=exchange,
            holding_type=holding_type, quantity=quantity, avg_price=avg_price,
        )
        await doc.insert()
        await self._invalidate("holdings", "sectors", "dashboard", "analytics", "portfolio_summary")
        return str(doc.id)

    async def add_transaction(self, symbol: str, txn_type: str, quantity: float,
                              price: float, date: str, holding_type: str = "EQUITY",
                              notes: str = "") -> dict:
        """Add buy/sell transaction with automatic avg price recalculation."""
        holding = await self.holdings.find_by_symbol(symbol)
        txn_doc = EmbeddedTransaction(type=txn_type, quantity=quantity, price=price, date=date, notes=notes)

        if not holding:
            if txn_type == "SELL":
                raise ValueError("Cannot sell — no holding found")
            holding = Holding(
                user_id=self.user_id, symbol=symbol, name=symbol, exchange="NSE",
                holding_type=holding_type, quantity=quantity, avg_price=price, transactions=[txn_doc],
            )
            await holding.insert()
            await self._invalidate("holdings", "sectors", "dashboard", "analytics", "portfolio_summary")
            return {"holding_id": str(holding.id), "new_quantity": quantity}

        old_qty, old_avg = holding.quantity, holding.avg_price
        if txn_type == "BUY":
            new_qty = round(old_qty + quantity, 4)
            new_avg = ((old_qty * old_avg) + (quantity * price)) / new_qty
        else:
            if quantity > old_qty:
                raise ValueError("Cannot sell more than held")
            new_qty = round(old_qty - quantity, 4)
            new_avg = old_avg

        if new_qty == 0:
            await holding.delete()
            await self._invalidate("holdings", "sectors", "dashboard", "analytics", "portfolio_summary")
            return {"sold_completely": True}

        holding.quantity = new_qty
        holding.avg_price = round(new_avg, 4)
        holding.transactions.append(txn_doc)
        await holding.save()
        await self._invalidate("holdings", "sectors", "dashboard", "analytics", "portfolio_summary")
        return {"new_quantity": new_qty, "new_avg_price": round(new_avg, 2)}
