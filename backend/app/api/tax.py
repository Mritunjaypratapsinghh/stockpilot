from fastapi import APIRouter, Depends
from datetime import datetime, date, timedelta
from bson import ObjectId
from ..database import get_db
from ..api.auth import get_current_user

router = APIRouter()

# Tax rates for India FY 2024-25
LTCG_RATE = 0.125  # 12.5% for gains > 1.25L
STCG_RATE = 0.20   # 20% for equity
LTCG_EXEMPTION = 125000  # 1.25 Lakh exemption

def calculate_holding_period(buy_date: str) -> int:
    """Returns holding period in days"""
    if isinstance(buy_date, str):
        buy = datetime.fromisoformat(buy_date).date()
    else:
        buy = buy_date
    return (date.today() - buy).days

def is_long_term(buy_date: str) -> bool:
    """Equity is long-term if held > 12 months"""
    return calculate_holding_period(buy_date) > 365

@router.get("/summary")
async def get_tax_summary(fy: str = None, current_user: dict = Depends(get_current_user)):
    """Get tax summary for financial year"""
    db = get_db()
    
    # Default to current FY
    if not fy:
        today = date.today()
        fy_start = date(today.year if today.month >= 4 else today.year - 1, 4, 1)
        fy_end = date(fy_start.year + 1, 3, 31)
    else:
        year = int(fy.split("-")[0])
        fy_start = date(year, 4, 1)
        fy_end = date(year + 1, 3, 31)
    
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    
    realized_stcg = 0
    realized_ltcg = 0
    unrealized_stcg = 0
    unrealized_ltcg = 0
    
    sell_transactions = []
    
    for h in holdings:
        current_price = h.get("current_price", h["avg_price"])
        
        for txn in h.get("transactions", []):
            if txn["type"] == "SELL":
                txn_date = datetime.fromisoformat(txn["date"]).date() if isinstance(txn["date"], str) else txn["date"]
                if fy_start <= txn_date <= fy_end:
                    # Find corresponding buy for FIFO
                    gain = (txn["price"] - h["avg_price"]) * txn["quantity"]
                    
                    # Check if long-term (simplified - using avg holding)
                    first_buy = next((t for t in h.get("transactions", []) if t["type"] == "BUY"), None)
                    if first_buy and is_long_term(first_buy["date"]):
                        realized_ltcg += gain
                    else:
                        realized_stcg += gain
                    
                    sell_transactions.append({
                        "symbol": h["symbol"],
                        "date": txn["date"],
                        "quantity": txn["quantity"],
                        "sell_price": txn["price"],
                        "buy_price": h["avg_price"],
                        "gain": round(gain, 2),
                        "type": "LTCG" if first_buy and is_long_term(first_buy["date"]) else "STCG"
                    })
        
        # Unrealized gains
        if h["quantity"] > 0:
            unrealized = (current_price - h["avg_price"]) * h["quantity"]
            first_buy = next((t for t in h.get("transactions", []) if t["type"] == "BUY"), None)
            if first_buy and is_long_term(first_buy["date"]):
                unrealized_ltcg += unrealized
            else:
                unrealized_stcg += unrealized
    
    # Calculate tax liability
    taxable_ltcg = max(0, realized_ltcg - LTCG_EXEMPTION)
    ltcg_tax = taxable_ltcg * LTCG_RATE
    stcg_tax = max(0, realized_stcg) * STCG_RATE
    
    return {
        "financial_year": f"{fy_start.year}-{fy_end.year % 100}",
        "realized": {
            "stcg": round(realized_stcg, 2),
            "ltcg": round(realized_ltcg, 2),
            "total": round(realized_stcg + realized_ltcg, 2)
        },
        "unrealized": {
            "stcg": round(unrealized_stcg, 2),
            "ltcg": round(unrealized_ltcg, 2),
            "total": round(unrealized_stcg + unrealized_ltcg, 2)
        },
        "tax_liability": {
            "ltcg_exemption": LTCG_EXEMPTION,
            "taxable_ltcg": round(taxable_ltcg, 2),
            "ltcg_tax": round(ltcg_tax, 2),
            "stcg_tax": round(stcg_tax, 2),
            "total_tax": round(ltcg_tax + stcg_tax, 2)
        },
        "transactions": sell_transactions
    }

@router.get("/harvest")
async def get_tax_harvest_suggestions(current_user: dict = Depends(get_current_user)):
    """Suggest stocks to sell for tax-loss harvesting"""
    db = get_db()
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    
    suggestions = []
    total_harvestable_loss = 0
    
    for h in holdings:
        if h["quantity"] <= 0:
            continue
            
        current_price = h.get("current_price", h["avg_price"])
        pnl = (current_price - h["avg_price"]) * h["quantity"]
        pnl_pct = ((current_price - h["avg_price"]) / h["avg_price"] * 100) if h["avg_price"] > 0 else 0
        
        first_buy = next((t for t in h.get("transactions", []) if t["type"] == "BUY"), None)
        is_lt = first_buy and is_long_term(first_buy["date"]) if first_buy else False
        
        # Suggest harvesting if loss > 5%
        if pnl < 0 and pnl_pct < -5:
            suggestions.append({
                "symbol": h["symbol"],
                "quantity": h["quantity"],
                "avg_price": h["avg_price"],
                "current_price": current_price,
                "loss": round(abs(pnl), 2),
                "loss_pct": round(pnl_pct, 1),
                "type": "LTCG" if is_lt else "STCG",
                "tax_saved": round(abs(pnl) * (LTCG_RATE if is_lt else STCG_RATE), 2),
                "recommendation": "Sell to book loss, can rebuy after 30 days"
            })
            total_harvestable_loss += abs(pnl)
    
    # Sort by loss amount
    suggestions.sort(key=lambda x: x["loss"], reverse=True)
    
    return {
        "suggestions": suggestions[:10],
        "total_harvestable_loss": round(total_harvestable_loss, 2),
        "potential_tax_saved": round(total_harvestable_loss * STCG_RATE, 2),
        "note": "Sell loss-making stocks before March 31 to offset gains. Avoid wash sale - wait 30 days before rebuying."
    }

@router.get("/report")
async def generate_tax_report(fy: str = None, current_user: dict = Depends(get_current_user)):
    """Generate ITR-compatible tax report"""
    summary = await get_tax_summary(fy, current_user)
    
    return {
        **summary,
        "itr_schedule": "Schedule CG (Capital Gains)",
        "sections": {
            "112A": {
                "description": "LTCG on equity shares (STT paid)",
                "amount": summary["realized"]["ltcg"],
                "exemption": LTCG_EXEMPTION,
                "taxable": summary["tax_liability"]["taxable_ltcg"],
                "tax_rate": f"{LTCG_RATE * 100}%"
            },
            "111A": {
                "description": "STCG on equity shares (STT paid)",
                "amount": summary["realized"]["stcg"],
                "taxable": max(0, summary["realized"]["stcg"]),
                "tax_rate": f"{STCG_RATE * 100}%"
            }
        }
    }
