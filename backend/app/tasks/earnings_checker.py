from ..database import get_db
from ..services.notification_service import send_email
from datetime import datetime, timedelta
import httpx

async def get_earnings_date(symbol: str):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}.NS?modules=calendarEvents", headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                data = resp.json()["quoteSummary"]["result"][0].get("calendarEvents", {})
                earnings = data.get("earnings", {}).get("earningsDate", [])
                if earnings:
                    return datetime.fromtimestamp(earnings[0]["raw"])
    except:
        pass
    return None

async def check_earnings_alerts():
    db = get_db()
    alerts = await db.alerts.find({"alert_type": "EARNINGS", "is_active": True}).to_list(100)
    
    for alert in alerts:
        earnings_date = await get_earnings_date(alert["symbol"])
        if not earnings_date:
            continue
        
        days_until = (earnings_date.date() - datetime.utcnow().date()).days
        
        if days_until <= alert.get("target_value", 3) and days_until >= 0:
            user = await db.users.find_one({"_id": alert["user_id"]})
            if user:
                msg = f"📅 Earnings Reminder: {alert['symbol']} reports in {days_until} day(s) on {earnings_date.strftime('%b %d, %Y')}"
                
                if user.get("telegram_chat_id"):
                    from ..config import get_settings
                    settings = get_settings()
                    if settings.telegram_bot_token:
                        async with httpx.AsyncClient() as client:
                            await client.post(f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                                json={"chat_id": user["telegram_chat_id"], "text": msg})
                
                if user.get("email"):
                    await send_email(user["email"], f"Earnings Alert: {alert['symbol']}", f"<p>{msg}</p>")
            
            await db.alerts.update_one({"_id": alert["_id"]}, {"$set": {"triggered_at": datetime.utcnow(), "notification_sent": True, "is_active": False}})
