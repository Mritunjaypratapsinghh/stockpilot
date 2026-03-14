from datetime import datetime, timezone

import httpx

from ..models.documents import Alert, Holding, User
from ..services.cache import cache_get, cache_set, get_redis
from ..services.market.price_service import get_bulk_prices
from ..services.notification.service import send_alert_notification
from ..utils.logger import logger


async def get_52week_data(symbol: str):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS?interval=1d&range=1y",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if resp.status_code == 200:
                result = resp.json()["chart"]["result"][0]
                highs = [h for h in result["indicators"]["quote"][0]["high"] if h]
                lows = [low for low in result["indicators"]["quote"][0]["low"] if low]
                volumes = [v for v in result["indicators"]["quote"][0]["volume"] if v]
                return {
                    "high_52w": max(highs) if highs else None,
                    "low_52w": min(lows) if lows else None,
                    "avg_volume": sum(volumes[-20:]) / 20 if len(volumes) >= 20 else None,
                }
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.debug(f"52week data error for {symbol}: {e}")
    return {}


async def check_alerts():
    redis = await get_redis()
    if redis:
        acquired = await redis.set("lock:check_alerts", "1", ex=50, nx=True)
        if not acquired:
            return

    alerts = await Alert.find(
        Alert.is_active == True,  # noqa: E712
        Alert.notification_sent == False,  # noqa: E712
    ).to_list()

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
            await send_alert_notification(
                {
                    "symbol": alert.symbol,
                    "alert_type": alert.alert_type,
                    "target_value": alert.target_value,
                    "user_id": str(alert.user_id),
                },
                current_price,
            )


async def check_stop_losses():
    """Check if any holding breached its signal engine stop_loss."""
    redis = await get_redis()
    if redis:
        acquired = await redis.set("lock:check_stop_losses", "1", ex=280, nx=True)
        if not acquired:
            return

    users = await User.find(User.settings.alerts_enabled != False).to_list()  # noqa: E712

    for user in users:
        try:
            await _check_user_stop_losses(user)
        except Exception as e:
            logger.error(f"Stop-loss check failed for {user.email}: {e}")


async def _check_user_stop_losses(user):
    holdings = await Holding.find(Holding.user_id == user.id).to_list()
    equity = [h for h in holdings if h.holding_type != "MF"]
    if not equity:
        return

    # Get cached signals (from hourly update or signals page)
    sig_map = await cache_get(f"hourly_signals:{user.id}")
    if not sig_map:
        sig_map = await cache_get(f"daily_signals:{user.id}")
    if not sig_map:
        return

    symbols = [h.symbol for h in equity]
    prices = await get_bulk_prices(symbols)

    # Track which stop-losses we already alerted today
    today = datetime.now(timezone.utc).date().isoformat()
    alerted_key = f"sl_alerted:{user.id}:{today}"
    alerted_raw = await cache_get(alerted_key)
    alerted = set(alerted_raw) if alerted_raw else set()

    newly_alerted = []
    for h in equity:
        if h.symbol in alerted:
            continue
        sig = sig_map.get(h.symbol, {})
        stop_loss = sig.get("stop_loss")
        if not stop_loss:
            continue

        curr = prices.get(h.symbol, {}).get("current_price")
        if not curr or curr > stop_loss:
            continue

        # Breached!
        newly_alerted.append(h.symbol)
        await send_alert_notification(
            {
                "symbol": h.symbol,
                "alert_type": "STOP_LOSS",
                "target_value": stop_loss,
                "user_id": str(user.id),
            },
            curr,
        )

    if newly_alerted:
        alerted.update(newly_alerted)
        await cache_set(alerted_key, list(alerted), ttl=43200)
