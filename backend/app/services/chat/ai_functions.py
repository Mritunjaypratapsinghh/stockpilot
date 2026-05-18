"""AI function calling for chat - enables AI to take actions."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from beanie import PydanticObjectId

logger = logging.getLogger("stockpilot")

# Tool definitions for Groq function calling
AI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_price_alert",
            "description": "Create a price alert to notify user when a stock reaches a target price",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock symbol (e.g., TCS, RELIANCE, HDFCBANK)"},
                    "alert_type": {
                        "type": "string",
                        "enum": ["PRICE_ABOVE", "PRICE_BELOW", "PERCENT_UP", "PERCENT_DOWN"],
                        "description": "Type of alert: PRICE_ABOVE/PRICE_BELOW for target price, PERCENT_UP/PERCENT_DOWN for % change",
                    },
                    "target_value": {
                        "type": "number",
                        "description": "Target price (for PRICE_ABOVE/BELOW) or percentage (for PERCENT_UP/DOWN)",
                    },
                },
                "required": ["symbol", "alert_type", "target_value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_portfolio_summary",
            "description": "Get user's portfolio summary including total value, P&L, and top holdings",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Get current price and day change for a stock",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock symbol (e.g., TCS, RELIANCE)"},
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_tax",
            "description": "Calculate STCG/LTCG tax if user sells a holding",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock symbol to calculate tax for"},
                    "quantity": {"type": "number", "description": "Number of shares to sell (optional, defaults to all)"},
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_tax_harvesting_opportunities",
            "description": "Find stocks with losses that can be sold to offset gains (tax loss harvesting)",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_watchlist",
            "description": "Add a stock to user's watchlist",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock symbol to add"},
                },
                "required": ["symbol"],
            },
        },
    },
]


async def execute_function(name: str, args: dict, user_id: str) -> dict[str, Any]:
    """Execute an AI function and return the result."""
    uid = PydanticObjectId(user_id)

    if name == "create_price_alert":
        return await _create_alert(uid, args)
    elif name == "get_portfolio_summary":
        return await _get_portfolio_summary(uid)
    elif name == "get_stock_price":
        return await _get_stock_price(args.get("symbol", ""))
    elif name == "calculate_tax":
        return await _calculate_tax(uid, args)
    elif name == "get_tax_harvesting_opportunities":
        return await _get_tax_harvesting(uid)
    elif name == "add_to_watchlist":
        return await _add_to_watchlist(uid, args.get("symbol", ""))
    else:
        return {"error": f"Unknown function: {name}"}


async def _create_alert(user_id: PydanticObjectId, args: dict) -> dict:
    """Create a price alert."""
    from ...models.documents import Alert

    symbol = args.get("symbol", "").upper().replace(".NS", "")
    alert_type = args.get("alert_type", "PRICE_ABOVE")
    target_value = args.get("target_value", 0)

    if not symbol or target_value <= 0:
        return {"success": False, "error": "Invalid symbol or target value"}

    alert = Alert(
        user_id=user_id,
        symbol=symbol,
        alert_type=alert_type,
        target_value=target_value,
        is_active=True,
    )
    await alert.insert()

    type_desc = {
        "PRICE_ABOVE": f"goes above ₹{target_value:,.0f}",
        "PRICE_BELOW": f"goes below ₹{target_value:,.0f}",
        "PERCENT_UP": f"rises {target_value}%",
        "PERCENT_DOWN": f"falls {target_value}%",
    }

    return {
        "success": True,
        "message": f"Alert created: Notify when {symbol} {type_desc.get(alert_type, '')}",
        "alert_id": str(alert.id),
    }


async def _get_portfolio_summary(user_id: PydanticObjectId) -> dict:
    """Get portfolio summary."""
    from ...models.documents import Holding
    from ...services.market.price_service import get_bulk_prices

    holdings = await Holding.find(Holding.user_id == user_id).to_list()
    if not holdings:
        return {"success": True, "message": "No holdings found", "holdings": []}

    symbols = [h.symbol for h in holdings if h.holding_type != "MF"]
    prices = await get_bulk_prices(symbols) if symbols else {}

    total_invested = total_current = 0
    top_holdings = []

    for h in holdings:
        p = prices.get(h.symbol, {})
        curr = p.get("current_price") or h.current_price or h.avg_price
        invested = h.avg_price * h.quantity
        current = curr * h.quantity
        pnl = current - invested
        total_invested += invested
        total_current += current
        top_holdings.append({"symbol": h.symbol, "value": current, "pnl": pnl})

    top_holdings.sort(key=lambda x: x["value"], reverse=True)

    return {
        "success": True,
        "total_invested": total_invested,
        "total_current": total_current,
        "total_pnl": total_current - total_invested,
        "pnl_pct": ((total_current - total_invested) / total_invested * 100) if total_invested else 0,
        "holdings_count": len(holdings),
        "top_5": top_holdings[:5],
    }


async def _get_stock_price(symbol: str) -> dict:
    """Get live stock price."""
    from ...services.market.price_service import get_stock_price

    symbol = symbol.upper().replace(".NS", "")
    try:
        data = await get_stock_price(symbol)
        if data and data.get("current_price"):
            return {
                "success": True,
                "symbol": symbol,
                "price": data["current_price"],
                "change": data.get("day_change", 0),
                "change_pct": data.get("day_change_pct", 0),
            }
        return {"success": False, "error": f"Price not found for {symbol}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _calculate_tax(user_id: PydanticObjectId, args: dict) -> dict:
    """Calculate tax on selling a holding."""
    from ...models.documents import Holding

    symbol = args.get("symbol", "").upper()
    qty_to_sell = args.get("quantity")

    holding = await Holding.find_one(Holding.user_id == user_id, Holding.symbol == symbol)
    if not holding:
        return {"success": False, "error": f"{symbol} not found in portfolio"}

    qty = qty_to_sell or holding.quantity
    if qty > holding.quantity:
        qty = holding.quantity

    price = holding.current_price or holding.avg_price
    invested = qty * holding.avg_price
    current = qty * price
    pnl = current - invested

    # Determine holding period
    first_buy = None
    for t in holding.transactions:
        if t.type == "BUY":
            try:
                td = datetime.strptime(t.date, "%Y-%m-%d") if isinstance(t.date, str) else t.date
                if first_buy is None or td < first_buy:
                    first_buy = td
            except Exception:
                pass

    is_ltcg = first_buy and first_buy < datetime.now() - timedelta(days=365)
    tax_type = "LTCG" if is_ltcg else "STCG"
    tax_rate = 0.125 if is_ltcg else 0.20
    exemption = 125000 if is_ltcg and pnl > 0 else 0
    taxable = max(0, pnl - exemption) if pnl > 0 else 0
    tax = taxable * tax_rate

    return {
        "success": True,
        "symbol": symbol,
        "quantity": qty,
        "sale_value": current,
        "pnl": pnl,
        "tax_type": tax_type,
        "tax_rate": f"{tax_rate*100:.1f}%",
        "exemption": exemption,
        "taxable_amount": taxable,
        "estimated_tax": tax,
        "holding_days": (datetime.now() - first_buy).days if first_buy else 0,
    }


async def _get_tax_harvesting(user_id: PydanticObjectId) -> dict:
    """Find tax harvesting opportunities."""
    from ...models.documents import Holding
    from ...services.market.price_service import get_bulk_prices

    holdings = await Holding.find(Holding.user_id == user_id).to_list()
    if not holdings:
        return {"success": True, "opportunities": [], "message": "No holdings"}

    symbols = [h.symbol for h in holdings if h.holding_type != "MF"]
    prices = await get_bulk_prices(symbols) if symbols else {}

    losses = []
    for h in holdings:
        p = prices.get(h.symbol, {})
        curr = p.get("current_price") or h.current_price or h.avg_price
        invested = h.avg_price * h.quantity
        current = curr * h.quantity
        pnl = current - invested
        if pnl < 0:
            losses.append({"symbol": h.symbol, "loss": abs(pnl), "value": current})

    losses.sort(key=lambda x: x["loss"], reverse=True)
    total_loss = sum(l["loss"] for l in losses)
    potential_tax_saved = total_loss * 0.20  # STCG rate

    return {
        "success": True,
        "opportunities": losses[:5],
        "total_harvestable_loss": total_loss,
        "potential_tax_saved": potential_tax_saved,
    }


async def _add_to_watchlist(user_id: PydanticObjectId, symbol: str) -> dict:
    """Add stock to watchlist."""
    from ...models.documents import WatchlistItem

    symbol = symbol.upper().replace(".NS", "")
    if not symbol:
        return {"success": False, "error": "Invalid symbol"}

    existing = await WatchlistItem.find_one(WatchlistItem.user_id == user_id, WatchlistItem.symbol == symbol)
    if existing:
        return {"success": True, "message": f"{symbol} is already in your watchlist"}

    watchlist = WatchlistItem(user_id=user_id, symbol=symbol)
    await watchlist.insert()

    return {"success": True, "message": f"{symbol} added to watchlist"}
