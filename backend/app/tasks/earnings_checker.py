from ..models.documents import Alert, User
from ..services.notification.service import send_email
from ..core.config import settings
from ..utils.logger import logger
from datetime import datetime, timezone
import httpx


async def get_earnings_date(symbol: str):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}.NS?modules=calendarEvents", headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                data = resp.json()["quoteSummary"]["result"][0].get("calendarEvents", {})
                earnings = data.get("earnings", {}).get("earningsDate", [])
                if earnings:
                    return datetime.fromtimestamp(earnings[0]["raw"], tz=timezone.utc)
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.debug(f"Earnings date error for {symbol}: {e}")
    return None


async def check_earnings_alerts():
    alerts = await Alert.find(Alert.alert_type == "EARNINGS", Alert.is_active == True).to_list()
    
    for alert in alerts:
        earnings_date = await get_earnings_date(alert.symbol)
        if not earnings_date:
            continue
        
        days_until = (earnings_date.date() - datetime.now(timezone.utc).date()).days
        
        if days_until <= (alert.target_value or 3) and days_until >= 0:
            user = await User.get(alert.user_id)
            if user:
                msg = f"📅 Earnings Reminder: {alert.symbol} reports in {days_until} day(s) on {earnings_date.strftime('%b %d, %Y')}"
                
                if user.telegram_chat_id and settings.telegram_bot_token:
                    async with httpx.AsyncClient() as client:
                        await client.post(f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                            json={"chat_id": user.telegram_chat_id, "text": msg})
                
                if user.email:
                    await send_email(user.email, f"Earnings Alert: {alert.symbol}", f"<p>{msg}</p>")
            
            alert.triggered_at = datetime.now(timezone.utc)
            alert.notification_sent = True
            alert.is_active = False
            await alert.save()
