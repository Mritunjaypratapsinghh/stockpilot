"""Finance routes - goals, SIP, tax, dividends, networth."""
from fastapi import APIRouter, HTTPException, Depends
from beanie import PydanticObjectId

from ....models.documents import Goal, SIP, Dividend
from ....core.security import get_current_user
from ....core.response_handler import StandardResponse
from ....services.portfolio import get_user_holdings, get_prices_for_holdings
from ....core.constants import TAX_RATES
from .schemas import GoalCreate, SIPCreate, AssetCreate, AssetUpdate, ImportHistory, GoalResponse, SIPResponse, TaxSummary, NetworthSummary

router = APIRouter()


@router.get("/goals", summary="Get goals", description="List all financial goals")
async def get_goals(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get all financial goals."""
    goals = await Goal.find(Goal.user_id == PydanticObjectId(current_user["_id"])).to_list()
    holdings = await get_user_holdings(current_user["_id"])
    portfolio_value = sum(h.quantity * h.avg_price for h in holdings) if holdings else 0
    return StandardResponse.ok({
        "goals": [GoalResponse(_id=str(g.id), name=g.name, target_amount=g.target_amount, current_amount=g.current_value,
                 target_date=g.target_date, progress=round(g.current_value / g.target_amount * 100, 1) if g.target_amount > 0 else 0) for g in goals],
        "portfolio_value": round(portfolio_value, 2)
    })


@router.post("/goals", summary="Create goal", description="Create a new financial goal")
async def create_goal(goal: GoalCreate, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Create a new financial goal."""
    doc = Goal(user_id=PydanticObjectId(current_user["_id"]), name=goal.name, target_amount=goal.target_amount,
               target_date=goal.target_date, current_value=goal.current_amount)
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
    """Get all SIP investments with actual performance from holdings."""
    sips = await SIP.find(SIP.user_id == PydanticObjectId(current_user["_id"])).to_list()
    holdings = await get_user_holdings(current_user["_id"])
    prices = await get_prices_for_holdings(holdings) if holdings else {}
    
    # Map holdings by symbol for quick lookup
    holdings_map = {h.symbol: h for h in holdings}
    
    sip_list = []
    total_invested = total_current = 0
    
    for s in sips:
        holding = holdings_map.get(s.symbol)
        if holding:
            curr_price = prices.get(s.symbol, {}).get("current_price") or holding.avg_price
            invested = holding.quantity * holding.avg_price
            current_val = holding.quantity * curr_price
            returns = current_val - invested
            returns_pct = (returns / invested * 100) if invested > 0 else 0
        else:
            invested = current_val = returns = returns_pct = 0
        
        total_invested += invested
        total_current += current_val
        
        sip_list.append({
            "_id": str(s.id),
            "symbol": s.symbol,
            "amount": s.amount,
            "frequency": s.frequency,
            "sip_date": s.sip_date,
            "is_active": s.is_active,
            "total_invested": round(invested, 2),
            "current_value": round(current_val, 2),
            "returns": round(returns, 2),
            "returns_pct": round(returns_pct, 2)
        })
    
    total_returns = total_current - total_invested
    return StandardResponse.ok({
        "sips": sip_list,
        "summary": {
            "total_invested": round(total_invested, 2),
            "current_value": round(total_current, 2),
            "total_returns": round(total_returns, 2),
            "returns_pct": round((total_returns / total_invested * 100) if total_invested > 0 else 0, 2)
        }
    })


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


@router.put("/sip/{sip_id}/toggle", summary="Toggle SIP", description="Enable or disable a SIP")
async def toggle_sip(sip_id: str, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Toggle SIP active status."""
    if not PydanticObjectId.is_valid(sip_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    sip = await SIP.find_one(SIP.id == PydanticObjectId(sip_id), SIP.user_id == PydanticObjectId(current_user["_id"]))
    if not sip:
        raise HTTPException(status_code=404, detail="SIP not found")
    sip.is_active = not sip.is_active
    await sip.save()
    return StandardResponse.ok({"is_active": sip.is_active})


@router.get("/sip/calculator", summary="SIP Calculator", description="Calculate SIP returns")
async def sip_calculator(monthly_amount: float, years: int, expected_return: float = 12) -> StandardResponse:
    """Calculate SIP future value."""
    months = years * 12
    r = expected_return / 100 / 12
    fv = monthly_amount * (((1 + r) ** months - 1) / r) * (1 + r)
    invested = monthly_amount * months
    return StandardResponse.ok({"total_invested": round(invested, 2), "future_value": round(fv, 2), "wealth_gained": round(fv - invested, 2)})


@router.get("/goals/projections", summary="Get goal projections", description="Get portfolio projections for goals")
async def get_goal_projections(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get goal projections."""
    holdings = await get_user_holdings(current_user["_id"])
    total = sum(h.quantity * h.avg_price for h in holdings) if holdings else 0
    return StandardResponse.ok({"current_value": round(total, 2), "projected_5y": round(total * 1.6, 2), "projected_10y": round(total * 2.6, 2)})


@router.get("/tax/harvest", summary="Get tax harvest opportunities", description="Find tax loss harvesting opportunities")
async def get_tax_harvest(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get tax loss harvesting opportunities."""
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok({"opportunities": [], "potential_savings": 0})
    
    prices = await get_prices_for_holdings(holdings)
    opportunities = []
    for h in holdings:
        curr_price = prices.get(h.symbol, {}).get("current_price") or h.avg_price
        loss = (h.avg_price - curr_price) * h.quantity
        if loss > 1000:
            opportunities.append({"symbol": h.symbol, "loss": round(loss, 2), "tax_saving": round(loss * 0.15, 2)})
    
    total_saving = sum(o["tax_saving"] for o in opportunities)
    return StandardResponse.ok({"opportunities": opportunities, "potential_savings": round(total_saving, 2)})


@router.get("/tax", summary="Get tax summary", description="Calculate LTCG and STCG tax liability")
async def get_tax_summary(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Calculate tax liability based on holding period."""
    from datetime import datetime, timedelta
    
    holdings = await get_user_holdings(current_user["_id"])
    now = datetime.now()
    fy_start = datetime(now.year if now.month >= 4 else now.year - 1, 4, 1)
    fy = f"{fy_start.year}-{fy_start.year + 1}"
    one_year_ago = now - timedelta(days=365)
    
    if not holdings:
        return StandardResponse.ok({
            "financial_year": fy,
            "realized": {"stcg": 0, "ltcg": 0},
            "unrealized": {"total": 0, "stcg": 0, "ltcg": 0},
            "tax_liability": {"stcg_tax": 0, "ltcg_tax": 0, "total_tax": 0}
        })

    prices = await get_prices_for_holdings(holdings)
    unrealized_ltcg = unrealized_stcg = 0

    for h in holdings:
        curr_price = prices.get(h.symbol, {}).get("current_price") or h.avg_price
        pnl = (curr_price - h.avg_price) * h.quantity
        
        if pnl > 0:
            # Check holding period from first transaction
            first_buy = None
            for t in h.transactions:
                if t.type == "BUY":
                    t_date = datetime.fromisoformat(t.date) if isinstance(t.date, str) else t.date
                    if first_buy is None or t_date < first_buy:
                        first_buy = t_date
            
            # If held > 1 year, it's LTCG, else STCG
            if first_buy and first_buy < one_year_ago:
                unrealized_ltcg += pnl
            else:
                unrealized_stcg += pnl

    # LTCG: 12.5% above 1.25L exemption, STCG: 20%
    ltcg_taxable = max(0, unrealized_ltcg - 125000)
    ltcg_tax = ltcg_taxable * 0.125
    stcg_tax = unrealized_stcg * 0.20

    return StandardResponse.ok({
        "financial_year": fy,
        "realized": {"stcg": 0, "ltcg": 0},
        "unrealized": {
            "total": round(unrealized_ltcg + unrealized_stcg, 2),
            "stcg": round(unrealized_stcg, 2),
            "ltcg": round(unrealized_ltcg, 2)
        },
        "tax_liability": {
            "stcg_tax": round(stcg_tax, 2),
            "ltcg_tax": round(ltcg_tax, 2),
            "total_tax": round(ltcg_tax + stcg_tax, 2)
        }
    })


@router.get("/dividends", summary="Get dividends", description="List dividend income")
async def get_dividends(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get dividend income history."""
    dividends = await Dividend.find(Dividend.user_id == PydanticObjectId(current_user["_id"])).sort(-Dividend.ex_date).limit(50).to_list()
    total = sum(d.amount for d in dividends)
    return StandardResponse.ok({"dividends": [{"id": str(d.id), "symbol": d.symbol, "amount": d.amount, "date": d.ex_date} for d in dividends], "total": round(total, 2), "expected_income": 0})


@router.get("/networth", summary="Get networth", description="Get total networth breakdown")
async def get_networth(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get total networth breakdown."""
    from ....models.documents import Asset
    
    holdings = await get_user_holdings(current_user["_id"])
    prices = await get_prices_for_holdings(holdings) if holdings else {}
    
    equity = mf = 0
    for h in holdings:
        curr_price = prices.get(h.symbol, {}).get("current_price") or h.avg_price
        value = h.quantity * curr_price
        if h.holding_type == "MF":
            mf += value
        else:
            equity += value
    
    # Get other assets
    assets = await Asset.find(Asset.user_id == PydanticObjectId(current_user["_id"])).to_list()
    
    assets_by_category = {}
    for asset in assets:
        category = asset.category
        assets_by_category[category] = assets_by_category.get(category, 0) + asset.value
    
    total = equity + mf + sum(assets_by_category.values())
    
    return StandardResponse.ok({
        "total": round(total, 2),
        "equity": round(equity, 2),
        "mf": round(mf, 2),
        "categories": {
            "Equity": round(equity, 2),
            "Mutual Funds": round(mf, 2),
            **{k: round(v, 2) for k, v in assets_by_category.items()}
        },
        "assets": [{"name": a.name, "category": a.category, "value": a.value, "id": str(a.id)} for a in assets]
    })


@router.get("/networth/history", summary="Get networth history")
async def get_networth_history(year: int, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get monthly networth history for a year."""
    from ....models.documents import NetworthHistory
    from datetime import datetime
    
    start = datetime(year, 1, 1)
    end = datetime(year, 12, 31, 23, 59, 59)
    
    history = await NetworthHistory.find(
        NetworthHistory.user_id == PydanticObjectId(current_user["_id"]),
        NetworthHistory.date >= start,
        NetworthHistory.date <= end
    ).sort("+date").to_list()
    
    # Get last snapshot of previous year's December for Jan comparison
    prev_dec = await NetworthHistory.find(
        NetworthHistory.user_id == PydanticObjectId(current_user["_id"]),
        NetworthHistory.date >= datetime(year - 1, 12, 1),
        NetworthHistory.date <= datetime(year - 1, 12, 31, 23, 59, 59)
    ).sort("-date").first_or_none()
    
    monthly = [None] * 12
    for h in history:
        month_idx = h.date.month - 1
        if monthly[month_idx] is None:  # Keep first snapshot of month
            monthly[month_idx] = {
                "month": h.date.month,
                "month_name": h.date.strftime("%b"),
                "value": h.value,
                "date": h.date.isoformat(),
                "breakdown": h.breakdown or {},
                "has_data": True,
                "change": 0,
                "change_pct": 0
            }
    
    # Fill missing months
    for i in range(12):
        if not monthly[i]:
            monthly[i] = {
                "month": i + 1,
                "month_name": datetime(year, i + 1, 1).strftime("%b"),
                "value": 0,
                "has_data": False,
                "change": 0,
                "change_pct": 0
            }
    
    # Calculate changes (Jan compares to prev Dec)
    if monthly[0]["has_data"] and prev_dec:
        prev = prev_dec.value
        curr = monthly[0]["value"]
        monthly[0]["change"] = curr - prev
        monthly[0]["change_pct"] = ((curr - prev) / prev * 100) if prev else 0
    
    for i in range(1, 12):
        if monthly[i]["has_data"] and monthly[i-1]["has_data"]:
            prev = monthly[i-1]["value"]
            curr = monthly[i]["value"]
            monthly[i]["change"] = curr - prev
            monthly[i]["change_pct"] = ((curr - prev) / prev * 100) if prev else 0
    
    # Calculate YTD and performance (use prev Dec as baseline if available)
    first_val = prev_dec.value if prev_dec else next((m["value"] for m in monthly if m["has_data"]), 0)
    last_val = next((m["value"] for m in reversed(monthly) if m["has_data"]), 0)
    last_month = next((m["month"] for m in reversed(monthly) if m["has_data"]), 1)
    ytd_growth = ((last_val - first_val) / first_val * 100) if first_val else 0
    annualized = (ytd_growth / last_month) * 12 if last_month else 0
    
    return StandardResponse.ok({
        "monthly": monthly,
        "ytd_growth": round(ytd_growth, 2),
        "annualized_growth": round(annualized, 2),
        "rating": "Excellent" if annualized >= 15 else "Good" if annualized >= 12 else "Average" if annualized >= 7 else "Poor",
        "performance": {
            "beating_inflation": annualized >= 6,
            "beating_fd": annualized >= 7,
            "beating_nifty": annualized >= 12,
            "good_growth": annualized >= 15
        }
    })


@router.post("/networth/snapshot", summary="Take networth snapshot")
async def take_networth_snapshot(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Take a snapshot of current networth."""
    from ....models.documents import NetworthHistory, Asset
    from datetime import datetime
    
    holdings = await get_user_holdings(current_user["_id"])
    prices = await get_prices_for_holdings(holdings) if holdings else {}
    
    equity = mf = 0
    for h in holdings:
        curr_price = prices.get(h.symbol, {}).get("current_price") or h.avg_price
        value = h.quantity * curr_price
        if h.holding_type == "MF":
            mf += value
        else:
            equity += value
    
    assets = await Asset.find(Asset.user_id == PydanticObjectId(current_user["_id"])).to_list()
    breakdown = {"Equity": equity, "Mutual Funds": mf}
    for a in assets:
        breakdown[a.category] = breakdown.get(a.category, 0) + a.value
    
    total = sum(breakdown.values())
    
    snapshot = NetworthHistory(
        user_id=PydanticObjectId(current_user["_id"]),
        date=datetime.now(),
        total=total,
        breakdown=breakdown
    )
    await snapshot.insert()
    
    return StandardResponse.ok({"message": "Snapshot saved", "total": round(total, 2)})


@router.post("/networth/import-history", summary="Import networth history")
async def import_networth_history(
    data: ImportHistory,
    current_user: dict = Depends(get_current_user)
) -> StandardResponse:
    """Import historical networth data."""
    from ....models.documents import NetworthHistory
    from datetime import datetime
    
    imported = 0
    for snap in data.snapshots:
        date = datetime.fromisoformat(snap.date)
        existing = await NetworthHistory.find_one(
            NetworthHistory.user_id == PydanticObjectId(current_user["_id"]),
            NetworthHistory.date >= datetime(date.year, date.month, date.day),
            NetworthHistory.date < datetime(date.year, date.month, date.day, 23, 59, 59)
        )
        
        if existing:
            existing.total = snap.total
            existing.breakdown = snap.breakdown
            await existing.save()
        else:
            history = NetworthHistory(
                user_id=PydanticObjectId(current_user["_id"]),
                date=date,
                total=snap.total,
                breakdown=snap.breakdown
            )
            await history.insert()
        imported += 1
    
    return StandardResponse.ok({"message": f"Imported {imported} snapshots"})


@router.post("/asset", summary="Add asset")
async def add_asset(
    data: AssetCreate,
    current_user: dict = Depends(get_current_user)
) -> StandardResponse:
    """Add a new asset."""
    from ....models.documents import Asset
    
    asset = Asset(
        user_id=PydanticObjectId(current_user["_id"]),
        name=data.name,
        category=data.category,
        value=data.value
    )
    await asset.insert()
    
    return StandardResponse.ok({"message": "Asset added", "id": str(asset.id)})


@router.put("/asset/{asset_id}", summary="Update asset")
async def update_asset(
    asset_id: str,
    data: AssetUpdate,
    current_user: dict = Depends(get_current_user)
) -> StandardResponse:
    """Update an asset."""
    from ....models.documents import Asset
    
    asset = await Asset.get(PydanticObjectId(asset_id))
    if not asset or str(asset.user_id) != current_user["_id"]:
        raise HTTPException(404, "Asset not found")
    
    asset.name = data.name
    asset.category = data.category
    asset.value = data.value
    await asset.save()
    
    return StandardResponse.ok({"message": "Asset updated"})


@router.delete("/asset/{asset_id}", summary="Delete asset")
async def delete_asset(
    asset_id: str,
    current_user: dict = Depends(get_current_user)
) -> StandardResponse:
    """Delete an asset."""
    from ....models.documents import Asset
    
    asset = await Asset.get(PydanticObjectId(asset_id))
    if not asset or str(asset.user_id) != current_user["_id"]:
        raise HTTPException(404, "Asset not found")
    
    await asset.delete()
    
    return StandardResponse.ok({"message": "Asset deleted"})
