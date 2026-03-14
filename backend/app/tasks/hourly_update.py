from datetime import datetime

import httpx
import pytz

from ..core.config import settings
from ..models.documents import Holding, User
from ..services.cache import cache_get, cache_set, get_redis
from ..services.market.price_service import get_bulk_prices
from ..services.notification.service import send_email
from ..utils.logger import logger

IST = pytz.timezone("Asia/Kolkata")


async def send_hourly_update():
    redis = await get_redis()
    if redis:
        acquired = await redis.set("lock:hourly_update", "1", ex=55, nx=True)
        if not acquired:
            return

    users = await User.find(User.settings.hourly_alerts == True).to_list()  # noqa: E712
    time_str = datetime.now(IST).strftime("%-I:%M %p")

    for user in users:
        try:
            await _send_user_update(user, time_str)
        except Exception as e:
            logger.error(f"Hourly update failed for {user.email}: {e}")


async def _get_signals_for_user(user_id: str, holdings: list) -> dict:
    """Get cached signals or generate fresh ones."""
    ck = f"hourly_signals:{user_id}"
    cached = await cache_get(ck)
    if cached:
        return cached

    try:
        from ..services.signals import SignalEngine
        from ..tasks.portfolio_advisor import get_bulk_stock_data

        equity = [h for h in holdings if h.holding_type != "MF"]
        symbols = [h.symbol for h in equity]
        stock_data = await get_bulk_stock_data(symbols)
        engine = SignalEngine()
        result = await engine.analyze_portfolio(holdings, stock_data)
        # Map signals by symbol
        sig_map = {s["symbol"]: s for s in result.get("signals", [])}
        await cache_set(ck, sig_map, ttl=1800)  # cache 30 min
        return sig_map
    except Exception as e:
        logger.warning(f"Signal generation failed for hourly: {e}")
        return {}


async def _send_user_update(user, time_str: str):
    holdings = await Holding.find(Holding.user_id == user.id).to_list()
    if not holdings:
        return

    equity = [h for h in holdings if h.holding_type != "MF"]
    if not equity:
        return

    prices = await get_bulk_prices([h.symbol for h in equity])
    signals = await _get_signals_for_user(str(user.id), holdings)

    stocks = []
    total_inv = 0
    current_val = 0
    day_pnl = 0

    for h in equity:
        p = prices.get(h.symbol, {})
        curr = p.get("current_price") or h.avg_price
        prev = p.get("previous_close") or curr
        inv = h.quantity * h.avg_price
        val = h.quantity * curr
        d_chg = (curr - prev) * h.quantity
        d_pct = p.get("day_change_pct", 0)
        pnl = val - inv
        pnl_pct = (pnl / inv * 100) if inv else 0

        total_inv += inv
        current_val += val
        day_pnl += d_chg

        sig = signals.get(h.symbol, {})
        stocks.append(
            {
                "symbol": h.symbol,
                "curr": curr,
                "day_pct": d_pct,
                "pnl_pct": pnl_pct,
                "val": val,
                "action": sig.get("action", "—"),
                "confidence": sig.get("confidence", ""),
                "reason": (sig.get("reasons") or [""])[0],
            }
        )

    total_pnl = current_val - total_inv
    total_pnl_pct = (total_pnl / total_inv * 100) if total_inv else 0
    day_pnl_pct = (day_pnl / (current_val - day_pnl) * 100) if (current_val - day_pnl) else 0

    stocks.sort(key=lambda x: abs(x["day_pct"]), reverse=True)

    ai_insight = await _get_ai_insight(stocks, day_pnl, day_pnl_pct, current_val)

    if user.email:
        html = _build_email(time_str, current_val, day_pnl, day_pnl_pct, total_pnl, total_pnl_pct, stocks, ai_insight)
        await send_email(user.email, f"StockPilot {time_str} Update", html)

    if user.telegram_chat_id and settings.telegram_bot_token:
        msg = _build_telegram(time_str, current_val, day_pnl, day_pnl_pct, stocks, ai_insight)
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                    json={"chat_id": user.telegram_chat_id, "text": msg, "parse_mode": "Markdown"},
                )
        except httpx.HTTPError as e:
            logger.warning(f"Hourly telegram error: {e}")


async def _get_ai_insight(stocks: list, day_pnl: float, day_pnl_pct: float, portfolio_val: float) -> str:
    if not settings.groq_api_key or not stocks:
        return ""
    try:
        from groq import Groq

        stock_str = ", ".join(f"{s['symbol']}({s['day_pct']:+.1f}%, {s['action']})" for s in stocks[:8])
        client = Groq(api_key=settings.groq_api_key)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a concise Indian stock market analyst. "
                        "Write 2-3 sentences (max 50 words total) analyzing this portfolio. "
                        "Reference the signal actions (BUY/SELL/HOLD/EXIT). "
                        "Mention specific stocks. No disclaimers."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Portfolio ₹{portfolio_val:,.0f}, today {day_pnl_pct:+.1f}% (₹{day_pnl:+,.0f}). "
                        f"Holdings: {stock_str}"
                    ),
                },
            ],
            temperature=0.4,
            max_completion_tokens=100,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"Groq hourly insight error: {e}")
        return ""


# ── Formatting helpers ──────────────────────────────────────────────

_ACTION_COLORS = {
    "STRONG BUY": "#10b981",
    "BUY MORE": "#10b981",
    "ADD": "#10b981",
    "HOLD": "#888",
    "WAIT": "#8b5cf6",
    "TRIM": "#f59e0b",
    "PARTIAL SELL": "#f59e0b",
    "EXIT": "#ef4444",
    "AVOID": "#ef4444",
}

_ACTION_EMOJI = {
    "STRONG BUY": "🟢",
    "BUY MORE": "🟢",
    "ADD": "🟢",
    "HOLD": "⚪",
    "WAIT": "🟣",
    "TRIM": "🟡",
    "PARTIAL SELL": "🟡",
    "EXIT": "🔴",
    "AVOID": "🔴",
}


def _color(val: float) -> str:
    return "#10b981" if val > 0 else "#ef4444" if val < 0 else "#888"


def _arrow(val: float) -> str:
    return "▲" if val > 0 else "▼" if val < 0 else "–"


def _build_email(
    time_str: str,
    current_val: float,
    day_pnl: float,
    day_pnl_pct: float,
    total_pnl: float,
    total_pnl_pct: float,
    stocks: list,
    ai_insight: str,
) -> str:
    rows = ""
    for s in stocks:
        dc = _color(s["day_pct"])
        pc = _color(s["pnl_pct"])
        ac = _ACTION_COLORS.get(s["action"], "#888")
        reason_html = ""
        if s["reason"]:
            reason_html = (
                '<div style="font-size:11px;color:#666;' f'margin-top:2px;line-height:1.3">💡 {s["reason"]}</div>'
            )
        td = "padding:7px 8px;vertical-align:top"
        day_val = f"{_arrow(s['day_pct'])} {s['day_pct']:+.1f}%"
        badge = (
            f'<span style="background:{ac}18;color:{ac};'
            "padding:2px 8px;border-radius:4px;"
            f'font-size:11px;font-weight:700">{s["action"]}</span>'
        )
        rows += (
            '<tr style="border-bottom:1px solid #f0f0f0">'
            f'<td style="{td}">'
            f'<div style="font-weight:600;font-size:13px">'
            f'{s["symbol"]}</div>{reason_html}</td>'
            f'<td style="{td};text-align:right;font-size:13px">'
            f'₹{s["curr"]:,.2f}</td>'
            f'<td style="{td};text-align:right;color:{dc};'
            f'font-weight:600;font-size:13px">{day_val}</td>'
            f'<td style="{td};text-align:right;color:{pc};'
            f'font-size:13px">{s["pnl_pct"]:+.1f}%</td>'
            f'<td style="{td};text-align:center">{badge}</td>'
            "</tr>"
        )

    ai_block = ""
    if ai_insight:
        ai_block = (
            '<div style="background:#f0f0ff;border-left:3px solid'
            " #6366f1;padding:10px 14px;margin:16px 0;"
            'border-radius:0 6px 6px 0">'
            '<div style="font-size:12px;color:#6366f1;'
            'font-weight:600;margin-bottom:4px">🤖 AI Insight</div>'
            '<div style="font-size:13px;color:#333;'
            f'line-height:1.4">{ai_insight}</div></div>'
        )

    day_c = "#a7f3d0" if day_pnl >= 0 else "#fca5a5"
    tot_c = "#a7f3d0" if total_pnl >= 0 else "#fca5a5"

    hdr_style = (
        "font-family:-apple-system,BlinkMacSystemFont,"
        "'Segoe UI',Roboto,sans-serif;max-width:560px;"
        "margin:0 auto;background:#fff;"
        "border-radius:8px;overflow:hidden"
    )
    grad = "background:linear-gradient(135deg,#6366f1,#8b5cf6);" "padding:16px 20px;color:#fff"
    th = "padding:6px 8px;font-size:11px;color:#888;font-weight:600"

    return (
        f'<div style="{hdr_style}">'
        f'<div style="{grad}">'
        f'<div style="font-size:12px;opacity:0.85">'
        f"⏰ {time_str} Update</div>"
        '<div style="font-size:28px;font-weight:700;'
        f'margin:4px 0">₹{current_val:,.0f}</div>'
        '<div style="font-size:13px;margin-top:2px">'
        f'Today: <b style="color:{day_c}">'
        f"₹{day_pnl:+,.0f} ({day_pnl_pct:+.1f}%)</b>"
        " &nbsp;·&nbsp; "
        f'Overall: <b style="color:{tot_c}">'
        f"₹{total_pnl:+,.0f} ({total_pnl_pct:+.1f}%)</b>"
        "</div></div>"
        '<div style="padding:16px 16px">'
        '<div style="font-size:11px;text-transform:uppercase;'
        "color:#888;font-weight:600;margin-bottom:8px;"
        'letter-spacing:0.5px">📊 Portfolio Analysis</div>'
        '<table style="width:100%;border-collapse:collapse">'
        '<tr style="border-bottom:2px solid #eee">'
        f'<th style="{th};text-align:left">STOCK</th>'
        f'<th style="{th};text-align:right">PRICE</th>'
        f'<th style="{th};text-align:right">TODAY</th>'
        f'<th style="{th};text-align:right">P&L</th>'
        f'<th style="{th};text-align:center">SIGNAL</th>'
        f"</tr>{rows}</table>"
        f"{ai_block}</div></div>"
    )


def _build_telegram(
    time_str: str,
    current_val: float,
    day_pnl: float,
    day_pnl_pct: float,
    stocks: list,
    ai_insight: str,
) -> str:
    emoji = "🟢" if day_pnl >= 0 else "🔴"
    lines = [
        f"⏰ *{time_str} Update*",
        f"💰 ₹{current_val:,.0f}  {emoji} {day_pnl_pct:+.1f}%",
        "",
        "📊 *Portfolio Analysis*",
    ]
    for s in stocks:
        ae = _ACTION_EMOJI.get(s["action"], "⚪")
        sym = s["symbol"][:10].ljust(10)
        act = s["action"][:6].ljust(6)
        lines.append(f"{ae} `{sym}` {s['day_pct']:+.1f}% │ *{act}*")
        if s["reason"]:
            lines.append(f"     ↳ _{s['reason']}_")

    if ai_insight:
        lines += ["", f"🤖 _{ai_insight}_"]

    return "\n".join(lines)
