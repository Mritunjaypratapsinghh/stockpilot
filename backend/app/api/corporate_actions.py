from fastapi import APIRouter, Depends
from datetime import datetime
from beanie import PydanticObjectId
import httpx
import asyncio

from ..models.documents import Holding
from ..api.auth import get_current_user
from ..logger import logger

router = APIRouter()


async def fetch_corporate_actions(symbol: str) -> list:
    actions = []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS?interval=1d&range=1y&events=div"
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                events = resp.json().get("chart", {}).get("result", [{}])[0].get("events", {})
                for ts, div in events.get("dividends", {}).items():
                    actions.append({"type": "DIVIDEND", "symbol": symbol, "date": datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d"), "value": div.get("amount", 0), "description": f"Dividend ₹{div.get('amount', 0):.2f} per share"})
                for ts, split in events.get("splits", {}).items():
                    ratio = f"{split.get('numerator', 1)}:{split.get('denominator', 1)}"
                    actions.append({"type": "SPLIT", "symbol": symbol, "date": datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d"), "value": ratio, "description": f"Stock split {ratio}"})
    except Exception as e:
        logger.error(f"Error fetching actions for {symbol}: {e}")
    return actions


@router.get("/")
async def get_corporate_actions(current_user: dict = Depends(get_current_user)):
    holdings = await Holding.find(Holding.user_id == PydanticObjectId(current_user["_id"])).to_list()
    if not holdings:
        return {"actions": [], "upcoming": [], "recent": []}

    symbols = [h.symbol for h in holdings if h.holding_type != "MF"][:20]
    results = await asyncio.gather(*[fetch_corporate_actions(s) for s in symbols])

    all_actions = [a for actions in results for a in actions]
    all_actions.sort(key=lambda x: x["date"], reverse=True)

    today = datetime.now().strftime("%Y-%m-%d")
    return {"actions": all_actions[:50], "upcoming": [a for a in all_actions if a["date"] >= today][:10], "recent": [a for a in all_actions if a["date"] < today][:20]}


@router.get("/dividends")
async def get_dividend_calendar(current_user: dict = Depends(get_current_user)):
    holdings = await Holding.find(Holding.user_id == PydanticObjectId(current_user["_id"])).to_list()
    if not holdings:
        return {"dividends": [], "expected_income": 0}

    symbols = [h.symbol for h in holdings if h.holding_type != "MF"][:20]
    results = await asyncio.gather(*[fetch_corporate_actions(s) for s in symbols])
    holdings_map = {h.symbol: h.quantity for h in holdings}

    dividends = []
    expected_income = 0
    for actions in results:
        for a in actions:
            if a["type"] == "DIVIDEND":
                qty = holdings_map.get(a["symbol"], 0)
                income = a["value"] * qty
                expected_income += income
                dividends.append({**a, "quantity": qty, "expected_income": round(income, 2)})

    dividends.sort(key=lambda x: x["date"], reverse=True)
    return {"dividends": dividends[:30], "expected_income": round(expected_income, 2)}


@router.get("/splits")
async def get_splits(current_user: dict = Depends(get_current_user)):
    holdings = await Holding.find(Holding.user_id == PydanticObjectId(current_user["_id"])).to_list()
    if not holdings:
        return {"splits": []}

    symbols = [h.symbol for h in holdings if h.holding_type != "MF"][:20]
    results = await asyncio.gather(*[fetch_corporate_actions(s) for s in symbols])
    splits = [a for actions in results for a in actions if a["type"] == "SPLIT"]
    splits.sort(key=lambda x: x["date"], reverse=True)
    return {"splits": splits[:20]}


@router.post("/adjust/{symbol}")
async def adjust_for_split(symbol: str, ratio: str, current_user: dict = Depends(get_current_user)):
    try:
        num, den = map(int, ratio.split(":"))
        multiplier = num / den
    except:
        return {"error": "Invalid ratio format. Use format like '2:1'"}

    holding = await Holding.find_one(Holding.user_id == PydanticObjectId(current_user["_id"]), Holding.symbol == symbol.upper())
    if not holding:
        return {"error": "Holding not found"}

    old_qty, old_avg = holding.quantity, holding.avg_price
    holding.quantity = round(old_qty * multiplier, 4)
    holding.avg_price = round(old_avg / multiplier, 2)
    await holding.save()

    return {"message": f"Adjusted {symbol} for {ratio} split", "old_qty": old_qty, "new_qty": holding.quantity, "old_avg": old_avg, "new_avg": holding.avg_price}
