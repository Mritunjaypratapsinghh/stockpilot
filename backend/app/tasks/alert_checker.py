from ..models.documents import Alert
from ..services.price_service import get_bulk_prices
from ..services.notification_service import send_alert_notification
from datetime import datetime, timezone
import httpx


async def get_52week_data(symbol: str):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS?interval=1d&range=1y", headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                result = resp.json()["chart"]["result"][0]
                highs = [h for h in result["indicators"]["quote"][0]["high"] if h]
                lows = [l for l in result["indicators"]["quote"][0]["low"] if l]
                volumes = [v for v in result["indicators"]["quote"][0]["volume"] if v]
                return {"high_52w": max(highs) if highs else None, "low_52w": min(lows) if lows else None, "avg_volume": sum(volumes[-20:]) / 20 if len(volumes) >= 20 else None}
    except:
        pass
    return {}


async def check_alerts():
    alerts = await Alert.find(Alert.is_active == True, Alert.notification_sent == False).to_list()
    
    if not alerts:
        return
    
    symbols = list(set(a.symbol for a in alerts))
    prices = await get_bulk_prices(symbols)
    
    week52_data = {}
    for a in alerts:
        if a.alert_type in ["WEEK_52_HIGH", "WEEK_52_LOW", "VOLUME_SPIKE"] and a.symbol not in week52_data:
            week52_data[a.symbol] = await get_52week_data(a.symbol)
    
    for alert in alerts:
        price_data = prices.get(alert.symbol, {})
        current_price = price_data.get("current_price")
        
        if not current_price:
            continue
        
        triggered = False
        if alert.alert_type == "PRICE_ABOVE" and current_price >= alert.target_value:
            triggered = True
        elif alert.alert_type == "PRICE_BELOW" and current_price <= alert.target_value:
            triggered = True
        elif alert.alert_type == "PERCENT_CHANGE":
            change_pct = abs(price_data.get("day_change_pct", 0))
            if change_pct >= alert.target_value:
                triggered = True
        elif alert.alert_type == "WEEK_52_HIGH":
            w52 = week52_data.get(alert.symbol, {})
            if w52.get("high_52w") and current_price >= w52["high_52w"] * 0.98:
                triggered = True
        elif alert.alert_type == "WEEK_52_LOW":
            w52 = week52_data.get(alert.symbol, {})
            if w52.get("low_52w") and current_price <= w52["low_52w"] * 1.02:
                triggered = True
        elif alert.alert_type == "VOLUME_SPIKE":
            w52 = week52_data.get(alert.symbol, {})
            curr_vol = price_data.get("volume", 0)
            avg_vol = w52.get("avg_volume", 0)
            if avg_vol and curr_vol >= avg_vol * (alert.target_value / 100 + 1):
                triggered = True
        
        if triggered:
            alert.triggered_at = datetime.now(timezone.utc)
            alert.notification_sent = True
            alert.is_active = False
            await alert.save()
            await send_alert_notification({"symbol": alert.symbol, "alert_type": alert.alert_type, "target_value": alert.target_value, "user_id": str(alert.user_id)}, current_price)
