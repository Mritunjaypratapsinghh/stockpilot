import logging
from typing import List, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from groq import Groq
from pydantic import BaseModel

from ....core.config import settings
from ....core.response_handler import StandardResponse
from ....core.security import get_current_user
from ....models.documents import Holding

logger = logging.getLogger("stockpilot")

router = APIRouter()

client = Groq(api_key=settings.groq_api_key) if settings.groq_api_key else None

SYSTEM_PROMPT = """You are StockPilot AI — a friendly, expert Indian stock market portfolio assistant built into the StockPilot app.

Style:
- Be conversational and warm, not robotic. Use emojis sparingly (📊 📈 📉 💡 ⚠️).
- Format currency in Indian style with ₹ symbol (e.g., ₹1,21,992).
- Keep responses 3-8 lines. Use bullet points for lists.
- Bold important numbers and stock names using **text**.

Rules:
- Answer ONLY from the portfolio data below. Never fabricate holdings or prices.
- When suggesting action, explain WHY briefly (e.g., "DAMCAPITAL is down 28% — if fundamentals haven't changed, consider averaging down or booking the loss for tax harvesting").
- If sector data shows N/A, say "sector info isn't available for some holdings" — don't say "data doesn't provide enough information".
- Reference other StockPilot features when relevant (Tax Center, MF Overlap Analyzer, Signals page).
- Never give specific price targets or guaranteed advice. Use words like "consider", "you might want to".
"""


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []


async def build_context(user_id: str) -> str:
    uid = PydanticObjectId(user_id)
    holdings = await Holding.find(Holding.user_id == uid).to_list()

    if not holdings:
        return "User has no holdings."

    lines = []
    total_invested = total_current = 0
    sectors = {}
    stcg_loss = ltcg_loss = stcg_gain = ltcg_gain = 0

    for h in holdings:
        current = (h.current_price or h.avg_price) * h.quantity
        invested = h.avg_price * h.quantity
        pnl = current - invested
        pnl_pct = (pnl / invested * 100) if invested else 0
        total_invested += invested
        total_current += current

        # Sector tracking
        sec = h.sector or "Unknown"
        sectors[sec] = sectors.get(sec, 0) + current

        # Tax estimation (simplified: <1yr = STCG, >1yr = LTCG)
        if pnl > 0:
            stcg_gain += pnl
        else:
            stcg_loss += pnl

        lines.append(
            f"{h.symbol} | {h.holding_type} | Qty:{h.quantity:.2f} | "
            f"Avg:₹{h.avg_price:.1f} | CMP:₹{h.current_price or 0:.1f} | "
            f"P&L:₹{pnl:,.0f} ({pnl_pct:+.1f}%) | Sector:{sec}"
        )

    total_pnl = total_current - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested else 0

    # Sector summary
    sector_lines = sorted(sectors.items(), key=lambda x: -x[1])
    sector_str = ", ".join(f"{s}: {v / total_current * 100:.1f}%" for s, v in sector_lines[:8] if s != "Unknown")

    return (
        f"PORTFOLIO SUMMARY: {len(holdings)} holdings | "
        f"Invested: ₹{total_invested:,.0f} | Current: ₹{total_current:,.0f} | "
        f"P&L: ₹{total_pnl:,.0f} ({total_pnl_pct:+.1f}%)\n"
        f"SECTORS: {sector_str or 'Not available for most holdings'}\n"
        f"TAX ESTIMATE: Gains: ₹{stcg_gain:,.0f} | Losses: ₹{abs(stcg_loss):,.0f} | "
        f"Net taxable: ₹{max(0, stcg_gain + stcg_loss):,.0f}\n\n"
        f"HOLDINGS:\n" + "\n".join(lines)
    )


@router.post("/ask")
async def chat_ask(
    req: ChatRequest, current_user: dict = Depends(get_current_user)
):
    if not client:
        return StandardResponse.error("AI chat not configured. Set GROQ_API_KEY.")

    context = await build_context(current_user["_id"])

    messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n\n" + context}]
    for msg in (req.history or [])[-10:]:
        messages.append({"role": msg.get("role", "user"), "content": msg["content"]})
    messages.append({"role": "user", "content": req.message})

    try:
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.3,
            max_completion_tokens=500,
            stream=True,
        )

        async def generate():
            full = []
            for chunk in stream:
                token = chunk.choices[0].delta.content or ""
                if token:
                    full.append(token)
                    yield token
            logger.info(f"Groq streamed: {''.join(full)[:200]}")

        return StreamingResponse(generate(), media_type="text/plain")
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return StandardResponse.error(f"AI error: {str(e)}")
