"""
Portfolio Service — ALL portfolio business logic extracted from routes.

Handles: summary, holdings CRUD, transactions, sectors, imports, MF analytics.
Routes should only call methods here and return the result.
"""

from beanie import PydanticObjectId

from ...core.constants import SECTOR_MAP
from ...models.documents import Holding
from ...models.documents.holding import EmbeddedTransaction
from ..base import BaseService
from ..cache import cache_get, cache_set, market_ttl
from . import get_prices_for_holdings, get_user_holdings


class PortfolioService(BaseService):
    """Portfolio business logic — summary, holdings, transactions, sectors."""

    def __init__(self, user_id: str):
        super().__init__(PydanticObjectId(user_id))

    async def get_summary(self) -> dict:
        holdings = await get_user_holdings(str(self.user_id))
        if not holdings:
            return {
                "total_investment": 0,
                "current_value": 0,
                "total_pnl": 0,
                "total_pnl_pct": 0,
                "day_pnl": 0,
                "day_pnl_pct": 0,
                "holdings_count": 0,
            }
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

    async def get_holdings_with_prices(self) -> list[dict]:
        ck = self._cache_key("holdings")
        cached = await cache_get(ck)
        if cached:
            return cached
        holdings = await get_user_holdings(str(self.user_id))
        prices = await get_prices_for_holdings(holdings) or {}
        result = []
        for h in holdings:
            p = prices.get(h.symbol, {})
            curr = p.get("current_price") or h.current_price or h.avg_price
            inv = h.quantity * h.avg_price
            val = h.quantity * curr
            pnl = val - inv
            result.append(
                {
                    "_id": str(h.id),
                    "symbol": h.symbol,
                    "name": h.name,
                    "holding_type": h.holding_type,
                    "quantity": h.quantity,
                    "avg_price": h.avg_price,
                    "current_price": round(curr, 2),
                    "day_change_pct": p.get("day_change_pct", 0),
                    "current_value": round(val, 2),
                    "total_investment": round(inv, 2),
                    "pnl": round(pnl, 2),
                    "pnl_pct": round((pnl / inv * 100) if inv > 0 else 0, 2),
                }
            )
        await cache_set(ck, result, ttl=market_ttl())
        return result

    async def get_sectors(self) -> dict:
        ck = self._cache_key("sectors")
        cached = await cache_get(ck)
        if cached:
            return cached
        holdings = await get_user_holdings(str(self.user_id))
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
        result = {"sectors": sectors, "total_value": round(total, 2)}
        await cache_set(ck, result, ttl=market_ttl(300, 3600))
        return result

    async def add_holding(
        self, symbol: str, name: str, exchange: str, holding_type: str, quantity: float, avg_price: float
    ) -> str:
        existing = await Holding.find_one(Holding.user_id == self.user_id, Holding.symbol == symbol)
        if existing:
            raise ValueError("Holding already exists")
        doc = Holding(
            user_id=self.user_id,
            symbol=symbol,
            name=name,
            exchange=exchange,
            holding_type=holding_type,
            quantity=quantity,
            avg_price=avg_price,
        )
        await doc.insert()
        await self._invalidate("holdings", "sectors", "dashboard", "analytics")
        return str(doc.id)

    async def update_holding(self, holding_id: str, quantity: float = None, avg_price: float = None) -> None:
        if not PydanticObjectId.is_valid(holding_id):
            raise ValueError("Invalid ID")
        h = await Holding.find_one(Holding.id == PydanticObjectId(holding_id), Holding.user_id == self.user_id)
        if not h:
            raise LookupError("Holding not found")
        if quantity is not None:
            h.quantity = quantity
        if avg_price is not None:
            h.avg_price = avg_price
        await h.save()
        await self._invalidate("holdings", "sectors", "dashboard", "analytics")

    async def delete_holding(self, holding_id: str) -> None:
        if not PydanticObjectId.is_valid(holding_id):
            raise ValueError("Invalid ID")
        h = await Holding.find_one(Holding.id == PydanticObjectId(holding_id), Holding.user_id == self.user_id)
        if not h:
            raise LookupError("Holding not found")
        await h.delete()
        await self._invalidate("holdings", "sectors", "dashboard", "analytics")

    async def get_transactions(self, page: int = 1, limit: int = 50) -> dict:
        page = max(1, page)
        limit = max(1, min(limit, 200))
        holdings = await Holding.find(Holding.user_id == self.user_id).to_list()
        txns = []
        for h in holdings:
            for i, t in enumerate(h.transactions):
                txns.append({"symbol": h.symbol, "holding_id": str(h.id), "index": i, **t.model_dump()})
        txns.sort(key=lambda x: x.get("date", ""), reverse=True)
        total = len(txns)
        start = (page - 1) * limit
        return {
            "transactions": txns[start : start + limit],
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
        }

    async def add_transaction(
        self,
        symbol: str,
        txn_type: str,
        quantity: float,
        price: float,
        date_str: str,
        holding_type: str = "EQUITY",
        notes: str = "",
        amount: float = None,
    ) -> dict:
        if not quantity and amount:
            quantity = round(amount / price, 4)
        if not quantity:
            raise ValueError("Provide quantity or amount")

        holding = await Holding.find_one(Holding.user_id == self.user_id, Holding.symbol == symbol)
        txn_doc = EmbeddedTransaction(type=txn_type, quantity=quantity, price=price, date=date_str, notes=notes)

        if not holding:
            if txn_type == "SELL":
                raise ValueError("Cannot sell - no holding found")
            holding = Holding(
                user_id=self.user_id,
                symbol=symbol,
                name=symbol,
                exchange="NSE",
                holding_type=holding_type,
                quantity=quantity,
                avg_price=price,
                transactions=[txn_doc],
            )
            await holding.insert()
            await self._invalidate("holdings", "sectors", "dashboard", "analytics")
            return {"holding_id": str(holding.id)}

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
            await self._invalidate("holdings", "sectors", "dashboard", "analytics")
            return {"sold_completely": True}

        holding.quantity = new_qty
        holding.avg_price = round(new_avg, 4)
        holding.transactions.append(txn_doc)
        await holding.save()
        await self._invalidate("holdings", "sectors", "dashboard", "analytics")
        return {"new_quantity": new_qty, "new_avg_price": round(new_avg, 2)}

    async def delete_transaction(self, holding_id: str, index: int) -> None:
        if not PydanticObjectId.is_valid(holding_id) or index < 0:
            raise ValueError("Invalid ID or index")
        holding = await Holding.find_one(Holding.id == PydanticObjectId(holding_id), Holding.user_id == self.user_id)
        if not holding or index >= len(holding.transactions):
            raise LookupError("Transaction not found")
        holding.transactions.pop(index)
        if holding.transactions:
            qty, cost = 0.0, 0.0
            for t in holding.transactions:
                if t.type == "BUY":
                    cost += t.quantity * t.price
                    qty += t.quantity
                else:
                    qty -= t.quantity
            holding.avg_price = round(cost / qty, 4) if qty > 0 else holding.avg_price
            holding.quantity = round(qty, 4) if qty > 0 else holding.quantity
        await holding.save()
        await self._invalidate("holdings", "sectors", "dashboard", "analytics")
