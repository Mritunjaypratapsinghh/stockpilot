"""Finance routes - goals, SIP, tax, dividends, networth."""
from fastapi import APIRouter, HTTPException, Depends
from beanie import PydanticObjectId

from ....models.documents import Goal, SIP, Dividend
from ....core.security import get_current_user
from ....core.response_handler import StandardResponse
from ....services.portfolio import get_user_holdings, get_prices_for_holdings
from ....core.constants import TAX_RATES
from .schemas import GoalCreate, SIPCreate, GoalResponse, SIPResponse, TaxSummary, NetworthSummary

router = APIRouter()


@router.get("/goals", summary="Get goals", description="List all financial goals")
async def get_goals(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get all financial goals."""
    goals = await Goal.find(Goal.user_id == PydanticObjectId(current_user["_id"])).to_list()
    return StandardResponse.ok([GoalResponse(_id=str(g.id), name=g.name, target_amount=g.target_amount, current_amount=g.current_amount,
             target_date=g.target_date, progress=round(g.current_amount / g.target_amount * 100, 1) if g.target_amount > 0 else 0) for g in goals])


@router.post("/goals", summary="Create goal", description="Create a new financial goal")
async def create_goal(goal: GoalCreate, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Create a new financial goal."""
    doc = Goal(user_id=PydanticObjectId(current_user["_id"]), name=goal.name, target_amount=goal.target_amount,
               target_date=goal.target_date, current_amount=goal.current_amount)
    await doc.insert()
    return StandardResponse.ok({"id": str(doc.id), "name": doc.name}, "Goal created")


@router.delete("/goals/{goal_id}", summary="Delete goal", description="Delete a financial goal")
async def delete_goal(goal_id: str, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Delete a financial goal."""
    if not PydanticObjectId.is_valid(goal_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    goal = await Goal.find_one(Goal.id == PydanticObjectId(goal_id), Goal.user_id == PydanticObjectId(current_user["_id"]))
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    await goal.delete()
    return StandardResponse.ok(message="Goal deleted")


@router.get("/sip", summary="Get SIPs", description="List all SIP investments")
async def get_sips(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get all SIP investments."""
    sips = await SIP.find(SIP.user_id == PydanticObjectId(current_user["_id"])).to_list()
    return StandardResponse.ok([SIPResponse(_id=str(s.id), symbol=s.symbol, amount=s.amount, frequency=s.frequency, sip_date=s.sip_date, is_active=s.is_active) for s in sips])


@router.post("/sip", summary="Create SIP", description="Create a new SIP")
async def create_sip(sip: SIPCreate, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Create a new SIP."""
    doc = SIP(user_id=PydanticObjectId(current_user["_id"]), symbol=sip.symbol.upper(), amount=sip.amount, frequency=sip.frequency, sip_date=sip.sip_date)
    await doc.insert()
    return StandardResponse.ok({"id": str(doc.id), "symbol": doc.symbol}, "SIP created")


@router.delete("/sip/{sip_id}", summary="Delete SIP", description="Delete a SIP")
async def delete_sip(sip_id: str, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Delete a SIP."""
    if not PydanticObjectId.is_valid(sip_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    sip = await SIP.find_one(SIP.id == PydanticObjectId(sip_id), SIP.user_id == PydanticObjectId(current_user["_id"]))
    if not sip:
        raise HTTPException(status_code=404, detail="SIP not found")
    await sip.delete()
    return StandardResponse.ok(message="SIP deleted")


@router.get("/tax", summary="Get tax summary", description="Calculate LTCG and STCG tax liability")
async def get_tax_summary(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Calculate tax liability."""
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok(TaxSummary(ltcg=0, stcg=0, ltcg_taxable=0, ltcg_tax=0, stcg_tax=0, total_tax=0))

    prices = await get_prices_for_holdings(holdings)
    ltcg = stcg = 0

    for h in holdings:
        curr_price = prices.get(h.symbol, {}).get("current_price") or h.avg_price
        pnl = (curr_price - h.avg_price) * h.quantity
        if pnl > 0:
            ltcg += pnl

    ltcg_taxable = max(0, ltcg - TAX_RATES["LTCG_EXEMPTION"])
    ltcg_tax = ltcg_taxable * TAX_RATES["LTCG_RATE"]
    stcg_tax = stcg * TAX_RATES["STCG_RATE"]

    return StandardResponse.ok(TaxSummary(ltcg=round(ltcg, 2), stcg=round(stcg, 2), ltcg_taxable=round(ltcg_taxable, 2),
            ltcg_tax=round(ltcg_tax, 2), stcg_tax=round(stcg_tax, 2), total_tax=round(ltcg_tax + stcg_tax, 2)))


@router.get("/dividends", summary="Get dividends", description="List dividend income")
async def get_dividends(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get dividend income history."""
    dividends = await Dividend.find(Dividend.user_id == PydanticObjectId(current_user["_id"])).sort(-Dividend.date).limit(50).to_list()
    total = sum(d.amount for d in dividends)
    return StandardResponse.ok({"dividends": [{"id": str(d.id), "symbol": d.symbol, "amount": d.amount, "date": d.date} for d in dividends], "total": round(total, 2)})


@router.get("/networth", summary="Get networth", description="Get total networth breakdown")
async def get_networth(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get total networth breakdown."""
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok(NetworthSummary(total=0, equity=0, mf=0))

    prices = await get_prices_for_holdings(holdings)
    equity = mf = 0

    for h in holdings:
        curr_price = prices.get(h.symbol, {}).get("current_price") or h.avg_price
        value = h.quantity * curr_price
        if h.holding_type == "MF":
            mf += value
        else:
            equity += value

    return StandardResponse.ok(NetworthSummary(total=round(equity + mf, 2), equity=round(equity, 2), mf=round(mf, 2)))
