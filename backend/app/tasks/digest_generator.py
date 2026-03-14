from datetime import datetime, timezone

import httpx
import pytz

from ..core.config import settings
from ..models.documents import DailyDigest, Holding, User
from ..services.cache import cache_get, cache_set, get_redis
from ..services.market.price_service import get_bulk_prices
from ..services.notification.service import send_email
from ..utils.logger import logger

IST = pytz.timezone("Asia/Kolkata")


async def generate_daily_digest():
    redis = await get_redis()
    if redis:
        acquired = await redis.set("lock:daily_digest", "1", ex=55, nx=True)
        if not acquired:
            return

    users = await User.find(User.settings.daily_digest == True).to_list()  # noqa: E712

    for user in users:
        try:
            await _generate_for_user(user)
        except Exception as e:
            logger.error(f"Daily digest failed for {user.email}: {e}")


async def _get_nifty_day_change() -> float:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                "https://query1.finance.yahoo.com/v8/finance/chart/" "%5ENSEI?interval=1d&range=5d",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if resp.status_code == 200:
                closes = [c for c in resp.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"] if c]
                if len(closes) >= 2:
                    return round((closes[-1] - closes[-2]) / closes[-2] * 100, 2)
    except Exception:
        pass
    return 0.0


async def _get_signals(user_id: str, holdings: list) -> dict:
    ck = f"daily_signals:{user_id}"
    cached = await cache_get(ck)
    if cached:
        return cached
    try:
        from ..services.signals import SignalEngine
        from ..tasks.portfolio_advisor import get_bulk_stock_data

        equity = [h for h in holdings if h.holding_type != "MF"]
        stock_data = await get_bulk_stock_data([h.symbol for h in equity])
        engine = SignalEngine()
        result = await engine.analyze_portfolio(holdings, stock_data)
        sig_map = {s["symbol"]: s for s in result.get("signals", [])}
        await cache_set(ck, sig_map, ttl=3600)
        return sig_map
    except Exception as e:
        logger.warning(f"Signal gen failed for digest: {e}")
        return {}


async def _get_ai_digest(
    stocks: list,
    day_pnl: float,
    day_pnl_pct: float,
    nifty_pct: float,
    portfolio_val: float,
) -> str:
    if not settings.groq_api_key or not stocks:
        return ""
    try:
        from groq import Groq

        stock_str = ", ".join(
            f"{s['symbol']}(day:{s['day_pct']:+.1f}%," f" P&L:{s['pnl_pct']:+.1f}%, {s['action']})" for s in stocks[:8]
        )
        client = Groq(api_key=settings.groq_api_key)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a concise Indian stock market analyst. "
                        "Write a 3-4 sentence end-of-day portfolio summary "
                        "(max 80 words). Cover: today's performance vs "
                        "Nifty, key movers, any actionable signals "
                        "(BUY/SELL/EXIT). Be specific. No disclaimers."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Portfolio ₹{portfolio_val:,.0f}, "
                        f"today {day_pnl_pct:+.1f}% "
                        f"(₹{day_pnl:+,.0f}). "
                        f"Nifty: {nifty_pct:+.1f}%. "
                        f"Holdings: {stock_str}"
                    ),
                },
            ],
            temperature=0.4,
            max_completion_tokens=150,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"Groq digest error: {e}")
        return ""


async def _generate_for_user(user):
    holdings = await Holding.find(Holding.user_id == user.id).to_list()
    if not holdings:
        return

    equity = [h for h in holdings if h.holding_type != "MF"]
    if not equity:
        return

    prices = await get_bulk_prices([h.symbol for h in equity])
    signals = await _get_signals(str(user.id), holdings)
    nifty_pct = await _get_nifty_day_change()

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
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "val": val,
                "action": sig.get("action", "—"),
                "reason": (sig.get("reasons") or [""])[0],
            }
        )

    total_pnl = current_val - total_inv
    total_pnl_pct = (total_pnl / total_inv * 100) if total_inv else 0
    day_pnl_pct = (day_pnl / (current_val - day_pnl) * 100) if (current_val - day_pnl) else 0

    stocks.sort(key=lambda x: x["day_pct"], reverse=True)

    ai_insight = await _get_ai_digest(stocks, day_pnl, day_pnl_pct, nifty_pct, current_val)

    # Save digest to DB
    sorted_perf = sorted(stocks, key=lambda x: x["day_pct"], reverse=True)
    digest = DailyDigest(
        user_id=user.id,
        date=datetime.now(timezone.utc).date().isoformat(),
        portfolio_value=round(current_val, 0),
        day_pnl=round(day_pnl, 0),
        day_pnl_pct=round(day_pnl_pct, 1),
        total_pnl=round(total_pnl, 0),
        total_pnl_pct=round(total_pnl_pct, 1),
        top_gainer=sorted_perf[0] if sorted_perf else None,
        top_loser=sorted_perf[-1] if sorted_perf else None,
        sent_at=datetime.now(timezone.utc),
    )
    await digest.insert()

    # Send email
    if user.email:
        html = _build_email(
            current_val,
            day_pnl,
            day_pnl_pct,
            total_pnl,
            total_pnl_pct,
            nifty_pct,
            stocks,
            ai_insight,
        )
        await send_email(user.email, "StockPilot Daily Digest", html)

    # Send Telegram
    if user.telegram_chat_id and settings.telegram_bot_token:
        msg = _build_telegram(
            current_val,
            day_pnl,
            day_pnl_pct,
            nifty_pct,
            stocks,
            ai_insight,
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
            logger.warning(f"Digest telegram error: {e}")


# ── Formatting ──────────────────────────────────────────────

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


def _c(val: float) -> str:
    return "#10b981" if val > 0 else "#ef4444" if val < 0 else "#888"


def _arrow(val: float) -> str:
    return "▲" if val > 0 else "▼" if val < 0 else "–"


def _build_email(
    current_val,
    day_pnl,
    day_pnl_pct,
    total_pnl,
    total_pnl_pct,
    nifty_pct,
    stocks,
    ai_insight,
):
    # Benchmark comparison
    beat = day_pnl_pct > nifty_pct
    bench_color = "#10b981" if beat else "#ef4444"
    diff = day_pnl_pct - nifty_pct
    bench_text = (
        f'<span style="color:{bench_color};font-weight:600">'
        f'{"Outperformed" if beat else "Underperformed"} Nifty by '
        f"{abs(diff):.1f}%</span>"
    )

    # Stock rows
    rows = ""
    for s in stocks:
        dc = _c(s["day_pct"])
        pc = _c(s["pnl_pct"])
        ac = _ACTION_COLORS.get(s["action"], "#888")
        reason_html = ""
        if s["reason"]:
            reason_html = '<div style="font-size:11px;color:#666;' f'margin-top:2px">💡 {s["reason"]}</div>'
        td = "padding:7px 8px;vertical-align:top"
        day_val = f"{_arrow(s['day_pct'])} {s['day_pct']:+.1f}%"
        badge = (
            f'<span style="background:{ac}18;color:{ac};'
            "padding:2px 8px;border-radius:4px;"
            f'font-size:11px;font-weight:700">'
            f'{s["action"]}</span>'
        )
        rows += (
            '<tr style="border-bottom:1px solid #f0f0f0">'
            f'<td style="{td}">'
            f'<div style="font-weight:600;font-size:13px">'
            f'{s["symbol"]}</div>{reason_html}</td>'
            f'<td style="{td};text-align:right;'
            f'font-size:13px">₹{s["curr"]:,.2f}</td>'
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
            'font-weight:600;margin-bottom:4px">'
            "🤖 AI Daily Summary</div>"
            '<div style="font-size:13px;color:#333;'
            f'line-height:1.4">{ai_insight}</div></div>'
        )

    day_c = "#a7f3d0" if day_pnl >= 0 else "#fca5a5"
    tot_c = "#a7f3d0" if total_pnl >= 0 else "#fca5a5"
    nifty_c = "#a7f3d0" if nifty_pct >= 0 else "#fca5a5"

    hdr = (
        "font-family:-apple-system,BlinkMacSystemFont,"
        "'Segoe UI',Roboto,sans-serif;max-width:560px;"
        "margin:0 auto;background:#fff;"
        "border-radius:8px;overflow:hidden"
    )
    grad = "background:linear-gradient(135deg,#4f46e5,#7c3aed);" "padding:18px 20px;color:#fff"
    th = "padding:6px 8px;font-size:11px;" "color:#888;font-weight:600"

    return (
        f'<div style="{hdr}">'
        f'<div style="{grad}">'
        '<div style="font-size:12px;opacity:0.85">'
        "📊 Daily Digest</div>"
        '<div style="font-size:28px;font-weight:700;'
        f'margin:4px 0">₹{current_val:,.0f}</div>'
        '<div style="font-size:13px;margin-top:2px">'
        f'Today: <b style="color:{day_c}">'
        f"₹{day_pnl:+,.0f} ({day_pnl_pct:+.1f}%)</b>"
        " &nbsp;·&nbsp; "
        f'Overall: <b style="color:{tot_c}">'
        f"₹{total_pnl:+,.0f} ({total_pnl_pct:+.1f}%)</b>"
        "</div>"
        '<div style="font-size:12px;margin-top:6px;opacity:0.9">'
        f'Nifty 50: <b style="color:{nifty_c}">'
        f"{nifty_pct:+.1f}%</b>"
        f" &nbsp;·&nbsp; {bench_text}"
        "</div></div>"
        '<div style="padding:16px">'
        '<div style="font-size:11px;text-transform:uppercase;'
        "color:#888;font-weight:600;margin-bottom:8px;"
        'letter-spacing:0.5px">'
        "📈 Portfolio Breakdown</div>"
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
    current_val,
    day_pnl,
    day_pnl_pct,
    nifty_pct,
    stocks,
    ai_insight,
):
    emoji = "🟢" if day_pnl >= 0 else "🔴"
    beat = day_pnl_pct > nifty_pct
    bench = "✅ Beat Nifty" if beat else "❌ Trailed Nifty"
    diff = abs(day_pnl_pct - nifty_pct)

    lines = [
        "📊 *Daily Digest*",
        f"💰 ₹{current_val:,.0f}  {emoji} {day_pnl_pct:+.1f}%",
        f"📉 Nifty: {nifty_pct:+.1f}%  {bench} by {diff:.1f}%",
        "",
        "📈 *Portfolio Breakdown*",
    ]
    for s in stocks:
        ae = _ACTION_EMOJI.get(s["action"], "⚪")
        sym = s["symbol"][:10].ljust(10)
        lines.append(f"{ae} `{sym}` {s['day_pct']:+.1f}% │ *{s['action']}*")
        if s["reason"]:
            lines.append(f"     ↳ _{s['reason']}_")

    if ai_insight:
        lines += ["", f"🤖 _{ai_insight}_"]

    return "\n".join(lines)
