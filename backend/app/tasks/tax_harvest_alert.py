"""Proactive tax harvesting alerts — check portfolio for opportunities."""

from datetime import datetime, timedelta

import httpx
import pytz

from ..core.config import settings
from ..models.documents import Holding, User
from ..services.cache import cache_get, cache_set, get_redis
from ..services.market.price_service import get_bulk_prices
from ..services.notification.service import send_email
from ..utils.logger import logger

IST = pytz.timezone("Asia/Kolkata")
STCG_RATE = 0.20
LTCG_RATE = 0.125


async def check_tax_harvesting():
    redis = await get_redis()
    if redis:
        acquired = await redis.set("lock:tax_harvest_alert", "1", ex=300, nx=True)
        if not acquired:
            return

    users = await User.find(User.settings.alerts_enabled != False).to_list()  # noqa: E712

    for user in users:
        try:
            await _check_user(user)
        except Exception as e:
            logger.error(f"Tax harvest alert failed: {e}")


async def _check_user(user):
    # Only alert once per week
    ck = f"tax_harvest_alerted:{user.id}"
    if await cache_get(ck):
        return

    holdings = await Holding.find(Holding.user_id == user.id).to_list()
    equity = [h for h in holdings if h.holding_type != "MF"]
    if not equity:
        return

    prices = await get_bulk_prices([h.symbol for h in equity])
    one_year_ago = datetime.now() - timedelta(days=365)

    opportunities = []
    total_tax_saved = 0

    for h in equity:
        curr = prices.get(h.symbol, {}).get("current_price") or h.avg_price
        pnl = (curr - h.avg_price) * h.quantity
        if pnl >= 0:
            continue

        first_buy = None
        for t in h.transactions:
            if t.type == "BUY":
                td = datetime.fromisoformat(t.date) if isinstance(t.date, str) else t.date
                if first_buy is None or td < first_buy:
                    first_buy = td

        is_lt = first_buy and first_buy < one_year_ago
        rate = LTCG_RATE if is_lt else STCG_RATE
        tax_saved = abs(pnl) * rate

        if tax_saved >= 500:  # Only alert if meaningful
            opportunities.append(
                {
                    "symbol": h.symbol,
                    "loss": round(pnl, 0),
                    "tax_saved": round(tax_saved, 0),
                    "type": "LTCG" if is_lt else "STCG",
                }
            )
            total_tax_saved += tax_saved

    if not opportunities or total_tax_saved < 1000:
        return

    opportunities.sort(key=lambda x: x["tax_saved"], reverse=True)
    top = opportunities[:5]

    await cache_set(ck, True, ttl=604800)  # 7 days

    # AI insight
    ai = await _get_ai_insight(top, total_tax_saved)

    if user.email:
        html = _build_email(top, total_tax_saved, ai)
        await send_email(user.email, "StockPilot: Tax Harvesting Opportunity", html)

    if user.telegram_chat_id and settings.telegram_bot_token:
        msg = _build_telegram(top, total_tax_saved, ai)
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot" f"{settings.telegram_bot_token}/sendMessage",
                    json={
                        "chat_id": user.telegram_chat_id,
                        "text": msg,
                        "parse_mode": "Markdown",
                    },
                )
        except httpx.HTTPError as e:
            logger.warning(f"Tax harvest telegram error: {e}")


async def _get_ai_insight(opps, total_saved):
    if not settings.groq_api_key:
        return ""
    try:
        from groq import Groq

        stocks = ", ".join(f"{o['symbol']}(loss ₹{o['loss']:,.0f}, save ₹{o['tax_saved']:,.0f})" for o in opps[:3])
        client = Groq(api_key=settings.groq_api_key)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a concise Indian tax advisor. "
                        "Write 2 sentences (max 40 words) about "
                        "this tax harvesting opportunity. "
                        "Mention specific stocks and savings. "
                        "Remind about 30-day wash sale rule. "
                        "No disclaimers."
                    ),
                },
                {
                    "role": "user",
                    "content": (f"Total potential tax savings: " f"₹{total_saved:,.0f}. Stocks: {stocks}"),
                },
            ],
            temperature=0.3,
            max_completion_tokens=80,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return ""


def _build_email(opps, total_saved, ai):
    rows = ""
    for o in opps:
        rows += (
            '<tr style="border-bottom:1px solid #f0f0f0">'
            f'<td style="padding:6px 8px;font-weight:600">'
            f'{o["symbol"]}</td>'
            f'<td style="padding:6px 8px;text-align:right;'
            f'color:#ef4444">₹{o["loss"]:,.0f}</td>'
            f'<td style="padding:6px 8px;text-align:right;'
            f'color:#10b981;font-weight:600">'
            f'₹{o["tax_saved"]:,.0f}</td>'
            f'<td style="padding:6px 8px;text-align:center;'
            f'font-size:12px">{o["type"]}</td></tr>'
        )

    ai_html = ""
    if ai:
        ai_html = (
            '<div style="background:#f0f0ff;border-left:3px solid'
            " #6366f1;padding:10px 14px;margin:12px 0;"
            'border-radius:0 6px 6px 0">'
            '<div style="font-size:13px;color:#333;'
            f'line-height:1.4">🤖 {ai}</div></div>'
        )

    hdr = (
        "font-family:-apple-system,BlinkMacSystemFont,"
        "'Segoe UI',Roboto,sans-serif;max-width:520px;"
        "margin:0 auto;background:#fff;"
        "border-radius:8px;overflow:hidden"
    )
    grad = "background:linear-gradient(135deg,#f59e0b,#d97706);" "padding:16px 20px;color:#fff"
    th = "padding:6px 8px;font-size:11px;color:#888;font-weight:600"

    return (
        f'<div style="{hdr}">'
        f'<div style="{grad}">'
        '<div style="font-size:12px;opacity:0.85">'
        "💰 Tax Harvesting Alert</div>"
        '<div style="font-size:24px;font-weight:700;'
        f'margin:4px 0">Save ₹{total_saved:,.0f} in tax</div>'
        '<div style="font-size:13px;opacity:0.9">'
        "Sell these loss-making stocks to offset gains"
        "</div></div>"
        '<div style="padding:16px">'
        '<table style="width:100%;border-collapse:collapse">'
        '<tr style="border-bottom:2px solid #eee">'
        f'<th style="{th};text-align:left">STOCK</th>'
        f'<th style="{th};text-align:right">LOSS</th>'
        f'<th style="{th};text-align:right">TAX SAVED</th>'
        f'<th style="{th};text-align:center">TYPE</th>'
        f"</tr>{rows}</table>"
        f"{ai_html}"
        '<div style="margin-top:12px;padding:10px;'
        "background:#fef3c7;border-radius:6px;"
        'font-size:12px;color:#92400e">'
        "⚠️ Wait 30 days before rebuying to avoid wash sale."
        "</div></div></div>"
    )


def _build_telegram(opps, total_saved, ai):
    lines = [
        "💰 *Tax Harvesting Alert*",
        f"Potential savings: *₹{total_saved:,.0f}*",
        "",
    ]
    for o in opps:
        lines.append(f"  📉 {o['symbol']}: loss ₹{o['loss']:,.0f}" f" → save ₹{o['tax_saved']:,.0f} ({o['type']})")
    if ai:
        lines += ["", f"🤖 _{ai}_"]
    lines.append("\n⚠️ _Wait 30 days before rebuying (wash sale)_")
    return "\n".join(lines)
