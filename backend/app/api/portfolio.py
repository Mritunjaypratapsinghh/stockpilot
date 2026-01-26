from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, date
from bson import ObjectId
from typing import List
from ..database import get_db
from ..api.auth import get_current_user
from ..models import HoldingCreate, HoldingUpdate
from ..services.price_service import get_bulk_prices

router = APIRouter()

# Sector mapping for NSE stocks
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

@router.get("")
@router.get("/")
async def get_portfolio_summary(current_user: dict = Depends(get_current_user)):
    db = get_db()
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    
    if not holdings:
        return {"total_investment": 0, "current_value": 0, "total_pnl": 0, "total_pnl_pct": 0, "day_pnl": 0, "day_pnl_pct": 0, "holdings_count": 0}
    
    stock_symbols = [h["symbol"] for h in holdings if h.get("holding_type") != "MF"]
    prices = await get_bulk_prices(stock_symbols) if stock_symbols else {}
    
    total_investment = 0
    current_value = 0
    day_pnl = 0
    
    for h in holdings:
        inv = h["quantity"] * h["avg_price"]
        total_investment += inv
        price_data = prices.get(h["symbol"], {})
        current_price = price_data.get("current_price") or h.get("current_price") or h["avg_price"]
        prev_close = price_data.get("previous_close") or current_price
        current_value += h["quantity"] * current_price
        day_pnl += (current_price - prev_close) * h["quantity"]
    
    total_pnl = current_value - total_investment
    total_pnl_pct = (total_pnl / total_investment * 100) if total_investment > 0 else 0
    day_pnl_pct = (day_pnl / (current_value - day_pnl) * 100) if (current_value - day_pnl) > 0 else 0
    
    return {
        "total_investment": round(total_investment, 2),
        "current_value": round(current_value, 2),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_pct": round(total_pnl_pct, 2),
        "day_pnl": round(day_pnl, 2),
        "day_pnl_pct": round(day_pnl_pct, 2),
        "holdings_count": len(holdings)
    }

@router.get("/holdings")
async def get_holdings(current_user: dict = Depends(get_current_user)):
    db = get_db()
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    
    # Only fetch prices for stocks (not MFs)
    stock_symbols = [h["symbol"] for h in holdings if h.get("holding_type") != "MF"]
    prices = await get_bulk_prices(stock_symbols) if stock_symbols else {}
    
    result = []
    for h in holdings:
        price_data = prices.get(h["symbol"], {})
        # Use live price if available, else stored current_price, else avg_price
        current_price = price_data.get("current_price") or h.get("current_price") or h["avg_price"]
        investment = h["quantity"] * h["avg_price"]
        current_val = h["quantity"] * current_price
        pnl = current_val - investment
        
        result.append({
            "_id": str(h["_id"]),
            "symbol": h["symbol"],
            "name": h.get("name", h["symbol"]),
            "holding_type": h.get("holding_type", "EQUITY"),
            "quantity": h["quantity"],
            "avg_price": h["avg_price"],
            "current_price": round(current_price, 2),
            "day_change_pct": price_data.get("day_change_pct", 0),
            "current_value": round(current_val, 2),
            "total_investment": round(investment, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round((pnl / investment * 100) if investment > 0 else 0, 2)
        })
    
    return result

@router.post("/holdings")
async def add_holding(holding: HoldingCreate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    existing = await db.holdings.find_one({"user_id": ObjectId(current_user["_id"]), "symbol": holding.symbol.upper()})
    if existing:
        raise HTTPException(status_code=400, detail="Holding already exists")
    
    doc = {
        "user_id": ObjectId(current_user["_id"]),
        "symbol": holding.symbol.upper(),
        "name": holding.name,
        "exchange": holding.exchange,
        "holding_type": holding.holding_type,
        "quantity": holding.quantity,
        "avg_price": holding.avg_price,
        "transactions": [],
        "created_at": datetime.utcnow()
    }
    result = await db.holdings.insert_one(doc)
    return {"_id": str(result.inserted_id), "symbol": doc["symbol"]}

@router.put("/holdings/{holding_id}")
async def update_holding(holding_id: str, update: HoldingUpdate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    update_doc = {"updated_at": datetime.utcnow()}
    if update.quantity is not None:
        update_doc["quantity"] = update.quantity
    if update.avg_price is not None:
        update_doc["avg_price"] = update.avg_price
    
    result = await db.holdings.update_one(
        {"_id": ObjectId(holding_id), "user_id": ObjectId(current_user["_id"])},
        {"$set": update_doc}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Holding not found")
    return {"message": "Updated"}

@router.delete("/holdings/{holding_id}")
async def delete_holding(holding_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    result = await db.holdings.delete_one({"_id": ObjectId(holding_id), "user_id": ObjectId(current_user["_id"])})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Holding not found")
    return {"message": "Deleted"}

@router.get("/performance")
async def get_portfolio_performance(current_user: dict = Depends(get_current_user)):
    db = get_db()
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    
    if not holdings:
        return {"total_investment": 0, "current_value": 0, "total_pnl": 0, "total_pnl_pct": 0, "day_pnl": 0, "day_pnl_pct": 0, "top_gainer": None, "top_loser": None}
    
    symbols = [h["symbol"] for h in holdings if h.get("holding_type") != "MF"]
    prices = await get_bulk_prices(symbols) if symbols else {}
    
    total_inv = 0
    current_val = 0
    day_pnl = 0
    performance = []
    
    for h in holdings:
        inv = h["quantity"] * h["avg_price"]
        total_inv += inv
        p = prices.get(h["symbol"], {})
        curr_price = p.get("current_price") or h["avg_price"]
        prev_close = p.get("previous_close") or curr_price
        val = h["quantity"] * curr_price
        current_val += val
        day_change = (curr_price - prev_close) * h["quantity"]
        day_pnl += day_change
        pnl_pct = ((val - inv) / inv * 100) if inv > 0 else 0
        performance.append({"symbol": h["symbol"], "pnl_pct": pnl_pct, "day_change_pct": p.get("day_change_pct", 0)})
    
    total_pnl = current_val - total_inv
    total_pnl_pct = (total_pnl / total_inv * 100) if total_inv > 0 else 0
    day_pnl_pct = (day_pnl / (current_val - day_pnl) * 100) if (current_val - day_pnl) > 0 else 0
    
    sorted_perf = sorted(performance, key=lambda x: x["day_change_pct"], reverse=True)
    top_gainer = sorted_perf[0] if sorted_perf and sorted_perf[0]["day_change_pct"] > 0 else None
    top_loser = sorted_perf[-1] if sorted_perf and sorted_perf[-1]["day_change_pct"] < 0 else None
    
    return {
        "total_investment": round(total_inv, 2),
        "current_value": round(current_val, 2),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_pct": round(total_pnl_pct, 2),
        "day_pnl": round(day_pnl, 2),
        "day_pnl_pct": round(day_pnl_pct, 2),
        "top_gainer": top_gainer,
        "top_loser": top_loser
    }

@router.get("/sectors")
async def get_sector_allocation(current_user: dict = Depends(get_current_user)):
    """Get portfolio allocation by sector"""
    db = get_db()
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    
    if not holdings:
        return {"sectors": [], "total_value": 0}
    
    symbols = [h["symbol"] for h in holdings if h.get("holding_type") != "MF"]
    prices = await get_bulk_prices(symbols) if symbols else {}
    
    sector_values = {}
    total_value = 0
    
    for h in holdings:
        p = prices.get(h["symbol"], {})
        curr_price = p.get("current_price") or h["avg_price"]
        value = h["quantity"] * curr_price
        total_value += value
        
        sector = SECTOR_MAP.get(h["symbol"], "Others")
        sector_values[sector] = sector_values.get(sector, 0) + value
    
    sectors = [
        {"sector": s, "value": round(v, 2), "percentage": round(v / total_value * 100, 1) if total_value > 0 else 0}
        for s, v in sorted(sector_values.items(), key=lambda x: x[1], reverse=True)
    ]
    
    return {"sectors": sectors, "total_value": round(total_value, 2)}

@router.get("/xirr")
async def get_portfolio_xirr(current_user: dict = Depends(get_current_user)):
    """Calculate XIRR (annualized returns) for portfolio"""
    db = get_db()
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    
    if not holdings:
        return {"xirr": 0, "message": "No holdings found"}
    
    symbols = [h["symbol"] for h in holdings if h.get("holding_type") != "MF"]
    prices = await get_bulk_prices(symbols) if symbols else {}
    
    # Collect all cashflows: negative for buys, positive for sells
    cashflows = []
    
    for h in holdings:
        for t in h.get("transactions", []):
            try:
                dt = datetime.fromisoformat(t["date"]) if isinstance(t["date"], str) else t["date"]
                amount = t["quantity"] * t["price"]
                if t["type"] == "BUY":
                    cashflows.append((dt, -amount))
                else:
                    cashflows.append((dt, amount))
            except:
                continue
    
    if not cashflows:
        return {"xirr": 0, "message": "No transactions with dates found"}
    
    # Add current portfolio value as final positive cashflow
    today = datetime.now()
    current_value = sum(
        h["quantity"] * (prices.get(h["symbol"], {}).get("current_price") or h["avg_price"])
        for h in holdings
    )
    cashflows.append((today, current_value))
    
    # Sort by date
    cashflows.sort(key=lambda x: x[0])
    
    # Calculate XIRR using Newton-Raphson
    def xnpv(rate, cashflows):
        t0 = cashflows[0][0]
        return sum(cf / ((1 + rate) ** ((dt - t0).days / 365)) for dt, cf in cashflows)
    
    def xirr_calc(cashflows, guess=0.1):
        rate = guess
        for _ in range(100):
            npv = xnpv(rate, cashflows)
            # Derivative approximation
            npv_deriv = (xnpv(rate + 0.0001, cashflows) - npv) / 0.0001
            if abs(npv_deriv) < 1e-10:
                break
            new_rate = rate - npv / npv_deriv
            if abs(new_rate - rate) < 1e-6:
                return new_rate
            rate = new_rate
        return rate
    
    try:
        xirr_value = xirr_calc(cashflows) * 100
        return {"xirr": round(xirr_value, 2), "cashflows_count": len(cashflows)}
    except:
        return {"xirr": 0, "message": "Could not calculate XIRR"}

@router.get("/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    """Single endpoint returning all portfolio data - reduces API calls"""
    db = get_db()
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    
    if not holdings:
        return {"holdings": [], "sectors": [], "xirr": None, "transactions": [], "summary": {"invested": 0, "current": 0, "pnl": 0, "pnl_pct": 0}}
    
    # Fetch prices once
    symbols = [h["symbol"] for h in holdings if h.get("holding_type") != "MF"]
    prices = await get_bulk_prices(symbols) if symbols else {}
    
    # Build holdings with prices
    holdings_list = []
    total_inv = 0
    total_val = 0
    sector_values = {}
    
    for h in holdings:
        p = prices.get(h["symbol"], {})
        curr_price = p.get("current_price") or h.get("current_price") or h["avg_price"]
        inv = h["quantity"] * h["avg_price"]
        val = h["quantity"] * curr_price
        pnl = val - inv
        total_inv += inv
        total_val += val
        
        sector = SECTOR_MAP.get(h["symbol"], "Others") if h.get("holding_type") != "MF" else h.get("name", h["symbol"])
        sector_values[sector] = sector_values.get(sector, 0) + val
        
        holdings_list.append({
            "_id": str(h["_id"]),
            "symbol": h["symbol"],
            "name": h.get("name", h["symbol"]),
            "holding_type": h.get("holding_type", "EQUITY"),
            "quantity": h["quantity"],
            "avg_price": h["avg_price"],
            "current_price": round(curr_price, 2),
            "day_change_pct": p.get("day_change_pct", 0),
            "current_value": round(val, 2),
            "total_investment": round(inv, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round((pnl / inv * 100) if inv > 0 else 0, 2),
            "sector": sector
        })
    
    # Sectors
    sectors = [{"sector": s, "value": round(v, 2), "percentage": round(v / total_val * 100, 1) if total_val > 0 else 0}
               for s, v in sorted(sector_values.items(), key=lambda x: x[1], reverse=True)]
    
    # Transactions
    txns = []
    for h in holdings:
        for t in h.get("transactions", []):
            txns.append({"symbol": h["symbol"], **t})
    txns.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    # XIRR (simplified)
    xirr_val = None
    if txns:
        try:
            from datetime import datetime as dt
            cashflows = []
            for t in txns:
                try:
                    d = dt.fromisoformat(t["date"]) if isinstance(t["date"], str) else t["date"]
                    amt = t["quantity"] * t["price"]
                    cashflows.append((d, -amt if t["type"] == "BUY" else amt))
                except:
                    pass
            if cashflows:
                cashflows.append((dt.now(), total_val))
                cashflows.sort(key=lambda x: x[0])
                # Simple XIRR approximation
                days = (cashflows[-1][0] - cashflows[0][0]).days
                if days > 0:
                    total_out = sum(-cf for _, cf in cashflows if cf < 0)
                    if total_out > 0:
                        xirr_val = round(((total_val / total_out) ** (365 / days) - 1) * 100, 2)
        except:
            pass
    
    return {
        "holdings": holdings_list,
        "sectors": sectors,
        "xirr": xirr_val,
        "transactions": txns[:50],
        "summary": {
            "invested": round(total_inv, 2),
            "current": round(total_val, 2),
            "pnl": round(total_val - total_inv, 2),
            "pnl_pct": round(((total_val - total_inv) / total_inv * 100) if total_inv > 0 else 0, 2)
        }
    }
