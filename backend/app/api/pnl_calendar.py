from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from beanie import PydanticObjectId

from ..models.documents import Holding
from ..models.documents.portfolio_snapshot import PortfolioSnapshot
from ..api.auth import get_current_user

router = APIRouter()


@router.get("/daily")
async def get_daily_pnl(year: int = None, month: int = None, current_user: dict = Depends(get_current_user)):
    user_id = PydanticObjectId(current_user["_id"])
    now = datetime.now(timezone.utc)
    year = year or now.year
    month = month or now.month

    start_date = datetime(year, month, 1, tzinfo=timezone.utc)
    end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc) if month < 12 else datetime(year + 1, 1, 1, tzinfo=timezone.utc)

    snapshots = await PortfolioSnapshot.find(PortfolioSnapshot.user_id == user_id, PortfolioSnapshot.date >= start_date, PortfolioSnapshot.date < end_date).to_list()

    calendar = {}
    prev_value = None
    for snap in sorted(snapshots, key=lambda x: x.date):
        date_str = snap.date.strftime("%Y-%m-%d") if isinstance(snap.date, datetime) else snap.date
        value = snap.value or 0
        pnl = value - prev_value if prev_value is not None else 0
        pnl_pct = (pnl / prev_value * 100) if prev_value and prev_value > 0 else 0
        calendar[date_str] = {"value": round(value, 2), "pnl": round(pnl, 2), "pnl_pct": round(pnl_pct, 2)}
        prev_value = value

    return {"year": year, "month": month, "calendar": calendar, "monthly_pnl": round(sum(d.get("pnl", 0) for d in calendar.values()), 2), "trading_days": len(calendar)}


@router.get("/monthly")
async def get_monthly_pnl(year: int = None, current_user: dict = Depends(get_current_user)):
    user_id = PydanticObjectId(current_user["_id"])
    year = year or datetime.now(timezone.utc).year

    monthly = []
    for month in range(1, 13):
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc) if month < 12 else datetime(year + 1, 1, 1, tzinfo=timezone.utc)

        first = await PortfolioSnapshot.find_one(PortfolioSnapshot.user_id == user_id, PortfolioSnapshot.date >= start, PortfolioSnapshot.date < end)
        last = await PortfolioSnapshot.find(PortfolioSnapshot.user_id == user_id, PortfolioSnapshot.date >= start, PortfolioSnapshot.date < end).sort(-PortfolioSnapshot.date).first_or_none()

        pnl = pnl_pct = 0
        if first and last:
            start_val = first.value or 0
            end_val = last.value or 0
            pnl = end_val - start_val
            pnl_pct = (pnl / start_val * 100) if start_val > 0 else 0

        monthly.append({"month": month, "month_name": datetime(year, month, 1).strftime("%b"), "pnl": round(pnl, 2), "pnl_pct": round(pnl_pct, 2)})

    return {"year": year, "monthly": monthly, "yearly_pnl": round(sum(m["pnl"] for m in monthly), 2)}


@router.get("/dividends")
async def get_dividend_calendar(year: int = None, current_user: dict = Depends(get_current_user)):
    holdings = await Holding.find(Holding.user_id == PydanticObjectId(current_user["_id"])).to_list()
    year = year or datetime.now(timezone.utc).year

    dividends = []
    for h in holdings:
        if h.holding_type != "MF":
            for q in [3, 6, 9, 12]:
                dividends.append({"symbol": h.symbol, "date": f"{year}-{q:02d}-15", "amount": round(h.quantity * 2.5, 2), "type": "dividend"})

    return {"year": year, "dividends": sorted(dividends, key=lambda x: x["date"]), "total_expected": round(sum(d["amount"] for d in dividends), 2)}
