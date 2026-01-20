from ..database import get_db
from ..services.price_service import get_bulk_prices
from ..services.notification_service import send_daily_digest
from datetime import datetime
from bson import ObjectId

async def generate_daily_digest():
    db = get_db()
    users = await db.users.find({"settings.daily_digest": True}).to_list(500)
    
    for user in users:
        holdings = await db.holdings.find({"user_id": user["_id"]}).to_list(100)
        if not holdings:
            continue
        
        symbols = [h["symbol"] for h in holdings]
        prices = await get_bulk_prices(symbols)
        
        total_inv = 0
        current_val = 0
        day_pnl = 0
        performance = []
        
        for h in holdings:
            inv = h["quantity"] * h["avg_price"]
            total_inv += inv
            p = prices.get(h["symbol"], {})
            curr_price = p.get("current_price") or h["avg_price"]
            prev_close = p.get("previous_close") or curr_price
            val = h["quantity"] * curr_price
            current_val += val
            day_change = (curr_price - prev_close) * h["quantity"]
            day_pnl += day_change
            performance.append({"symbol": h["symbol"], "change_pct": p.get("day_change_pct", 0)})
        
        total_pnl = current_val - total_inv
        total_pnl_pct = (total_pnl / total_inv * 100) if total_inv > 0 else 0
        day_pnl_pct = (day_pnl / (current_val - day_pnl) * 100) if (current_val - day_pnl) > 0 else 0
        
        sorted_perf = sorted(performance, key=lambda x: x["change_pct"], reverse=True)
        
        digest = {
            "user_id": user["_id"],
            "date": datetime.utcnow().date().isoformat(),
            "portfolio_value": round(current_val, 0),
            "day_pnl": round(day_pnl, 0),
            "day_pnl_pct": round(day_pnl_pct, 1),
            "total_pnl": round(total_pnl, 0),
            "total_pnl_pct": round(total_pnl_pct, 1),
            "top_gainer": sorted_perf[0] if sorted_perf else None,
            "top_loser": sorted_perf[-1] if sorted_perf else None,
            "sent_at": datetime.utcnow()
        }
        
        await db.daily_digest.insert_one(digest)
        await send_daily_digest(user["_id"], digest)
