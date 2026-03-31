import logging
import re
from typing import List, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from groq import Groq
from pydantic import BaseModel

from ....core.config import settings
from ....core.response_handler import StandardResponse
from ....core.security import get_current_user
from ....models.documents import ChatMessage, ChatSession, Holding

logger = logging.getLogger("stockpilot")

router = APIRouter()

client = Groq(api_key=settings.groq_api_key) if settings.groq_api_key else None

SYSTEM_PROMPT = (
    "You are StockPilot AI — a friendly, expert Indian stock market "
    "portfolio assistant built into the StockPilot app.\n\n"
    "Style:\n"
    "- Be conversational and warm, not robotic. Use emojis freely "
    "(📊 📈 📉 💡 ⚠️ 🎯 💰 🔥 ✅ ❌ 🏦 🧠) to make responses engaging.\n"
    "- Format currency in Indian style with ₹ symbol (e.g., ₹1,21,992).\n"
    "- Use markdown: **bold** for emphasis, bullet points with - for lists.\n"
    "- Keep responses focused but thorough (5-15 lines).\n\n"
    "Rules:\n"
    "- For portfolio-specific questions, use the data below. Never fabricate holdings.\n"
    "- For general finance/investing questions, use your knowledge to explain.\n"
    "- When user asks why a stock is falling/rising, use RECENT NEWS section.\n"
    "- For external companies/stocks, use WEB SEARCH RESULTS if available.\n"
    "- For comparison queries, compare the FUNDAMENTALS data provided.\n"
    "- For what-if queries, use the SIMULATION data provided.\n"
    "- If SENTIMENT data is available, mention the overall sentiment.\n"
    "- If no relevant data, say 'I don't have specific information on that'.\n"
    "- When suggesting action, explain WHY briefly.\n"
    "- Reference StockPilot features when relevant "
    "(Tax Center, MF Overlap Analyzer, Signals, MF Health Check).\n"
    "- Never give specific price targets. Use 'consider', 'you might want to'.\n"
    "- Mention STCG (20%) for <1yr and LTCG (12.5% above ₹1.25L) for >1yr.\n"
    "- For MFs, comment on diversification across fund categories.\n"
    "- End with a relevant follow-up question to keep conversation going.\n"
)

SUPPORTED_LANGUAGES = {
    "en": "",
    "hi": "Respond in Hindi (Devanagari script). ",
    "hinglish": "Respond in Hinglish (Hindi written in English). ",
    "ta": "Respond in Tamil. ",
    "te": "Respond in Telugu. ",
    "bn": "Respond in Bengali. ",
    "mr": "Respond in Marathi. ",
}


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []
    session_id: Optional[str] = None
    language: Optional[str] = "en"


async def fetch_news_for_holdings(symbols: List[str], limit: int = 5) -> str:
    """Fetch recent news for top holdings via shared news service."""
    import asyncio

    import httpx

    from ....services.news import fetch_stock_news

    top_symbols = symbols[:limit]
    async with httpx.AsyncClient(timeout=10, headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True) as client:
        results = await asyncio.gather(*[fetch_stock_news(s, client=client) for s in top_symbols])

    news_lines = []
    for sym, news in zip(top_symbols, results):
        if news:
            titles = [n["title"] for n in news[:3]]
            news_lines.append(f"{sym}: {' | '.join(titles)}")

    return "\n".join(news_lines) if news_lines else ""


async def build_context(user_id: str) -> str:
    from datetime import datetime, timedelta

    uid = PydanticObjectId(user_id)
    holdings = await Holding.find(Holding.user_id == uid).to_list()

    if not holdings:
        return "User has no holdings."

    from ....core.constants import SECTOR_MAP
    from ....services.market.price_service import get_bulk_prices

    symbols = [h.symbol for h in holdings if h.holding_type != "MF"]
    live_prices = await get_bulk_prices(symbols) if symbols else {}

    lines = []
    total_invested = total_current = 0
    sectors = {}
    stcg_loss = ltcg_loss = stcg_gain = ltcg_gain = 0
    now = datetime.now()
    one_year_ago = now - timedelta(days=365)

    for h in holdings:
        p = live_prices.get(h.symbol, {})
        curr_price = p.get("current_price") or h.current_price or h.avg_price
        current = curr_price * h.quantity
        invested = h.avg_price * h.quantity
        pnl = current - invested
        pnl_pct = (pnl / invested * 100) if invested else 0
        total_invested += invested
        total_current += current

        sec = SECTOR_MAP.get(h.symbol, h.sector or "Others")
        sectors[sec] = sectors.get(sec, 0) + current

        # First buy date and holding period
        first_buy = None
        for t in h.transactions:
            if t.type == "BUY":
                try:
                    td = datetime.strptime(t.date, "%Y-%m-%d")
                    if first_buy is None or td < first_buy:
                        first_buy = td
                except ValueError:
                    pass

        is_lt = first_buy and first_buy < one_year_ago
        holding_days = (now - first_buy).days if first_buy else 0
        tax_type = "LTCG" if is_lt else "STCG"

        if pnl > 0:
            if is_lt:
                ltcg_gain += pnl
            else:
                stcg_gain += pnl
        else:
            if is_lt:
                ltcg_loss += pnl
            else:
                stcg_loss += pnl

        period_str = f"{holding_days}d" if holding_days else "?"
        buy_str = first_buy.strftime("%Y-%m-%d") if first_buy else "?"
        lines.append(
            f"{h.symbol} | {h.holding_type} | Qty:{h.quantity:.2f} | "
            f"Avg:₹{h.avg_price:.1f} | CMP:₹{curr_price:.1f} | "
            f"P&L:₹{pnl:,.0f} ({pnl_pct:+.1f}%) | {tax_type} | "
            f"Held:{period_str} | Since:{buy_str} | Sector:{sec}"
        )

    total_pnl = total_current - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested else 0

    sector_lines = sorted(sectors.items(), key=lambda x: -x[1])
    sector_str = ", ".join(f"{s}: {v / total_current * 100:.1f}%" for s, v in sector_lines[:8] if s != "Others")

    # Fetch news for top 5 stock holdings (by value)
    stock_symbols = [h.symbol for h in holdings if h.holding_type != "MF"]
    news_context = await fetch_news_for_holdings(stock_symbols[:5]) if stock_symbols else ""

    context = (
        f"PORTFOLIO SUMMARY: {len(holdings)} holdings | "
        f"Invested: ₹{total_invested:,.0f} | Current: ₹{total_current:,.0f} | "
        f"P&L: ₹{total_pnl:,.0f} ({total_pnl_pct:+.1f}%)\n"
        f"SECTORS: {sector_str or 'Not available for most holdings'}\n"
        f"TAX: STCG gains: ₹{stcg_gain:,.0f} | STCG losses: ₹{abs(stcg_loss):,.0f} | "
        f"LTCG gains: ₹{ltcg_gain:,.0f} | LTCG losses: ₹{abs(ltcg_loss):,.0f}\n"
        f"DATE: {now.strftime('%d %b %Y, %A')}\n\n"
        f"HOLDINGS:\n" + "\n".join(lines)
    )

    if news_context:
        context += f"\n\nRECENT NEWS:\n{news_context}"

    return context


async def get_stock_fundamentals(symbol: str) -> str:
    """Fetch stock fundamentals from Screener.in."""
    from ....services.analytics.service import get_screener_fundamentals

    try:
        data = await get_screener_fundamentals(symbol.replace("?", "").strip())
        if not data:
            return ""
        return (
            f"FUNDAMENTALS for {symbol}:\n"
            f"Price: ₹{data.get('current_price', 'N/A')} | "
            f"PE: {data.get('pe', 'N/A')} | PB: {data.get('pb', 'N/A')} | "
            f"ROE: {data.get('roe', 'N/A')}% | ROCE: {data.get('roce', 'N/A')}%\n"
            f"Market Cap: ₹{data.get('market_cap', 'N/A')} Cr | "
            f"Div Yield: {data.get('dividend_yield', 'N/A')}% | "
            f"52W High/Low: ₹{data.get('high_52w', 'N/A')}/₹{data.get('low_52w', 'N/A')}"
        )
    except Exception:
        return ""


async def get_live_price(symbol: str) -> str:
    """Fetch live price for a stock."""
    from ....services.market.price_service import get_price

    try:
        data = await get_price(symbol.replace("?", "").strip())
        if not data or not data.get("current_price"):
            return ""
        change = data.get("day_change_pct", 0)
        return f"LIVE PRICE: {symbol} is trading at ₹{data['current_price']:.2f} ({change:+.2f}% today)"
    except Exception:
        return ""


def generate_suggestions(message: str, has_holdings: bool) -> list:
    """Generate contextual follow-up suggestions."""
    msg_lower = message.lower()
    suggestions = []

    if "tax" in msg_lower or "stcg" in msg_lower or "ltcg" in msg_lower:
        suggestions = ["Show tax harvesting opportunities", "What's my advance tax due?", "Export tax report"]
    elif "sell" in msg_lower:
        suggestions = ["What's the tax impact?", "Show my LTCG holdings", "Best time to sell?"]
    elif "buy" in msg_lower or "invest" in msg_lower:
        suggestions = ["Check portfolio overlap", "Show sector allocation", "Compare with alternatives"]
    elif "dividend" in msg_lower:
        suggestions = ["Show dividend calendar", "Top dividend stocks in portfolio", "Dividend tax implications"]
    elif "risk" in msg_lower or "volatile" in msg_lower:
        suggestions = ["Show portfolio beta", "Diversification analysis", "Rebalance suggestions"]
    elif has_holdings:
        suggestions = ["Portfolio summary", "Tax harvesting tips", "Top gainers in my portfolio"]
    else:
        suggestions = ["How to start investing?", "What is SIP?", "Explain mutual funds"]

    return suggestions[:3]


def detect_alert_intent(message: str) -> dict | None:
    """Detect if user wants to create a price alert."""
    import re

    msg_lower = message.lower()
    if not any(kw in msg_lower for kw in ["alert", "notify", "tell me when", "remind"]):
        return None

    # Pattern: "alert me when TCS hits 4000" or "notify when RELIANCE crosses 2500"
    pattern = (
        r"([A-Z]{2,15})\s+(?:hits|crosses|reaches|goes above|goes below|at|to)"
        r"\s*(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)"
    )
    match = re.search(pattern, message)

    if match:
        symbol = match.group(1).upper()
        price = float(match.group(2).replace(",", ""))
        condition = "below" if "below" in msg_lower else "above"
        return {"symbol": symbol, "target_price": price, "condition": condition}
    return None


def detect_tax_query(message: str) -> dict | None:
    """Detect if user is asking about tax on selling."""
    import re

    msg_lower = message.lower()
    if not any(kw in msg_lower for kw in ["tax", "stcg", "ltcg"]) or "sell" not in msg_lower:
        return None

    # Pattern: "tax if I sell RELIANCE" or "what's tax on selling TCS"
    # Look for stock symbol after sell keyword
    pattern = r"sell(?:ing)?\s+([A-Z]{2,15})"
    match = re.search(pattern, message)

    if match:
        return {"symbol": match.group(1).upper(), "action": "tax_calc"}
    return None


def detect_comparison(message: str) -> list | None:
    """Detect comparison queries like 'Compare TCS vs Infosys'."""
    msg_lower = message.lower()
    if not any(kw in msg_lower for kw in ["compare", "vs", "versus", "or"]):
        return None
    symbols = re.findall(r"\b([A-Z]{2,15})\b", message)
    return symbols[:2] if len(symbols) >= 2 else None


def detect_whatif(message: str, holding_symbols: set) -> dict | None:
    """Detect what-if queries like 'What if I sell RELIANCE'."""
    msg_lower = message.lower()
    if "what if" not in msg_lower and "what happens" not in msg_lower:
        return None
    match = re.search(r"(?:sell|buy|add)\s+(\d+)?\s*([A-Z]{2,15})", message)
    if match:
        qty = int(match.group(1)) if match.group(1) else None
        sym = match.group(2).upper()
        action = "sell" if "sell" in msg_lower else "buy"
        return {"symbol": sym, "action": action, "quantity": qty}
    return None


async def get_comparison_data(symbols: list) -> str:
    """Fetch fundamentals for both stocks for comparison."""
    import asyncio

    results = await asyncio.gather(*[get_stock_fundamentals(s) for s in symbols])
    parts = [r for r in results if r]
    if len(parts) < 2:
        return ""
    return "COMPARISON DATA:\n" + "\n".join(parts)


async def get_whatif_simulation(symbol: str, action: str, quantity: int | None, holdings: list) -> str:
    """Simulate what-if scenario."""
    holding = next((h for h in holdings if h.symbol.upper() == symbol), None)
    if not holding:
        return f"SIMULATION: {symbol} not found in portfolio."

    price = holding.current_price or holding.avg_price
    qty = quantity or holding.quantity
    value = qty * price
    invested = qty * holding.avg_price
    pnl = value - invested

    if action == "sell":
        remaining_qty = holding.quantity - qty
        remaining_val = remaining_qty * price
        return (
            f"WHAT-IF SIMULATION: Selling {qty} shares of {symbol}\n"
            f"Sale Value: ₹{value:,.0f} | P&L: ₹{pnl:,.0f}\n"
            f"Remaining: {remaining_qty:.2f} shares worth ₹{remaining_val:,.0f}"
        )
    else:
        new_qty = holding.quantity + qty
        new_avg = (holding.quantity * holding.avg_price + qty * price) / new_qty
        return (
            f"WHAT-IF SIMULATION: Buying {qty} shares of {symbol} at ₹{price:.2f}\n"
            f"New Qty: {new_qty:.2f} | New Avg: ₹{new_avg:.2f}\n"
            f"Total Investment: ₹{new_qty * new_avg:,.0f}"
        )


async def get_sentiment(symbol: str) -> str:
    """Analyze news sentiment for a stock."""
    from ....services.news import fetch_stock_news

    news = await fetch_stock_news(symbol, limit=5)
    if not news:
        return ""

    positive_words = {
        "surge",
        "rally",
        "gain",
        "rise",
        "up",
        "high",
        "profit",
        "beat",
        "strong",
        "growth",
        "buy",
        "bull",
    }
    negative_words = {"fall", "drop", "loss", "down", "low", "crash", "sell", "weak", "bear", "slump", "decline", "cut"}

    pos = neg = 0
    for n in news:
        title_lower = n["title"].lower()
        pos += sum(1 for w in positive_words if w in title_lower)
        neg += sum(1 for w in negative_words if w in title_lower)

    total = pos + neg
    if total == 0:
        sentiment = "Neutral"
    elif pos > neg:
        sentiment = f"Positive ({pos}/{total} signals)"
    else:
        sentiment = f"Negative ({neg}/{total} signals)"

    headlines = " | ".join(n["title"][:60] for n in news[:3])
    return f"SENTIMENT for {symbol}: {sentiment}\nHeadlines: {headlines}"


async def get_sparkline_data(symbol: str) -> list:
    """Fetch 30-day price data for sparkline chart."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=8) as c:
            resp = await c.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS?interval=1d&range=1mo",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if resp.status_code == 200:
                result = resp.json()["chart"]["result"][0]
                closes = result["indicators"]["quote"][0]["close"]
                timestamps = result["timestamp"]
                from datetime import datetime

                return [
                    {"date": datetime.fromtimestamp(t).strftime("%m/%d"), "price": round(c, 2)}
                    for t, c in zip(timestamps, closes)
                    if c is not None
                ]
    except Exception:
        pass
    return []


# ─── Chat History Endpoints ───


@router.get("/sessions")
async def list_sessions(
    current_user: dict = Depends(get_current_user),
) -> StandardResponse:
    """List all chat sessions for the user."""
    uid = PydanticObjectId(current_user["_id"])
    sessions = await ChatSession.find(ChatSession.user_id == uid).sort("-updated_at").to_list(50)
    return StandardResponse.ok(
        [
            {
                "id": str(s.id),
                "title": s.title,
                "last_message": s.last_message[:80],
                "message_count": s.message_count,
                "updated_at": s.updated_at.isoformat(),
            }
            for s in sessions
        ]
    )


@router.get("/sessions/{session_id}")
async def get_session_messages(
    session_id: str,
    current_user: dict = Depends(get_current_user),
) -> StandardResponse:
    """Load messages for a chat session."""
    uid = PydanticObjectId(current_user["_id"])
    messages = (
        await ChatMessage.find(
            ChatMessage.user_id == uid,
            ChatMessage.session_id == session_id,
        )
        .sort("+created_at")
        .to_list(100)
    )
    return StandardResponse.ok([{"role": m.role, "content": m.content, "suggestions": m.suggestions} for m in messages])


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
) -> StandardResponse:
    """Delete a chat session and its messages."""
    uid = PydanticObjectId(current_user["_id"])
    await ChatMessage.find(ChatMessage.user_id == uid, ChatMessage.session_id == session_id).delete()
    await ChatSession.find_one(ChatSession.id == PydanticObjectId(session_id), ChatSession.user_id == uid).delete()
    return StandardResponse.ok({"deleted": True})


@router.get("/export/{session_id}")
async def export_chat(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Export chat session as text file."""
    import io

    uid = PydanticObjectId(current_user["_id"])
    messages = (
        await ChatMessage.find(
            ChatMessage.user_id == uid,
            ChatMessage.session_id == session_id,
        )
        .sort("+created_at")
        .to_list(100)
    )

    lines = ["StockPilot AI Chat Export", "=" * 40, ""]
    for m in messages:
        role = "You" if m.role == "user" else "StockPilot AI"
        lines.append(f"[{m.created_at.strftime('%H:%M')}] {role}:")
        lines.append(m.content)
        lines.append("")

    content = "\n".join(lines)
    buffer = io.BytesIO(content.encode("utf-8"))
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=chat_export.txt"},
    )


# ─── Main Chat Endpoint ───


@router.post("/ask")
async def chat_ask(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    if not client:
        return StandardResponse.error("AI chat not configured. Set GROQ_API_KEY.")

    import asyncio

    context = await build_context(current_user["_id"])
    user_id = PydanticObjectId(current_user["_id"])

    # Create or load session
    session_id = req.session_id
    if not session_id:
        session = ChatSession(user_id=user_id, title=req.message[:50])
        await session.insert()
        session_id = str(session.id)

    # Get user's holdings for context
    holdings = await Holding.find(Holding.user_id == user_id).to_list()
    holding_symbols = {h.symbol.lower() for h in holdings}
    holding_names = {(h.name or "").lower() for h in holdings}

    # Detect if user is asking about external company/stock not in portfolio
    extra_context = []
    msg_lower = req.message.lower()
    sparkline_data = []
    detected_symbol = None

    # Check if message contains company-like patterns
    if any(
        kw in msg_lower
        for kw in ["about", "what is", "tell me", "company", "stock", "share", "invest in", "should i buy", "price"]
    ):
        from ....services.search import search_company_info

        skip_words = {
            "tell",
            "what",
            "how",
            "why",
            "when",
            "where",
            "should",
            "can",
            "is",
            "are",
            "the",
            "about",
            "me",
            "my",
            "i",
        }

        words = req.message.split()
        for i, word in enumerate(words):
            clean_word = word.rstrip("?.,!")
            if len(clean_word) > 2 and clean_word[0].isupper() and clean_word.lower() not in skip_words:
                company_parts = [clean_word]
                for j in range(i + 1, min(i + 5, len(words))):
                    next_word = words[j].rstrip("?.,!")
                    if next_word[0].isupper() or next_word.lower() in ["ltd", "limited", "pvt", "private", "inc"]:
                        company_parts.append(next_word)
                    else:
                        break
                potential_company = " ".join(company_parts)
                detected_symbol = company_parts[0].upper()

                # If not in portfolio, fetch external data
                if potential_company.lower() not in holding_names and detected_symbol.lower() not in holding_symbols:
                    # Fetch fundamentals, price, and web search in parallel
                    import asyncio

                    fund_task = get_stock_fundamentals(detected_symbol)
                    price_task = get_live_price(detected_symbol)
                    search_task = search_company_info(potential_company)

                    fundamentals, live_price, web_results = await asyncio.gather(fund_task, price_task, search_task)

                    if fundamentals:
                        extra_context.append(fundamentals)
                    if live_price:
                        extra_context.append(live_price)
                    if web_results:
                        extra_context.append(web_results)
                break

    # Detect comparison query
    comparison = detect_comparison(req.message)
    if comparison:
        comp_data = await get_comparison_data(comparison)
        if comp_data:
            extra_context.append(comp_data)
        sparkline_data = await get_sparkline_data(comparison[0])

    # Detect what-if simulation
    whatif = detect_whatif(req.message, holding_symbols)
    if whatif:
        sim = await get_whatif_simulation(whatif["symbol"], whatif["action"], whatif["quantity"], holdings)
        extra_context.append(sim)

    # Detect sentiment query
    if any(kw in msg_lower for kw in ["sentiment", "feeling", "mood", "outlook"]):
        # Find symbol in message
        sym_match = re.search(r"\b([A-Z]{2,15})\b", req.message)
        if sym_match:
            sentiment = await get_sentiment(sym_match.group(1))
            if sentiment:
                extra_context.append(sentiment)

    # Fetch sparkline for any detected symbol
    if not sparkline_data and detected_symbol:
        sparkline_data = await get_sparkline_data(detected_symbol)

    # Detect alert creation intent
    alert_intent = detect_alert_intent(req.message)
    alert_created = None
    if alert_intent:
        try:
            from ....models.documents import Alert

            alert = Alert(
                user_id=user_id,
                symbol=alert_intent["symbol"],
                condition=alert_intent["condition"],
                target_price=alert_intent["target_price"],
                active=True,
            )
            await alert.insert()
            sym = alert_intent["symbol"]
            cond = alert_intent["condition"]
            price = alert_intent["target_price"]
            alert_created = f"✅ Alert created: Notify when {sym} goes {cond} ₹{price:,.0f}"
            extra_context.append(f"ALERT CREATED: {alert_created}")
        except Exception as e:
            logger.error(f"Alert creation failed: {e}")

    # Detect tax calculation query
    tax_query = detect_tax_query(req.message)
    if tax_query and tax_query["symbol"].lower() in holding_symbols:
        # Find the holding and calculate tax
        for h in holdings:
            if h.symbol.lower() == tax_query["symbol"].lower():
                from datetime import datetime, timedelta

                invested = h.quantity * h.avg_price
                current = h.quantity * (h.current_price or h.avg_price)
                pnl = current - invested

                # Determine holding period
                first_buy = None
                for t in h.transactions:
                    if t.type == "BUY":
                        try:
                            td = datetime.strptime(t.date, "%Y-%m-%d") if isinstance(t.date, str) else t.date
                            if first_buy is None or td < first_buy:
                                first_buy = td
                        except Exception:
                            pass

                is_ltcg = first_buy and first_buy < datetime.now() - timedelta(days=365)
                tax_type = "LTCG" if is_ltcg else "STCG"
                tax_rate = 0.125 if is_ltcg else 0.20
                exemption = 125000 if is_ltcg else 0
                taxable = max(0, pnl - exemption) if pnl > 0 else 0
                tax = taxable * tax_rate

                tax_info = (
                    f"TAX CALCULATION for selling {h.symbol}:\n"
                    f"P&L: ₹{pnl:,.0f} | Type: {tax_type} | "
                    f"Tax Rate: {tax_rate*100:.1f}% | "
                    f"{'Exemption: ₹1.25L | ' if is_ltcg else ''}"
                    f"Estimated Tax: ₹{tax:,.0f}"
                )
                extra_context.append(tax_info)
                break

    # Build full context
    full_context = context
    if extra_context:
        full_context += "\n\n" + "\n\n".join(extra_context)

    # Multi-language support
    lang_prefix = SUPPORTED_LANGUAGES.get(req.language or "en", "")
    system_content = lang_prefix + SYSTEM_PROMPT + "\n\n" + full_context

    messages = [{"role": "system", "content": system_content}]
    for msg in (req.history or [])[-10:]:
        messages.append({"role": msg.get("role", "user"), "content": msg["content"]})
    messages.append({"role": "user", "content": req.message})

    # Save user message to DB
    await ChatMessage(user_id=user_id, session_id=session_id, role="user", content=req.message).insert()

    # Generate suggestions
    suggestions = generate_suggestions(req.message, len(holdings) > 0)

    try:
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.3,
            max_completion_tokens=800,
            stream=True,
        )

        async def generate():
            full = []
            for chunk in stream:
                token = chunk.choices[0].delta.content or ""
                if token:
                    full.append(token)
                    yield token

            # Metadata for frontend
            import json

            meta = {"suggestions": suggestions, "session_id": session_id}
            if sparkline_data:
                meta["sparkline"] = sparkline_data
            if alert_created:
                meta["alert"] = alert_created

            yield f"\n\n<!--META:{json.dumps(meta)}-->"

            # Save assistant message to DB
            full_text = "".join(full)
            try:
                await ChatMessage(
                    user_id=user_id,
                    session_id=session_id,
                    role="assistant",
                    content=full_text,
                    suggestions=suggestions,
                ).insert()
                # Update session
                await ChatSession.find_one(ChatSession.id == PydanticObjectId(session_id)).update(
                    {
                        "$set": {
                            "last_message": full_text[:80],
                            "updated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
                        },
                        "$inc": {"message_count": 2},
                    }
                )
            except Exception as e:
                logger.error(f"Save chat failed: {e}")

            logger.info(f"Groq streamed: {full_text[:200]}")

        return StreamingResponse(generate(), media_type="text/plain")
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return StandardResponse.error(f"AI error: {str(e)}")
