from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from beanie import PydanticObjectId
from pydantic import BaseModel, Field
from typing import Optional
import asyncio
import time

from ..models.documents import Holding, Asset, NetworthHistory
from ..api.auth import get_current_user

router = APIRouter()

_networth_cache = {}


class AssetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=50)
    value: float = Field(..., ge=0)
    invested: Optional[float] = Field(None, ge=0)
    interest_rate: Optional[float] = Field(None, ge=0, le=100)
    maturity_date: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)


@router.get("/")
async def get_networth(current_user: dict = Depends(get_current_user)):
    user_id = current_user["_id"]
    cache_key = f"networth:{user_id}"
    if cache_key in _networth_cache:
        cached, ts = _networth_cache[cache_key]
        if time.time() - ts < 30:
            return cached

    uid = PydanticObjectId(user_id)
    assets, holdings = await asyncio.gather(Asset.find(Asset.user_id == uid).to_list(), Holding.find(Holding.user_id == uid).to_list())

    stocks_value = sum(h.quantity * (h.current_price or h.avg_price) for h in holdings if h.holding_type != "MF")
    mf_value = sum(h.quantity * (h.current_price or h.avg_price) for h in holdings if h.holding_type == "MF")

    categories = {"Stocks": stocks_value, "Mutual Funds": mf_value, "Fixed Deposits": 0, "PPF": 0, "NPS": 0, "EPF": 0, "Gold": 0, "Real Estate": 0, "Savings": 0, "Others": 0}
    for asset in assets:
        cat = asset.category if asset.category in categories else "Others"
        categories[cat] += asset.value

    total = sum(categories.values())
    result = {"total_networth": round(total, 2), "categories": {k: round(v, 2) for k, v in categories.items() if v > 0}, "allocation": {k: round(v / total * 100, 1) for k, v in categories.items() if v > 0} if total > 0 else {}, "assets_count": len(assets) + len(holdings)}
    _networth_cache[cache_key] = (result, time.time())
    return result


@router.post("/asset")
async def add_asset(asset: AssetCreate, current_user: dict = Depends(get_current_user)):
    doc = Asset(user_id=PydanticObjectId(current_user["_id"]), name=asset.name, category=asset.category, value=asset.value, invested=asset.invested or asset.value, interest_rate=asset.interest_rate, maturity_date=asset.maturity_date, notes=asset.notes)
    await doc.insert()
    return {"message": "Asset added", "id": str(doc.id)}


@router.get("/assets")
async def list_assets(current_user: dict = Depends(get_current_user)):
    assets = await Asset.find(Asset.user_id == PydanticObjectId(current_user["_id"])).to_list()
    return {"assets": [{"_id": str(a.id), "name": a.name, "category": a.category, "value": a.value, "interest_rate": a.interest_rate, "maturity_date": a.maturity_date, "notes": a.notes} for a in assets]}


@router.put("/asset/{asset_id}")
async def update_asset(asset_id: str, asset: dict, current_user: dict = Depends(get_current_user)):
    if not PydanticObjectId.is_valid(asset_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    a = await Asset.find_one(Asset.id == PydanticObjectId(asset_id), Asset.user_id == PydanticObjectId(current_user["_id"]))
    if not a:
        raise HTTPException(status_code=404, detail="Asset not found")
    for k in ["name", "category", "value", "interest_rate", "maturity_date", "notes"]:
        if k in asset:
            setattr(a, k, asset[k])
    await a.save()
    return {"message": "Asset updated"}


@router.delete("/asset/{asset_id}")
async def delete_asset(asset_id: str, current_user: dict = Depends(get_current_user)):
    if not PydanticObjectId.is_valid(asset_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    a = await Asset.find_one(Asset.id == PydanticObjectId(asset_id), Asset.user_id == PydanticObjectId(current_user["_id"]))
    if a:
        await a.delete()
    return {"message": "Asset deleted"}


@router.get("/history")
async def get_networth_history(current_user: dict = Depends(get_current_user)):
    history = await NetworthHistory.find(NetworthHistory.user_id == PydanticObjectId(current_user["_id"])).sort(-NetworthHistory.date).limit(365).to_list()
    history.reverse()
    return {"history": [{"date": h.date.isoformat() if isinstance(h.date, datetime) else h.date, "value": h.value} for h in history]}


@router.post("/snapshot")
async def take_snapshot(current_user: dict = Depends(get_current_user)):
    uid = PydanticObjectId(current_user["_id"])
    now = datetime.now(timezone.utc)
    holdings, assets = await asyncio.gather(Holding.find(Holding.user_id == uid).to_list(), Asset.find(Asset.user_id == uid).to_list())

    breakdown = {}
    stocks_val = sum(h.quantity * (h.current_price or h.avg_price) for h in holdings if h.holding_type != "MF")
    mf_val = sum(h.quantity * (h.current_price or h.avg_price) for h in holdings if h.holding_type == "MF")
    if stocks_val > 0:
        breakdown["Stocks"] = round(stocks_val, 2)
    if mf_val > 0:
        breakdown["Mutual Funds"] = round(mf_val, 2)
    for a in assets:
        breakdown[a.name] = round(a.value, 2)

    total = sum(breakdown.values())
    today = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

    existing = await NetworthHistory.find_one(NetworthHistory.user_id == uid, NetworthHistory.date == today)
    if existing:
        existing.value = total
        existing.breakdown = breakdown
        await existing.save()
    else:
        await NetworthHistory(user_id=uid, date=today, value=total, breakdown=breakdown).insert()

    return {"message": "Snapshot saved", "date": today.strftime("%Y-%m-%d"), "total": total, "breakdown": breakdown}


@router.get("/monthly")
async def get_monthly_networth(year: int = None, current_user: dict = Depends(get_current_user)):
    uid = PydanticObjectId(current_user["_id"])
    year = year or datetime.now().year
    BENCHMARKS = {"inflation": 6.0, "fd_rate": 7.0, "nifty_avg": 12.0, "good_growth": 15.0}

    monthly = []
    prev_value = None
    for month in range(1, 13):
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc) if month < 12 else datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        snap = await NetworthHistory.find_one(NetworthHistory.user_id == uid, NetworthHistory.date >= start, NetworthHistory.date < end)
        value = snap.value if snap else (prev_value or 0)
        has_data = snap is not None
        change = value - prev_value if prev_value and has_data else 0
        change_pct = (change / prev_value * 100) if prev_value and prev_value > 0 and has_data else 0
        monthly.append({"month": month, "month_name": datetime(year, month, 1).strftime("%b"), "value": round(value, 2), "change": round(change, 2), "change_pct": round(change_pct, 2), "has_data": has_data})
        if value > 0:
            prev_value = value

    first_val = next((m["value"] for m in monthly if m["value"] > 0), 0)
    last_val = next((m["value"] for m in reversed(monthly) if m["value"] > 0), 0)
    ytd_growth = ((last_val - first_val) / first_val) * 100 if first_val > 0 else 0

    return {"year": year, "monthly": monthly, "ytd_growth": round(ytd_growth, 2), "benchmarks": BENCHMARKS}
