import logging
from typing import List, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends
from groq import Groq
from pydantic import BaseModel

from ....core.config import settings
from ....core.response_handler import StandardResponse
from ....core.security import get_current_user
from ....models.documents import Holding

logger = logging.getLogger("stockpilot")

router = APIRouter()

client = Groq(api_key=settings.groq_api_key) if settings.groq_api_key else None

SYSTEM_PROMPT = """You are StockPilot AI — a concise, expert Indian stock market portfolio assistant.

Rules:
- Answer ONLY based on the portfolio data provided below. Do not make up data.
- Use ₹ for currency, format Indian style (1,00,000).
- Keep responses short and actionable (3-8 lines). Use bullet points.
- If asked something not in the data, say so honestly.
- Never give specific buy/sell advice with price targets. Give general observations.
- Mention specific stock names and numbers from the data when relevant.
"""


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []


@router.post("/ask")
async def chat_ask(
    req: ChatRequest, current_user: dict = Depends(get_current_user)
) -> StandardResponse:
    if not client:
        return StandardResponse.error("AI chat not configured. Set GROQ_API_KEY.")

    uid = PydanticObjectId(current_user["_id"])
    holdings = await Holding.find(Holding.user_id == uid).to_list()

    if not holdings:
        context = "User has no holdings in their portfolio."
    else:
        lines = []
        total_invested = total_current = 0
        for h in holdings:
            current = (h.current_price or h.avg_price) * h.quantity
            invested = h.avg_price * h.quantity
            pnl = current - invested
            pnl_pct = (pnl / invested * 100) if invested else 0
            total_invested += invested
            total_current += current
            lines.append(
                f"{h.symbol} | {h.holding_type} | Qty:{h.quantity:.2f} | "
                f"Avg:₹{h.avg_price:.1f} | CMP:₹{h.current_price or 0:.1f} | "
                f"P&L:₹{pnl:,.0f} ({pnl_pct:+.1f}%) | Sector:{h.sector or 'N/A'}"
            )
        total_pnl = total_current - total_invested
        total_pnl_pct = (total_pnl / total_invested * 100) if total_invested else 0
        context = (
            f"Portfolio: {len(holdings)} holdings | "
            f"Invested: ₹{total_invested:,.0f} | Current: ₹{total_current:,.0f} | "
            f"P&L: ₹{total_pnl:,.0f} ({total_pnl_pct:+.1f}%)\n\n"
            + "\n".join(lines)
        )

    messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n\nPORTFOLIO DATA:\n" + context}]
    for msg in (req.history or [])[-10:]:
        messages.append({"role": msg.get("role", "user"), "content": msg["content"]})
    messages.append({"role": "user", "content": req.message})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.3,
            max_completion_tokens=500,
        )
        reply = response.choices[0].message.content
        logger.info(f"Groq response: {reply[:200]}")
        return StandardResponse.ok({"reply": reply})
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return StandardResponse.error(f"AI error: {str(e)}")
