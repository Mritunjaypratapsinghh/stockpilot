from fastapi import APIRouter, Depends
from datetime import datetime, date
from beanie import PydanticObjectId

from ..models.documents import Holding
from ..api.auth import get_current_user

router = APIRouter()

LTCG_RATE = 0.125
STCG_RATE = 0.20
LTCG_EXEMPTION = 125000


def is_long_term(buy_date: str) -> bool:
    buy = datetime.fromisoformat(buy_date).date() if isinstance(buy_date, str) else buy_date
    return (date.today() - buy).days > 365


@router.get("/summary")
async def get_tax_summary(fy: str = None, current_user: dict = Depends(get_current_user)):
    today = date.today()
    if not fy:
        fy_start = date(today.year if today.month >= 4 else today.year - 1, 4, 1)
    else:
        fy_start = date(int(fy.split("-")[0]), 4, 1)
    fy_end = date(fy_start.year + 1, 3, 31)

    holdings = await Holding.find(Holding.user_id == PydanticObjectId(current_user["_id"])).to_list()

    realized_stcg = realized_ltcg = unrealized_stcg = unrealized_ltcg = 0
    sell_transactions = []

    for h in holdings:
        current_price = h.current_price or h.avg_price
        first_buy = next((t for t in h.transactions if t.type == "BUY"), None)

        for txn in h.transactions:
            if txn.type == "SELL":
                txn_date = datetime.fromisoformat(txn.date).date() if isinstance(txn.date, str) else txn.date
                if fy_start <= txn_date <= fy_end:
                    gain = (txn.price - h.avg_price) * txn.quantity
                    is_lt = first_buy and is_long_term(first_buy.date)
                    if is_lt:
                        realized_ltcg += gain
                    else:
                        realized_stcg += gain
                    sell_transactions.append({"symbol": h.symbol, "date": txn.date, "quantity": txn.quantity, "sell_price": txn.price, "buy_price": h.avg_price, "gain": round(gain, 2), "type": "LTCG" if is_lt else "STCG"})

        if h.quantity > 0:
            unrealized = (current_price - h.avg_price) * h.quantity
            if first_buy and is_long_term(first_buy.date):
                unrealized_ltcg += unrealized
            else:
                unrealized_stcg += unrealized

    taxable_ltcg = max(0, realized_ltcg - LTCG_EXEMPTION)
    return {
        "financial_year": f"{fy_start.year}-{fy_end.year % 100}",
        "realized": {"stcg": round(realized_stcg, 2), "ltcg": round(realized_ltcg, 2), "total": round(realized_stcg + realized_ltcg, 2)},
        "unrealized": {"stcg": round(unrealized_stcg, 2), "ltcg": round(unrealized_ltcg, 2), "total": round(unrealized_stcg + unrealized_ltcg, 2)},
        "tax_liability": {"ltcg_exemption": LTCG_EXEMPTION, "taxable_ltcg": round(taxable_ltcg, 2), "ltcg_tax": round(taxable_ltcg * LTCG_RATE, 2), "stcg_tax": round(max(0, realized_stcg) * STCG_RATE, 2), "total_tax": round(taxable_ltcg * LTCG_RATE + max(0, realized_stcg) * STCG_RATE, 2)},
        "transactions": sell_transactions
    }


@router.get("/harvest")
async def get_tax_harvest_suggestions(current_user: dict = Depends(get_current_user)):
    holdings = await Holding.find(Holding.user_id == PydanticObjectId(current_user["_id"])).to_list()

    suggestions = []
    total_harvestable_loss = 0

    for h in holdings:
        if h.quantity <= 0:
            continue
        current_price = h.current_price or h.avg_price
        pnl = (current_price - h.avg_price) * h.quantity
        pnl_pct = ((current_price - h.avg_price) / h.avg_price * 100) if h.avg_price > 0 else 0
        first_buy = next((t for t in h.transactions if t.type == "BUY"), None)
        is_lt = first_buy and is_long_term(first_buy.date) if first_buy else False

        if pnl < 0 and pnl_pct < -5:
            suggestions.append({"symbol": h.symbol, "quantity": h.quantity, "avg_price": h.avg_price, "current_price": current_price, "loss": round(abs(pnl), 2), "loss_pct": round(pnl_pct, 1), "type": "LTCG" if is_lt else "STCG", "tax_saved": round(abs(pnl) * (LTCG_RATE if is_lt else STCG_RATE), 2)})
            total_harvestable_loss += abs(pnl)

    suggestions.sort(key=lambda x: x["loss"], reverse=True)
    return {"suggestions": suggestions[:10], "total_harvestable_loss": round(total_harvestable_loss, 2), "potential_tax_saved": round(total_harvestable_loss * STCG_RATE, 2)}


@router.get("/report")
async def generate_tax_report(fy: str = None, current_user: dict = Depends(get_current_user)):
    summary = await get_tax_summary(fy, current_user)
    return {**summary, "itr_schedule": "Schedule CG (Capital Gains)", "sections": {"112A": {"description": "LTCG on equity shares", "amount": summary["realized"]["ltcg"], "exemption": LTCG_EXEMPTION, "taxable": summary["tax_liability"]["taxable_ltcg"], "tax_rate": f"{LTCG_RATE * 100}%"}, "111A": {"description": "STCG on equity shares", "amount": summary["realized"]["stcg"], "taxable": max(0, summary["realized"]["stcg"]), "tax_rate": f"{STCG_RATE * 100}%"}}}
