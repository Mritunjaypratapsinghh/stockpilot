from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
from bson import ObjectId
import math
from ..database import get_db
from ..api.auth import get_current_user
from ..services.price_service import get_bulk_prices

router = APIRouter()

# NIFTY 50 as benchmark
BENCHMARK_SYMBOL = "^NSEI"
RISK_FREE_RATE = 0.07  # 7% (10-year G-Sec yield approx)

@router.get("/metrics")
async def get_portfolio_metrics(current_user: dict = Depends(get_current_user)):
    """Calculate advanced portfolio metrics"""
    db = get_db()
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    
    if not holdings:
        return {"error": "No holdings found"}
    
    symbols = [h["symbol"] for h in holdings if h.get("holding_type") != "MF"]
    prices = await get_bulk_prices(symbols) if symbols else {}
    
    # Portfolio value and weights
    total_value = 0
    holdings_data = []
    
    for h in holdings:
        p = prices.get(h["symbol"], {})
        current_price = p.get("current_price") or h.get("current_price") or h["avg_price"]
        value = h["quantity"] * current_price
        total_value += value
        holdings_data.append({
            "symbol": h["symbol"],
            "value": value,
            "day_change_pct": p.get("day_change_pct", 0),
            "beta": p.get("beta", 1.0)
        })
    
    if total_value == 0:
        return {"error": "Portfolio value is zero"}
    
    # Calculate weights
    for h in holdings_data:
        h["weight"] = h["value"] / total_value
    
    # Portfolio Beta (weighted average)
    portfolio_beta = sum(h["weight"] * h.get("beta", 1.0) for h in holdings_data)
    
    # Daily returns for volatility calculation
    daily_returns = [h["day_change_pct"] * h["weight"] for h in holdings_data]
    portfolio_daily_return = sum(daily_returns)
    
    # Annualized volatility (simplified - using day change as proxy)
    # In production, use historical daily returns
    volatility = abs(portfolio_daily_return) * math.sqrt(252) if portfolio_daily_return != 0 else 15
    
    # Concentration metrics
    sorted_holdings = sorted(holdings_data, key=lambda x: x["value"], reverse=True)
    top_5_concentration = sum(h["weight"] for h in sorted_holdings[:5]) * 100
    
    # Herfindahl Index (measure of concentration)
    hhi = sum(h["weight"] ** 2 for h in holdings_data) * 10000
    
    return {
        "portfolio_value": round(total_value, 2),
        "holdings_count": len(holdings_data),
        "metrics": {
            "beta": round(portfolio_beta, 2),
            "volatility_annual": round(volatility, 1),
            "top_5_concentration": round(top_5_concentration, 1),
            "herfindahl_index": round(hhi, 0),
            "diversification": "Good" if hhi < 1500 else "Moderate" if hhi < 2500 else "Concentrated"
        },
        "risk_profile": get_risk_profile(portfolio_beta, volatility),
        "top_holdings": [{"symbol": h["symbol"], "weight": round(h["weight"] * 100, 1)} for h in sorted_holdings[:5]]
    }

def get_risk_profile(beta: float, volatility: float) -> dict:
    if beta < 0.8 and volatility < 15:
        return {"level": "Conservative", "description": "Lower risk, stable returns"}
    elif beta < 1.2 and volatility < 25:
        return {"level": "Moderate", "description": "Balanced risk-reward"}
    else:
        return {"level": "Aggressive", "description": "Higher risk, potential for higher returns"}

@router.get("/returns")
async def get_returns_analysis(current_user: dict = Depends(get_current_user)):
    """Analyze portfolio returns over different periods"""
    db = get_db()
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    
    total_invested = sum(h["quantity"] * h["avg_price"] for h in holdings)
    total_current = sum(h["quantity"] * h.get("current_price", h["avg_price"]) for h in holdings)
    
    absolute_return = total_current - total_invested
    absolute_return_pct = (absolute_return / total_invested * 100) if total_invested > 0 else 0
    
    # Calculate CAGR based on first transaction
    all_txns = []
    for h in holdings:
        for t in h.get("transactions", []):
            if t["type"] == "BUY":
                all_txns.append(t)
    
    if all_txns:
        first_date = min(datetime.fromisoformat(t["date"]) if isinstance(t["date"], str) else t["date"] for t in all_txns)
        years = max(0.1, (datetime.now() - first_date).days / 365)
        cagr = ((total_current / total_invested) ** (1 / years) - 1) * 100 if total_invested > 0 else 0
    else:
        cagr = 0
        years = 0
    
    return {
        "invested": round(total_invested, 2),
        "current_value": round(total_current, 2),
        "absolute_return": round(absolute_return, 2),
        "absolute_return_pct": round(absolute_return_pct, 2),
        "cagr": round(cagr, 2),
        "holding_period_years": round(years, 1),
        "benchmark_comparison": {
            "nifty_cagr_5yr": 12.5,
            "outperformance": round(cagr - 12.5, 2) if cagr else 0
        }
    }

@router.get("/drawdown")
async def get_drawdown_analysis(current_user: dict = Depends(get_current_user)):
    """Analyze portfolio drawdown"""
    db = get_db()
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    
    # Calculate current drawdown from peak
    total_invested = sum(h["quantity"] * h["avg_price"] for h in holdings)
    total_current = sum(h["quantity"] * h.get("current_price", h["avg_price"]) for h in holdings)
    
    # Estimate peak (simplified - assume 20% higher than current if in loss)
    if total_current < total_invested:
        estimated_peak = total_invested * 1.1
        current_drawdown = ((estimated_peak - total_current) / estimated_peak) * 100
    else:
        estimated_peak = total_current
        current_drawdown = 0
    
    # Holdings in drawdown
    holdings_in_drawdown = []
    for h in holdings:
        current_price = h.get("current_price", h["avg_price"])
        if current_price < h["avg_price"]:
            drawdown_pct = ((h["avg_price"] - current_price) / h["avg_price"]) * 100
            holdings_in_drawdown.append({
                "symbol": h["symbol"],
                "drawdown_pct": round(drawdown_pct, 1),
                "loss": round((h["avg_price"] - current_price) * h["quantity"], 2)
            })
    
    holdings_in_drawdown.sort(key=lambda x: x["drawdown_pct"], reverse=True)
    
    return {
        "portfolio_drawdown": round(current_drawdown, 1),
        "estimated_peak": round(estimated_peak, 2),
        "current_value": round(total_current, 2),
        "recovery_needed": round((estimated_peak / total_current - 1) * 100, 1) if total_current > 0 else 0,
        "holdings_in_drawdown": holdings_in_drawdown[:10],
        "total_holdings_down": len(holdings_in_drawdown),
        "risk_note": "A 50% loss requires 100% gain to recover. Consider rebalancing if drawdown exceeds 20%."
    }

@router.get("/sector-risk")
async def get_sector_risk(current_user: dict = Depends(get_current_user)):
    """Analyze sector concentration risk"""
    db = get_db()
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    
    from ..api.portfolio import SECTOR_MAP
    
    # MF category detection based on common naming patterns
    def get_mf_category(symbol: str) -> str:
        s = symbol.upper()
        if any(x in s for x in ['LIQ', 'LIQUID', 'OVERNIGHT', 'MONEY', '-LM']):
            return "Liquid/Debt"
        if any(x in s for x in ['GILT', 'GSEC', 'BOND', 'DEBT', 'INCOME']):
            return "Debt"
        if any(x in s for x in ['HYBRID', 'BAL', 'BALANCED', 'EQUITY-HYBRID']):
            return "Hybrid"
        if any(x in s for x in ['SMALL', '-SC', 'SMALLCAP']):
            return "Small Cap"
        if any(x in s for x in ['-MC', 'MID', 'MIDCAP']):
            return "Mid Cap"
        if any(x in s for x in ['LARGE', 'BLUECHIP', 'NIFTY', 'INDEX', 'ALPHA']):
            return "Large Cap"
        if any(x in s for x in ['FLEXI', 'MULTI', 'DIVERSIFIED', 'PPFAS', 'PARAG']):
            return "Flexi Cap"
        if any(x in s for x in ['TAX', 'ELSS']):
            return "ELSS"
        if any(x in s for x in ['BANK', 'FIN', 'PSU']):
            return "Sectoral-BFSI"
        if any(x in s for x in ['IT', 'TECH', 'DIGI']):
            return "Sectoral-IT"
        if any(x in s for x in ['PHARMA', 'HEALTH']):
            return "Sectoral-Pharma"
        if any(x in s for x in ['USD', 'GLOBAL', 'US', 'NASDAQ', 'INTERNATIONAL', 'PGIM']):
            return "International"
        if any(x in s for x in ['GOLD', 'SILVER', 'COMMODITY']):
            return "Commodity"
        if any(x in s for x in ['MOM', 'MOMENTUM', 'ETF']):
            return "ETF/Factor"
        return "Equity-Other"
    
    sector_values = {}
    total_value = 0
    
    for h in holdings:
        value = h["quantity"] * h.get("current_price", h["avg_price"])
        total_value += value
        
        if h.get("holding_type") == "MF":
            sector = get_mf_category(h["symbol"])
        else:
            sector = SECTOR_MAP.get(h["symbol"], "Others")
        
        sector_values[sector] = sector_values.get(sector, 0) + value
    
    sectors = []
    for sector, value in sorted(sector_values.items(), key=lambda x: x[1], reverse=True):
        weight = (value / total_value * 100) if total_value > 0 else 0
        risk = "High" if weight > 30 else "Moderate" if weight > 20 else "Low"
        sectors.append({
            "sector": sector,
            "value": round(value, 2),
            "weight": round(weight, 1),
            "concentration_risk": risk
        })
    
    # Recommendations
    recommendations = []
    for s in sectors:
        if s["weight"] > 30:
            recommendations.append(f"Reduce {s['sector']} exposure (currently {s['weight']}%)")
    
    if len(sectors) < 5:
        recommendations.append("Consider diversifying into more sectors")
    
    return {
        "sectors": sectors,
        "total_sectors": len(sectors),
        "recommendations": recommendations,
        "ideal_allocation": "No single sector should exceed 25-30% for balanced risk"
    }
