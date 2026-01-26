from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
from bson import ObjectId
import httpx
from ..database import get_db
from ..api.auth import get_current_user
from ..logger import logger

router = APIRouter()

async def fetch_corporate_actions(symbol: str) -> list:
    """Fetch corporate actions from Yahoo Finance"""
    actions = []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Dividends
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS?interval=1d&range=1y&events=div"
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                data = resp.json().get("chart", {}).get("result", [{}])[0]
                events = data.get("events", {})
                
                for ts, div in events.get("dividends", {}).items():
                    actions.append({
                        "type": "DIVIDEND",
                        "symbol": symbol,
                        "date": datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d"),
                        "value": div.get("amount", 0),
                        "description": f"Dividend ₹{div.get('amount', 0):.2f} per share"
                    })
                
                for ts, split in events.get("splits", {}).items():
                    ratio = f"{split.get('numerator', 1)}:{split.get('denominator', 1)}"
                    actions.append({
                        "type": "SPLIT",
                        "symbol": symbol,
                        "date": datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d"),
                        "value": ratio,
                        "description": f"Stock split {ratio}"
                    })
    except Exception as e:
        logger.error(f"Error fetching actions for {symbol}: {e}")
    
    return actions

@router.get("/")
async def get_corporate_actions(current_user: dict = Depends(get_current_user)):
    """Get corporate actions for user's holdings"""
    db = get_db()
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    
    if not holdings:
        return {"actions": [], "upcoming": [], "recent": []}
    
    # Fetch actions for all holdings
    import asyncio
    symbols = [h["symbol"] for h in holdings if h.get("holding_type") != "MF"]
    tasks = [fetch_corporate_actions(s) for s in symbols[:20]]  # Limit for speed
    results = await asyncio.gather(*tasks)
    
    all_actions = []
    for actions in results:
        all_actions.extend(actions)
    
    # Sort by date
    all_actions.sort(key=lambda x: x["date"], reverse=True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    upcoming = [a for a in all_actions if a["date"] >= today]
    recent = [a for a in all_actions if a["date"] < today][:20]
    
    return {
        "actions": all_actions[:50],
        "upcoming": upcoming[:10],
        "recent": recent
    }

@router.get("/dividends")
async def get_dividend_calendar(current_user: dict = Depends(get_current_user)):
    """Get dividend calendar for holdings"""
    db = get_db()
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    
    if not holdings:
        return {"dividends": [], "expected_income": 0}
    
    import asyncio
    symbols = [h["symbol"] for h in holdings if h.get("holding_type") != "MF"]
    tasks = [fetch_corporate_actions(s) for s in symbols[:20]]
    results = await asyncio.gather(*tasks)
    
    holdings_map = {h["symbol"]: h["quantity"] for h in holdings}
    dividends = []
    expected_income = 0
    
    for actions in results:
        for a in actions:
            if a["type"] == "DIVIDEND":
                qty = holdings_map.get(a["symbol"], 0)
                income = a["value"] * qty
                expected_income += income
                dividends.append({
                    **a,
                    "quantity": qty,
                    "expected_income": round(income, 2)
                })
    
    dividends.sort(key=lambda x: x["date"], reverse=True)
    
    return {
        "dividends": dividends[:30],
        "expected_income": round(expected_income, 2)
    }

@router.get("/splits")
async def get_splits(current_user: dict = Depends(get_current_user)):
    """Get stock splits for holdings"""
    db = get_db()
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    
    if not holdings:
        return {"splits": []}
    
    import asyncio
    symbols = [h["symbol"] for h in holdings if h.get("holding_type") != "MF"]
    tasks = [fetch_corporate_actions(s) for s in symbols[:20]]
    results = await asyncio.gather(*tasks)
    
    splits = []
    for actions in results:
        for a in actions:
            if a["type"] == "SPLIT":
                splits.append(a)
    
    splits.sort(key=lambda x: x["date"], reverse=True)
    
    return {"splits": splits[:20]}

@router.get("/bonus")
async def get_bonus_issues(current_user: dict = Depends(get_current_user)):
    """Get bonus issues - Note: Yahoo doesn't provide bonus data, using splits as proxy"""
    return {"bonus": [], "note": "Bonus issue data not available from current data source"}

@router.post("/adjust/{symbol}")
async def adjust_for_split(symbol: str, ratio: str, current_user: dict = Depends(get_current_user)):
    """Manually adjust holdings for a stock split"""
    db = get_db()
    
    try:
        num, den = map(int, ratio.split(":"))
        multiplier = num / den
    except:
        return {"error": "Invalid ratio format. Use format like '2:1' or '5:1'"}
    
    holding = await db.holdings.find_one({"user_id": ObjectId(current_user["_id"]), "symbol": symbol.upper()})
    if not holding:
        return {"error": "Holding not found"}
    
    new_qty = holding["quantity"] * multiplier
    new_avg = holding["avg_price"] / multiplier
    
    await db.holdings.update_one(
        {"_id": holding["_id"]},
        {"$set": {"quantity": round(new_qty, 4), "avg_price": round(new_avg, 2)}}
    )
    
    return {
        "message": f"Adjusted {symbol} for {ratio} split",
        "old_qty": holding["quantity"],
        "new_qty": round(new_qty, 4),
        "old_avg": holding["avg_price"],
        "new_avg": round(new_avg, 2)
    }
