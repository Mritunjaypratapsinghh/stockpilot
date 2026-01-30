from fastapi import APIRouter, HTTPException, Depends
from datetime import date
from beanie import PydanticObjectId
from pydantic import BaseModel, Field
from typing import Optional

from ..models.documents import Dividend, Holding
from ..api.auth import get_current_user

router = APIRouter()


class DividendCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=30)
    amount: float = Field(..., gt=0)
    ex_date: date
    record_date: Optional[date] = None
    payment_date: Optional[date] = None


@router.get("")
@router.get("/")
async def get_dividends(current_user: dict = Depends(get_current_user)):
    dividends = await Dividend.find(Dividend.user_id == PydanticObjectId(current_user["_id"])).sort(-Dividend.ex_date).to_list()
    return [{"_id": str(d.id), "symbol": d.symbol, "amount": d.amount, "quantity": d.quantity, "total": d.total, "ex_date": d.ex_date} for d in dividends]


@router.get("/summary")
async def get_dividend_summary(current_user: dict = Depends(get_current_user)):
    user_id = PydanticObjectId(current_user["_id"])
    dividends = await Dividend.find(Dividend.user_id == user_id).to_list()
    holdings = await Holding.find(Holding.user_id == user_id).to_list()

    total_dividend = sum(d.amount * d.quantity for d in dividends)
    total_investment = sum(h.quantity * h.avg_price for h in holdings)

    by_year, by_symbol = {}, {}
    for d in dividends:
        year = d.ex_date[:4]
        by_year[year] = by_year.get(year, 0) + d.amount * d.quantity
        by_symbol[d.symbol] = by_symbol.get(d.symbol, 0) + d.amount * d.quantity

    return {
        "total_dividend": round(total_dividend, 2),
        "dividend_yield": round((total_dividend / total_investment * 100) if total_investment > 0 else 0, 2),
        "by_year": [{"year": y, "amount": round(a, 2)} for y, a in sorted(by_year.items(), reverse=True)],
        "by_symbol": [{"symbol": s, "amount": round(a, 2)} for s, a in sorted(by_symbol.items(), key=lambda x: x[1], reverse=True)[:10]]
    }


@router.post("/")
async def add_dividend(div: DividendCreate, current_user: dict = Depends(get_current_user)):
    user_id = PydanticObjectId(current_user["_id"])
    symbol = div.symbol.strip().upper()
    
    holding = await Holding.find_one(Holding.user_id == user_id, Holding.symbol == symbol)
    quantity = holding.quantity if holding else 0

    doc = Dividend(
        user_id=user_id,
        symbol=symbol,
        amount=div.amount,
        quantity=quantity,
        total=round(div.amount * quantity, 2),
        ex_date=div.ex_date.isoformat(),
        record_date=div.record_date.isoformat() if div.record_date else None,
        payment_date=div.payment_date.isoformat() if div.payment_date else None
    )
    await doc.insert()
    return {"_id": str(doc.id), "total": doc.total}


@router.delete("/{dividend_id}")
async def delete_dividend(dividend_id: str, current_user: dict = Depends(get_current_user)):
    if not PydanticObjectId.is_valid(dividend_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    div = await Dividend.find_one(Dividend.id == PydanticObjectId(dividend_id), Dividend.user_id == PydanticObjectId(current_user["_id"]))
    if not div:
        raise HTTPException(status_code=404, detail="Not found")
    await div.delete()
    return {"message": "Deleted"}
