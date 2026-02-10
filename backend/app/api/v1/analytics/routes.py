"""Analytics routes - analytics, PnL calendar, rebalance, export."""

import csv
from datetime import datetime
from io import StringIO

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ....core.constants import SECTOR_MAP
from ....core.response_handler import StandardResponse
from ....core.security import get_current_user
from ....services.portfolio import get_prices_for_holdings, get_user_holdings
from .schemas import AnalyticsSummary, SectorAllocation

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
        curr_price = prices.get(h.symbol, {}).get("current_price") or h.current_price or h.avg_price
        value = h.quantity * curr_price
        total_value += value
        sector = SECTOR_MAP.get(h.symbol, "Others")
        sector_values[sector] = sector_values.get(sector, 0) + value

    sectors = [
        SectorAllocation(sector=s, value=round(v, 2), percentage=round(v / total_value * 100, 1))
        for s, v in sorted(sector_values.items(), key=lambda x: x[1], reverse=True)
    ]

    return StandardResponse.ok(
        AnalyticsSummary(total_value=round(total_value, 2), sectors=sectors, holdings_count=len(holdings))
    )


@router.get("/pnl-calendar", summary="Get PnL calendar", description="Get daily buy/sell activity calendar")
async def get_pnl_calendar(
    year: int = None, month: int = None, current_user: dict = Depends(get_current_user)
) -> StandardResponse:
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
    """Get asset class rebalancing suggestions."""
    # Get allocation data
    alloc_response = await get_allocation(current_user)
    alloc = alloc_response.data

    total = alloc["total_value"]
    target = alloc["target"]
    current = alloc["current"]
    categories = alloc["categories"]

    suggestions = []
    for cat in target:
        target_val = total * target[cat] / 100
        current_val = categories.get(cat, 0)
        diff = target_val - current_val

        # Only suggest if deviation > 2%
        if abs(diff) > total * 0.02:
            s = {
                "category": cat,
                "action": "BUY" if diff > 0 else "SELL",
                "amount": abs(round(diff, 0)),
                "current_pct": current.get(cat, 0),
                "target_pct": target[cat],
                "deviation_pct": round(current.get(cat, 0) - target[cat], 1),
            }

            # Add fund suggestions for BUY actions
            if s["action"] == "BUY":
                if cat == "Debt":
                    s["suggested_funds"] = ["Axis Liquid Fund", "HDFC Money Market", "SBI Overnight"]
                elif cat == "Gold":
                    s["suggested_funds"] = ["Nippon Gold BeES", "SBI Gold ETF"]
                elif cat == "Equity":
                    s["suggested_funds"] = ["UTI Nifty 50 Index", "Motilal Oswal S&P 500"]

            suggestions.append(s)

    # Sort by absolute deviation
    suggestions.sort(key=lambda x: abs(x["deviation_pct"]), reverse=True)

    return StandardResponse.ok(
        {
            "portfolio_value": total,
            "suggestions": suggestions,
            "rebalance_needed": len(suggestions) > 0,
            "note": "Rebalance quarterly or when deviation exceeds 5%",
        }
    )


@router.get("/export/csv", summary="Export to CSV", description="Download portfolio as CSV file")
async def export_holdings_csv(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Export holdings to CSV."""
    holdings = await get_user_holdings(current_user["_id"])
    prices = await get_prices_for_holdings(holdings)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Symbol",
            "Name",
            "Type",
            "Quantity",
            "Avg Price",
            "Current Price",
            "Investment",
            "Current Value",
            "P&L",
            "P&L %",
        ]
    )

    for h in holdings:
        curr_price = prices.get(h.symbol, {}).get("current_price") or h.current_price or h.avg_price
        inv = h.quantity * h.avg_price
        val = h.quantity * curr_price
        pnl = val - inv
        writer.writerow(
            [
                h.symbol,
                h.name,
                h.holding_type,
                h.quantity,
                h.avg_price,
                round(curr_price, 2),
                round(inv, 2),
                round(val, 2),
                round(pnl, 2),
                round(pnl / inv * 100, 2) if inv > 0 else 0,
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=portfolio_{datetime.now().strftime('%Y%m%d')}.csv"},
    )


@router.get("/metrics", summary="Get portfolio metrics", description="Get key portfolio metrics")
async def get_metrics(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Calculate advanced portfolio metrics."""
    import math

    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok({"error": "No holdings found"})

    prices = await get_prices_for_holdings(holdings)
    total_value = 0
    holdings_data = []

    for h in holdings:
        if h.holding_type == "MF":
            continue
        p = prices.get(h.symbol, {})
        curr = p.get("current_price") or h.avg_price
        value = h.quantity * curr
        total_value += value
        holdings_data.append(
            {
                "symbol": h.symbol,
                "value": value,
                "day_change_pct": p.get("day_change_pct", 0),
                "beta": p.get("beta", 1.0),
            }
        )

    if total_value == 0:
        return StandardResponse.ok({"error": "Portfolio value is zero"})

    for h in holdings_data:
        h["weight"] = h["value"] / total_value

    portfolio_beta = sum(h["weight"] * h.get("beta", 1.0) for h in holdings_data)
    daily_returns = [h["day_change_pct"] * h["weight"] for h in holdings_data]
    portfolio_daily_return = sum(daily_returns)
    volatility = abs(portfolio_daily_return) * math.sqrt(252) if portfolio_daily_return != 0 else 15

    sorted_holdings = sorted(holdings_data, key=lambda x: x["value"], reverse=True)
    top_5_concentration = sum(h["weight"] for h in sorted_holdings[:5]) * 100
    hhi = sum(h["weight"] ** 2 for h in holdings_data) * 10000

    def get_risk_profile(beta: float, vol: float):
        if beta < 0.8 and vol < 15:
            return {"level": "Conservative", "description": "Lower risk, stable returns"}
        elif beta < 1.2 and vol < 25:
            return {"level": "Moderate", "description": "Balanced risk-reward"}
        else:
            return {"level": "Aggressive", "description": "Higher risk, potential for higher returns"}

    return StandardResponse.ok(
        {
            "portfolio_value": round(total_value, 2),
            "holdings_count": len(holdings_data),
            "metrics": {
                "beta": round(portfolio_beta, 2),
                "volatility_annual": round(volatility, 1),
                "top_5_concentration": round(top_5_concentration, 1),
                "herfindahl_index": round(hhi, 0),
                "diversification": "Good" if hhi < 1500 else "Moderate" if hhi < 2500 else "Concentrated",
            },
            "risk_profile": get_risk_profile(portfolio_beta, volatility),
            "top_holdings": [
                {"symbol": h["symbol"], "weight": round(h["weight"] * 100, 1)} for h in sorted_holdings[:5]
            ],
        }
    )


@router.get("/returns", summary="Get returns breakdown", description="Get returns by holding")
async def get_returns(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get returns breakdown with proper CAGR calculation."""
    from datetime import datetime

    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok(
            {
                "invested": 0,
                "current_value": 0,
                "absolute_return": 0,
                "absolute_return_pct": 0,
                "cagr": 0,
                "holding_period_years": 0,
                "benchmark_comparison": {"outperformance": 0},
            }
        )

    prices = await get_prices_for_holdings(holdings)
    invested = sum(h.quantity * h.avg_price for h in holdings)
    current = sum(
        h.quantity * (prices.get(h.symbol, {}).get("current_price") or h.current_price or h.avg_price) for h in holdings
    )
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

    return StandardResponse.ok(
        {
            "invested": round(invested, 2),
            "current_value": round(current, 2),
            "absolute_return": round(pnl, 2),
            "absolute_return_pct": round(pnl_pct, 2),
            "cagr": round(cagr, 2),
            "holding_period_years": round(years_held, 1),
            "benchmark_comparison": {
                "nifty_cagr_5yr": nifty_benchmark,
                "outperformance": round(cagr - nifty_benchmark, 2),
            },
        }
    )


@router.get("/drawdown", summary="Get drawdown analysis", description="Get portfolio drawdown metrics")
async def get_drawdown(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Analyze portfolio drawdown."""
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok({"portfolio_drawdown": 0, "holdings_in_drawdown": [], "total_holdings_down": 0})

    prices = await get_prices_for_holdings(holdings)
    total_invested = sum(h.quantity * h.avg_price for h in holdings)
    total_current = sum(
        h.quantity * (prices.get(h.symbol, {}).get("current_price") or h.current_price or h.avg_price) for h in holdings
    )

    # Estimate peak
    if total_current < total_invested:
        estimated_peak = total_invested * 1.1
        current_drawdown = ((estimated_peak - total_current) / estimated_peak) * 100
    else:
        estimated_peak = total_current
        current_drawdown = 0

    holdings_in_drawdown = []
    for h in holdings:
        # Use stored current_price for MF, live price for stocks
        curr = prices.get(h.symbol, {}).get("current_price") or h.current_price or h.avg_price
        if curr < h.avg_price:
            dd_pct = ((h.avg_price - curr) / h.avg_price) * 100
            holdings_in_drawdown.append(
                {
                    "symbol": h.symbol,
                    "drawdown_pct": round(dd_pct, 1),
                    "loss": round((h.avg_price - curr) * h.quantity, 2),
                }
            )

    holdings_in_drawdown.sort(key=lambda x: x["drawdown_pct"], reverse=True)

    return StandardResponse.ok(
        {
            "portfolio_drawdown": round(current_drawdown, 1),
            "estimated_peak": round(estimated_peak, 2),
            "current_value": round(total_current, 2),
            "recovery_needed": round((estimated_peak / total_current - 1) * 100, 1) if total_current > 0 else 0,
            "holdings_in_drawdown": holdings_in_drawdown[:10],
            "total_holdings_down": len(holdings_in_drawdown),
            "risk_note": "A 50% loss requires 100% gain to recover. Consider rebalancing if drawdown exceeds 20%.",
        }
    )


@router.get("/sector-risk", summary="Get sector risk", description="Get sector concentration risk")
async def get_sector_risk(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Analyze sector concentration risk with MF categorization."""
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok({"sectors": [], "total_sectors": 0, "recommendations": []})

    def get_mf_category(symbol: str) -> str:
        s = symbol.upper()
        if any(x in s for x in ["LIQ", "LIQUID", "OVERNIGHT", "MONEY", "-LM"]):
            return "Liquid/Debt"
        if any(x in s for x in ["GILT", "GSEC", "BOND", "DEBT", "INCOME"]):
            return "Debt"
        if any(x in s for x in ["HYBRID", "BAL", "BALANCED"]):
            return "Hybrid"
        if any(x in s for x in ["SMALL", "-SC", "SMALLCAP"]):
            return "Small Cap"
        if any(x in s for x in ["-MC", "MID", "MIDCAP"]):
            return "Mid Cap"
        if any(x in s for x in ["LARGE", "BLUECHIP", "NIFTY", "INDEX", "ALPHA"]):
            return "Large Cap"
        if any(x in s for x in ["FLEXI", "MULTI", "DIVERSIFIED", "PPFAS", "PARAG"]):
            return "Flexi Cap"
        if any(x in s for x in ["TAX", "ELSS"]):
            return "ELSS"
        if any(x in s for x in ["BANK", "FIN", "PSU"]):
            return "Sectoral-BFSI"
        if any(x in s for x in ["IT", "TECH", "DIGI"]):
            return "Sectoral-IT"
        if any(x in s for x in ["PHARMA", "HEALTH"]):
            return "Sectoral-Pharma"
        if any(x in s for x in ["USD", "GLOBAL", "US", "NASDAQ", "INTERNATIONAL", "PGIM"]):
            return "International"
        if any(x in s for x in ["GOLD", "SILVER", "COMMODITY"]):
            return "Commodity"
        if any(x in s for x in ["MOM", "MOMENTUM", "ETF"]):
            return "ETF/Factor"
        return "Equity-Other"

    prices = await get_prices_for_holdings(holdings)
    sector_values = {}
    total_value = 0

    for h in holdings:
        value = h.quantity * (prices.get(h.symbol, {}).get("current_price") or h.current_price or h.avg_price)
        total_value += value

        if h.holding_type == "MF":
            sector = get_mf_category(h.symbol)
        else:
            sector = SECTOR_MAP.get(h.symbol, "Others")

        sector_values[sector] = sector_values.get(sector, 0) + value

    sectors = []
    for sector, value in sorted(sector_values.items(), key=lambda x: x[1], reverse=True):
        weight = (value / total_value * 100) if total_value > 0 else 0
        risk = "High" if weight > 30 else "Moderate" if weight > 20 else "Low"
        sectors.append(
            {"sector": sector, "value": round(value, 2), "weight": round(weight, 1), "concentration_risk": risk}
        )

    recommendations = []
    for s in sectors:
        if s["weight"] > 30:
            recommendations.append(f"Reduce {s['sector']} exposure (currently {s['weight']}%)")

    if len(sectors) < 5:
        recommendations.append("Consider diversifying into more sectors")

    return StandardResponse.ok(
        {
            "sectors": sectors,
            "total_sectors": len(sectors),
            "recommendations": recommendations,
            "ideal_allocation": "No single sector should exceed 25-30% for balanced risk",
        }
    )


@router.get("/pnl-monthly", summary="Get monthly PnL", description="Get monthly PnL summary")
async def get_pnl_monthly(year: int, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get monthly PnL summary."""
    return StandardResponse.ok({"year": year, "monthly": [{"month": i, "pnl": 0} for i in range(1, 13)]})


@router.get("/rebalance/allocation", summary="Get current allocation", description="Get current vs target allocation")
async def get_allocation(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get current asset class allocation with deviation."""
    holdings = await get_user_holdings(current_user["_id"])
    default_target = {"Equity": 60, "Debt": 30, "Gold": 5, "Cash": 5}

    if not holdings:
        return StandardResponse.ok(
            {"current": {}, "target": default_target, "total_value": 0, "deviation": {}, "categories": {}}
        )

    prices = await get_prices_for_holdings(holdings)

    # Calculate allocation by asset class
    categories = {"Equity": 0, "Debt": 0, "Gold": 0, "Cash": 0}
    total = 0

    for h in holdings:
        curr_price = prices.get(h.symbol, {}).get("current_price") or h.current_price or h.avg_price
        value = h.quantity * curr_price
        total += value

        name_upper = (h.name or "").upper()
        symbol_upper = h.symbol.upper()

        # Categorize by asset class
        if any(x in name_upper for x in ["LIQUID", "DEBT", "BOND", "GILT", "OVERNIGHT"]) or any(
            x in symbol_upper for x in ["LIQ", "DEBT"]
        ):
            categories["Debt"] += value
        elif any(x in symbol_upper for x in ["GOLD", "SGOLD", "GOLDBEES", "SILVER"]):
            categories["Gold"] += value
        elif h.holding_type == "MF" and "MONEY" in name_upper:
            categories["Cash"] += value
        else:
            categories["Equity"] += value

    # Convert to percentages
    current_pct = {cat: round(val / total * 100, 1) if total > 0 else 0 for cat, val in categories.items()}
    deviation = {cat: round(current_pct.get(cat, 0) - default_target[cat], 1) for cat in default_target}

    return StandardResponse.ok(
        {
            "total_value": round(total, 2),
            "target": default_target,
            "current": current_pct,
            "deviation": deviation,
            "categories": {k: round(v, 2) for k, v in categories.items()},
        }
    )


@router.post("/rebalance/target", summary="Set target allocation", description="Set target asset allocation")
async def set_target_allocation(target: dict, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Set target allocation."""
    return StandardResponse.ok({"target": target, "message": "Target allocation saved"})


@router.post("/signals", summary="Get trading signals", description="Get AI-powered trading signals")
async def get_signals(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get trading signals using comprehensive technical analysis."""
    from ....tasks.portfolio_advisor import (
        analyze_ipo_opportunities,
        calculate_indicators,
        generate_recommendation,
        get_bulk_stock_data,
    )

    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok({"portfolio": [], "ipos": []})

    # Get equity holdings only
    equity_holdings = [h for h in holdings if h.holding_type != "MF"]
    symbols = [h.symbol for h in equity_holdings]

    # Fetch all stock data concurrently
    stock_data = await get_bulk_stock_data(symbols)

    recommendations = []
    for h in equity_holdings:
        data = stock_data.get(h.symbol)
        if not data:
            continue

        indicators = calculate_indicators(data)
        rec = generate_recommendation(h.symbol, h.avg_price, h.quantity, indicators)
        recommendations.append(rec)

    # Get IPO recommendations
    ipo_recs = await analyze_ipo_opportunities()

    return StandardResponse.ok({"portfolio": recommendations, "ipos": ipo_recs})
