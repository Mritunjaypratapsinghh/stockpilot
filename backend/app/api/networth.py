from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
from ..api.auth import get_current_user
from ..database import get_db
from ..api.portfolio import get_holdings

router = APIRouter()

@router.get("/")
async def get_networth(current_user: dict = Depends(get_current_user)):
    """Get complete net worth breakdown"""
    db = get_db()
    if db is None:
        return {"error": "Database not connected"}
    
    user_id = str(current_user["_id"])
    
    # Get all assets
    assets = await db.assets.find({"user_id": user_id}).to_list(100)
    
    # Get holdings with current prices
    holdings = await get_holdings(current_user)
    
    # Calculate holdings value
    stocks_value = sum(h.get("current_value", 0) for h in holdings if h.get("holding_type") != "MF")
    mf_value = sum(h.get("current_value", 0) for h in holdings if h.get("holding_type") == "MF")
    
    # Categorize other assets
    categories = {
        "Stocks": stocks_value,
        "Mutual Funds": mf_value,
        "Fixed Deposits": 0,
        "PPF": 0,
        "NPS": 0,
        "EPF": 0,
        "Gold": 0,
        "Real Estate": 0,
        "Savings": 0,
        "Others": 0
    }
    
    for asset in assets:
        cat = asset.get("category", "Others")
        if cat in categories:
            categories[cat] += asset.get("value", 0)
        else:
            categories["Others"] += asset.get("value", 0)
    
    total = sum(categories.values())
    
    # Calculate allocation percentages
    allocation = {k: round(v / total * 100, 1) if total > 0 else 0 for k, v in categories.items()}
    
    return {
        "total_networth": round(total, 2),
        "categories": {k: round(v, 2) for k, v in categories.items() if v > 0},
        "allocation": {k: v for k, v in allocation.items() if v > 0},
        "assets_count": len(assets) + len(holdings)
    }

@router.post("/asset")
async def add_asset(asset: dict, current_user: dict = Depends(get_current_user)):
    """Add a non-market asset (FD, PPF, etc.)"""
    db = get_db()
    if db is None:
        return {"error": "Database not connected"}
    
    user_id = str(current_user["_id"])
    
    new_asset = {
        "user_id": user_id,
        "name": asset.get("name"),
        "category": asset.get("category"),  # FD, PPF, NPS, EPF, Gold, Real Estate, Savings
        "value": asset.get("value", 0),
        "invested": asset.get("invested", asset.get("value", 0)),
        "interest_rate": asset.get("interest_rate"),
        "maturity_date": asset.get("maturity_date"),
        "notes": asset.get("notes"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.assets.insert_one(new_asset)
    return {"message": "Asset added", "id": str(result.inserted_id)}

@router.get("/assets")
async def list_assets(current_user: dict = Depends(get_current_user)):
    """List all non-market assets"""
    db = get_db()
    if db is None:
        return {"error": "Database not connected"}
    
    user_id = str(current_user["_id"])
    assets = await db.assets.find({"user_id": user_id}).to_list(100)
    
    for a in assets:
        a["_id"] = str(a["_id"])
    
    return {"assets": assets}

@router.put("/asset/{asset_id}")
async def update_asset(asset_id: str, asset: dict, current_user: dict = Depends(get_current_user)):
    """Update an asset"""
    db = get_db()
    if db is None:
        return {"error": "Database not connected"}
    
    from bson import ObjectId
    update = {"updated_at": datetime.utcnow()}
    for k in ["name", "category", "value", "interest_rate", "maturity_date", "notes"]:
        if k in asset:
            update[k] = asset[k]
    
    await db.assets.update_one({"_id": ObjectId(asset_id), "user_id": str(current_user["_id"])}, {"$set": update})
    return {"message": "Asset updated"}

@router.delete("/asset/{asset_id}")
async def delete_asset(asset_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an asset"""
    db = get_db()
    if db is None:
        return {"error": "Database not connected"}
    
    from bson import ObjectId
    await db.assets.delete_one({"_id": ObjectId(asset_id), "user_id": str(current_user["_id"])})
    return {"message": "Asset deleted"}

@router.get("/history")
async def get_networth_history(current_user: dict = Depends(get_current_user)):
    """Get net worth history for chart"""
    db = get_db()
    if db is None:
        return {"error": "Database not connected"}
    
    user_id = str(current_user["_id"])
    
    # Get history from snapshots collection
    history = await db.networth_history.find(
        {"user_id": user_id}
    ).sort("date", -1).limit(365).to_list(365)
    
    history.reverse()
    
    return {
        "history": [{"date": h["date"].isoformat() if isinstance(h["date"], datetime) else h["date"], 
                     "value": h["value"]} for h in history]
    }

@router.post("/snapshot")
async def take_snapshot(current_user: dict = Depends(get_current_user)):
    """Manually take a net worth snapshot with current values"""
    db = get_db()
    if db is None:
        return {"error": "Database not connected"}
    
    user_id = str(current_user["_id"])
    now = datetime.now()
    
    # Get current holdings
    from ..api.portfolio import get_holdings
    holdings = await get_holdings(current_user)
    assets = await db.assets.find({"user_id": user_id}).to_list(100)
    
    stocks_val = sum(h.get("current_value", 0) for h in holdings if h.get("holding_type") != "MF")
    mf_val = sum(h.get("current_value", 0) for h in holdings if h.get("holding_type") == "MF")
    
    breakdown = {}
    if stocks_val > 0:
        breakdown["Stocks"] = round(stocks_val, 2)
    if mf_val > 0:
        breakdown["Mutual"] = round(mf_val, 2)
    
    # Use asset NAME for breakdown (not category)
    for a in assets:
        name = a.get("name", a.get("category", "Others"))
        breakdown[name] = round(a.get("value", 0), 2)
    
    total = sum(breakdown.values())
    
    # Upsert for today
    today = datetime(now.year, now.month, now.day)
    await db.networth_history.update_one(
        {"user_id": user_id, "date": today},
        {"$set": {"user_id": user_id, "date": today, "value": total, "breakdown": breakdown}},
        upsert=True
    )
    
    return {"message": "Snapshot saved", "date": today.strftime("%Y-%m-%d"), "total": total, "breakdown": breakdown}

@router.get("/monthly")
async def get_monthly_networth(year: int = None, current_user: dict = Depends(get_current_user)):
    """Get monthly net worth with growth tracking and benchmarks"""
    db = get_db()
    if db is None:
        return {"error": "Database not connected"}
    
    user_id = str(current_user["_id"])
    year = year or datetime.now().year
    now = datetime.now()
    
    # Auto-snapshot current month if viewing current year and no snapshot exists this month
    if year == now.year:
        current_month_start = datetime(now.year, now.month, 1)
        current_month_end = datetime(now.year, now.month + 1, 1) if now.month < 12 else datetime(now.year + 1, 1, 1)
        
        existing = await db.networth_history.find_one({
            "user_id": user_id,
            "date": {"$gte": current_month_start, "$lt": current_month_end}
        })
        
        if not existing:
            # Get current net worth from holdings + assets
            from ..api.portfolio import get_holdings
            holdings = await get_holdings(current_user)
            assets = await db.assets.find({"user_id": user_id}).to_list(100)
            
            stocks_val = sum(h.get("current_value", 0) for h in holdings if h.get("holding_type") != "MF")
            mf_val = sum(h.get("current_value", 0) for h in holdings if h.get("holding_type") == "MF")
            
            breakdown = {"Stocks": round(stocks_val, 2), "Mutual": round(mf_val, 2)}
            for a in assets:
                cat = a.get("category", a.get("name", "Others"))
                breakdown[cat] = breakdown.get(cat, 0) + a.get("value", 0)
            
            total = sum(breakdown.values())
            
            if total > 0:
                await db.networth_history.insert_one({
                    "user_id": user_id,
                    "date": now,
                    "value": total,
                    "breakdown": breakdown
                })
    
    # Benchmarks (annual rates)
    BENCHMARKS = {
        "inflation": 6.0,      # India avg inflation
        "fd_rate": 7.0,        # FD returns
        "nifty_avg": 12.0,     # Nifty long-term avg
        "good_growth": 15.0    # Target for good wealth building
    }
    
    monthly = []
    prev_value = None
    
    for month in range(1, 13):
        start = datetime(year, month, 1)
        end = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
        
        # Get FIRST snapshot of month (for consistent month-start comparison)
        snap = await db.networth_history.find_one(
            {"user_id": user_id, "date": {"$gte": start, "$lt": end}},
            sort=[("date", 1)]
        )
        
        # Use snapshot value, or carry forward previous value if no data
        value = snap.get("value", 0) if snap else (prev_value or 0)
        has_data = snap is not None
        
        if prev_value and prev_value > 0 and has_data:
            change = value - prev_value
            change_pct = (change / prev_value) * 100
        else:
            change = 0
            change_pct = 0
        
        monthly.append({
            "month": month,
            "month_name": datetime(year, month, 1).strftime("%b"),
            "value": round(value, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "has_data": has_data
        })
        if value > 0:
            prev_value = value
    
    # Get last value from previous year if first month has no comparison
    prev_year_last = await db.networth_history.find_one(
        {"user_id": user_id, "date": {"$lt": datetime(year, 1, 1)}},
        sort=[("date", -1)]
    )
    prev_year_val = prev_year_last.get("value", 0) if prev_year_last else 0
    
    # Update Jan change if we have prev year data
    if monthly and monthly[0]["has_data"] and prev_year_val > 0:
        jan_change = monthly[0]["value"] - prev_year_val
        monthly[0]["change"] = round(jan_change, 2)
        monthly[0]["change_pct"] = round((jan_change / prev_year_val) * 100, 2)
    
    # Calculate YTD growth - use prev year end as baseline if available
    first_val = prev_year_val if prev_year_val > 0 else next((m["value"] for m in monthly if m["value"] > 0), 0)
    last_val = next((m["value"] for m in reversed(monthly) if m["value"] > 0), 0)
    
    # Count months with actual data
    months_with_data = sum(1 for m in monthly if m["has_data"])
    
    if first_val > 0 and last_val > 0:
        ytd_growth = ((last_val - first_val) / first_val) * 100
        # Annualize based on months elapsed
        annualized = (ytd_growth / max(months_with_data, 1)) * 12
    else:
        ytd_growth = 0
        annualized = 0
    
    # Performance vs benchmarks
    performance = {
        "beating_inflation": annualized > BENCHMARKS["inflation"],
        "beating_fd": annualized > BENCHMARKS["fd_rate"],
        "beating_nifty": annualized > BENCHMARKS["nifty_avg"],
        "good_growth": annualized >= BENCHMARKS["good_growth"]
    }
    
    # Rating
    score = sum([performance["beating_inflation"], performance["beating_fd"], performance["beating_nifty"], performance["good_growth"]])
    rating = ["Poor", "Below Avg", "Average", "Good", "Excellent"][score]
    
    return {
        "year": year,
        "monthly": monthly,
        "ytd_growth": round(ytd_growth, 2),
        "annualized_growth": round(annualized, 2),
        "benchmarks": BENCHMARKS,
        "performance": performance,
        "rating": rating
    }


@router.post("/import-history")
async def import_networth_history(data: dict, current_user: dict = Depends(get_current_user)):
    """Import net worth history with detailed breakdown
    
    Expected format:
    { "snapshots": [
        {
          "date": "2025-01-01",
          "total": 274422,
          "breakdown": {
            "Union": 143352,
            "Mutual Funds": 80461,
            "Stocks": 26609,
            "Cash": 3000,
            "Savings": 21000
          }
        }
      ]
    }
    """
    db = get_db()
    if db is None:
        return {"error": "Database not connected"}
    
    user_id = str(current_user["_id"])
    imported = 0
    
    snapshots = data.get("snapshots") or []
    
    # Also support simple format
    if not snapshots and data.get("history"):
        for h in data["history"]:
            snapshots.append({"date": h.get("date"), "total": h.get("value"), "breakdown": {}})
    
    if not snapshots and data.get("monthly"):
        for m in data["monthly"]:
            month_str = m.get("month", "")
            try:
                if "-" in month_str and len(month_str) == 7:
                    dt = datetime.strptime(month_str + "-28", "%Y-%m-%d")
                else:
                    dt = datetime.strptime(month_str, "%b %Y")
                    if dt.month == 12:
                        dt = dt.replace(day=31)
                    else:
                        dt = (dt.replace(month=dt.month + 1, day=1) - timedelta(days=1))
                snapshots.append({"date": dt.strftime("%Y-%m-%d"), "total": m.get("value"), "breakdown": m.get("breakdown", {})})
            except:
                continue
    
    for snap in snapshots:
        date_str = snap.get("date")
        total = snap.get("total", 0)
        breakdown = snap.get("breakdown", {})
        
        if not date_str or not total:
            continue
        
        try:
            dt = datetime.strptime(date_str[:10], "%Y-%m-%d") if isinstance(date_str, str) else date_str
        except:
            continue
        
        await db.networth_history.update_one(
            {"user_id": user_id, "date": dt},
            {"$set": {"user_id": user_id, "date": dt, "value": float(total), "breakdown": breakdown}},
            upsert=True
        )
        imported += 1
    
    return {"message": f"Imported {imported} records", "imported": imported}

@router.get("/history-detail")
async def get_networth_history_detail(year: int = None, current_user: dict = Depends(get_current_user)):
    """Get detailed net worth history with breakdown"""
    db = get_db()
    if db is None:
        return {"error": "Database not connected"}
    
    user_id = str(current_user["_id"])
    year = year or datetime.now().year
    
    start = datetime(year, 1, 1)
    end = datetime(year + 1, 1, 1)
    
    history = await db.networth_history.find(
        {"user_id": user_id, "date": {"$gte": start, "$lt": end}}
    ).sort("date", 1).to_list(100)
    
    result = []
    prev_value = None
    for h in history:
        value = h.get("value", 0)
        change = value - prev_value if prev_value else 0
        change_pct = (change / prev_value * 100) if prev_value and prev_value > 0 else 0
        
        result.append({
            "date": h["date"].strftime("%Y-%m-%d") if isinstance(h["date"], datetime) else h["date"],
            "total": value,
            "breakdown": h.get("breakdown", {}),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2)
        })
        prev_value = value
    
    return {"year": year, "history": result}
