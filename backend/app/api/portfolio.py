from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from beanie import PydanticObjectId

from ..models.documents import Holding
from ..api.auth import get_current_user
from ..models import HoldingCreate, HoldingUpdate
from ..services.price_service import get_bulk_prices

router = APIRouter()

SECTOR_MAP = {
    "RELIANCE": "Oil & Gas", "ONGC": "Oil & Gas", "IOC": "Oil & Gas", "BPCL": "Oil & Gas", "GAIL": "Oil & Gas",
    "TCS": "IT", "INFY": "IT", "WIPRO": "IT", "HCLTECH": "IT", "TECHM": "IT", "LTI": "IT", "LTIM": "IT", "COFORGE": "IT", "MPHASIS": "IT", "PERSISTENT": "IT",
    "HDFCBANK": "Banking", "ICICIBANK": "Banking", "KOTAKBANK": "Banking", "AXISBANK": "Banking", "SBIN": "Banking", "INDUSINDBK": "Banking", "BANDHANBNK": "Banking", "FEDERALBNK": "Banking", "IDFCFIRSTB": "Banking", "PNB": "Banking",
    "HDFC": "Finance", "BAJFINANCE": "Finance", "BAJAJFINSV": "Finance", "SBILIFE": "Finance", "HDFCLIFE": "Finance", "ICICIPRULI": "Finance", "CHOLAFIN": "Finance", "M&MFIN": "Finance", "SHRIRAMFIN": "Finance",
    "SUNPHARMA": "Pharma", "DRREDDY": "Pharma", "CIPLA": "Pharma", "DIVISLAB": "Pharma", "APOLLOHOSP": "Pharma", "BIOCON": "Pharma", "LUPIN": "Pharma", "AUROPHARMA": "Pharma", "TORNTPHARM": "Pharma",
    "HINDUNILVR": "FMCG", "ITC": "FMCG", "NESTLEIND": "FMCG", "BRITANNIA": "FMCG", "DABUR": "FMCG", "MARICO": "FMCG", "COLPAL": "FMCG", "GODREJCP": "FMCG", "TATACONSUM": "FMCG",
    "TATAMOTORS": "Auto", "MARUTI": "Auto", "M&M": "Auto", "BAJAJ-AUTO": "Auto", "HEROMOTOCO": "Auto", "EICHERMOT": "Auto", "ASHOKLEY": "Auto", "TVSMOTOR": "Auto", "TATAMTRDVR": "Auto",
    "TATASTEEL": "Metals", "JSWSTEEL": "Metals", "HINDALCO": "Metals", "VEDL": "Metals", "COALINDIA": "Metals", "NMDC": "Metals", "SAIL": "Metals", "JINDALSTEL": "Metals",
    "LT": "Infrastructure", "ULTRACEMCO": "Infrastructure", "GRASIM": "Infrastructure", "ADANIPORTS": "Infrastructure", "ADANIENT": "Infrastructure", "DLF": "Infrastructure", "GODREJPROP": "Infrastructure",
    "POWERGRID": "Power", "NTPC": "Power", "TATAPOWER": "Power", "ADANIGREEN": "Power", "ADANIPOWER": "Power", "NHPC": "Power", "TORNTPOWER": "Power",
    "BHARTIARTL": "Telecom", "IDEA": "Telecom", "INDUSTOWER": "Telecom",
    "ASIANPAINT": "Paints", "BERGEPAINT": "Paints", "PIDILITIND": "Paints",
    "TITAN": "Consumer", "PAGEIND": "Consumer", "RELAXO": "Consumer", "BATAINDIA": "Consumer", "TRENT": "Consumer",
}


async def get_user_holdings(user_id: str):
    return await Holding.find(Holding.user_id == PydanticObjectId(user_id)).to_list()


async def get_prices_for_holdings(holdings):
    symbols = [h.symbol for h in holdings if h.holding_type != "MF"]
    return await get_bulk_prices(symbols) if symbols else {}


@router.get("")
@router.get("/")
async def get_portfolio_summary(current_user: dict = Depends(get_current_user)):
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return {"total_investment": 0, "current_value": 0, "total_pnl": 0, "total_pnl_pct": 0, "day_pnl": 0, "day_pnl_pct": 0, "holdings_count": 0}

    prices = await get_prices_for_holdings(holdings)
    total_investment = current_value = day_pnl = 0

    for h in holdings:
        inv = h.quantity * h.avg_price
        total_investment += inv
        p = prices.get(h.symbol, {})
        curr_price = p.get("current_price") or h.current_price or h.avg_price
        prev_close = p.get("previous_close") or curr_price
        current_value += h.quantity * curr_price
        day_pnl += (curr_price - prev_close) * h.quantity

    total_pnl = current_value - total_investment
    return {
        "total_investment": round(total_investment, 2), "current_value": round(current_value, 2),
        "total_pnl": round(total_pnl, 2), "total_pnl_pct": round((total_pnl / total_investment * 100) if total_investment > 0 else 0, 2),
        "day_pnl": round(day_pnl, 2), "day_pnl_pct": round((day_pnl / (current_value - day_pnl) * 100) if (current_value - day_pnl) > 0 else 0, 2),
        "holdings_count": len(holdings)
    }


@router.get("/holdings")
async def get_holdings(current_user: dict = Depends(get_current_user)):
    holdings = await get_user_holdings(current_user["_id"])
    prices = await get_prices_for_holdings(holdings)

    result = []
    for h in holdings:
        p = prices.get(h.symbol, {})
        curr_price = p.get("current_price") or h.current_price or h.avg_price
        inv = h.quantity * h.avg_price
        val = h.quantity * curr_price
        pnl = val - inv
        result.append({
            "_id": str(h.id), "symbol": h.symbol, "name": h.name, "holding_type": h.holding_type,
            "quantity": h.quantity, "avg_price": h.avg_price, "current_price": round(curr_price, 2),
            "day_change_pct": p.get("day_change_pct", 0), "current_value": round(val, 2),
            "total_investment": round(inv, 2), "pnl": round(pnl, 2),
            "pnl_pct": round((pnl / inv * 100) if inv > 0 else 0, 2)
        })
    return result


@router.post("/holdings")
async def add_holding(holding: HoldingCreate, current_user: dict = Depends(get_current_user)):
    user_id = PydanticObjectId(current_user["_id"])
    symbol = holding.symbol.upper()
    existing = await Holding.find_one(Holding.user_id == user_id, Holding.symbol == symbol)
    if existing:
        raise HTTPException(status_code=400, detail="Holding already exists")

    doc = Holding(
        user_id=user_id, symbol=symbol, name=holding.name, exchange=holding.exchange,
        holding_type=holding.holding_type, quantity=holding.quantity, avg_price=holding.avg_price
    )
    await doc.insert()
    return {"_id": str(doc.id), "symbol": symbol}


@router.put("/holdings/{holding_id}")
async def update_holding(holding_id: str, update: HoldingUpdate, current_user: dict = Depends(get_current_user)):
    if not PydanticObjectId.is_valid(holding_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    h = await Holding.find_one(Holding.id == PydanticObjectId(holding_id), Holding.user_id == PydanticObjectId(current_user["_id"]))
    if not h:
        raise HTTPException(status_code=404, detail="Holding not found")

    if update.quantity is not None:
        h.quantity = update.quantity
    if update.avg_price is not None:
        h.avg_price = update.avg_price
    await h.save()
    return {"message": "Updated"}


@router.delete("/holdings/{holding_id}")
async def delete_holding(holding_id: str, current_user: dict = Depends(get_current_user)):
    if not PydanticObjectId.is_valid(holding_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    h = await Holding.find_one(Holding.id == PydanticObjectId(holding_id), Holding.user_id == PydanticObjectId(current_user["_id"]))
    if not h:
        raise HTTPException(status_code=404, detail="Holding not found")
    await h.delete()
    return {"message": "Deleted"}


@router.get("/performance")
async def get_portfolio_performance(current_user: dict = Depends(get_current_user)):
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return {"total_investment": 0, "current_value": 0, "total_pnl": 0, "total_pnl_pct": 0, "day_pnl": 0, "day_pnl_pct": 0, "top_gainer": None, "top_loser": None}

    prices = await get_prices_for_holdings(holdings)
    total_inv = current_val = day_pnl = 0
    performance = []

    for h in holdings:
        inv = h.quantity * h.avg_price
        total_inv += inv
        p = prices.get(h.symbol, {})
        curr_price = p.get("current_price") or h.avg_price
        prev_close = p.get("previous_close") or curr_price
        val = h.quantity * curr_price
        current_val += val
        day_pnl += (curr_price - prev_close) * h.quantity
        performance.append({"symbol": h.symbol, "pnl_pct": ((val - inv) / inv * 100) if inv > 0 else 0, "day_change_pct": p.get("day_change_pct", 0)})

    total_pnl = current_val - total_inv
    sorted_perf = sorted(performance, key=lambda x: x["day_change_pct"], reverse=True)
    return {
        "total_investment": round(total_inv, 2), "current_value": round(current_val, 2),
        "total_pnl": round(total_pnl, 2), "total_pnl_pct": round((total_pnl / total_inv * 100) if total_inv > 0 else 0, 2),
        "day_pnl": round(day_pnl, 2), "day_pnl_pct": round((day_pnl / (current_val - day_pnl) * 100) if (current_val - day_pnl) > 0 else 0, 2),
        "top_gainer": sorted_perf[0] if sorted_perf and sorted_perf[0]["day_change_pct"] > 0 else None,
        "top_loser": sorted_perf[-1] if sorted_perf and sorted_perf[-1]["day_change_pct"] < 0 else None
    }


@router.get("/sectors")
async def get_sector_allocation(current_user: dict = Depends(get_current_user)):
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return {"sectors": [], "total_value": 0}

    prices = await get_prices_for_holdings(holdings)
    sector_values = {}
    total_value = 0

    for h in holdings:
        curr_price = prices.get(h.symbol, {}).get("current_price") or h.avg_price
        value = h.quantity * curr_price
        total_value += value
        sector = SECTOR_MAP.get(h.symbol, "Others")
        sector_values[sector] = sector_values.get(sector, 0) + value

    sectors = [{"sector": s, "value": round(v, 2), "percentage": round(v / total_value * 100, 1) if total_value > 0 else 0}
               for s, v in sorted(sector_values.items(), key=lambda x: x[1], reverse=True)]
    return {"sectors": sectors, "total_value": round(total_value, 2)}


@router.get("/xirr")
async def get_portfolio_xirr(current_user: dict = Depends(get_current_user)):
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return {"xirr": 0, "message": "No holdings found"}

    prices = await get_prices_for_holdings(holdings)
    cashflows = []

    for h in holdings:
        for t in h.transactions:
            try:
                dt = datetime.fromisoformat(t.date) if isinstance(t.date, str) else t.date
                amount = t.quantity * t.price
                cashflows.append((dt, -amount if t.type == "BUY" else amount))
            except:
                continue

    if not cashflows:
        return {"xirr": 0, "message": "No transactions with dates found"}

    today = datetime.now()
    current_value = sum(h.quantity * (prices.get(h.symbol, {}).get("current_price") or h.avg_price) for h in holdings)
    cashflows.append((today, current_value))
    cashflows.sort(key=lambda x: x[0])

    def xnpv(rate, cfs):
        t0 = cfs[0][0]
        return sum(cf / ((1 + rate) ** ((dt - t0).days / 365)) for dt, cf in cfs)

    rate = 0.1
    for _ in range(100):
        npv = xnpv(rate, cashflows)
        npv_deriv = (xnpv(rate + 0.0001, cashflows) - npv) / 0.0001
        if abs(npv_deriv) < 1e-10:
            break
        new_rate = max(-0.99, min(rate - npv / npv_deriv, 10))
        if abs(new_rate - rate) < 1e-6:
            rate = new_rate
            break
        rate = new_rate

    xirr_value = rate * 100
    if abs(xirr_value) > 1000:
        return {"xirr": 0, "message": "XIRR calculation did not converge"}
    return {"xirr": round(xirr_value, 2), "cashflows_count": len(cashflows)}


@router.get("/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return {"holdings": [], "sectors": [], "xirr": None, "transactions": [], "summary": {"invested": 0, "current": 0, "pnl": 0, "pnl_pct": 0}}

    prices = await get_prices_for_holdings(holdings)
    holdings_list = []
    total_inv = total_val = 0
    sector_values = {}
    txns = []

    for h in holdings:
        p = prices.get(h.symbol, {})
        curr_price = p.get("current_price") or h.current_price or h.avg_price
        inv = h.quantity * h.avg_price
        val = h.quantity * curr_price
        pnl = val - inv
        total_inv += inv
        total_val += val

        sector = SECTOR_MAP.get(h.symbol, "Others") if h.holding_type != "MF" else h.name
        sector_values[sector] = sector_values.get(sector, 0) + val

        holdings_list.append({
            "_id": str(h.id), "symbol": h.symbol, "name": h.name, "holding_type": h.holding_type,
            "quantity": h.quantity, "avg_price": h.avg_price, "current_price": round(curr_price, 2),
            "day_change_pct": p.get("day_change_pct", 0), "current_value": round(val, 2),
            "total_investment": round(inv, 2), "pnl": round(pnl, 2),
            "pnl_pct": round((pnl / inv * 100) if inv > 0 else 0, 2), "sector": sector
        })

        for i, t in enumerate(h.transactions):
            txns.append({"symbol": h.symbol, "holding_id": str(h.id), "index": i, **t.model_dump()})

    txns.sort(key=lambda x: x.get("date", ""), reverse=True)
    sectors = [{"sector": s, "value": round(v, 2), "percentage": round(v / total_val * 100, 1) if total_val > 0 else 0}
               for s, v in sorted(sector_values.items(), key=lambda x: x[1], reverse=True)]

    # Simple XIRR
    xirr_val = None
    if txns:
        try:
            cashflows = []
            for t in txns:
                d = datetime.fromisoformat(t["date"])
                amt = t["quantity"] * t["price"]
                cashflows.append((d, -amt if t["type"] == "BUY" else amt))
            if cashflows:
                cashflows.append((datetime.now(), total_val))
                cashflows.sort(key=lambda x: x[0])
                days = (cashflows[-1][0] - cashflows[0][0]).days
                if days > 7:
                    total_out = sum(-cf for _, cf in cashflows if cf < 0)
                    if total_out > 0:
                        ratio = total_val / total_out
                        if 0.01 < ratio < 100:
                            xirr_val = round(((ratio) ** (365 / days) - 1) * 100, 2)
        except:
            pass

    return {
        "holdings": holdings_list, "sectors": sectors, "xirr": xirr_val, "transactions": txns[:50],
        "summary": {"invested": round(total_inv, 2), "current": round(total_val, 2),
                    "pnl": round(total_val - total_inv, 2),
                    "pnl_pct": round(((total_val - total_inv) / total_inv * 100) if total_inv > 0 else 0, 2)}
    }
