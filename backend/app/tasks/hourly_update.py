from ..database import get_db
from ..services.price_service import get_bulk_prices
from ..config import get_settings
import httpx

settings = get_settings()

async def send_hourly_update():
    db = get_db()
    users = await db.users.find({"settings.hourly_alerts": True}).to_list(500)
    
    for user in users:
        holdings = await db.holdings.find({"user_id": user["_id"]}).to_list(100)
        if not holdings:
            continue
        
        symbols = [h["symbol"] for h in holdings]
        prices = await get_bulk_prices(symbols)
        
        total_inv = sum(h["quantity"] * h["avg_price"] for h in holdings)
        current_val = sum(h["quantity"] * (prices.get(h["symbol"], {}).get("current_price") or h["avg_price"]) for h in holdings)
        pnl = current_val - total_inv
        pnl_pct = (pnl / total_inv * 100) if total_inv > 0 else 0
        
        emoji = "🟢" if pnl >= 0 else "🔴"
        msg = f"⏰ *Hourly Update*\n\n💰 Value: ₹{current_val:,.0f}\n{emoji} P&L: ₹{pnl:,.0f} ({pnl_pct:+.1f}%)"
        
        # Telegram
        if user.get("telegram_chat_id") and settings.telegram_bot_token:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                        json={"chat_id": user["telegram_chat_id"], "text": msg, "parse_mode": "Markdown"})
            except:
                pass
