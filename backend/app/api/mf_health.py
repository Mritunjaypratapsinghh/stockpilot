from fastapi import APIRouter, Depends

from ..api.auth import get_current_user
from ..api.portfolio import get_holdings

router = APIRouter()


def get_recommendations(analysis, issues):
    recs = []
    underperformers = [a for a in analysis if a["status"] == "Underperforming"]
    if underperformers:
        recs.append({"type": "switch", "message": f"Consider switching {len(underperformers)} underperforming fund(s)", "funds": [u["symbol"] for u in underperformers]})
    high_expense = [a for a in analysis if a["expense_ratio"] > 1]
    if high_expense:
        recs.append({"type": "expense", "message": "Switch to direct plans to save on expense ratio", "potential_savings": round(sum(a["annual_expense"] * 0.5 for a in high_expense), 2)})
    if not any("Index" in a["category"] for a in analysis):
        recs.append({"type": "add", "message": "Consider adding low-cost index funds for core allocation"})
    return recs


def categorize_mf(name: str) -> tuple:
    name = name.upper()
    if any(x in name for x in ["LIQUID", "OVERNIGHT", "MONEY"]):
        return "Liquid", 6
    if any(x in name for x in ["DEBT", "BOND", "GILT"]):
        return "Debt", 7
    if "SMALL" in name:
        return "Small Cap", 15
    if "MID" in name:
        return "Mid Cap", 14
    if any(x in name for x in ["LARGE", "BLUECHIP"]):
        return "Large Cap", 12
    if any(x in name for x in ["FLEXI", "MULTI"]):
        return "Flexi Cap", 13
    if any(x in name for x in ["INDEX", "NIFTY", "SENSEX"]):
        return "Index", 12
    if any(x in name for x in ["INTERNATIONAL", "US", "GLOBAL", "NASDAQ"]):
        return "International", 14
    return "Equity", 12


@router.get("/health")
async def mf_health_check(current_user: dict = Depends(get_current_user)):
    all_holdings = await get_holdings(current_user)
    holdings = [h for h in all_holdings if h.get("holding_type") == "MF"]
    if not holdings:
        return {"message": "No mutual funds in portfolio", "funds": []}

    analysis, issues = [], []
    total_expense = total_value = 0

    for h in holdings:
        name = h.get("name") or ""
        value = h.get("current_value", 0)
        total_value += value

        expense_ratio = 0.2 if any(x in name.upper() for x in ["INDEX", "ETF"]) else 0.5 if "DIRECT" in name.upper() else 1.5
        annual_expense = value * expense_ratio / 100
        total_expense += annual_expense

        category, benchmark_return = categorize_mf(name)
        returns_pct = h.get("pnl_pct", 0)
        status = "Underperforming" if returns_pct < benchmark_return - 5 else "Outperforming" if returns_pct > benchmark_return + 5 else "On Track"
        if status == "Underperforming":
            issues.append(f"{h.get('symbol')} is underperforming benchmark")

        analysis.append({"symbol": h.get("symbol"), "name": name, "category": category, "value": round(value, 2), "returns_pct": round(returns_pct, 2), "benchmark_return": benchmark_return, "expense_ratio": expense_ratio, "annual_expense": round(annual_expense, 2), "status": status})

    categories = [a["category"] for a in analysis]
    for cat in set(categories):
        if categories.count(cat) > 2:
            issues.append(f"High overlap: {categories.count(cat)} funds in {cat} category")

    avg_expense = (total_expense / total_value * 100) if total_value > 0 else 0
    if avg_expense > 1:
        issues.append(f"High expense ratio: {round(avg_expense, 2)}%")

    return {"total_mf_value": round(total_value, 2), "total_annual_expense": round(total_expense, 2), "avg_expense_ratio": round(avg_expense, 2), "funds": analysis, "issues": issues, "health_score": max(10, 100 - len(issues) * 10), "recommendations": get_recommendations(analysis, issues)}


@router.get("/overlap")
async def check_overlap(current_user: dict = Depends(get_current_user)):
    all_holdings = await get_holdings(current_user)
    holdings = [h for h in all_holdings if h.get("holding_type") == "MF"]

    categories = {}
    for h in holdings:
        cat, _ = categorize_mf(h.get("name") or "")
        if cat not in categories:
            categories[cat] = {"funds": [], "total_value": 0}
        categories[cat]["funds"].append(h.get("symbol"))
        categories[cat]["total_value"] += h.get("current_value", 0)

    overlap_issues = [{"category": cat, "funds": data["funds"], "message": f"{len(data['funds'])} funds with similar {cat} exposure"} for cat, data in categories.items() if len(data["funds"]) > 2]
    return {"categories": categories, "overlap_issues": overlap_issues, "overlap_score": max(0, 100 - len(overlap_issues) * 20)}
