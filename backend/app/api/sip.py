from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, date, timezone
from beanie import PydanticObjectId
from pydantic import BaseModel, Field
from typing import Optional, Literal

from ..models.documents import SIP
from ..models.documents.sip import Installment
from ..api.auth import get_current_user

router = APIRouter()


class SIPCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=30)
    amount: float = Field(..., gt=0)
    frequency: Literal["monthly", "weekly", "quarterly"] = "monthly"
    sip_date: int = Field(1, ge=1, le=28)
    start_date: date
    end_date: Optional[date] = None


def calculate_xirr(cashflows):
    def npv(rate, cfs):
        return sum(amt / ((1 + rate) ** ((d - cfs[0][1]).days / 365.0)) for amt, d in cfs)
    rate = 0.1
    for _ in range(100):
        npv_val = npv(rate, cashflows)
        if abs(npv_val) < 0.001:
            break
        npv_deriv = (npv(rate + 0.001, cashflows) - npv_val) / 0.001
        if abs(npv_deriv) < 0.0001:
            break
        rate = rate - npv_val / npv_deriv
    return rate * 100


@router.get("/")
async def get_sips(current_user: dict = Depends(get_current_user)):
    sips = await SIP.find(SIP.user_id == PydanticObjectId(current_user["_id"])).to_list()

    result = []
    total_invested = total_current = 0

    for sip in sips:
        invested = sum(i.amount for i in sip.installments)
        units = sum(i.units for i in sip.installments)
        current_nav = sip.installments[-1].nav if sip.installments else (sip.last_nav or 0)
        current_value = units * current_nav

        total_invested += invested
        total_current += current_value

        xirr = None
        if len(sip.installments) >= 2:
            try:
                cashflows = [(-i.amount, datetime.fromisoformat(i.date)) for i in sip.installments]
                cashflows.append((current_value, datetime.now()))
                xirr = calculate_xirr(cashflows)
            except:
                pass

        result.append({
            "_id": str(sip.id), "symbol": sip.symbol, "amount": sip.amount, "frequency": sip.frequency,
            "sip_date": sip.sip_date, "start_date": sip.start_date, "is_active": sip.is_active,
            "installments_count": len(sip.installments), "total_invested": round(invested, 2),
            "total_units": round(units, 4), "current_value": round(current_value, 2),
            "returns": round(current_value - invested, 2),
            "returns_pct": round((current_value - invested) / invested * 100, 2) if invested > 0 else 0,
            "xirr": round(xirr, 2) if xirr else None
        })

    return {
        "sips": result,
        "summary": {
            "total_invested": round(total_invested, 2), "current_value": round(total_current, 2),
            "total_returns": round(total_current - total_invested, 2),
            "returns_pct": round((total_current - total_invested) / total_invested * 100, 2) if total_invested > 0 else 0
        }
    }


@router.post("/")
async def create_sip(sip: SIPCreate, current_user: dict = Depends(get_current_user)):
    doc = SIP(
        user_id=PydanticObjectId(current_user["_id"]),
        symbol=sip.symbol.strip().upper(),
        amount=sip.amount,
        frequency=sip.frequency,
        sip_date=sip.sip_date,
        start_date=sip.start_date.isoformat(),
        end_date=sip.end_date.isoformat() if sip.end_date else None
    )
    await doc.insert()
    return {"message": "SIP created", "id": str(doc.id)}


@router.post("/{sip_id}/installment")
async def add_installment(sip_id: str, amount: float = Query(..., gt=0), nav: float = Query(..., gt=0), date: date = Query(...), current_user: dict = Depends(get_current_user)):
    if not PydanticObjectId.is_valid(sip_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    sip = await SIP.find_one(SIP.id == PydanticObjectId(sip_id), SIP.user_id == PydanticObjectId(current_user["_id"]))
    if not sip:
        raise HTTPException(status_code=404, detail="SIP not found")

    units = round(amount / nav, 4)
    sip.installments.append(Installment(amount=amount, nav=nav, units=units, date=date.isoformat()))
    sip.last_nav = nav
    await sip.save()
    return {"message": "Installment recorded", "units": units}


@router.put("/{sip_id}/toggle")
async def toggle_sip(sip_id: str, current_user: dict = Depends(get_current_user)):
    if not PydanticObjectId.is_valid(sip_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    sip = await SIP.find_one(SIP.id == PydanticObjectId(sip_id), SIP.user_id == PydanticObjectId(current_user["_id"]))
    if not sip:
        raise HTTPException(status_code=404, detail="SIP not found")
    sip.is_active = not sip.is_active
    await sip.save()
    return {"message": "SIP paused" if not sip.is_active else "SIP resumed", "is_active": sip.is_active}


@router.delete("/{sip_id}")
async def delete_sip(sip_id: str, current_user: dict = Depends(get_current_user)):
    if not PydanticObjectId.is_valid(sip_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    sip = await SIP.find_one(SIP.id == PydanticObjectId(sip_id), SIP.user_id == PydanticObjectId(current_user["_id"]))
    if sip:
        await sip.delete()
    return {"message": "SIP deleted"}


@router.get("/calculator")
async def sip_calculator(monthly_amount: float = Query(..., gt=0), years: int = Query(..., ge=1, le=50), expected_return: float = Query(12, ge=0, le=50)):
    months = years * 12
    r = expected_return / 100 / 12
    future_value = monthly_amount * (((1 + r) ** months - 1) / r) * (1 + r) if r > 0 else monthly_amount * months
    total_invested = monthly_amount * months
    wealth_gained = future_value - total_invested
    return {"monthly_amount": monthly_amount, "years": years, "expected_return": expected_return, "total_invested": round(total_invested, 0), "future_value": round(future_value, 0), "wealth_gained": round(wealth_gained, 0), "absolute_return_pct": round(wealth_gained / total_invested * 100, 1) if total_invested > 0 else 0}


@router.get("/lumpsum-vs-sip")
async def lumpsum_vs_sip(amount: float = Query(..., gt=0), years: int = Query(..., ge=1, le=50), expected_return: float = Query(12, ge=0, le=50)):
    r = expected_return / 100
    months = years * 12
    monthly_r = r / 12
    monthly_sip = amount / months
    lumpsum_value = amount * ((1 + r) ** years)
    sip_value = monthly_sip * (((1 + monthly_r) ** months - 1) / monthly_r) * (1 + monthly_r) if monthly_r > 0 else amount
    return {"total_investment": amount, "years": years, "expected_return": expected_return, "lumpsum": {"final_value": round(lumpsum_value, 0), "returns": round(lumpsum_value - amount, 0)}, "sip": {"monthly_amount": round(monthly_sip, 0), "final_value": round(sip_value, 0), "returns": round(sip_value - amount, 0)}, "better": "Lumpsum" if lumpsum_value > sip_value else "SIP", "difference": round(abs(lumpsum_value - sip_value), 0)}
