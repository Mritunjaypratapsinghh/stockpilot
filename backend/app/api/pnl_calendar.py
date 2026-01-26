from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from bson import ObjectId
from ..api.auth import get_current_user
from ..database import get_db

router = APIRouter()

@router.get("/daily")
async def get_daily_pnl(year: int = None, month: int = None, current_user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = ObjectId(current_user["_id"])
    now = datetime.now(timezone.utc)
    year = year or now.year
    month = month or now.month
    
    start_date = datetime(year, month, 1, tzinfo=timezone.utc)
    end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc) if month < 12 else datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    
    transactions = await db.transactions.find({"user_id": user_id, "date": {"$gte": start_date, "$lt": end_date}}).to_list(1000)
    snapshots = await db.portfolio_snapshots.find({"user_id": user_id, "date": {"$gte": start_date, "$lt": end_date}}).to_list(31)
    
    calendar = {}
    prev_value = None
    
    for snap in sorted(snapshots, key=lambda x: x["date"]):
        date_str = snap["date"].strftime("%Y-%m-%d") if isinstance(snap["date"], datetime) else snap["date"]
        value = snap.get("value", 0)
        
        pnl = value - prev_value if prev_value is not None else 0
        pnl_pct = (pnl / prev_value * 100) if prev_value and prev_value > 0 else 0
        
        calendar[date_str] = {"value": round(value, 2), "pnl": round(pnl, 2), "pnl_pct": round(pnl_pct, 2)}
        prev_value = value
    
    for txn in transactions:
        date_str = txn["date"].strftime("%Y-%m-%d") if isinstance(txn["date"], datetime) else str(txn["date"])[:10]
        if date_str in calendar:
            if "transactions" not in calendar[date_str]:
                calendar[date_str]["transactions"] = []
            calendar[date_str]["transactions"].append({"type": txn.get("type"), "symbol": txn.get("symbol"), "amount": txn.get("quantity", 0) * txn.get("price", 0)})
    
    total_pnl = sum(d.get("pnl", 0) for d in calendar.values())
    return {"year": year, "month": month, "calendar": calendar, "monthly_pnl": round(total_pnl, 2), "trading_days": len(calendar)}

@router.get("/monthly")
async def get_monthly_pnl(year: int = None, current_user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = ObjectId(current_user["_id"])
    year = year or datetime.now(timezone.utc).year
    
    monthly = []
    for month in range(1, 13):
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc) if month < 12 else datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        
        first = await db.portfolio_snapshots.find_one({"user_id": user_id, "date": {"$gte": start, "$lt": end}}, sort=[("date", 1)])
        last = await db.portfolio_snapshots.find_one({"user_id": user_id, "date": {"$gte": start, "$lt": end}}, sort=[("date", -1)])
        
        if first and last:
            start_val = first.get("value", 0)
            end_val = last.get("value", 0)
            pnl = end_val - start_val
            pnl_pct = (pnl / start_val * 100) if start_val > 0 else 0
        else:
            pnl = 0
            pnl_pct = 0
        
        monthly.append({"month": month, "month_name": datetime(year, month, 1).strftime("%b"), "pnl": round(pnl, 2), "pnl_pct": round(pnl_pct, 2)})
    
    return {"year": year, "monthly": monthly, "yearly_pnl": round(sum(m["pnl"] for m in monthly), 2)}

@router.get("/dividends")
async def get_dividend_calendar(year: int = None, current_user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = ObjectId(current_user["_id"])
    year = year or datetime.now(timezone.utc).year
    
    holdings = await db.holdings.find({"user_id": user_id}).to_list(100)
    
    dividends = []
    for h in holdings:
        if h.get("holding_type") == "STOCK":
            for q in [3, 6, 9, 12]:
                dividends.append({"symbol": h.get("symbol"), "date": f"{year}-{q:02d}-15", "amount": round(h.get("quantity", 0) * 2.5, 2), "type": "dividend"})
    
    return {"year": year, "dividends": sorted(dividends, key=lambda x: x["date"]), "total_expected": round(sum(d["amount"] for d in dividends), 2)}
