from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, date
from bson import ObjectId
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..api.auth import get_current_user

router = APIRouter()

class SIPCreate(BaseModel):
    symbol: str
    amount: float
    frequency: str = "monthly"  # monthly, weekly, quarterly
    sip_date: int = 1  # day of month (1-28)
    start_date: date
    end_date: Optional[date] = None

@router.get("/")
async def get_sips(current_user: dict = Depends(get_current_user)):
    """Get all SIPs with performance"""
    db = get_db()
    sips = await db.sips.find({"user_id": ObjectId(current_user["_id"])}).to_list(50)
    
    result = []
    total_invested = 0
    total_current = 0
    
    for sip in sips:
        installments = sip.get("installments", [])
        invested = sum(i["amount"] for i in installments)
        units = sum(i["units"] for i in installments)
        
        # Get current NAV (simplified - use last price or avg)
        current_nav = installments[-1]["nav"] if installments else sip.get("last_nav", 0)
        current_value = units * current_nav
        
        total_invested += invested
        total_current += current_value
        
        # Calculate XIRR for this SIP
        xirr = None
        if len(installments) >= 2:
            try:
                from datetime import datetime as dt
                cashflows = [(-i["amount"], dt.fromisoformat(i["date"])) for i in installments]
                cashflows.append((current_value, dt.now()))
                xirr = calculate_xirr(cashflows)
            except:
                pass
        
        result.append({
            "_id": str(sip["_id"]),
            "symbol": sip["symbol"],
            "amount": sip["amount"],
            "frequency": sip.get("frequency", "monthly"),
            "sip_date": sip.get("sip_date", 1),
            "start_date": sip.get("start_date"),
            "is_active": sip.get("is_active", True),
            "installments_count": len(installments),
            "total_invested": round(invested, 2),
            "total_units": round(units, 4),
            "current_value": round(current_value, 2),
            "returns": round(current_value - invested, 2),
            "returns_pct": round((current_value - invested) / invested * 100, 2) if invested > 0 else 0,
            "xirr": round(xirr, 2) if xirr else None
        })
    
    return {
        "sips": result,
        "summary": {
            "total_invested": round(total_invested, 2),
            "current_value": round(total_current, 2),
            "total_returns": round(total_current - total_invested, 2),
            "returns_pct": round((total_current - total_invested) / total_invested * 100, 2) if total_invested > 0 else 0
        }
    }

def calculate_xirr(cashflows):
    """Calculate XIRR from cashflows [(amount, date), ...]"""
    from datetime import datetime as dt
    
    def npv(rate, cashflows):
        total = 0
        for amount, d in cashflows:
            years = (d - cashflows[0][1]).days / 365.0
            total += amount / ((1 + rate) ** years)
        return total
    
    # Newton-Raphson method
    rate = 0.1
    for _ in range(100):
        npv_val = npv(rate, cashflows)
        if abs(npv_val) < 0.001:
            break
        # Numerical derivative
        npv_deriv = (npv(rate + 0.001, cashflows) - npv_val) / 0.001
        if abs(npv_deriv) < 0.0001:
            break
        rate = rate - npv_val / npv_deriv
    
    return rate * 100

@router.post("/")
async def create_sip(sip: SIPCreate, current_user: dict = Depends(get_current_user)):
    """Create a new SIP"""
    db = get_db()
    
    doc = {
        "user_id": ObjectId(current_user["_id"]),
        "symbol": sip.symbol.upper(),
        "amount": sip.amount,
        "frequency": sip.frequency,
        "sip_date": sip.sip_date,
        "start_date": sip.start_date.isoformat(),
        "end_date": sip.end_date.isoformat() if sip.end_date else None,
        "is_active": True,
        "installments": [],
        "created_at": datetime.utcnow()
    }
    
    result = await db.sips.insert_one(doc)
    return {"message": "SIP created", "id": str(result.inserted_id)}

@router.post("/{sip_id}/installment")
async def add_installment(sip_id: str, amount: float, nav: float, date: date, current_user: dict = Depends(get_current_user)):
    """Record a SIP installment"""
    db = get_db()
    
    units = amount / nav
    installment = {
        "amount": amount,
        "nav": nav,
        "units": round(units, 4),
        "date": date.isoformat()
    }
    
    await db.sips.update_one(
        {"_id": ObjectId(sip_id), "user_id": ObjectId(current_user["_id"])},
        {"$push": {"installments": installment}, "$set": {"last_nav": nav}}
    )
    
    return {"message": "Installment recorded", "units": round(units, 4)}

@router.put("/{sip_id}/toggle")
async def toggle_sip(sip_id: str, current_user: dict = Depends(get_current_user)):
    """Pause/Resume SIP"""
    db = get_db()
    sip = await db.sips.find_one({"_id": ObjectId(sip_id), "user_id": ObjectId(current_user["_id"])})
    if not sip:
        raise HTTPException(status_code=404, detail="SIP not found")
    
    new_status = not sip.get("is_active", True)
    await db.sips.update_one({"_id": ObjectId(sip_id)}, {"$set": {"is_active": new_status}})
    
    return {"message": "SIP paused" if not new_status else "SIP resumed", "is_active": new_status}

@router.delete("/{sip_id}")
async def delete_sip(sip_id: str, current_user: dict = Depends(get_current_user)):
    """Delete SIP"""
    db = get_db()
    await db.sips.delete_one({"_id": ObjectId(sip_id), "user_id": ObjectId(current_user["_id"])})
    return {"message": "SIP deleted"}

@router.get("/calculator")
async def sip_calculator(monthly_amount: float, years: int, expected_return: float = 12):
    """Calculate SIP returns"""
    months = years * 12
    r = expected_return / 100 / 12  # monthly rate
    
    # Future value of SIP
    if r > 0:
        future_value = monthly_amount * (((1 + r) ** months - 1) / r) * (1 + r)
    else:
        future_value = monthly_amount * months
    
    total_invested = monthly_amount * months
    wealth_gained = future_value - total_invested
    
    return {
        "monthly_amount": monthly_amount,
        "years": years,
        "expected_return": expected_return,
        "total_invested": round(total_invested, 0),
        "future_value": round(future_value, 0),
        "wealth_gained": round(wealth_gained, 0),
        "absolute_return_pct": round(wealth_gained / total_invested * 100, 1) if total_invested > 0 else 0
    }

@router.get("/lumpsum-vs-sip")
async def lumpsum_vs_sip(amount: float, years: int, expected_return: float = 12):
    """Compare lumpsum vs SIP investment"""
    r = expected_return / 100
    months = years * 12
    monthly_r = r / 12
    monthly_sip = amount / months
    
    # Lumpsum
    lumpsum_value = amount * ((1 + r) ** years)
    
    # SIP
    if monthly_r > 0:
        sip_value = monthly_sip * (((1 + monthly_r) ** months - 1) / monthly_r) * (1 + monthly_r)
    else:
        sip_value = amount
    
    return {
        "total_investment": amount,
        "years": years,
        "expected_return": expected_return,
        "lumpsum": {
            "final_value": round(lumpsum_value, 0),
            "returns": round(lumpsum_value - amount, 0)
        },
        "sip": {
            "monthly_amount": round(monthly_sip, 0),
            "final_value": round(sip_value, 0),
            "returns": round(sip_value - amount, 0)
        },
        "better": "Lumpsum" if lumpsum_value > sip_value else "SIP",
        "difference": round(abs(lumpsum_value - sip_value), 0)
    }
