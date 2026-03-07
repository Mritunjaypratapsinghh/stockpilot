from typing import List, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from google import genai
from pydantic import BaseModel

from ....core.config import settings
from ....core.security import get_current_user
from ....models.documents import Holding
from ....core.response_handler import StandardResponse

router = APIRouter()

client = genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key else None

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
        return StandardResponse.error("AI chat not configured. Set GEMINI_API_KEY.")

    # Gather portfolio context
    uid = PydanticObjectId(current_user["_id"])
    holdings = await Holding.find(Holding.user_id == uid).to_list()

    if not holdings:
        context = "User has no holdings in their portfolio."
    else:
        lines = []
        total_invested = 0
        total_current = 0
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

    # Build conversation
    contents = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT + "\n\nPORTFOLIO DATA:\n" + context}]},
                {"role": "model", "parts": [{"text": "Understood. I have your portfolio data. Ask me anything."}]}]

    for msg in (req.history or [])[-10:]:
        contents.append({"role": "user" if msg.get("role") == "user" else "model",
                         "parts": [{"text": msg["content"]}]})

    contents.append({"role": "user", "parts": [{"text": req.message}]})

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
        )
        return StandardResponse.ok({"reply": response.text})
    except Exception as e:
        return StandardResponse.error(f"AI error: {str(e)}")
