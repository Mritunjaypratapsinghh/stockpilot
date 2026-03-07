"""Finance routes - goals, SIP, tax, dividends, networth."""

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException

from ....core.response_handler import StandardResponse
from ....core.security import get_current_user
from ....models.documents import SIP, Goal, Holding
from ....services.portfolio import get_prices_for_holdings, get_user_holdings
from .schemas import (
    AssetCreate,
    AssetUpdate,
    GoalCreate,
    ImportHistory,
    SIPCreate,
)

router = APIRouter()


@router.get("/goals", summary="Get goals", description="List all financial goals")
async def get_goals(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get all financial goals with SIP calculations."""
    from datetime import datetime

    goals = await Goal.find(Goal.user_id == PydanticObjectId(current_user["_id"])).to_list()
    holdings = await get_user_holdings(current_user["_id"])
    portfolio_value = sum(h.quantity * h.avg_price for h in holdings) if holdings else 0

    result = []
    for g in goals:
        target = g.target_amount
        current = g.current_value
        progress = (current / target * 100) if target > 0 else 0

        target_date = datetime.fromisoformat(g.target_date) if isinstance(g.target_date, str) else g.target_date
        months_left = max(0, (target_date.year - datetime.now().year) * 12 + (target_date.month - datetime.now().month))

        remaining = target - current
        if months_left > 0 and remaining > 0:
            r = 0.12 / 12  # 12% annual return
            required_sip = remaining * r / ((1 + r) ** months_left - 1)
        else:
            required_sip = remaining if remaining > 0 else 0

        result.append(
            {
                "_id": str(g.id),
                "name": g.name,
                "category": g.category if hasattr(g, "category") else "general",
                "target_amount": target,
                "current_value": current,
                "progress": round(progress, 1),
                "target_date": g.target_date,
                "months_left": months_left,
                "monthly_sip": g.monthly_sip if hasattr(g, "monthly_sip") else 0,
                "required_sip": round(required_sip, 0),
                "on_track": (
                    (g.monthly_sip if hasattr(g, "monthly_sip") else 0) >= required_sip if required_sip > 0 else True
                ),
            }
        )

    return StandardResponse.ok({"goals": result, "portfolio_value": round(portfolio_value, 2)})


@router.post("/goals", summary="Create goal", description="Create a new financial goal")
async def create_goal(goal: GoalCreate, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Create a new financial goal."""
    doc = Goal(
        user_id=PydanticObjectId(current_user["_id"]),
        name=goal.name,
        target_amount=goal.target_amount,
        target_date=goal.target_date,
        current_value=goal.current_amount,
    )
    await doc.insert()
    return StandardResponse.ok({"id": str(doc.id), "name": doc.name}, "Goal created")


@router.delete("/goals/{goal_id}", summary="Delete goal", description="Delete a financial goal")
async def delete_goal(goal_id: str, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Delete a financial goal."""
    if not PydanticObjectId.is_valid(goal_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    goal = await Goal.find_one(
        Goal.id == PydanticObjectId(goal_id), Goal.user_id == PydanticObjectId(current_user["_id"])
    )
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    await goal.delete()
    return StandardResponse.ok(message="Goal deleted")


@router.get("/sip", summary="Get SIPs", description="List all SIP investments")
async def get_sips(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get all SIP investments with actual performance from holdings."""
    from ....services.market.price_service import get_bulk_mf_nav, get_bulk_prices

    sips = await SIP.find(SIP.user_id == PydanticObjectId(current_user["_id"])).to_list()
    if not sips:
        return StandardResponse.ok(
            {"sips": [], "summary": {"total_invested": 0, "current_value": 0, "total_returns": 0, "returns_pct": 0}}
        )

    # Only fetch holdings for SIP symbols
    sip_symbols = list({s.symbol for s in sips})
    holdings = await Holding.find(
        Holding.user_id == PydanticObjectId(current_user["_id"]), {"symbol": {"$in": sip_symbols}}
    ).to_list()

    # Map holdings by symbol for quick lookup
    holdings_map = {h.symbol: h for h in holdings}

    # Separate MF and stock symbols
    mf_symbols = [sym for sym in sip_symbols if holdings_map.get(sym) and holdings_map[sym].holding_type == "MF"]
    stock_symbols = [sym for sym in sip_symbols if holdings_map.get(sym) and holdings_map[sym].holding_type != "MF"]

    # Fetch prices in parallel
    import asyncio

    mf_nav_task = get_bulk_mf_nav(mf_symbols) if mf_symbols else asyncio.coroutine(lambda: {})()
    stock_prices_task = get_bulk_prices(stock_symbols) if stock_symbols else asyncio.coroutine(lambda: {})()
    mf_navs, stock_prices = await asyncio.gather(mf_nav_task, stock_prices_task)

    sip_list = []
    total_invested = total_current = 0

    for s in sips:
        holding = holdings_map.get(s.symbol)
        if holding:
            # For MFs use NAV, for stocks use live price
            if holding.holding_type == "MF":
                curr_price = mf_navs.get(s.symbol, {}).get("nav") or holding.current_price or holding.avg_price
            else:
                curr_price = (
                    stock_prices.get(s.symbol, {}).get("current_price") or holding.current_price or holding.avg_price
                )
            invested = holding.quantity * holding.avg_price
            current_val = holding.quantity * curr_price
            returns = current_val - invested
            returns_pct = (returns / invested * 100) if invested > 0 else 0
        else:
            invested = current_val = returns = returns_pct = 0

        total_invested += invested
        total_current += current_val

        sip_list.append(
            {
                "_id": str(s.id),
                "symbol": s.symbol,
                "amount": s.amount,
                "frequency": s.frequency,
                "sip_date": s.sip_date,
                "is_active": s.is_active,
                "total_invested": round(invested, 2),
                "current_value": round(current_val, 2),
                "returns": round(returns, 2),
                "returns_pct": round(returns_pct, 2),
            }
        )

    total_returns = total_current - total_invested
    return StandardResponse.ok(
        {
            "sips": sip_list,
            "summary": {
                "total_invested": round(total_invested, 2),
                "current_value": round(total_current, 2),
                "total_returns": round(total_returns, 2),
                "returns_pct": round((total_returns / total_invested * 100) if total_invested > 0 else 0, 2),
            },
        }
    )


@router.post("/sip", summary="Create SIP", description="Create a new SIP")
async def create_sip(sip: SIPCreate, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Create a new SIP."""
    from datetime import date

    doc = SIP(
        user_id=PydanticObjectId(current_user["_id"]),
        symbol=sip.symbol.upper(),
        amount=sip.amount,
        frequency=sip.frequency,
        sip_date=sip.sip_date,
        start_date=sip.start_date or date.today().isoformat(),
    )
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
    return StandardResponse.ok(
        {"total_invested": round(invested, 2), "future_value": round(fv, 2), "wealth_gained": round(fv - invested, 2)}
    )


@router.get("/goals/projections", summary="Get goal projections", description="Get portfolio projections for goals")
async def get_goal_projections(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get portfolio projections with conservative, moderate, and aggressive scenarios."""
    holdings = await get_user_holdings(current_user["_id"])
    prices = (await get_prices_for_holdings(holdings) if holdings else {}) or {}
    current_value = (
        sum(
            h.quantity * (prices.get(h.symbol, {}).get("current_price") or h.current_price or h.avg_price)
            for h in holdings
        )
        if holdings
        else 0
    )

    # Conservative: 8%, Moderate: 12%, Aggressive: 15% annual returns
    projections = [
        {
            "years": y,
            "conservative": round(current_value * (1.08**y), 0),
            "moderate": round(current_value * (1.12**y), 0),
            "aggressive": round(current_value * (1.15**y), 0),
        }
        for y in [1, 3, 5, 10]
    ]

    return StandardResponse.ok({"current_value": round(current_value, 0), "projections": projections})


@router.get(
    "/tax/harvest", summary="Get tax harvest opportunities", description="Find tax loss harvesting opportunities"
)
async def get_tax_harvest(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get tax loss harvesting opportunities."""
    from datetime import datetime, timedelta

    from ....services.cache import cache_get, cache_set

    cache_key = f"tax_harvest:{current_user['_id']}"
    cached = await cache_get(cache_key)
    if cached:
        return StandardResponse.ok(cached)

    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok({"losses": [], "gains": [], "stcg": {}, "ltcg": {}, "note": ""})

    prices = await get_prices_for_holdings(holdings) or {}
    losses = []
    gains = []
    one_year_ago = datetime.now() - timedelta(days=365)
    LTCG_RATE = 0.125
    STCG_RATE = 0.20

    stcg_total = stcl_total = ltcg_total = ltcl_total = 0

    for h in holdings:
        if h.quantity <= 0:
            continue

        curr_price = prices.get(h.symbol, {}).get("current_price") or h.current_price or h.avg_price
        pnl = (curr_price - h.avg_price) * h.quantity
        pnl_pct = ((curr_price - h.avg_price) / h.avg_price * 100) if h.avg_price > 0 else 0

        first_buy = None
        for t in h.transactions:
            if t.type == "BUY":
                t_date = datetime.fromisoformat(t.date) if isinstance(t.date, str) else t.date
                if first_buy is None or t_date < first_buy:
                    first_buy = t_date

        is_lt = first_buy and first_buy < one_year_ago
        entry = {
            "symbol": h.symbol,
            "quantity": h.quantity,
            "avg_price": h.avg_price,
            "current_price": round(curr_price, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 1),
            "type": "LTCG" if is_lt else "STCG",
        }

        if pnl < 0:
            entry["tax_saved"] = round(abs(pnl) * (LTCG_RATE if is_lt else STCG_RATE), 2)
            losses.append(entry)
            if is_lt:
                ltcl_total += abs(pnl)
            else:
                stcl_total += abs(pnl)
        elif pnl > 0:
            entry["tax_due"] = round(pnl * (LTCG_RATE if is_lt else STCG_RATE), 2)
            gains.append(entry)
            if is_lt:
                ltcg_total += pnl
            else:
                stcg_total += pnl

    losses.sort(key=lambda x: x["pnl"])
    gains.sort(key=lambda x: -x["pnl"])

    stcg_net = stcg_total - stcl_total
    ltcg_net = ltcg_total - ltcl_total

    result = {
        "losses": losses[:10],
        "gains": gains[:10],
        "stcg": {
            "gains": round(stcg_total, 2),
            "losses": round(stcl_total, 2),
            "net": round(stcg_net, 2),
            "tax": round(max(0, stcg_net) * STCG_RATE, 2),
        },
        "ltcg": {
            "gains": round(ltcg_total, 2),
            "losses": round(ltcl_total, 2),
            "net": round(ltcg_net, 2),
            "tax": round(max(0, ltcg_net - 125000) * LTCG_RATE, 2),
            "exemption": 125000,
        },
        "total_harvestable_loss": round(stcl_total + ltcl_total, 2),
        "potential_tax_saved": round(stcl_total * STCG_RATE + ltcl_total * LTCG_RATE, 2),
        "note": (
            "Sell loss-making stocks before March 31 to offset gains. "
            "STCL offsets STCG (20%), LTCL offsets LTCG (12.5%). "
            "Avoid wash sale - wait 30 days before rebuying."
        ),
    }
    await cache_set(cache_key, result, ttl=300)
    return StandardResponse.ok(result)


@router.get("/tax", summary="Get tax summary", description="Calculate LTCG and STCG tax liability")
async def get_tax_summary(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Calculate tax liability based on holding period."""
    from datetime import datetime, timedelta

    from ....services.cache import cache_get, cache_set

    cache_key = f"tax_summary:{current_user['_id']}"
    cached = await cache_get(cache_key)
    if cached:
        return StandardResponse.ok(cached)

    holdings = await get_user_holdings(current_user["_id"])
    now = datetime.now()
    fy_start = datetime(now.year if now.month >= 4 else now.year - 1, 4, 1)
    fy = f"{fy_start.year}-{fy_start.year + 1}"
    one_year_ago = now - timedelta(days=365)

    if not holdings:
        return StandardResponse.ok(
            {
                "financial_year": fy,
                "realized": {"stcg": 0, "ltcg": 0},
                "unrealized": {"total": 0, "stcg": 0, "ltcg": 0},
                "tax_liability": {"stcg_tax": 0, "ltcg_tax": 0, "total_tax": 0},
            }
        )

    prices = await get_prices_for_holdings(holdings) or {}
    unrealized_ltcg = unrealized_stcg = 0

    for h in holdings:
        curr_price = prices.get(h.symbol, {}).get("current_price") or h.current_price or h.avg_price
        pnl = (curr_price - h.avg_price) * h.quantity

        # Check holding period from first transaction
        first_buy = None
        for t in h.transactions:
            if t.type == "BUY":
                t_date = datetime.fromisoformat(t.date) if isinstance(t.date, str) else t.date
                if first_buy is None or t_date < first_buy:
                    first_buy = t_date

        # If held > 1 year, it's LTCG, else STCG (includes both gains and losses)
        if first_buy and first_buy < one_year_ago:
            unrealized_ltcg += pnl
        else:
            unrealized_stcg += pnl

    # LTCG: 12.5% above 1.25L exemption, STCG: 20%
    ltcg_exemption = 125000
    ltcg_taxable = max(0, unrealized_ltcg - ltcg_exemption)
    ltcg_tax = ltcg_taxable * 0.125
    stcg_tax = max(0, unrealized_stcg) * 0.20  # Only tax on gains, not losses

    result = {
        "financial_year": fy,
        "realized": {"stcg": 0, "ltcg": 0, "total": 0},
        "unrealized": {
            "stcg": round(unrealized_stcg, 2),
            "ltcg": round(unrealized_ltcg, 2),
            "total": round(unrealized_ltcg + unrealized_stcg, 2),
        },
        "tax_liability": {
            "ltcg_exemption": ltcg_exemption,
            "taxable_ltcg": round(ltcg_taxable, 2),
            "ltcg_tax": round(ltcg_tax, 2),
            "stcg_tax": round(stcg_tax, 2),
            "total_tax": round(ltcg_tax + stcg_tax, 2),
        },
        "transactions": [],
    }
    await cache_set(cache_key, result, ttl=300)
    return StandardResponse.ok(result)


@router.get("/dividends", summary="Get dividends", description="List dividend income from holdings")
async def get_dividends(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get dividend income based on holdings and Yahoo dividend data."""
    from datetime import datetime

    import httpx

    holdings = await Holding.find(Holding.user_id == PydanticObjectId(current_user["_id"])).to_list()
    if not holdings:
        return StandardResponse.ok({"dividends": [], "upcoming": [], "total": 0, "expected_income": 0})

    holdings_map = {h.symbol: h for h in holdings if h.holding_type != "MF"}
    past_dividends = []
    upcoming_dividends = []
    past_income = 0
    upcoming_income = 0
    now = datetime.now()

    async with httpx.AsyncClient(timeout=10) as client:
        for symbol, holding in list(holdings_map.items())[:10]:
            try:
                resp = await client.get(
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS?interval=1d&range=1y&events=div",
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if resp.status_code == 200:
                    events = resp.json().get("chart", {}).get("result", [{}])[0].get("events", {})
                    for ts, div in events.get("dividends", {}).items():
                        div_date = datetime.fromtimestamp(int(ts))
                        amount = div.get("amount", 0)
                        income = amount * holding.quantity
                        dividend = {
                            "symbol": symbol,
                            "date": div_date.strftime("%Y-%m-%d"),
                            "value": amount,
                            "quantity": holding.quantity,
                            "expected_income": round(income, 2),
                        }
                        if div_date > now:
                            upcoming_dividends.append(dividend)
                            upcoming_income += income
                        else:
                            past_dividends.append(dividend)
                            past_income += income
            except Exception:
                pass

    past_dividends.sort(key=lambda x: x["date"], reverse=True)
    upcoming_dividends.sort(key=lambda x: x["date"])

    return StandardResponse.ok(
        {
            "dividends": past_dividends[:20],
            "upcoming": upcoming_dividends,
            "total": len(past_dividends),
            "expected_income": round(upcoming_income, 2),
            "past_income": round(past_income, 2),
        }
    )


@router.get("/networth", summary="Get networth", description="Get total networth breakdown")
async def get_networth(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get total networth breakdown."""
    from ....models.documents import Asset

    holdings = await get_user_holdings(current_user["_id"])
    prices = (await get_prices_for_holdings(holdings) if holdings else {}) or {}

    equity = mf = 0
    for h in holdings:
        curr_price = prices.get(h.symbol, {}).get("current_price") or h.current_price or h.avg_price
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

    categories = {"Equity": equity, "Mutual Funds": mf, **assets_by_category}
    allocation = {k: round(v / total * 100, 1) if total > 0 else 0 for k, v in categories.items()}

    return StandardResponse.ok(
        {
            "total": round(total, 2),
            "equity": round(equity, 2),
            "mf": round(mf, 2),
            "categories": {k: round(v, 2) for k, v in categories.items()},
            "allocation": allocation,
            "assets": [{"name": a.name, "category": a.category, "value": a.value, "id": str(a.id)} for a in assets],
        }
    )


@router.get("/networth/history", summary="Get networth history")
async def get_networth_history(year: int, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get monthly networth history for a year."""
    from datetime import datetime

    from ....models.documents import NetworthHistory

    start = datetime(year, 1, 1)
    end = datetime(year, 12, 31, 23, 59, 59)

    history = (
        await NetworthHistory.find(
            NetworthHistory.user_id == PydanticObjectId(current_user["_id"]),
            NetworthHistory.date >= start,
            NetworthHistory.date <= end,
        )
        .sort("+date")
        .to_list()
    )

    # Get last snapshot of previous year's December for Jan comparison
    prev_dec = (
        await NetworthHistory.find(
            NetworthHistory.user_id == PydanticObjectId(current_user["_id"]),
            NetworthHistory.date >= datetime(year - 1, 12, 1),
            NetworthHistory.date <= datetime(year - 1, 12, 31, 23, 59, 59),
        )
        .sort("-date")
        .first_or_none()
    )

    monthly = [None] * 12
    for h in history:
        month_idx = h.date.month - 1
        # Keep first snapshot of month
        if monthly[month_idx] is None:
            monthly[month_idx] = {
                "month": h.date.month,
                "month_name": h.date.strftime("%b"),
                "value": h.value,
                "date": h.date.isoformat(),
                "breakdown": h.breakdown or {},
                "has_data": True,
                "change": 0,
                "change_pct": 0,
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
                "change_pct": 0,
            }

    # Calculate changes (Jan compares to prev Dec)
    if monthly[0]["has_data"] and prev_dec:
        prev = prev_dec.value
        curr = monthly[0]["value"]
        monthly[0]["change"] = curr - prev
        monthly[0]["change_pct"] = ((curr - prev) / prev * 100) if prev else 0

    for i in range(1, 12):
        if monthly[i]["has_data"] and monthly[i - 1]["has_data"]:
            prev = monthly[i - 1]["value"]
            curr = monthly[i]["value"]
            monthly[i]["change"] = curr - prev
            monthly[i]["change_pct"] = ((curr - prev) / prev * 100) if prev else 0

    # Calculate YTD and performance (use prev Dec as baseline if available)
    first_val = prev_dec.value if prev_dec else next((m["value"] for m in monthly if m["has_data"]), 0)
    last_val = next((m["value"] for m in reversed(monthly) if m["has_data"]), 0)
    last_month = next((m["month"] for m in reversed(monthly) if m["has_data"]), 1)
    ytd_growth = ((last_val - first_val) / first_val * 100) if first_val else 0
    annualized = (ytd_growth / last_month) * 12 if last_month else 0

    return StandardResponse.ok(
        {
            "monthly": monthly,
            "ytd_growth": round(ytd_growth, 2),
            "annualized_growth": round(annualized, 2),
            "rating": (
                "Excellent"
                if annualized >= 15
                else "Good" if annualized >= 12 else "Average" if annualized >= 7 else "Poor"
            ),
            "performance": {
                "beating_inflation": annualized >= 6,
                "beating_fd": annualized >= 7,
                "beating_nifty": annualized >= 12,
                "good_growth": annualized >= 15,
            },
        }
    )


@router.post("/networth/snapshot", summary="Take networth snapshot")
async def take_networth_snapshot(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Take a snapshot of current networth."""
    from datetime import datetime

    from ....models.documents import Asset, NetworthHistory

    holdings = await get_user_holdings(current_user["_id"])
    prices = (await get_prices_for_holdings(holdings) if holdings else {}) or {}

    equity = mf = 0
    for h in holdings:
        curr_price = prices.get(h.symbol, {}).get("current_price") or h.current_price or h.avg_price
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
        user_id=PydanticObjectId(current_user["_id"]), date=datetime.now(), value=total, breakdown=breakdown
    )
    await snapshot.insert()

    return StandardResponse.ok({"message": "Snapshot saved", "total": round(total, 2)})


@router.post("/networth/import-history", summary="Import networth history")
async def import_networth_history(
    data: ImportHistory, current_user: dict = Depends(get_current_user)
) -> StandardResponse:
    """Import historical networth data."""
    from datetime import datetime

    from ....models.documents import NetworthHistory

    imported = 0
    for snap in data.snapshots:
        date = datetime.fromisoformat(snap.date)
        existing = await NetworthHistory.find_one(
            NetworthHistory.user_id == PydanticObjectId(current_user["_id"]),
            NetworthHistory.date >= datetime(date.year, date.month, date.day),
            NetworthHistory.date < datetime(date.year, date.month, date.day, 23, 59, 59),
        )

        if existing:
            existing.value = snap.total
            existing.breakdown = snap.breakdown
            await existing.save()
        else:
            history = NetworthHistory(
                user_id=PydanticObjectId(current_user["_id"]), date=date, value=snap.total, breakdown=snap.breakdown
            )
            await history.insert()
        imported += 1

    return StandardResponse.ok({"message": f"Imported {imported} snapshots"})


@router.post("/asset", summary="Add asset")
async def add_asset(data: AssetCreate, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Add a new asset."""
    from ....models.documents import Asset

    asset = Asset(
        user_id=PydanticObjectId(current_user["_id"]), name=data.name, category=data.category, value=data.value
    )
    await asset.insert()

    return StandardResponse.ok({"message": "Asset added", "id": str(asset.id)})


@router.put("/asset/{asset_id}", summary="Update asset")
async def update_asset(
    asset_id: str, data: AssetUpdate, current_user: dict = Depends(get_current_user)
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
async def delete_asset(asset_id: str, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Delete an asset."""
    from ....models.documents import Asset

    asset = await Asset.get(PydanticObjectId(asset_id))
    if not asset or str(asset.user_id) != current_user["_id"]:
        raise HTTPException(404, "Asset not found")

    await asset.delete()

    return StandardResponse.ok({"message": "Asset deleted"})


@router.get("/tax/export", summary="Export tax report to Excel")
async def export_tax_report(current_user: dict = Depends(get_current_user)):
    """Export tax report as Excel file for CA/ITR filing."""
    import io
    from datetime import datetime, timedelta

    from fastapi.responses import StreamingResponse

    holdings = await get_user_holdings(current_user["_id"])
    now = datetime.now()
    fy_start = datetime(now.year if now.month >= 4 else now.year - 1, 4, 1)
    fy = f"FY{fy_start.year}-{fy_start.year + 1}"
    one_year_ago = now - timedelta(days=365)

    prices = (await get_prices_for_holdings(holdings) if holdings else {}) or {}

    # Build CSV content
    lines = [
        f"Tax Report - {fy}",
        f"Generated: {now.strftime('%Y-%m-%d %H:%M')}",
        "",
        "HOLDINGS SUMMARY",
        "Symbol,Quantity,Avg Price,Current Price,Invested,Current Value,P&L,P&L %,Holding Type,Tax Type",
    ]

    total_stcg = total_ltcg = 0
    for h in holdings:
        curr_price = prices.get(h.symbol, {}).get("current_price") or h.current_price or h.avg_price
        invested = h.quantity * h.avg_price
        current_val = h.quantity * curr_price
        pnl = current_val - invested
        pnl_pct = (pnl / invested * 100) if invested > 0 else 0

        first_buy = None
        for t in h.transactions:
            if t.type == "BUY":
                t_date = datetime.fromisoformat(t.date) if isinstance(t.date, str) else t.date
                if first_buy is None or t_date < first_buy:
                    first_buy = t_date

        tax_type = "LTCG" if first_buy and first_buy < one_year_ago else "STCG"
        if tax_type == "LTCG":
            total_ltcg += pnl
        else:
            total_stcg += pnl

        lines.append(
            f"{h.symbol},{h.quantity},{h.avg_price:.2f},{curr_price:.2f},{invested:.2f},{current_val:.2f},{pnl:.2f},{pnl_pct:.1f}%,{h.holding_type},{tax_type}"
        )

    # Tax calculation
    ltcg_exemption = 125000
    ltcg_taxable = max(0, total_ltcg - ltcg_exemption)
    ltcg_tax = ltcg_taxable * 0.125
    stcg_tax = max(0, total_stcg) * 0.20

    lines.extend(
        [
            "",
            "TAX CALCULATION",
            f"Total STCG (Short Term),{total_stcg:.2f}",
            f"STCG Tax @ 20%,{stcg_tax:.2f}",
            f"Total LTCG (Long Term),{total_ltcg:.2f}",
            f"Less: Exemption u/s 112A,{ltcg_exemption}",
            f"Taxable LTCG,{ltcg_taxable:.2f}",
            f"LTCG Tax @ 12.5%,{ltcg_tax:.2f}",
            f"Total Tax Liability,{ltcg_tax + stcg_tax:.2f}",
        ]
    )

    content = "\n".join(lines)
    buffer = io.BytesIO(content.encode("utf-8"))
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=tax_report_{fy}.csv"},
    )


@router.get("/tax/advance", summary="Get advance tax schedule")
async def get_advance_tax_schedule(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get advance tax payment schedule and reminders."""
    from datetime import datetime

    now = datetime.now()
    fy_start = datetime(now.year if now.month >= 4 else now.year - 1, 4, 1)

    # Advance tax due dates
    schedule = [
        {"due_date": f"{fy_start.year}-06-15", "percent": 15, "label": "Q1 - 15th June"},
        {"due_date": f"{fy_start.year}-09-15", "percent": 45, "label": "Q2 - 15th September"},
        {"due_date": f"{fy_start.year}-12-15", "percent": 75, "label": "Q3 - 15th December"},
        {"due_date": f"{fy_start.year + 1}-03-15", "percent": 100, "label": "Q4 - 15th March"},
    ]

    # Get estimated tax
    tax_data = await get_tax_summary(current_user)
    total_tax = tax_data.data.get("tax_liability", {}).get("total_tax", 0) if hasattr(tax_data, "data") else 0

    for s in schedule:
        due = datetime.strptime(s["due_date"], "%Y-%m-%d")
        s["amount_due"] = round(total_tax * s["percent"] / 100, 2)
        s["is_past"] = now > due
        s["is_upcoming"] = not s["is_past"] and (due - now).days <= 30

    next_due = next((s for s in schedule if not s["is_past"]), None)

    return StandardResponse.ok(
        {
            "financial_year": f"{fy_start.year}-{fy_start.year + 1}",
            "estimated_tax": total_tax,
            "schedule": schedule,
            "next_due": next_due,
            "note": "Advance tax applies if total tax liability exceeds ₹10,000 in a financial year.",
        }
    )


@router.get("/tax/dividend-income", summary="Get dividend income for tax")
async def get_dividend_tax(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get dividend income summary for tax purposes (taxable at slab rate)."""
    from datetime import datetime

    import httpx

    holdings = await Holding.find(Holding.user_id == PydanticObjectId(current_user["_id"])).to_list()
    now = datetime.now()
    fy_start = datetime(now.year if now.month >= 4 else now.year - 1, 4, 1)

    if not holdings:
        return StandardResponse.ok({"dividends": [], "total_income": 0, "tax_note": ""})

    holdings_map = {h.symbol: h for h in holdings if h.holding_type != "MF"}
    dividends = []
    total_income = 0

    async with httpx.AsyncClient(timeout=10) as client:
        for symbol, holding in list(holdings_map.items())[:15]:
            try:
                resp = await client.get(
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS?interval=1d&range=1y&events=div",
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if resp.status_code == 200:
                    events = resp.json().get("chart", {}).get("result", [{}])[0].get("events", {})
                    for ts, div in events.get("dividends", {}).items():
                        div_date = datetime.fromtimestamp(int(ts))
                        if div_date >= fy_start and div_date <= now:
                            amount = div.get("amount", 0)
                            income = amount * holding.quantity
                            dividends.append(
                                {
                                    "symbol": symbol,
                                    "date": div_date.strftime("%Y-%m-%d"),
                                    "per_share": amount,
                                    "quantity": holding.quantity,
                                    "income": round(income, 2),
                                }
                            )
                            total_income += income
            except Exception:
                pass

    dividends.sort(key=lambda x: x["date"], reverse=True)

    return StandardResponse.ok(
        {
            "financial_year": f"{fy_start.year}-{fy_start.year + 1}",
            "dividends": dividends,
            "total_income": round(total_income, 2),
            "tax_note": (
                "Dividend income is taxable at your income tax slab rate."
                " TDS of 10% applies if dividend exceeds ₹5,000 from a company."
            ),
        }
    )
