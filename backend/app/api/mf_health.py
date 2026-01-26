from fastapi import APIRouter, Depends
from ..api.auth import get_current_user
from ..database import get_db
from ..api.portfolio import get_holdings

router = APIRouter()

# Benchmark returns (approximate)
BENCHMARKS = {
    "NIFTY_50": {"1y": 12, "3y": 10, "5y": 11},
    "NIFTY_NEXT_50": {"1y": 15, "3y": 12, "5y": 13},
    "SENSEX": {"1y": 11, "3y": 9, "5y": 10}
}

@router.get("/health")
async def mf_health_check(current_user: dict = Depends(get_current_user)):
    """Analyze mutual fund portfolio health"""
    # Get holdings with current prices
    all_holdings = await get_holdings(current_user)
    holdings = [h for h in all_holdings if h.get("holding_type") == "MF"]
    
    if not holdings:
        return {"message": "No mutual funds in portfolio", "funds": []}
    
    analysis = []
    issues = []
    total_expense = 0
    total_value = 0
    
    for h in holdings:
        name = (h.get("name") or "").upper()
        value = h.get("current_value", 0)
        total_value += value
        
        # Estimate expense ratio based on fund type
        if "DIRECT" in name:
            expense_ratio = 0.5
        elif "INDEX" in name or "ETF" in name:
            expense_ratio = 0.2
        else:
            expense_ratio = 1.5  # Regular plan estimate
        
        annual_expense = value * expense_ratio / 100
        total_expense += annual_expense
        
        # Determine fund category and benchmark
        if "LIQUID" in name or "OVERNIGHT" in name or "MONEY" in name:
            category = "Liquid"
            benchmark_return = 6
        elif "DEBT" in name or "BOND" in name or "GILT" in name:
            category = "Debt"
            benchmark_return = 7
        elif "SMALL" in name:
            category = "Small Cap"
            benchmark_return = 15
        elif "MID" in name:
            category = "Mid Cap"
            benchmark_return = 14
        elif "LARGE" in name or "BLUECHIP" in name:
            category = "Large Cap"
            benchmark_return = 12
        elif "FLEXI" in name or "MULTI" in name:
            category = "Flexi Cap"
            benchmark_return = 13
        elif "INDEX" in name or "NIFTY" in name or "SENSEX" in name:
            category = "Index"
            benchmark_return = 12
        elif "INTERNATIONAL" in name or "US" in name or "GLOBAL" in name or "NASDAQ" in name:
            category = "International"
            benchmark_return = 14
        else:
            category = "Equity"
            benchmark_return = 12
        
        # Calculate returns
        invested = h.get("total_investment", 0)
        current = value
        returns_pct = h.get("pnl_pct", 0)
        
        # Health status
        if returns_pct < benchmark_return - 5:
            status = "Underperforming"
            issues.append(f"{h.get('symbol')} is underperforming benchmark by {round(benchmark_return - returns_pct, 1)}%")
        elif returns_pct > benchmark_return + 5:
            status = "Outperforming"
        else:
            status = "On Track"
        
        analysis.append({
            "symbol": h.get("symbol"),
            "name": h.get("name"),
            "category": category,
            "value": round(value, 2),
            "returns_pct": round(returns_pct, 2),
            "benchmark_return": benchmark_return,
            "expense_ratio": expense_ratio,
            "annual_expense": round(annual_expense, 2),
            "status": status
        })
    
    # Check for overlap (simplified - check for similar categories)
    categories = [a["category"] for a in analysis]
    category_counts = {c: categories.count(c) for c in set(categories)}
    for cat, count in category_counts.items():
        if count > 2:
            issues.append(f"High overlap: {count} funds in {cat} category")
    
    # Check expense ratio
    avg_expense = (total_expense / total_value * 100) if total_value > 0 else 0
    if avg_expense > 1:
        issues.append(f"High expense ratio: {round(avg_expense, 2)}% - Consider switching to direct plans")
    
    return {
        "total_mf_value": round(total_value, 2),
        "total_annual_expense": round(total_expense, 2),
        "avg_expense_ratio": round(avg_expense, 2),
        "funds": analysis,
        "issues": issues,
        "health_score": max(10, 100 - len(issues) * 10),  # Min 10, -10 per issue
        "recommendations": get_recommendations(analysis, issues),
        "note": "Returns comparison is vs annual benchmarks. Short holding periods may show underperformance."
    }

def get_recommendations(analysis, issues):
    recs = []
    
    underperformers = [a for a in analysis if a["status"] == "Underperforming"]
    if underperformers:
        recs.append({
            "type": "switch",
            "message": f"Consider switching {len(underperformers)} underperforming fund(s)",
            "funds": [u["symbol"] for u in underperformers]
        })
    
    high_expense = [a for a in analysis if a["expense_ratio"] > 1]
    if high_expense:
        recs.append({
            "type": "expense",
            "message": "Switch to direct plans to save on expense ratio",
            "potential_savings": round(sum(a["annual_expense"] * 0.5 for a in high_expense), 2)
        })
    
    categories = [a["category"] for a in analysis]
    if categories.count("Equity") > 3 or categories.count("Flexi Cap") > 2:
        recs.append({
            "type": "consolidate",
            "message": "Consider consolidating overlapping funds to reduce complexity"
        })
    
    if not any("Index" in a["category"] for a in analysis):
        recs.append({
            "type": "add",
            "message": "Consider adding low-cost index funds for core allocation"
        })
    
    return recs

@router.get("/overlap")
async def check_overlap(current_user: dict = Depends(get_current_user)):
    """Check stock overlap between mutual funds"""
    all_holdings = await get_holdings(current_user)
    holdings = [h for h in all_holdings if h.get("holding_type") == "MF"]
    
    categories = {}
    for h in holdings:
        name = (h.get("name") or "").upper()
        value = h.get("current_value", 0)
        
        if "LARGE" in name or "BLUECHIP" in name or "NIFTY 50" in name:
            cat = "Large Cap"
        elif "MID" in name:
            cat = "Mid Cap"
        elif "SMALL" in name:
            cat = "Small Cap"
        elif "FLEXI" in name or "MULTI" in name:
            cat = "Flexi Cap"
        else:
            cat = "Other"
        
        if cat not in categories:
            categories[cat] = {"funds": [], "total_value": 0}
        categories[cat]["funds"].append(h.get("symbol"))
        categories[cat]["total_value"] += value
    
    overlap_issues = []
    for cat, data in categories.items():
        if len(data["funds"]) > 2:
            overlap_issues.append({
                "category": cat,
                "funds": data["funds"],
                "message": f"{len(data['funds'])} funds with similar {cat} exposure"
            })
    
    return {
        "categories": categories,
        "overlap_issues": overlap_issues,
        "overlap_score": max(0, 100 - len(overlap_issues) * 20)
    }

@router.get("/expense-impact")
async def expense_impact(years: int = 20, current_user: dict = Depends(get_current_user)):
    """Calculate long-term impact of expense ratios"""
    all_holdings = await get_holdings(current_user)
    holdings = [h for h in all_holdings if h.get("holding_type") == "MF"]
    
    total_value = 0
    total_expense_current = 0
    total_expense_direct = 0
    
    for h in holdings:
        name = (h.get("name") or "").upper()
        value = h.get("current_value", 0)
        total_value += value
        
        # Current expense
        if "DIRECT" in name:
            current_exp = 0.5
            direct_exp = 0.5
        elif "INDEX" in name:
            current_exp = 0.2
            direct_exp = 0.1
        else:
            current_exp = 1.5
            direct_exp = 0.5
        
        total_expense_current += value * current_exp / 100
        total_expense_direct += value * direct_exp / 100
    
    # Project over years with 12% return
    annual_return = 0.12
    
    def project_value(principal, expense_ratio, years):
        value = principal
        for _ in range(years):
            value = value * (1 + annual_return - expense_ratio/100)
        return value
    
    current_expense_ratio = (total_expense_current / total_value * 100) if total_value > 0 else 0
    direct_expense_ratio = (total_expense_direct / total_value * 100) if total_value > 0 else 0
    
    future_current = project_value(total_value, current_expense_ratio, years)
    future_direct = project_value(total_value, direct_expense_ratio, years)
    
    return {
        "current_value": round(total_value, 2),
        "current_expense_ratio": round(current_expense_ratio, 2),
        "direct_expense_ratio": round(direct_expense_ratio, 2),
        "annual_expense_current": round(total_expense_current, 2),
        "annual_expense_direct": round(total_expense_direct, 2),
        "projection_years": years,
        "future_value_current": round(future_current, 2),
        "future_value_direct": round(future_direct, 2),
        "potential_savings": round(future_direct - future_current, 2),
        "message": f"Switching to direct plans could save you ₹{round((future_direct - future_current)/100000, 1)}L over {years} years"
    }
