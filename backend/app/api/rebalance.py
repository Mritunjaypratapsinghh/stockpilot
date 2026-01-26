from fastapi import APIRouter, Depends
from ..api.auth import get_current_user
from ..database import get_db
from ..api.portfolio import get_holdings

router = APIRouter()

DEFAULT_ALLOCATION = {"Equity": 60, "Debt": 30, "Gold": 5, "Cash": 5}

@router.get("/allocation")
async def get_allocation(current_user: dict = Depends(get_current_user)):
    """Get current vs target allocation"""
    db = get_db()
    if db is None:
        return {"error": "Database not connected"}
    
    user_id = str(current_user["_id"])
    
    # Get target allocation (user-defined or default)
    settings = await db.users.find_one({"_id": current_user["_id"]}) or {}
    target = settings.get("target_allocation", DEFAULT_ALLOCATION)
    
    # Get holdings with current prices
    holdings = await get_holdings(current_user)
    
    # Categorize holdings
    categories = {"Equity": 0, "Debt": 0, "Gold": 0, "Cash": 0}
    total = 0
    
    for h in holdings:
        value = h.get("current_value", 0)
        total += value
        
        # Categorize based on holding type or name
        name = (h.get("name", "") or h.get("symbol", "")).upper()
        htype = h.get("holding_type", "STOCK")
        
        if "LIQUID" in name or "DEBT" in name or "BOND" in name or "GILT" in name or "OVERNIGHT" in name:
            categories["Debt"] += value
        elif "GOLD" in name or "GOLDBEES" in name:
            categories["Gold"] += value
        elif "SILVER" in name or "SILVERBEES" in name:
            categories["Gold"] += value  # Count silver as gold/commodities
        elif htype == "MF" and ("MONEY" in name):
            categories["Cash"] += value
        else:
            categories["Equity"] += value
    
    # Calculate current allocation %
    current = {}
    for cat, val in categories.items():
        current[cat] = round(val / total * 100, 1) if total > 0 else 0
    
    # Calculate deviation
    deviation = {}
    for cat in target:
        deviation[cat] = round(current.get(cat, 0) - target[cat], 1)
    
    return {
        "total_value": round(total, 2),
        "target": target,
        "current": current,
        "deviation": deviation,
        "categories": {k: round(v, 2) for k, v in categories.items()}
    }

@router.post("/target")
async def set_target(allocation: dict, current_user: dict = Depends(get_current_user)):
    """Set target allocation"""
    db = get_db()
    if db is None:
        return {"error": "Database not connected"}
    
    # Validate total = 100
    total = sum(allocation.values())
    if abs(total - 100) > 0.1:
        return {"error": f"Allocation must sum to 100%, got {total}%"}
    
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"target_allocation": allocation}}
    )
    return {"message": "Target allocation updated", "allocation": allocation}

@router.get("/suggestions")
async def get_rebalance_suggestions(current_user: dict = Depends(get_current_user)):
    """Get buy/sell suggestions to rebalance"""
    alloc = await get_allocation(current_user)
    total = alloc["total_value"]
    target = alloc["target"]
    current = alloc["current"]
    categories = alloc["categories"]
    
    suggestions = []
    for cat in target:
        target_val = total * target[cat] / 100
        current_val = categories.get(cat, 0)
        diff = target_val - current_val
        
        if abs(diff) > total * 0.02:  # Only suggest if >2% deviation
            suggestions.append({
                "category": cat,
                "action": "BUY" if diff > 0 else "SELL",
                "amount": abs(round(diff, 0)),
                "current_pct": current.get(cat, 0),
                "target_pct": target[cat],
                "deviation_pct": round(current.get(cat, 0) - target[cat], 1)
            })
    
    # Sort by absolute deviation
    suggestions.sort(key=lambda x: abs(x["deviation_pct"]), reverse=True)
    
    # Add specific fund suggestions
    for s in suggestions:
        if s["action"] == "BUY":
            if s["category"] == "Debt":
                s["suggested_funds"] = ["Axis Liquid Fund", "HDFC Money Market", "SBI Overnight"]
            elif s["category"] == "Gold":
                s["suggested_funds"] = ["Nippon Gold BeES", "SBI Gold ETF"]
            elif s["category"] == "Equity":
                s["suggested_funds"] = ["UTI Nifty 50 Index", "Motilal Oswal S&P 500"]
    
    return {
        "portfolio_value": total,
        "suggestions": suggestions,
        "rebalance_needed": len(suggestions) > 0,
        "note": "Rebalance quarterly or when deviation exceeds 5%"
    }
