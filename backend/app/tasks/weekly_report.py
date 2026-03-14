"""Weekly AI Report — sent every Saturday 10 AM IST."""

import httpx
import pytz

from ..core.config import settings
from ..models.documents import Holding, User
from ..services.cache import get_redis
from ..services.market.price_service import get_bulk_prices
from ..services.notification.service import send_email
from ..utils.logger import logger

IST = pytz.timezone("Asia/Kolkata")


async def send_weekly_report():
    redis = await get_redis()
    if redis:
        acquired = await redis.set("lock:weekly_report", "1", ex=300, nx=True)
        if not acquired:
            return

    users = await User.find(User.settings.daily_digest == True).to_list()  # noqa: E712

    for user in users:
        try:
            await _send_report(user)
        except Exception as e:
            logger.error(f"Weekly report failed for {user.email}: {e}")


async def _get_nifty_week_change() -> float:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                "https://query1.finance.yahoo.com/v8/finance/chart/" "%5ENSEI?interval=1d&range=10d",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if resp.status_code == 200:
                closes = [c for c in resp.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"] if c]
                if len(closes) >= 6:
                    return round((closes[-1] - closes[-6]) / closes[-6] * 100, 2)
    except Exception:
        pass
    return 0.0


async def _send_report(user):
    holdings = await Holding.find(Holding.user_id == user.id).to_list()
    equity = [h for h in holdings if h.holding_type != "MF"]
    if not equity:
        return

    prices = await get_bulk_prices([h.symbol for h in equity])
    nifty_pct = await _get_nifty_week_change()

    stocks = []
    total_inv = 0
    current_val = 0

    for h in equity:
        p = prices.get(h.symbol, {})
        curr = p.get("current_price") or h.avg_price
        inv = h.quantity * h.avg_price
        val = h.quantity * curr
        pnl_pct = ((val - inv) / inv * 100) if inv else 0
        day_pct = p.get("day_change_pct", 0)
        total_inv += inv
        current_val += val
        stocks.append(
            {
                "symbol": h.symbol,
                "pnl_pct": pnl_pct,
                "day_pct": day_pct,
                "val": val,
            }
        )

    total_pnl = current_val - total_inv
    total_pnl_pct = (total_pnl / total_inv * 100) if total_inv else 0

    stocks.sort(key=lambda x: x["pnl_pct"], reverse=True)
    best = stocks[:3]
    worst = stocks[-3:]

    # Tax harvesting opportunities
    losses = [s for s in stocks if s["pnl_pct"] < -5]
    harvest_note = ""
    if losses:
        names = ", ".join(s["symbol"] for s in losses[:3])
        harvest_note = f"Tax harvesting: {names} in loss — consider booking before March 31."

    # AI summary
    ai_summary = await _get_ai_summary(stocks, total_pnl_pct, nifty_pct, current_val, harvest_note)

    if user.email:
        html = _build_email(
            current_val,
            total_pnl,
            total_pnl_pct,
            nifty_pct,
            best,
            worst,
            harvest_note,
            ai_summary,
        )
        await send_email(user.email, "StockPilot Weekly Report", html)

    if user.telegram_chat_id and settings.telegram_bot_token:
        msg = _build_telegram(
            current_val,
            total_pnl_pct,
            nifty_pct,
            best,
            worst,
            harvest_note,
            ai_summary,
        )
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
            logger.warning(f"Weekly report telegram error: {e}")


async def _get_ai_summary(stocks, pnl_pct, nifty_pct, val, harvest):
    if not settings.groq_api_key:
        return ""
    try:
        from groq import Groq

        top = ", ".join(f"{s['symbol']}({s['pnl_pct']:+.1f}%)" for s in stocks[:6])
        client = Groq(api_key=settings.groq_api_key)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a concise Indian stock market analyst. "
                        "Write a 4-5 sentence weekly portfolio review "
                        "(max 100 words). Cover: week performance vs "
                        "Nifty, best/worst stocks, any action items. "
                        "Be specific. No disclaimers."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Portfolio ₹{val:,.0f}, overall {pnl_pct:+.1f}%. "
                        f"Nifty week: {nifty_pct:+.1f}%. "
                        f"Holdings: {top}. {harvest}"
                    ),
                },
            ],
            temperature=0.4,
            max_completion_tokens=200,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"Groq weekly error: {e}")
        return ""


def _c(v):
    return "#10b981" if v > 0 else "#ef4444" if v < 0 else "#888"


def _build_email(val, pnl, pnl_pct, nifty, best, worst, harvest, ai):
    def _rows(items, label):
        rows = ""
        for s in items:
            c = _c(s["pnl_pct"])
            rows += (
                f'<tr><td style="padding:4px 8px;font-weight:600">'
                f'{s["symbol"]}</td>'
                f'<td style="padding:4px 8px;text-align:right;'
                f'color:{c};font-weight:600">'
                f'{s["pnl_pct"]:+.1f}%</td></tr>'
            )
        return rows

    harvest_html = ""
    if harvest:
        harvest_html = (
            '<div style="background:#fef3c7;border-left:3px solid'
            " #f59e0b;padding:10px 14px;margin:12px 0;"
            'border-radius:0 6px 6px 0">'
            '<div style="font-size:12px;color:#92400e;'
            f'font-weight:600">💰 Tax Tip</div>'
            f'<div style="font-size:13px;color:#78350f">'
            f"{harvest}</div></div>"
        )

    ai_html = ""
    if ai:
        ai_html = (
            '<div style="background:#f0f0ff;border-left:3px solid'
            " #6366f1;padding:10px 14px;margin:12px 0;"
            'border-radius:0 6px 6px 0">'
            '<div style="font-size:12px;color:#6366f1;'
            'font-weight:600;margin-bottom:4px">'
            "🤖 AI Weekly Review</div>"
            '<div style="font-size:13px;color:#333;'
            f'line-height:1.4">{ai}</div></div>'
        )

    beat = pnl_pct > nifty
    bc = "#10b981" if beat else "#ef4444"
    diff = abs(pnl_pct - nifty)
    bl = "Outperformed" if beat else "Underperformed"

    hdr = (
        "font-family:-apple-system,BlinkMacSystemFont,"
        "'Segoe UI',Roboto,sans-serif;max-width:520px;"
        "margin:0 auto;background:#fff;"
        "border-radius:8px;overflow:hidden"
    )
    grad = "background:linear-gradient(135deg,#7c3aed,#6366f1);" "padding:18px 20px;color:#fff"

    return (
        f'<div style="{hdr}">'
        f'<div style="{grad}">'
        '<div style="font-size:12px;opacity:0.85">'
        "📅 Weekly Report</div>"
        '<div style="font-size:28px;font-weight:700;'
        f'margin:4px 0">₹{val:,.0f}</div>'
        '<div style="font-size:13px">'
        f'Overall: <b style="color:{_c(pnl_pct)}">'
        f"₹{pnl:+,.0f} ({pnl_pct:+.1f}%)</b></div>"
        '<div style="font-size:12px;margin-top:4px;opacity:0.9">'
        f"Nifty week: {nifty:+.1f}% · "
        f'<span style="color:{bc}">{bl} by {diff:.1f}%</span>'
        "</div></div>"
        '<div style="padding:16px">'
        '<div style="display:flex;gap:16px">'
        '<div style="flex:1">'
        '<div style="font-size:11px;color:#888;'
        'font-weight:600;margin-bottom:6px">🏆 BEST</div>'
        '<table style="width:100%">'
        f"{_rows(best, 'best')}</table></div>"
        '<div style="flex:1">'
        '<div style="font-size:11px;color:#888;'
        'font-weight:600;margin-bottom:6px">📉 WORST</div>'
        '<table style="width:100%">'
        f"{_rows(worst, 'worst')}</table></div></div>"
        f"{harvest_html}{ai_html}</div></div>"
    )


def _build_telegram(val, pnl_pct, nifty, best, worst, harvest, ai):
    beat = "✅ Beat" if pnl_pct > nifty else "❌ Trailed"
    lines = [
        "📅 *Weekly Report*",
        f"💰 ₹{val:,.0f}  ({pnl_pct:+.1f}%)",
        f"📉 Nifty: {nifty:+.1f}%  {beat}",
        "",
        "🏆 *Best*",
    ]
    for s in best:
        lines.append(f"  {s['symbol']} {s['pnl_pct']:+.1f}%")
    lines.append("\n📉 *Worst*")
    for s in worst:
        lines.append(f"  {s['symbol']} {s['pnl_pct']:+.1f}%")
    if harvest:
        lines += ["", f"💰 _{harvest}_"]
    if ai:
        lines += ["", f"🤖 _{ai}_"]
    return "\n".join(lines)
