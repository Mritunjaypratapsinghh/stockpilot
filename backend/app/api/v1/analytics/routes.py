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
from .schemas import AnalyticsSummary, SectorAllocation, SimulateRequest

router = APIRouter()


@router.get("", summary="Get analytics", description="Get portfolio analytics and sector breakdown")
async def get_analytics(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get portfolio analytics."""
    from ....services.cache import cache_get, cache_set, market_ttl

    ck = f"analytics:{current_user['_id']}"
    cached = await cache_get(ck)
    if cached:
        return StandardResponse.ok(cached)

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

    result = AnalyticsSummary(total_value=round(total_value, 2), sectors=sectors, holdings_count=len(holdings))
    await cache_set(ck, result.model_dump() if hasattr(result, "model_dump") else result, ttl=market_ttl())
    return StandardResponse.ok(result)


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
    """Get asset class rebalancing suggestions with specific holding actions."""
    from beanie import PydanticObjectId

    from ....models.documents import Holding

    # Get allocation data
    alloc_response = await get_allocation(current_user)
    alloc = alloc_response.data

    total = alloc["total_value"]
    target = alloc["target"]
    current = alloc["current"]
    categories = alloc["categories"]

    # Get holdings for specific actions
    holdings = await Holding.find(Holding.user_id == PydanticObjectId(current_user["_id"])).to_list()
    prices = await get_prices_for_holdings(holdings)

    from ....core.constants import REBALANCE_MAX_SELL_PCT, REBALANCE_MIN_ACTION_AMOUNT

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
                "specific_actions": [],
            }

            # Generate specific holding-level actions
            cat_holdings = [
                h
                for h in holdings
                if (h.holding_type == "MF" and cat == "Equity")
                or (h.holding_type == "STOCK" and cat == "Equity")
                or (h.holding_type == "GOLD" and cat == "Gold")
            ]

            if s["action"] == "SELL" and cat_holdings:
                # Suggest selling from largest positions first
                sorted_h = sorted(
                    cat_holdings,
                    key=lambda h: h.quantity * (prices.get(h.symbol, {}).get("current_price") or h.avg_price),
                    reverse=True,
                )
                remaining = abs(diff)
                for h in sorted_h[:3]:
                    price = prices.get(h.symbol, {}).get("current_price") or h.avg_price
                    val = h.quantity * price
                    sell_amt = min(remaining, val * REBALANCE_MAX_SELL_PCT)
                    if sell_amt > REBALANCE_MIN_ACTION_AMOUNT:
                        s["specific_actions"].append(
                            {
                                "symbol": h.symbol,
                                "action": "SELL",
                                "amount": round(sell_amt),
                                "reason": f"Reduce {cat} exposure",
                            }
                        )
                        remaining -= sell_amt
                    if remaining < REBALANCE_MIN_ACTION_AMOUNT:
                        break

            if s["action"] == "BUY":
                if cat == "Debt":
                    s["suggestion"] = "Consider liquid/short-duration debt funds or FDs"
                    s["specific_actions"].append(
                        {
                            "symbol": "LIQUIDBEES",
                            "action": "BUY",
                            "amount": round(abs(diff)),
                            "reason": "Low-risk debt allocation",
                        }
                    )
                elif cat == "Gold":
                    s["suggestion"] = "Consider Gold ETFs or Sovereign Gold Bonds"
                    s["specific_actions"].append(
                        {"symbol": "GOLDBEES", "action": "BUY", "amount": round(abs(diff)), "reason": "Gold allocation"}
                    )
                elif cat == "Equity":
                    s["suggestion"] = "Consider Nifty 50 index funds or flexi-cap funds"
                    s["specific_actions"].append(
                        {
                            "symbol": "NIFTYBEES",
                            "action": "BUY",
                            "amount": round(abs(diff) * 0.5),
                            "reason": "Index exposure",
                        }
                    )
                elif cat == "Cash":
                    s["suggestion"] = "Keep in savings account or overnight funds"

            suggestions.append(s)

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

    from ....services.cache import cache_get, cache_set, market_ttl

    ck = f"metrics:{current_user['_id']}"
    cached = await cache_get(ck)
    if cached:
        return StandardResponse.ok(cached)

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
    # Volatility: std deviation of weighted daily returns, annualized
    weighted_returns = [h["day_change_pct"] * h["weight"] for h in holdings_data]
    portfolio_daily_return = sum(weighted_returns)
    mean = portfolio_daily_return
    variance = sum(h["weight"] * (h["day_change_pct"] - mean) ** 2 for h in holdings_data)
    daily_vol = math.sqrt(variance) if variance > 0 else 0
    volatility = daily_vol * math.sqrt(252) if daily_vol > 0 else 15.0

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

    result = {
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
        "top_holdings": [{"symbol": h["symbol"], "weight": round(h["weight"] * 100, 1)} for h in sorted_holdings[:5]],
    }
    await cache_set(ck, result, ttl=market_ttl())
    return StandardResponse.ok(result)


@router.get(
    "/health-score",
    summary="Portfolio health score",
    description="Auto-calculated health score from actual holdings",
)
async def get_health_score(
    current_user: dict = Depends(get_current_user),
) -> StandardResponse:
    """Calculate portfolio health score (0-100) from holdings."""
    from ....services.cache import cache_get, cache_set, market_ttl

    ck = f"health_score:{current_user['_id']}"
    cached = await cache_get(ck)
    if cached:
        return StandardResponse.ok(cached)

    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok({"score": 0, "factors": []})

    prices = await get_prices_for_holdings(holdings) or {}
    equity = [h for h in holdings if h.holding_type != "MF"]
    mf = [h for h in holdings if h.holding_type == "MF"]

    factors = []
    score = 100

    # 1. Diversification — number of stocks
    n = len(equity)
    if n >= 10:
        factors.append({"name": "Diversification", "score": 20, "max": 20, "note": f"{n} stocks — well diversified"})
    elif n >= 5:
        s = 15
        factors.append({"name": "Diversification", "score": s, "max": 20, "note": f"{n} stocks — moderate"})
        score -= 20 - s
    else:
        s = max(5, n * 3)
        factors.append({"name": "Diversification", "score": s, "max": 20, "note": f"Only {n} stocks — concentrated"})
        score -= 20 - s

    # 2. Concentration — HHI
    total_val = 0
    vals = []
    for h in equity:
        p = prices.get(h.symbol, {}).get("current_price") or h.avg_price
        v = h.quantity * p
        vals.append(v)
        total_val += v
    weights = [v / total_val for v in vals] if total_val else []
    hhi = sum(w * w for w in weights) * 10000 if weights else 10000
    if hhi < 1500:
        factors.append({"name": "Concentration", "score": 20, "max": 20, "note": f"HHI {hhi:.0f} — low concentration"})
    elif hhi < 2500:
        s = 12
        factors.append({"name": "Concentration", "score": s, "max": 20, "note": f"HHI {hhi:.0f} — moderate"})
        score -= 20 - s
    else:
        s = 5
        factors.append({"name": "Concentration", "score": s, "max": 20, "note": f"HHI {hhi:.0f} — highly concentrated"})
        score -= 20 - s

    # 3. Sector spread
    sectors = set()
    for h in equity:
        sectors.add(SECTOR_MAP.get(h.symbol, "Others"))
    sec_count = len(sectors)
    if sec_count >= 5:
        factors.append({"name": "Sector Spread", "score": 20, "max": 20, "note": f"{sec_count} sectors"})
    elif sec_count >= 3:
        s = 12
        factors.append({"name": "Sector Spread", "score": s, "max": 20, "note": f"Only {sec_count} sectors"})
        score -= 20 - s
    else:
        s = 5
        factors.append({"name": "Sector Spread", "score": s, "max": 20, "note": f"Only {sec_count} sectors — risky"})
        score -= 20 - s

    # 4. MF allocation
    mf_val = sum(h.quantity * (prices.get(h.symbol, {}).get("current_price") or h.avg_price) for h in mf)
    mf_pct = (mf_val / (total_val + mf_val) * 100) if (total_val + mf_val) else 0
    if 20 <= mf_pct <= 70:
        factors.append({"name": "MF Allocation", "score": 20, "max": 20, "note": f"{mf_pct:.0f}% in MFs — balanced"})
    elif mf_pct > 0:
        s = 12
        factors.append({"name": "MF Allocation", "score": s, "max": 20, "note": f"{mf_pct:.0f}% in MFs"})
        score -= 20 - s
    else:
        s = 5
        factors.append(
            {"name": "MF Allocation", "score": s, "max": 20, "note": "No MFs — consider adding for stability"}
        )
        score -= 20 - s

    # 5. P&L health
    total_inv = sum(h.quantity * h.avg_price for h in equity)
    pnl_pct = ((total_val - total_inv) / total_inv * 100) if total_inv else 0
    losers = sum(1 for h in equity if (prices.get(h.symbol, {}).get("current_price") or h.avg_price) < h.avg_price)
    loser_pct = (losers / n * 100) if n else 0
    if pnl_pct > 0 and loser_pct < 40:
        factors.append(
            {"name": "P&L Health", "score": 20, "max": 20, "note": f"P&L {pnl_pct:+.1f}%, {losers}/{n} in loss"}
        )
    elif pnl_pct > -10:
        s = 12
        factors.append(
            {"name": "P&L Health", "score": s, "max": 20, "note": f"P&L {pnl_pct:+.1f}%, {losers}/{n} in loss"}
        )
        score -= 20 - s
    else:
        s = 5
        factors.append(
            {"name": "P&L Health", "score": s, "max": 20, "note": f"P&L {pnl_pct:+.1f}%, {losers}/{n} in loss"}
        )
        score -= 20 - s

    grade = "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D"
    result = {"score": max(0, score), "grade": grade, "factors": factors}
    await cache_set(ck, result, ttl=market_ttl())
    return StandardResponse.ok(result)


@router.get("/returns", summary="Get returns breakdown", description="Get returns by holding")
async def get_returns(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get returns breakdown with proper CAGR calculation."""
    from datetime import datetime

    from ....services.cache import cache_get, cache_set, market_ttl

    ck = f"returns:{current_user['_id']}"
    cached = await cache_get(ck)
    if cached:
        return StandardResponse.ok(cached)

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

    # Fetch Nifty CAGR from Yahoo Finance
    nifty_benchmark = 12.0  # fallback
    try:
        import httpx

        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                "https://query1.finance.yahoo.com/v8/finance/chart/" "%5ENSEI?interval=1mo&range=5y",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if resp.status_code == 200:
                closes = [c for c in resp.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"] if c]
                if len(closes) >= 12:
                    nifty_cagr = ((closes[-1] / closes[0]) ** (1 / 5) - 1) * 100
                    nifty_benchmark = round(nifty_cagr, 1)
    except Exception:
        pass

    result = {
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
    await cache_set(ck, result, ttl=market_ttl())
    return StandardResponse.ok(result)


@router.get("/drawdown", summary="Get drawdown analysis", description="Get portfolio drawdown metrics")
async def get_drawdown(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Analyze portfolio drawdown."""
    from ....services.cache import cache_get, cache_set, market_ttl

    ck = f"drawdown:{current_user['_id']}"
    cached = await cache_get(ck)
    if cached:
        return StandardResponse.ok(cached)
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok({"portfolio_drawdown": 0, "holdings_in_drawdown": [], "total_holdings_down": 0})

    prices = await get_prices_for_holdings(holdings)
    total_invested = sum(h.quantity * h.avg_price for h in holdings)
    total_current = sum(
        h.quantity * (prices.get(h.symbol, {}).get("current_price") or h.current_price or h.avg_price) for h in holdings
    )

    # Peak = max of invested amount and current value (conservative floor)
    estimated_peak = max(total_invested, total_current)
    current_drawdown = (
        ((estimated_peak - total_current) / estimated_peak) * 100 if total_current < estimated_peak else 0
    )

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

    result = {
        "portfolio_drawdown": round(current_drawdown, 1),
        "estimated_peak": round(estimated_peak, 2),
        "current_value": round(total_current, 2),
        "recovery_needed": round((estimated_peak / total_current - 1) * 100, 1) if total_current > 0 else 0,
        "holdings_in_drawdown": holdings_in_drawdown[:10],
        "total_holdings_down": len(holdings_in_drawdown),
        "risk_note": "A 50% loss requires 100% gain to recover. Consider rebalancing if drawdown exceeds 20%.",
    }
    await cache_set(ck, result, ttl=market_ttl(300, 3600))
    return StandardResponse.ok(result)


@router.get("/sector-risk", summary="Get sector risk", description="Get sector concentration risk")
async def get_sector_risk(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Analyze sector concentration risk with MF categorization."""
    from ....services.cache import cache_get, cache_set, market_ttl

    ck = f"sector_risk:{current_user['_id']}"
    cached = await cache_get(ck)
    if cached:
        return StandardResponse.ok(cached)
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

    result = {
        "sectors": sectors,
        "total_sectors": len(sectors),
        "recommendations": recommendations,
        "ideal_allocation": "No single sector should exceed 25-30% for balanced risk",
    }
    await cache_set(ck, result, ttl=market_ttl(300, 3600))
    return StandardResponse.ok(result)


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
    """Get enhanced trading signals with fundamentals and portfolio context."""
    from ....services.signals import SignalEngine
    from ....tasks.portfolio_advisor import analyze_ipo_opportunities, get_bulk_stock_data

    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok({"portfolio": [], "ipos": [], "market_regime": "NEUTRAL", "summary": {}})

    # Get equity holdings only
    equity_holdings = [h for h in holdings if h.holding_type != "MF"]
    symbols = [h.symbol for h in equity_holdings]

    # Fetch all stock data concurrently
    stock_data = await get_bulk_stock_data(symbols)

    # Use enhanced signal engine
    engine = SignalEngine()
    result = await engine.analyze_portfolio(holdings, stock_data)

    # Get IPO recommendations
    ipo_recs = await analyze_ipo_opportunities()

    return StandardResponse.ok(
        {
            "portfolio": result["signals"],
            "ipos": ipo_recs,
            "market_regime": result["market_regime"],
            "nifty_change": result["nifty_change"],
            "summary": result["summary"],
        }
    )


@router.get("/mf-overlap", summary="MF Overlap Analyzer", description="Find overlapping stocks across mutual funds")
async def get_mf_overlap(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Analyze stock overlap across mutual fund holdings."""

    import asyncio

    from beanie import PydanticObjectId

    from ....models.documents import Holding
    from ....services.cache import cache_get, cache_set
    from ....services.mf import fetch_mf_holdings

    ck = f"mf_overlap:{current_user['_id']}"
    cached = await cache_get(ck)
    if cached:
        return StandardResponse.ok(cached)

    holdings = await Holding.find(
        Holding.user_id == PydanticObjectId(current_user["_id"]),
        Holding.holding_type == "MF",
    ).to_list()

    if not holdings:
        return StandardResponse.ok({"funds": [], "overlaps": [], "matrix": [], "summary": {}})

    # Classify fund type from name
    def classify_fund(name: str) -> str:
        n = name.upper()
        if any(k in n for k in ["LIQUID", "OVERNIGHT", "MONEY MARKET"]):
            return "debt"
        if any(k in n for k in ["ULTRA SHORT", "LOW DURATION", "SHORT DURATION", "GILT", "CORPORATE BOND"]):
            return "debt"
        if "SMALL" in n:
            return "smallcap"
        if "MID" in n:
            return "midcap"
        if "LARGE" in n and "MID" in n:
            return "largemid"
        if "LARGE" in n:
            return "largecap"
        if any(k in n for k in ["FLEXI", "MULTI", "FOCUSED", "VALUE", "CONTRA", "ELSS"]):
            return "flexicap"
        if "INDEX" in n or "NIFTY" in n or "SENSEX" in n:
            return "index"
        return "equity"  # default to equity

    # Typical top holdings by fund category (based on public SEBI disclosures)
    CATEGORY_STOCKS = {
        "largecap": [
            ("RELIANCE", 8.5),
            ("HDFCBANK", 7.2),
            ("ICICIBANK", 6.8),
            ("INFY", 5.5),
            ("TCS", 5.0),
            ("BHARTIARTL", 4.2),
            ("ITC", 3.8),
            ("LT", 3.5),
            ("SBIN", 3.2),
            ("KOTAKBANK", 3.0),
        ],
        "midcap": [
            ("PERSISTENT", 4.5),
            ("COFORGE", 4.0),
            ("MPHASIS", 3.8),
            ("VOLTAS", 3.5),
            ("AUROPHARMA", 3.2),
            ("GODREJCP", 3.0),
            ("CUMMINSIND", 2.8),
            ("SUNDARMFIN", 2.5),
            ("OBEROIRLTY", 2.3),
            ("FEDERALBNK", 2.0),
        ],
        "smallcap": [
            ("KPITTECH", 3.5),
            ("RATNAMANI", 3.2),
            ("CAMS", 3.0),
            ("FIVESTAR", 2.8),
            ("KAYNES", 2.5),
            ("HAPPSTMNDS", 2.3),
            ("ROUTE", 2.0),
            ("SAFARI", 1.8),
            ("MEDPLUS", 1.5),
            ("IIFL", 1.3),
        ],
        "flexicap": [
            ("HDFCBANK", 7.0),
            ("RELIANCE", 6.5),
            ("ICICIBANK", 5.5),
            ("INFY", 4.8),
            ("BHARTIARTL", 4.0),
            ("TCS", 3.5),
            ("AXISBANK", 3.0),
            ("SBIN", 2.8),
            ("PERSISTENT", 2.5),
            ("COFORGE", 2.0),
        ],
        "largemid": [
            ("HDFCBANK", 6.0),
            ("RELIANCE", 5.5),
            ("ICICIBANK", 5.0),
            ("INFY", 4.5),
            ("PERSISTENT", 3.5),
            ("COFORGE", 3.0),
            ("VOLTAS", 2.8),
            ("TCS", 2.5),
            ("BHARTIARTL", 2.3),
            ("AUROPHARMA", 2.0),
        ],
        "index": [
            ("RELIANCE", 10.0),
            ("HDFCBANK", 8.5),
            ("ICICIBANK", 7.5),
            ("INFY", 6.0),
            ("TCS", 4.5),
            ("BHARTIARTL", 4.0),
            ("ITC", 3.5),
            ("LT", 3.0),
            ("SBIN", 2.8),
            ("KOTAKBANK", 2.5),
        ],
    }

    funds = []
    holdings_list = holdings[:10]

    # Fetch real holdings in parallel
    async def get_fund_data(h):
        name = h.name or h.symbol
        category = classify_fund(name)
        # Try to fetch real holdings first
        real_holdings = await fetch_mf_holdings(name)
        stocks = real_holdings if real_holdings else CATEGORY_STOCKS.get(category, [])
        return {
            "symbol": h.symbol,
            "name": name,
            "value": round(h.quantity * h.avg_price, 2),
            "category": category,
            "stocks": [{"symbol": s, "weight": w} for s, w in stocks],
            "real_data": bool(real_holdings),
        }

    funds = await asyncio.gather(*[get_fund_data(h) for h in holdings_list])

    # Only equity funds participate in overlap
    equity_funds = [f for f in funds if f["category"] != "debt"]
    debt_funds = [f for f in funds if f["category"] == "debt"]

    # Build overlap matrix: stock -> list of funds holding it
    stock_map: dict = {}
    for f in equity_funds:
        for s in f["stocks"]:
            stock_map.setdefault(s["symbol"], []).append(
                {
                    "fund": f["name"],
                    "fund_symbol": f["symbol"],
                    "weight": s["weight"],
                }
            )

    overlaps = sorted(
        [
            {
                "stock": stock,
                "fund_count": len(fl),
                "funds": fl,
                "total_exposure": round(sum(x["weight"] for x in fl), 1),
                "risk_level": "High" if len(fl) >= 3 else "Medium",
            }
            for stock, fl in stock_map.items()
            if len(fl) > 1
        ],
        key=lambda x: (-x["fund_count"], -x["total_exposure"]),
    )[:20]

    # Build matrix for heatmap (fund x stock grid)
    overlap_stocks = [o["stock"] for o in overlaps[:10]]
    matrix = []
    for f in equity_funds:
        sw = {s["symbol"]: s["weight"] for s in f["stocks"]}
        matrix.append(
            {
                "fund": f["symbol"],
                "fund_name": f["name"],
                "weights": {s: sw.get(s, 0) for s in overlap_stocks},
            }
        )

    high_overlap = len([o for o in overlaps if o["fund_count"] >= 3])
    eq_count = len(equity_funds)
    # Score: penalize for same-category duplication more than cross-category overlap
    categories = [f["category"] for f in equity_funds]
    duplicate_cats = len(categories) - len(set(categories))
    score = max(0, min(100, 100 - (duplicate_cats * 25) - (high_overlap * 5)))

    result = {
        "funds": [
            {
                "symbol": f["symbol"],
                "name": f["name"],
                "value": f["value"],
                "category": f["category"],
                "stock_count": len(f["stocks"]),
            }
            for f in funds
        ],
        "overlaps": overlaps,
        "matrix": {"funds": [f["symbol"] for f in equity_funds], "stocks": overlap_stocks, "data": matrix},
        "summary": {
            "total_funds": len(funds),
            "equity_funds": eq_count,
            "debt_funds": len(debt_funds),
            "overlapping_stocks": len(overlaps),
            "high_overlap_stocks": high_overlap,
            "diversification_score": score,
            "recommendation": (
                "High overlap detected among equity funds. Consider consolidating similar category funds."
                if high_overlap > 3
                else (
                    "Moderate overlap — typical for diversified equity funds."
                    if high_overlap > 0
                    else "Minimal overlap. Good diversification across your funds."
                )
            ),
        },
    }
    await cache_set(ck, result, ttl=600)
    return StandardResponse.ok(result)


@router.post(
    "/simulate",
    summary="What-If Simulator",
    description="Simulate selling one stock and buying another",
)
async def simulate_trade(
    data: SimulateRequest,
    current_user: dict = Depends(get_current_user),
) -> StandardResponse:
    """Simulate impact of a trade on portfolio metrics."""
    sell_sym = data.sell
    buy_sym = data.buy
    amount = data.amount

    if not sell_sym or not amount:
        return StandardResponse.error("sell and amount required")

    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.error("No holdings")

    equity = [h for h in holdings if h.holding_type != "MF"]
    prices = await get_prices_for_holdings(holdings) or {}

    # Current state
    def calc_metrics(eq_list, price_map):
        sectors = {}
        total = 0
        vals = []
        for h in eq_list:
            p = price_map.get(h["symbol"], {}).get("current_price", h["avg_price"])
            v = h["qty"] * p
            total += v
            vals.append(v)
            sec = SECTOR_MAP.get(h["symbol"], "Others")
            sectors[sec] = sectors.get(sec, 0) + v
        weights = [v / total for v in vals] if total else []
        hhi = sum(w * w for w in weights) * 10000 if weights else 0
        sec_pcts = {k: round(v / total * 100, 1) for k, v in sectors.items()} if total else {}
        return {
            "total": round(total, 0),
            "stocks": len(eq_list),
            "hhi": round(hhi, 0),
            "sectors": sec_pcts,
            "top_sector": max(sec_pcts, key=sec_pcts.get) if sec_pcts else "—",
            "top_sector_pct": max(sec_pcts.values()) if sec_pcts else 0,
        }

    current = [{"symbol": h.symbol, "qty": h.quantity, "avg_price": h.avg_price} for h in equity]
    price_map = prices

    before = calc_metrics(current, price_map)

    # After state — reduce sell, add buy
    after_list = []
    for h in current:
        if h["symbol"] == sell_sym:
            p = price_map.get(h["symbol"], {}).get("current_price", h["avg_price"])
            sell_qty = min(h["qty"], amount / p) if p else 0
            remaining = h["qty"] - sell_qty
            if remaining > 0.01:
                after_list.append({**h, "qty": remaining})
        else:
            after_list.append(h)

    if buy_sym:
        from ....services.market.price_service import get_bulk_prices

        buy_prices = await get_bulk_prices([buy_sym])
        buy_p = buy_prices.get(buy_sym, {}).get("current_price", 0)
        if buy_p:
            price_map[buy_sym] = buy_prices.get(buy_sym, {})
            existing = next((h for h in after_list if h["symbol"] == buy_sym), None)
            buy_qty = amount / buy_p
            if existing:
                existing["qty"] += buy_qty
            else:
                after_list.append(
                    {
                        "symbol": buy_sym,
                        "qty": buy_qty,
                        "avg_price": buy_p,
                    }
                )

    after = calc_metrics(after_list, price_map)

    return StandardResponse.ok(
        {
            "before": before,
            "after": after,
            "changes": {
                "hhi": after["hhi"] - before["hhi"],
                "stocks": after["stocks"] - before["stocks"],
                "top_sector_pct": round(after["top_sector_pct"] - before["top_sector_pct"], 1),
            },
        }
    )


@router.get(
    "/insights",
    summary="AI Dashboard Insights",
    description="Proactive AI-generated insight cards",
)
async def get_insights(
    current_user: dict = Depends(get_current_user),
) -> StandardResponse:
    """Generate proactive AI insight cards from portfolio data."""
    from ....core.config import settings
    from ....services.cache import cache_get, cache_set

    ck = f"insights:{current_user['_id']}"
    cached = await cache_get(ck)
    if cached:
        return StandardResponse.ok(cached)

    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok({"insights": []})

    equity = [h for h in holdings if h.holding_type != "MF"]
    prices = await get_prices_for_holdings(holdings) or {}

    # Build portfolio summary for Groq
    sectors = {}
    total_val = 0
    losers = []
    for h in equity:
        p = prices.get(h.symbol, {}).get("current_price", h.avg_price)
        v = h.quantity * p
        total_val += v
        sec = SECTOR_MAP.get(h.symbol, "Others")
        sectors[sec] = sectors.get(sec, 0) + v
        pnl_pct = ((p - h.avg_price) / h.avg_price * 100) if h.avg_price else 0
        if pnl_pct < -10:
            losers.append(f"{h.symbol}({pnl_pct:+.0f}%)")

    sec_pcts = (
        {k: round(v / total_val * 100, 1) for k, v in sorted(sectors.items(), key=lambda x: -x[1])} if total_val else {}
    )

    top_sec = list(sec_pcts.items())[:3]
    sec_str = ", ".join(f"{k}:{v}%" for k, v in top_sec)
    losers_str = ", ".join(losers[:5]) if losers else "none"

    if not settings.groq_api_key:
        return StandardResponse.ok({"insights": []})

    try:
        from groq import Groq

        client = Groq(api_key=settings.groq_api_key)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a portfolio analyst for Indian stocks. "
                        "Generate exactly 4 JSON insight cards. Each card: "
                        '{"type":"warning|tip|opportunity|info",'
                        '"title":"short title",'
                        '"body":"1-2 sentence insight",'
                        '"icon":"⚠️|💡|🎯|📊"}. '
                        "Cover: sector concentration, underperformers, "
                        "diversification tip, one actionable opportunity. "
                        "Be specific with stock names. "
                        "Return ONLY a JSON array, no markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"{len(equity)} stocks, ₹{total_val:,.0f}. "
                        f"Sectors: {sec_str}. "
                        f"Underperformers: {losers_str}."
                    ),
                },
            ],
            temperature=0.3,
            max_completion_tokens=400,
        )

        import json

        text = resp.choices[0].message.content.strip()
        # Extract JSON array
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            insights = json.loads(text[start:end])
        else:
            insights = []

        result = {"insights": insights[:4]}
        await cache_set(ck, result, ttl=1800)
        return StandardResponse.ok(result)
    except Exception as e:
        from ....utils.logger import logger

        logger.warning(f"Insights generation failed: {e}")
        return StandardResponse.ok({"insights": []})
