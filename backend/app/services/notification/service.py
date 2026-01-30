import httpx
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ...core.database import get_database as get_db
from ...core.config import get_settings
from ...utils.logger import logger

settings = get_settings()

async def send_email(to_email: str, subject: str, body: str):
    if not settings.smtp_host or not settings.smtp_user:
        return
    try:
        msg = MIMEMultipart()
        msg["From"] = settings.smtp_user
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))
        
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_pass)
            server.send_message(msg)
    except Exception as e:
        logger.error(f"Email error: {e}")

async def send_web_push(user_id, title: str, body: str):
    """Send web push notification if user has subscription"""
    db = get_db()
    if db is None:
        return
    user = await db.users.find_one({"_id": user_id})
    
    if not user or not user.get("push_subscription"):
        return
    
    from datetime import datetime, timezone
    await db.notifications.insert_one({
        "user_id": user_id,
        "title": title,
        "body": body,
        "read": False,
        "created_at": datetime.now(timezone.utc)
    })

async def send_alert_notification(alert: dict, current_price: float):
    db = get_db()
    user = await db.users.find_one({"_id": alert["user_id"]})
    
    if not user:
        return
    
    msg = f"🔔 Alert Triggered!\n\n{alert['symbol']}: ₹{current_price:.2f}\nCondition: {alert['alert_type'].replace('_', ' ')} ₹{alert['target_value']}"
    
    # Telegram
    if user.get("telegram_chat_id") and settings.telegram_bot_token:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                    json={"chat_id": user["telegram_chat_id"], "text": msg, "parse_mode": "Markdown"}
                )
        except httpx.HTTPError as e:
            logger.warning(f"Telegram alert error: {e}")
    
    # Email
    if user.get("email"):
        html = f"<h2>🔔 StockPilot Alert</h2><p><strong>{alert['symbol']}</strong>: ₹{current_price:.2f}</p><p>Condition: {alert['alert_type'].replace('_', ' ')} ₹{alert['target_value']}</p>"
        await send_email(user["email"], f"StockPilot Alert: {alert['symbol']}", html)
    
    # Web Push
    await send_web_push(alert["user_id"], f"Alert: {alert['symbol']}", msg)

async def send_daily_digest(user_id, digest: dict):
    db = get_db()
    user = await db.users.find_one({"_id": user_id})
    
    if not user:
        return
    
    emoji = "🟢" if digest["day_pnl"] >= 0 else "🔴"
    msg = f"📊 *Daily Digest*\n\n💰 Portfolio: ₹{digest['portfolio_value']:,.0f}\n{emoji} Today: ₹{digest['day_pnl']:,.0f} ({digest['day_pnl_pct']:+.1f}%)\n📈 Total P&L: ₹{digest['total_pnl']:,.0f} ({digest['total_pnl_pct']:+.1f}%)"
    
    # Telegram
    if user.get("telegram_chat_id") and settings.telegram_bot_token:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                    json={"chat_id": user["telegram_chat_id"], "text": msg, "parse_mode": "Markdown"}
                )
        except httpx.HTTPError as e:
            logger.warning(f"Telegram digest error: {e}")
    
    # Email
    if user.get("email"):
        html = f"""<h2>📊 StockPilot Daily Digest</h2>
        <p><strong>Portfolio Value:</strong> ₹{digest['portfolio_value']:,.0f}</p>
        <p><strong>Today's P&L:</strong> ₹{digest['day_pnl']:,.0f} ({digest['day_pnl_pct']:+.1f}%)</p>
        <p><strong>Total P&L:</strong> ₹{digest['total_pnl']:,.0f} ({digest['total_pnl_pct']:+.1f}%)</p>"""
        if digest.get("top_gainer"):
            html += f"<p>🏆 Top Gainer: {digest['top_gainer']['symbol']} ({digest['top_gainer']['change_pct']:+.1f}%)</p>"
        if digest.get("top_loser"):
            html += f"<p>📉 Top Loser: {digest['top_loser']['symbol']} ({digest['top_loser']['change_pct']:+.1f}%)</p>"
        await send_email(user["email"], "StockPilot Daily Digest", html)
    
    # Web Push
    await send_web_push(user_id, "Daily Digest", f"Portfolio: ₹{digest['portfolio_value']:,.0f} | P&L: {digest['day_pnl_pct']:+.1f}%")
