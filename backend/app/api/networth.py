from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional
import asyncio
from ..api.auth import get_current_user
from ..database import get_db

router = APIRouter()

def validate_object_id(id_str: str) -> ObjectId:
    if not ObjectId.is_valid(id_str):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    return ObjectId(id_str)

class AssetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=50)
    value: float = Field(..., ge=0)
    invested: Optional[float] = Field(None, ge=0)
    interest_rate: Optional[float] = Field(None, ge=0, le=100)
    maturity_date: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)

import time

# Simple in-memory cache for networth (TTL: 30 seconds)
_networth_cache = {}

@router.get("/")
async def get_networth(current_user: dict = Depends(get_current_user)):
    user_id = current_user["_id"]
    cache_key = f"networth:{user_id}"
    
    # Check cache
    if cache_key in _networth_cache:
        cached, ts = _networth_cache[cache_key]
        if time.time() - ts < 30:  # 30 second TTL
            return cached
    
    db = get_db()
    oid = ObjectId(user_id)
    
    # Query with both string and ObjectId to handle legacy data
    assets_task = db.assets.find({"$or": [{"user_id": oid}, {"user_id": user_id}]}).to_list(100)
    holdings_task = db.holdings.find({"user_id": oid}).to_list(100)
    assets, holdings = await asyncio.gather(assets_task, holdings_task)
    
    stocks_value = sum(h["quantity"] * (h.get("current_price") or h["avg_price"]) for h in holdings if h.get("holding_type") != "MF")
    mf_value = sum(h["quantity"] * (h.get("current_price") or h["avg_price"]) for h in holdings if h.get("holding_type") == "MF")
    
    categories = {"Stocks": stocks_value, "Mutual Funds": mf_value, "Fixed Deposits": 0, "PPF": 0, "NPS": 0, "EPF": 0, "Gold": 0, "Real Estate": 0, "Savings": 0, "Others": 0}
    
    for asset in assets:
        cat = asset.get("category", "Others")
        if cat in categories:
            categories[cat] += asset.get("value", 0)
        else:
            categories["Others"] += asset.get("value", 0)
    
    total = sum(categories.values())
    allocation = {k: round(v / total * 100, 1) if total > 0 else 0 for k, v in categories.items()}
    
    result = {"total_networth": round(total, 2), "categories": {k: round(v, 2) for k, v in categories.items() if v > 0}, "allocation": {k: v for k, v in allocation.items() if v > 0}, "assets_count": len(assets) + len(holdings)}
    
    # Cache result
    _networth_cache[cache_key] = (result, time.time())
    
    return result

@router.post("/asset")
async def add_asset(asset: AssetCreate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = ObjectId(current_user["_id"])
    
    new_asset = {
        "user_id": user_id,
        "name": asset.name,
        "category": asset.category,
        "value": asset.value,
        "invested": asset.invested or asset.value,
        "interest_rate": asset.interest_rate,
        "maturity_date": asset.maturity_date,
        "notes": asset.notes,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    result = await db.assets.insert_one(new_asset)
    return {"message": "Asset added", "id": str(result.inserted_id)}

@router.get("/assets")
async def list_assets(current_user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = current_user["_id"]
    oid = ObjectId(user_id)
    assets = await db.assets.find({"$or": [{"user_id": oid}, {"user_id": user_id}]}).to_list(100)
    for a in assets:
        a["_id"] = str(a["_id"])
        a["user_id"] = str(a["user_id"])
    return {"assets": assets}

@router.put("/asset/{asset_id}")
async def update_asset(asset_id: str, asset: dict, current_user: dict = Depends(get_current_user)):
    oid = validate_object_id(asset_id)
    db = get_db()
    user_id = ObjectId(current_user["_id"])
    update = {"updated_at": datetime.now(timezone.utc)}
    for k in ["name", "category", "value", "interest_rate", "maturity_date", "notes"]:
        if k in asset:
            update[k] = asset[k]
    await db.assets.update_one({"_id": oid, "user_id": user_id}, {"$set": update})
    return {"message": "Asset updated"}

@router.delete("/asset/{asset_id}")
async def delete_asset(asset_id: str, current_user: dict = Depends(get_current_user)):
    oid = validate_object_id(asset_id)
    db = get_db()
    user_id = ObjectId(current_user["_id"])
    await db.assets.delete_one({"_id": oid, "user_id": user_id})
    return {"message": "Asset deleted"}

def user_id_query(user_id: str):
    """Query that matches both string and ObjectId user_id for legacy data"""
    return {"$or": [{"user_id": ObjectId(user_id)}, {"user_id": user_id}]}

@router.get("/history")
async def get_networth_history(current_user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = current_user["_id"]
    history = await db.networth_history.find(user_id_query(user_id)).sort("date", -1).limit(365).to_list(365)
    history.reverse()
    return {"history": [{"date": h["date"].isoformat() if isinstance(h["date"], datetime) else h["date"], "value": h["value"]} for h in history]}

@router.post("/snapshot")
async def take_snapshot(current_user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = current_user["_id"]
    oid = ObjectId(user_id)
    now = datetime.now(timezone.utc)
    
    holdings_task = db.holdings.find({"user_id": oid}).to_list(100)
    assets_task = db.assets.find(user_id_query(user_id)).to_list(100)
    holdings, assets = await asyncio.gather(holdings_task, assets_task)
    
    stocks_val = sum(h["quantity"] * (h.get("current_price") or h["avg_price"]) for h in holdings if h.get("holding_type") != "MF")
    mf_val = sum(h["quantity"] * (h.get("current_price") or h["avg_price"]) for h in holdings if h.get("holding_type") == "MF")
    
    breakdown = {}
    if stocks_val > 0:
        breakdown["Stocks"] = round(stocks_val, 2)
    if mf_val > 0:
        breakdown["Mutual"] = round(mf_val, 2)
    for a in assets:
        name = a.get("name", a.get("category", "Others"))
        breakdown[name] = round(a.get("value", 0), 2)
    
    total = sum(breakdown.values())
    today = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    
    # Use string user_id for consistency with existing data
    await db.networth_history.update_one({"user_id": user_id, "date": today}, {"$set": {"user_id": user_id, "date": today, "value": total, "breakdown": breakdown}}, upsert=True)
    return {"message": "Snapshot saved", "date": today.strftime("%Y-%m-%d"), "total": total, "breakdown": breakdown}

@router.get("/monthly")
async def get_monthly_networth(year: int = None, current_user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = current_user["_id"]
    year = year or datetime.now().year
    
    BENCHMARKS = {"inflation": 6.0, "fd_rate": 7.0, "nifty_avg": 12.0, "good_growth": 15.0}
    monthly = []
    prev_value = None
    
    for month in range(1, 13):
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc) if month < 12 else datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        
        q = user_id_query(user_id)
        q["date"] = {"$gte": start, "$lt": end}
        snap = await db.networth_history.find_one(q, sort=[("date", 1)])
        value = snap.get("value", 0) if snap else (prev_value or 0)
        has_data = snap is not None
        
        change = value - prev_value if prev_value and has_data else 0
        change_pct = (change / prev_value * 100) if prev_value and prev_value > 0 and has_data else 0
        
        monthly.append({"month": month, "month_name": datetime(year, month, 1).strftime("%b"), "value": round(value, 2), "change": round(change, 2), "change_pct": round(change_pct, 2), "has_data": has_data})
        if value > 0:
            prev_value = value
    
    q = user_id_query(user_id)
    q["date"] = {"$lt": datetime(year, 1, 1, tzinfo=timezone.utc)}
    prev_year_last = await db.networth_history.find_one(q, sort=[("date", -1)])
    prev_year_val = prev_year_last.get("value", 0) if prev_year_last else 0
    
    if monthly and monthly[0]["has_data"] and prev_year_val > 0:
        jan_change = monthly[0]["value"] - prev_year_val
        monthly[0]["change"] = round(jan_change, 2)
        monthly[0]["change_pct"] = round((jan_change / prev_year_val) * 100, 2)
    
    first_val = prev_year_val if prev_year_val > 0 else next((m["value"] for m in monthly if m["value"] > 0), 0)
    last_val = next((m["value"] for m in reversed(monthly) if m["value"] > 0), 0)
    months_with_data = sum(1 for m in monthly if m["has_data"])
    
    ytd_growth = ((last_val - first_val) / first_val) * 100 if first_val > 0 and last_val > 0 else 0
    annualized = (ytd_growth / max(months_with_data, 1)) * 12 if first_val > 0 else 0
    
    performance = {"beating_inflation": annualized > BENCHMARKS["inflation"], "beating_fd": annualized > BENCHMARKS["fd_rate"], "beating_nifty": annualized > BENCHMARKS["nifty_avg"], "good_growth": annualized >= BENCHMARKS["good_growth"]}
    score = sum(performance.values())
    rating = ["Poor", "Below Avg", "Average", "Good", "Excellent"][score]
    
    return {"year": year, "monthly": monthly, "ytd_growth": round(ytd_growth, 2), "annualized_growth": round(annualized, 2), "benchmarks": BENCHMARKS, "performance": performance, "rating": rating}

@router.post("/import-history")
async def import_networth_history(data: dict, current_user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = current_user["_id"]  # Keep as string for consistency
    imported = 0
    
    snapshots = data.get("snapshots") or []
    if not snapshots and data.get("history"):
        snapshots = [{"date": h.get("date"), "total": h.get("value"), "breakdown": {}} for h in data["history"]]
    
    for snap in snapshots:
        date_str = snap.get("date")
        total = snap.get("total", 0)
        breakdown = snap.get("breakdown", {})
        if not date_str or not total:
            continue
        try:
            dt = datetime.strptime(date_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except:
            continue
        await db.networth_history.update_one({"user_id": user_id, "date": dt}, {"$set": {"user_id": user_id, "date": dt, "value": float(total), "breakdown": breakdown}}, upsert=True)
        imported += 1
    
    return {"message": f"Imported {imported} records", "imported": imported}

@router.get("/history-detail")
async def get_networth_history_detail(year: int = None, current_user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = current_user["_id"]
    year = year or datetime.now().year
    
    start = datetime(year, 1, 1, tzinfo=timezone.utc)
    end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    
    q = user_id_query(user_id)
    q["date"] = {"$gte": start, "$lt": end}
    history = await db.networth_history.find(q).sort("date", 1).to_list(100)
    
    result = []
    prev_value = None
    for h in history:
        value = h.get("value", 0)
        change = value - prev_value if prev_value else 0
        change_pct = (change / prev_value * 100) if prev_value and prev_value > 0 else 0
        result.append({"date": h["date"].strftime("%Y-%m-%d") if isinstance(h["date"], datetime) else h["date"], "total": value, "breakdown": h.get("breakdown", {}), "change": round(change, 2), "change_pct": round(change_pct, 2)})
        prev_value = value
    
    return {"year": year, "history": result}
