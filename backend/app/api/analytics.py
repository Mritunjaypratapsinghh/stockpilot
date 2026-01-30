from fastapi import APIRouter, Depends
from datetime import datetime
from beanie import PydanticObjectId
import math

from ..models.documents import Holding
from ..api.auth import get_current_user
from ..services.price_service import get_bulk_prices
from ..api.portfolio import SECTOR_MAP

router = APIRouter()


async def get_user_holdings(user_id: str):
    return await Holding.find(Holding.user_id == PydanticObjectId(user_id)).to_list()


async def get_prices_for_holdings(holdings):
    symbols = [h.symbol for h in holdings if h.holding_type != "MF"]
    return await get_bulk_prices(symbols) if symbols else {}


def get_risk_profile(beta: float, volatility: float) -> dict:
    if beta < 0.8 and volatility < 15:
        return {"level": "Conservative", "description": "Lower risk, stable returns"}
    elif beta < 1.2 and volatility < 25:
        return {"level": "Moderate", "description": "Balanced risk-reward"}
    return {"level": "Aggressive", "description": "Higher risk, potential for higher returns"}


@router.get("/metrics")
async def get_portfolio_metrics(current_user: dict = Depends(get_current_user)):
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return {"error": "No holdings found"}

    prices = await get_prices_for_holdings(holdings)
    total_value = 0
    holdings_data = []

    for h in holdings:
        p = prices.get(h.symbol, {})
        curr_price = p.get("current_price") or h.current_price or h.avg_price
        value = h.quantity * curr_price
        total_value += value
        holdings_data.append({"symbol": h.symbol, "value": value, "day_change_pct": p.get("day_change_pct", 0), "beta": p.get("beta", 1.0)})

    if total_value == 0:
        return {"error": "Portfolio value is zero"}

    for h in holdings_data:
        h["weight"] = h["value"] / total_value

    portfolio_beta = sum(h["weight"] * h.get("beta", 1.0) for h in holdings_data)
    portfolio_daily_return = sum(h["day_change_pct"] * h["weight"] for h in holdings_data)
    volatility = abs(portfolio_daily_return) * math.sqrt(252) if portfolio_daily_return != 0 else 15

    sorted_holdings = sorted(holdings_data, key=lambda x: x["value"], reverse=True)
    hhi = sum(h["weight"] ** 2 for h in holdings_data) * 10000

    return {
        "portfolio_value": round(total_value, 2), "holdings_count": len(holdings_data),
        "metrics": {"beta": round(portfolio_beta, 2), "volatility_annual": round(volatility, 1), "top_5_concentration": round(sum(h["weight"] for h in sorted_holdings[:5]) * 100, 1), "herfindahl_index": round(hhi, 0), "diversification": "Good" if hhi < 1500 else "Moderate" if hhi < 2500 else "Concentrated"},
        "risk_profile": get_risk_profile(portfolio_beta, volatility),
        "top_holdings": [{"symbol": h["symbol"], "weight": round(h["weight"] * 100, 1)} for h in sorted_holdings[:5]]
    }


@router.get("/returns")
async def get_returns_analysis(current_user: dict = Depends(get_current_user)):
    holdings = await get_user_holdings(current_user["_id"])
    total_invested = sum(h.quantity * h.avg_price for h in holdings)
    total_current = sum(h.quantity * (h.current_price or h.avg_price) for h in holdings)

    absolute_return = total_current - total_invested
    all_txns = [t for h in holdings for t in h.transactions if t.type == "BUY"]

    cagr = years = 0
    if all_txns:
        first_date = min(datetime.fromisoformat(t.date) for t in all_txns)
        years = max(0.1, (datetime.now() - first_date).days / 365)
        cagr = ((total_current / total_invested) ** (1 / years) - 1) * 100 if total_invested > 0 else 0

    return {"invested": round(total_invested, 2), "current_value": round(total_current, 2), "absolute_return": round(absolute_return, 2), "absolute_return_pct": round((absolute_return / total_invested * 100) if total_invested > 0 else 0, 2), "cagr": round(cagr, 2), "holding_period_years": round(years, 1), "benchmark_comparison": {"nifty_cagr_5yr": 12.5, "outperformance": round(cagr - 12.5, 2) if cagr else 0}}


@router.get("/drawdown")
async def get_drawdown_analysis(current_user: dict = Depends(get_current_user)):
    holdings = await get_user_holdings(current_user["_id"])
    total_invested = sum(h.quantity * h.avg_price for h in holdings)
    total_current = sum(h.quantity * (h.current_price or h.avg_price) for h in holdings)

    estimated_peak = total_invested * 1.1 if total_current < total_invested else total_current
    current_drawdown = ((estimated_peak - total_current) / estimated_peak) * 100 if total_current < total_invested else 0

    holdings_in_drawdown = []
    for h in holdings:
        curr_price = h.current_price or h.avg_price
        if curr_price < h.avg_price:
            holdings_in_drawdown.append({"symbol": h.symbol, "drawdown_pct": round((h.avg_price - curr_price) / h.avg_price * 100, 1), "loss": round((h.avg_price - curr_price) * h.quantity, 2)})
    holdings_in_drawdown.sort(key=lambda x: x["drawdown_pct"], reverse=True)

    return {"portfolio_drawdown": round(current_drawdown, 1), "estimated_peak": round(estimated_peak, 2), "current_value": round(total_current, 2), "recovery_needed": round((estimated_peak / total_current - 1) * 100, 1) if total_current > 0 else 0, "holdings_in_drawdown": holdings_in_drawdown[:10], "total_holdings_down": len(holdings_in_drawdown)}


@router.get("/sector-risk")
async def get_sector_risk(current_user: dict = Depends(get_current_user)):
    holdings = await get_user_holdings(current_user["_id"])

    def get_mf_category(symbol: str) -> str:
        s = symbol.upper()
        if any(x in s for x in ['LIQ', 'LIQUID', 'OVERNIGHT', 'MONEY']):
            return "Liquid/Debt"
        if any(x in s for x in ['GILT', 'BOND', 'DEBT']):
            return "Debt"
        if any(x in s for x in ['SMALL', 'SMALLCAP']):
            return "Small Cap"
        if any(x in s for x in ['MID', 'MIDCAP']):
            return "Mid Cap"
        if any(x in s for x in ['LARGE', 'NIFTY', 'INDEX']):
            return "Large Cap"
        if any(x in s for x in ['FLEXI', 'MULTI']):
            return "Flexi Cap"
        return "Equity-Other"

    sector_values = {}
    total_value = 0
    for h in holdings:
        value = h.quantity * (h.current_price or h.avg_price)
        total_value += value
        sector = get_mf_category(h.symbol) if h.holding_type == "MF" else SECTOR_MAP.get(h.symbol, "Others")
        sector_values[sector] = sector_values.get(sector, 0) + value

    sectors = [{"sector": s, "value": round(v, 2), "weight": round(v / total_value * 100, 1) if total_value > 0 else 0, "concentration_risk": "High" if v / total_value > 0.3 else "Moderate" if v / total_value > 0.2 else "Low"} for s, v in sorted(sector_values.items(), key=lambda x: x[1], reverse=True)]
    recommendations = [f"Reduce {s['sector']} exposure (currently {s['weight']}%)" for s in sectors if s["weight"] > 30]
    if len(sectors) < 5:
        recommendations.append("Consider diversifying into more sectors")

    return {"sectors": sectors, "total_sectors": len(sectors), "recommendations": recommendations}
