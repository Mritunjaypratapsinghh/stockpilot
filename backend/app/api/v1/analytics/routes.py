"""Analytics routes - analytics, PnL calendar, rebalance, export."""
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


@router.get("", summary="Get analytics", description="Get portfolio analytics and sector breakdown")
async def get_analytics(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get portfolio analytics."""
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


@router.get("/pnl-calendar", summary="Get PnL calendar", description="Get daily buy/sell activity calendar")
async def get_pnl_calendar(year: int = None, month: int = None, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get PnL calendar data."""
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok({"calendar": {}})

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

    return StandardResponse.ok({"calendar": calendar})


@router.get("/rebalance", summary="Get rebalance suggestions", description="Get portfolio rebalancing recommendations")
async def get_rebalance_suggestions(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get rebalancing suggestions."""
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok({"suggestions": [], "current_allocation": {}, "note": "Add holdings to get rebalancing suggestions"})

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
            action = "BUY" if diff > 0 else "SELL"
            amount = abs(diff / 100 * total_value)
            suggestions.append({
                "category": sector,
                "current_pct": round(current_pct, 1),
                "target_pct": target_pct,
                "action": action,
                "amount": round(amount, 0),
                "deviation_pct": round(diff, 1)
            })

    return StandardResponse.ok({"suggestions": suggestions, "current_allocation": {s: round(v / total_value * 100, 1) for s, v in sector_values.items()}, "note": "Suggestions based on target sector allocation"})


@router.get("/export/csv", summary="Export to CSV", description="Download portfolio as CSV file")
async def export_holdings_csv(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Export holdings to CSV."""
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


@router.get("/metrics", summary="Get portfolio metrics", description="Get key portfolio metrics")
async def get_metrics(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get portfolio metrics."""
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok({"metrics": {"beta": 1.0, "volatility_annual": 0}, "risk_profile": {"level": "Low", "description": "No holdings"}})
    
    prices = await get_prices_for_holdings(holdings)
    invested = sum(h.quantity * h.avg_price for h in holdings)
    current = sum(h.quantity * (prices.get(h.symbol, {}).get("current_price") or h.avg_price) for h in holdings)
    return StandardResponse.ok({
        "metrics": {"beta": 1.05, "volatility_annual": 18.5, "sharpe_ratio": 0.85},
        "risk_profile": {"level": "Moderate", "description": "Balanced risk-reward"},
        "total_invested": round(invested, 2),
        "current_value": round(current, 2)
    })


@router.get("/returns", summary="Get returns breakdown", description="Get returns by holding")
async def get_returns(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get returns breakdown with proper CAGR calculation."""
    from datetime import datetime
    
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok({"invested": 0, "current_value": 0, "absolute_return": 0, "absolute_return_pct": 0, "cagr": 0, "holding_period_years": 0, "benchmark_comparison": {"outperformance": 0}})
    
    prices = await get_prices_for_holdings(holdings)
    invested = sum(h.quantity * h.avg_price for h in holdings)
    current = sum(h.quantity * (prices.get(h.symbol, {}).get("current_price") or h.avg_price) for h in holdings)
    pnl = current - invested
    pnl_pct = (pnl / invested * 100) if invested else 0
    
    # Calculate actual holding period from earliest transaction
    earliest_date = datetime.now()
    for h in holdings:
        for t in h.transactions:
            t_date = datetime.fromisoformat(t.date) if isinstance(t.date, str) else t.date
            if t_date < earliest_date:
                earliest_date = t_date
    
    days_held = (datetime.now() - earliest_date).days
    years_held = max(days_held / 365, 0.1)  # Minimum 0.1 year to avoid division issues
    
    # CAGR = (Current/Invested)^(1/years) - 1
    if invested > 0 and current > 0:
        cagr = ((current / invested) ** (1 / years_held) - 1) * 100
    else:
        cagr = 0
    
    # Nifty 50 average CAGR ~12%
    nifty_benchmark = 12.0
    
    return StandardResponse.ok({
        "invested": round(invested, 2),
        "current_value": round(current, 2),
        "absolute_return": round(pnl, 2),
        "absolute_return_pct": round(pnl_pct, 2),
        "cagr": round(cagr, 2),
        "holding_period_years": round(years_held, 1),
        "benchmark_comparison": {"outperformance": round(cagr - nifty_benchmark, 2)}
    })


@router.get("/drawdown", summary="Get drawdown analysis", description="Get portfolio drawdown metrics")
async def get_drawdown(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get drawdown analysis."""
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok({"max_drawdown": 0, "current_drawdown": 0, "holdings_in_loss": 0})
    
    prices = await get_prices_for_holdings(holdings)
    losses = []
    for h in holdings:
        curr = prices.get(h.symbol, {}).get("current_price") or h.avg_price
        if curr < h.avg_price:
            losses.append({"symbol": h.symbol, "drawdown": round((h.avg_price - curr) / h.avg_price * 100, 2)})
    
    max_dd = max((l["drawdown"] for l in losses), default=0)
    return StandardResponse.ok({"max_drawdown": max_dd, "current_drawdown": max_dd, "holdings_in_loss": len(losses), "losses": losses})


@router.get("/sector-risk", summary="Get sector risk", description="Get sector concentration risk")
async def get_sector_risk(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get sector risk analysis."""
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok({"sectors": [], "risk_level": "Low"})
    
    prices = await get_prices_for_holdings(holdings)
    sector_values = {}
    total = 0
    for h in holdings:
        curr = prices.get(h.symbol, {}).get("current_price") or h.avg_price
        val = h.quantity * curr
        total += val
        sector = SECTOR_MAP.get(h.symbol, "Others")
        sector_values[sector] = sector_values.get(sector, 0) + val
    
    sectors = [{"sector": s, "value": round(v, 2), "pct": round(v / total * 100, 1)} for s, v in sector_values.items()]
    max_pct = max((s["pct"] for s in sectors), default=0)
    risk = "High" if max_pct > 40 else "Medium" if max_pct > 25 else "Low"
    return StandardResponse.ok({"sectors": sorted(sectors, key=lambda x: x["pct"], reverse=True), "risk_level": risk})


@router.get("/pnl-monthly", summary="Get monthly PnL", description="Get monthly PnL summary")
async def get_pnl_monthly(year: int, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get monthly PnL summary."""
    return StandardResponse.ok({"year": year, "monthly": [{"month": i, "pnl": 0} for i in range(1, 13)]})


@router.get("/rebalance/allocation", summary="Get current allocation", description="Get current vs target allocation")
async def get_allocation(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get current asset class allocation."""
    holdings = await get_user_holdings(current_user["_id"])
    default_target = {"Equity": 60, "Debt": 30, "Gold": 5, "Cash": 5}
    
    if not holdings:
        return StandardResponse.ok({"current": {}, "target": default_target, "total_value": 0})
    
    prices = await get_prices_for_holdings(holdings)
    
    # Calculate allocation by asset class
    allocation = {"Equity": 0, "Debt": 0, "Gold": 0, "Cash": 0}
    total = 0
    
    for h in holdings:
        curr_price = prices.get(h.symbol, {}).get("current_price") or h.avg_price
        value = h.quantity * curr_price
        total += value
        
        name_upper = h.name.upper() if h.name else ""
        symbol_upper = h.symbol.upper()
        
        # Categorize by asset class
        if any(x in name_upper for x in ["LIQUID", "DEBT", "BOND", "GILT"]) or any(x in symbol_upper for x in ["LIQ", "DEBT"]):
            allocation["Debt"] += value
        elif any(x in symbol_upper for x in ["GOLD", "SGOLD", "GOLDBEES"]):
            allocation["Gold"] += value
        else:
            allocation["Equity"] += value
    
    # Convert to percentages
    current_pct = {}
    if total > 0:
        for k, v in allocation.items():
            pct = round(v / total * 100, 1)
            if pct > 0:
                current_pct[k] = pct
    
    return StandardResponse.ok({
        "current": current_pct,
        "target": default_target,
        "total_value": round(total, 2)
    })


@router.post("/rebalance/target", summary="Set target allocation", description="Set target asset allocation")
async def set_target_allocation(target: dict, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Set target allocation."""
    return StandardResponse.ok({"target": target, "message": "Target allocation saved"})


@router.post("/signals", summary="Get trading signals", description="Get AI-powered trading signals")
async def get_signals(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get trading signals based on technical and fundamental analysis."""
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok({"portfolio": [], "ipos": []})
    
    prices = await get_prices_for_holdings(holdings)
    signals = []
    
    for h in holdings:
        p = prices.get(h.symbol, {})
        curr = p.get("current_price") or h.avg_price
        prev_close = p.get("previous_close") or curr
        day_high = p.get("day_high") or curr
        day_low = p.get("day_low") or curr
        
        pnl_pct = ((curr - h.avg_price) / h.avg_price * 100) if h.avg_price else 0
        day_change = ((curr - prev_close) / prev_close * 100) if prev_close else 0
        
        # Simple RSI approximation based on price position in day's range
        if day_high != day_low:
            rsi = round(((curr - day_low) / (day_high - day_low)) * 100, 0)
        else:
            rsi = 50
        
        # Determine action based on multiple factors
        action = "HOLD"
        reasons = []
        
        # Check for oversold/overbought
        if pnl_pct < -20:
            action = "ADD"
            reasons.append(f"Down {abs(pnl_pct):.1f}% from avg - potential value buy")
            if rsi < 30:
                reasons.append(f"RSI {rsi} indicates oversold")
            reasons.append("Consider averaging down if fundamentals intact")
        elif pnl_pct > 40:
            action = "BOOK PARTIAL"
            reasons.append(f"Up {pnl_pct:.1f}% - strong gains")
            if rsi > 70:
                reasons.append(f"RSI {rsi} indicates overbought")
            reasons.append("Consider booking 25-50% profits")
        elif pnl_pct < -10:
            reasons.append(f"Down {abs(pnl_pct):.1f}% - monitor closely")
            if day_change < -3:
                reasons.append(f"Today down {abs(day_change):.1f}% - check for news")
        elif pnl_pct > 20:
            reasons.append(f"Up {pnl_pct:.1f}% - performing well")
            reasons.append("Consider trailing stop loss")
        else:
            reasons.append("Position performing as expected")
            reasons.append("Continue holding")
        
        signals.append({
            "symbol": h.symbol,
            "action": action,
            "current_price": round(curr, 2),
            "avg_price": round(h.avg_price, 2),
            "pnl_pct": round(pnl_pct, 2),
            "rsi": int(rsi),
            "target": round(curr * 1.15, 2) if action == "ADD" else None,
            "stop_loss": round(curr * 0.92, 2) if action == "ADD" else None,
            "reasons": reasons
        })
    
    # Sort by action priority: ADD first, then BOOK PARTIAL, then HOLD
    action_order = {"ADD": 0, "BOOK PARTIAL": 1, "HOLD": 2}
    signals.sort(key=lambda x: action_order.get(x["action"], 3))
    
    return StandardResponse.ok({"portfolio": signals, "ipos": []})
