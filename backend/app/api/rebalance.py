from fastapi import APIRouter, Depends, HTTPException
from beanie import PydanticObjectId

from ..models.documents import User, Holding
from ..api.auth import get_current_user
from ..api.portfolio import get_holdings

router = APIRouter()

DEFAULT_ALLOCATION = {"Equity": 60, "Debt": 30, "Gold": 5, "Cash": 5}


@router.get("/allocation")
async def get_allocation(current_user: dict = Depends(get_current_user)):
    user = await User.get(PydanticObjectId(current_user["_id"]))
    target = user.settings.get("target_allocation", DEFAULT_ALLOCATION) if user else DEFAULT_ALLOCATION
    holdings = await get_holdings(current_user)

    categories = {"Equity": 0, "Debt": 0, "Gold": 0, "Cash": 0}
    total = 0

    for h in holdings:
        value = h.get("current_value", 0)
        total += value
        name = (h.get("name", "") or h.get("symbol", "")).upper()

        if any(x in name for x in ["LIQUID", "DEBT", "BOND", "GILT", "OVERNIGHT"]):
            categories["Debt"] += value
        elif any(x in name for x in ["GOLD", "GOLDBEES", "SILVER"]):
            categories["Gold"] += value
        elif "MONEY" in name:
            categories["Cash"] += value
        else:
            categories["Equity"] += value

    current = {cat: round(val / total * 100, 1) if total > 0 else 0 for cat, val in categories.items()}
    deviation = {cat: round(current.get(cat, 0) - target[cat], 1) for cat in target}

    return {"total_value": round(total, 2), "target": target, "current": current, "deviation": deviation, "categories": {k: round(v, 2) for k, v in categories.items()}}


@router.post("/target")
async def set_target(allocation: dict, current_user: dict = Depends(get_current_user)):
    total = sum(allocation.values())
    if abs(total - 100) > 0.1:
        raise HTTPException(status_code=400, detail=f"Allocation must sum to 100%, got {total}%")

    user = await User.get(PydanticObjectId(current_user["_id"]))
    if user:
        user.settings["target_allocation"] = allocation
        await user.save()
    return {"message": "Target allocation updated", "allocation": allocation}


@router.get("/suggestions")
async def get_rebalance_suggestions(current_user: dict = Depends(get_current_user)):
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

        if abs(diff) > total * 0.02:
            s = {"category": cat, "action": "BUY" if diff > 0 else "SELL", "amount": abs(round(diff, 0)), "current_pct": current.get(cat, 0), "target_pct": target[cat], "deviation_pct": round(current.get(cat, 0) - target[cat], 1)}
            if s["action"] == "BUY":
                s["suggested_funds"] = {"Debt": ["Axis Liquid Fund", "HDFC Money Market"], "Gold": ["Nippon Gold BeES"], "Equity": ["UTI Nifty 50 Index"]}.get(cat, [])
            suggestions.append(s)

    suggestions.sort(key=lambda x: abs(x["deviation_pct"]), reverse=True)
    return {"portfolio_value": total, "suggestions": suggestions, "rebalance_needed": len(suggestions) > 0}
