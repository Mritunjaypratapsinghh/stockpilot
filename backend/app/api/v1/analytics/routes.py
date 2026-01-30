"""Analytics routes - analytics, PnL calendar, rebalance, export"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from datetime import datetime
from io import StringIO
import csv

from ....core.security import get_current_user
from ....core.response_handler import StandardResponse
from ....services.portfolio import get_user_holdings, get_prices_for_holdings
from ....core.constants import SECTOR_MAP
from .schemas import SectorAllocation, AnalyticsSummary, PnLCalendarEntry, RebalanceSuggestion

router = APIRouter()


@router.get("")
@router.get("/")
async def get_analytics(current_user: dict = Depends(get_current_user)):
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok(AnalyticsSummary(total_value=0, sectors=[], holdings_count=0))

    prices = await get_prices_for_holdings(holdings)
    sector_values = {}
    total_value = 0

    for h in holdings:
        curr_price = prices.get(h.symbol, {}).get("current_price") or h.avg_price
        value = h.quantity * curr_price
        total_value += value
        sector = SECTOR_MAP.get(h.symbol, "Others")
        sector_values[sector] = sector_values.get(sector, 0) + value

    sectors = [SectorAllocation(sector=s, value=round(v, 2), percentage=round(v / total_value * 100, 1))
               for s, v in sorted(sector_values.items(), key=lambda x: x[1], reverse=True)]

    return StandardResponse.ok(AnalyticsSummary(total_value=round(total_value, 2), sectors=sectors, holdings_count=len(holdings)))


@router.get("/pnl-calendar")
async def get_pnl_calendar(current_user: dict = Depends(get_current_user)):
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok({"calendar": []})

    calendar = {}
    for h in holdings:
        for t in h.transactions:
            date = t.date[:10] if isinstance(t.date, str) else t.date.strftime("%Y-%m-%d")
            if date not in calendar:
                calendar[date] = {"date": date, "buy": 0, "sell": 0}
            amount = t.quantity * t.price
            if t.type == "BUY":
                calendar[date]["buy"] += amount
            else:
                calendar[date]["sell"] += amount

    entries = [PnLCalendarEntry(**c) for c in sorted(calendar.values(), key=lambda x: x["date"], reverse=True)[:30]]
    return StandardResponse.ok({"calendar": entries})


@router.get("/rebalance")
async def get_rebalance_suggestions(current_user: dict = Depends(get_current_user)):
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok({"suggestions": [], "current_allocation": {}})

    prices = await get_prices_for_holdings(holdings)
    sector_values = {}
    total_value = 0

    for h in holdings:
        curr_price = prices.get(h.symbol, {}).get("current_price") or h.avg_price
        value = h.quantity * curr_price
        total_value += value
        sector = SECTOR_MAP.get(h.symbol, "Others")
        sector_values[sector] = sector_values.get(sector, 0) + value

    target = {"IT": 25, "Banking": 20, "Finance": 15, "Pharma": 10, "FMCG": 10, "Others": 20}
    suggestions = []

    for sector, target_pct in target.items():
        current_pct = (sector_values.get(sector, 0) / total_value * 100) if total_value > 0 else 0
        diff = target_pct - current_pct
        if abs(diff) > 5:
            action = "Increase" if diff > 0 else "Decrease"
            suggestions.append(RebalanceSuggestion(sector=sector, current_pct=round(current_pct, 1), target_pct=target_pct, action=action))

    return StandardResponse.ok({"suggestions": suggestions, "current_allocation": {s: round(v / total_value * 100, 1) for s, v in sector_values.items()}})


@router.get("/export/csv")
async def export_holdings_csv(current_user: dict = Depends(get_current_user)):
    holdings = await get_user_holdings(current_user["_id"])
    prices = await get_prices_for_holdings(holdings)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Symbol", "Name", "Type", "Quantity", "Avg Price", "Current Price", "Investment", "Current Value", "P&L", "P&L %"])

    for h in holdings:
        curr_price = prices.get(h.symbol, {}).get("current_price") or h.avg_price
        inv = h.quantity * h.avg_price
        val = h.quantity * curr_price
        pnl = val - inv
        writer.writerow([h.symbol, h.name, h.holding_type, h.quantity, h.avg_price, round(curr_price, 2), round(inv, 2), round(val, 2), round(pnl, 2), round(pnl / inv * 100, 2) if inv > 0 else 0])

    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=portfolio_{datetime.now().strftime('%Y%m%d')}.csv"})
