"""Portfolio routes - holdings, transactions, import, MF health."""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from beanie import PydanticObjectId
from typing import List
import csv
import io

from ....models.documents import Holding
from ....models.documents.holding import EmbeddedTransaction
from ....core.security import get_current_user
from ....core.response_handler import StandardResponse
from ....services.portfolio import get_user_holdings, get_prices_for_holdings
from ....core.constants import SECTOR_MAP
from .schemas import HoldingCreate, HoldingUpdate, TransactionCreate, HoldingResponse, PortfolioSummary, SectorAllocation, ImportResult

router = APIRouter()


@router.get("", summary="Get portfolio summary", description="Get total investment, current value, and P&L")
@router.get("/")
async def get_portfolio_summary(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get portfolio summary with total investment, current value, and P&L."""
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok(PortfolioSummary(total_investment=0, current_value=0, total_pnl=0, total_pnl_pct=0, day_pnl=0, day_pnl_pct=0, holdings_count=0))

    prices = await get_prices_for_holdings(holdings)
    total_investment = current_value = day_pnl = 0.0

    for h in holdings:
        inv = h.quantity * h.avg_price
        total_investment += inv
        p = prices.get(h.symbol, {})
        curr_price = p.get("current_price") or h.current_price or h.avg_price
        prev_close = p.get("previous_close") or curr_price
        current_value += h.quantity * curr_price
        day_pnl += (curr_price - prev_close) * h.quantity

    total_pnl = current_value - total_investment
    return StandardResponse.ok(PortfolioSummary(
        total_investment=round(total_investment, 2), current_value=round(current_value, 2),
        total_pnl=round(total_pnl, 2), total_pnl_pct=round((total_pnl / total_investment * 100) if total_investment > 0 else 0, 2),
        day_pnl=round(day_pnl, 2), day_pnl_pct=round((day_pnl / (current_value - day_pnl) * 100) if (current_value - day_pnl) > 0 else 0, 2),
        holdings_count=len(holdings)
    ))


@router.get("/holdings", summary="Get all holdings", description="List all stock and MF holdings with current prices")
async def get_holdings(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get all holdings with current prices and P&L."""
    holdings = await get_user_holdings(current_user["_id"])
    prices = await get_prices_for_holdings(holdings)

    result: List[HoldingResponse] = []
    for h in holdings:
        p = prices.get(h.symbol, {})
        curr_price = p.get("current_price") or h.current_price or h.avg_price
        inv = h.quantity * h.avg_price
        val = h.quantity * curr_price
        pnl = val - inv
        result.append(HoldingResponse(
            _id=str(h.id), symbol=h.symbol, name=h.name, holding_type=h.holding_type,
            quantity=h.quantity, avg_price=h.avg_price, current_price=round(curr_price, 2),
            day_change_pct=p.get("day_change_pct", 0), current_value=round(val, 2),
            total_investment=round(inv, 2), pnl=round(pnl, 2),
            pnl_pct=round((pnl / inv * 100) if inv > 0 else 0, 2)
        ))
    return StandardResponse.ok(result)


@router.post("/holdings", summary="Add holding", description="Add a new stock or MF holding")
async def add_holding(holding: HoldingCreate, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Add a new holding to portfolio."""
    user_id = PydanticObjectId(current_user["_id"])
    existing = await Holding.find_one(Holding.user_id == user_id, Holding.symbol == holding.symbol)
    if existing:
        raise HTTPException(status_code=400, detail="Holding already exists")

    doc = Holding(user_id=user_id, symbol=holding.symbol, name=holding.name, exchange=holding.exchange,
                  holding_type=holding.holding_type, quantity=holding.quantity, avg_price=holding.avg_price)
    await doc.insert()
    return StandardResponse.ok({"id": str(doc.id), "symbol": holding.symbol}, "Holding added")


@router.put("/holdings/{holding_id}", summary="Update holding", description="Update quantity or average price")
async def update_holding(holding_id: str, update: HoldingUpdate, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Update holding quantity or average price."""
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
    return StandardResponse.ok(message="Holding updated")


@router.delete("/holdings/{holding_id}", summary="Delete holding", description="Remove a holding from portfolio")
async def delete_holding(holding_id: str, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Delete a holding from portfolio."""
    if not PydanticObjectId.is_valid(holding_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    h = await Holding.find_one(Holding.id == PydanticObjectId(holding_id), Holding.user_id == PydanticObjectId(current_user["_id"]))
    if not h:
        raise HTTPException(status_code=404, detail="Holding not found")
    await h.delete()
    return StandardResponse.ok(message="Holding deleted")


@router.get("/sectors", summary="Get sector allocation", description="Get portfolio breakdown by sector")
async def get_sector_allocation(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get portfolio sector allocation breakdown."""
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok({"sectors": [], "total_value": 0})

    prices = await get_prices_for_holdings(holdings)
    sector_values: dict[str, float] = {}
    total_value = 0.0

    for h in holdings:
        curr_price = prices.get(h.symbol, {}).get("current_price") or h.avg_price
        value = h.quantity * curr_price
        total_value += value
        sector = SECTOR_MAP.get(h.symbol, "Others")
        sector_values[sector] = sector_values.get(sector, 0) + value

    sectors = [SectorAllocation(sector=s, value=round(v, 2), percentage=round(v / total_value * 100, 1) if total_value > 0 else 0)
               for s, v in sorted(sector_values.items(), key=lambda x: x[1], reverse=True)]
    return StandardResponse.ok({"sectors": sectors, "total_value": round(total_value, 2)})


@router.get("/dashboard", summary="Get dashboard data", description="Get complete portfolio dashboard with holdings, sectors, and transactions")
async def get_dashboard(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get complete dashboard with holdings, sectors, and recent transactions."""
    holdings = await get_user_holdings(current_user["_id"])
    if not holdings:
        return StandardResponse.ok({"holdings": [], "sectors": [], "xirr": None, "transactions": [], "summary": {"invested": 0, "current": 0, "pnl": 0, "pnl_pct": 0}})

    prices = await get_prices_for_holdings(holdings)
    holdings_list: list = []
    txns: list = []
    total_inv = total_val = 0.0
    sector_values: dict[str, float] = {}

    for h in holdings:
        p = prices.get(h.symbol, {})
        curr_price = p.get("current_price") or h.current_price or h.avg_price
        inv = h.quantity * h.avg_price
        val = h.quantity * curr_price
        total_inv += inv
        total_val += val
        sector = SECTOR_MAP.get(h.symbol, "Others") if h.holding_type != "MF" else h.name
        sector_values[sector] = sector_values.get(sector, 0) + val

        holdings_list.append({
            "_id": str(h.id), "symbol": h.symbol, "name": h.name, "holding_type": h.holding_type,
            "quantity": h.quantity, "avg_price": h.avg_price, "current_price": round(curr_price, 2),
            "day_change_pct": p.get("day_change_pct", 0), "current_value": round(val, 2),
            "total_investment": round(inv, 2), "pnl": round(val - inv, 2),
            "pnl_pct": round(((val - inv) / inv * 100) if inv > 0 else 0, 2), "sector": sector
        })
        for i, t in enumerate(h.transactions):
            txns.append({"symbol": h.symbol, "holding_id": str(h.id), "index": i, **t.model_dump()})

    txns.sort(key=lambda x: x.get("date", ""), reverse=True)
    sectors = [{"sector": s, "value": round(v, 2), "percentage": round(v / total_val * 100, 1) if total_val > 0 else 0}
               for s, v in sorted(sector_values.items(), key=lambda x: x[1], reverse=True)]

    return StandardResponse.ok({
        "holdings": holdings_list, "sectors": sectors, "xirr": None, "transactions": txns[:50],
        "summary": {"invested": round(total_inv, 2), "current": round(total_val, 2),
                    "pnl": round(total_val - total_inv, 2),
                    "pnl_pct": round(((total_val - total_inv) / total_inv * 100) if total_inv > 0 else 0, 2)}
    })


@router.get("/transactions", summary="Get transactions", description="List all buy/sell transactions")
async def get_transactions(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get all transactions across holdings."""
    holdings = await Holding.find(Holding.user_id == PydanticObjectId(current_user["_id"])).to_list()
    txns: list = []
    for h in holdings:
        for i, t in enumerate(h.transactions):
            txns.append({"symbol": h.symbol, "holding_id": str(h.id), "index": i, **t.model_dump()})
    return StandardResponse.ok(sorted(txns, key=lambda x: x.get("date", ""), reverse=True))


@router.post("/transactions", summary="Add transaction", description="Record a buy or sell transaction")
async def add_transaction(txn: TransactionCreate, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Add a buy or sell transaction."""
    user_id = PydanticObjectId(current_user["_id"])
    quantity = txn.quantity or (round(txn.amount / txn.price, 4) if txn.amount else None)
    if not quantity:
        raise HTTPException(status_code=400, detail="Provide quantity or amount")

    holding = await Holding.find_one(Holding.user_id == user_id, Holding.symbol == txn.symbol)
    txn_doc = EmbeddedTransaction(type=txn.type, quantity=quantity, price=txn.price, date=txn.date.isoformat(), notes=txn.notes)

    if not holding:
        if txn.type == "SELL":
            raise HTTPException(status_code=400, detail="Cannot sell - no holding found")
        holding = Holding(user_id=user_id, symbol=txn.symbol, name=txn.symbol, exchange="NSE",
                          holding_type=txn.holding_type, quantity=quantity, avg_price=txn.price, transactions=[txn_doc])
        await holding.insert()
        return StandardResponse.ok({"holding_id": str(holding.id)}, "Holding created")

    old_qty, old_avg = holding.quantity, holding.avg_price
    if txn.type == "BUY":
        new_qty = old_qty + quantity
        new_avg = ((old_qty * old_avg) + (quantity * txn.price)) / new_qty
    else:
        if quantity > old_qty:
            raise HTTPException(status_code=400, detail="Cannot sell more than held")
        new_qty = old_qty - quantity
        new_avg = old_avg

    if new_qty == 0:
        await holding.delete()
        return StandardResponse.ok(message="Holding sold completely")

    holding.quantity = new_qty
    holding.avg_price = round(new_avg, 2)
    holding.transactions.append(txn_doc)
    await holding.save()
    return StandardResponse.ok({"new_quantity": new_qty, "new_avg_price": round(new_avg, 2)}, "Transaction added")


@router.delete("/transactions/{holding_id}/{index}")
async def delete_transaction(holding_id: str, index: int, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Delete a transaction by index."""
    if not PydanticObjectId.is_valid(holding_id) or index < 0:
        raise HTTPException(status_code=400, detail="Invalid ID or index")

    holding = await Holding.find_one(Holding.id == PydanticObjectId(holding_id), Holding.user_id == PydanticObjectId(current_user["_id"]))
    if not holding or index >= len(holding.transactions):
        raise HTTPException(status_code=404, detail="Transaction not found")

    holding.transactions.pop(index)
    if holding.transactions:
        qty, cost = 0.0, 0.0
        for t in holding.transactions:
            if t.type == "BUY":
                cost += t.quantity * t.price
                qty += t.quantity
            else:
                qty -= t.quantity
        holding.avg_price = round(cost / qty, 2) if qty > 0 else holding.avg_price
        holding.quantity = qty if qty > 0 else holding.quantity
    await holding.save()
    return StandardResponse.ok(message="Transaction deleted")


@router.post("/import", summary="Import holdings", description="Import holdings from CSV file (Zerodha, Groww)")
async def import_holdings(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Import holdings from broker CSV file."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files supported")

    text = (await file.read()).decode("utf-8")
    try:
        rows = list(csv.DictReader(io.StringIO(text)))
    except csv.Error as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {e}")

    if not rows:
        raise HTTPException(status_code=400, detail="Empty CSV")

    headers = [h.lower() for h in rows[0].keys()]
    broker = "zerodha" if "trade_type" in headers else "groww" if "avg cost" in headers else "unknown"
    if broker == "unknown":
        raise HTTPException(status_code=400, detail="Unsupported format")

    user_id = PydanticObjectId(current_user["_id"])
    imported = skipped = 0

    for row in rows:
        try:
            if broker == "zerodha":
                symbol = row.get("symbol", "").split("-")[0].strip().upper()
                qty = float(row.get("quantity", 0))
                price = float(row.get("price", 0))
            else:
                symbol = str(list(row.values())[0]).split()[0].upper()
                qty = float(str(row.get("qty", row.get("quantity", 0))).replace(",", ""))
                price = float(str(row.get("avg cost", row.get("avg_price", 0))).replace(",", ""))

            if not symbol or qty <= 0:
                skipped += 1
                continue

            existing = await Holding.find_one(Holding.user_id == user_id, Holding.symbol == symbol)
            if existing:
                skipped += 1
                continue

            await Holding(user_id=user_id, symbol=symbol, name=symbol, quantity=qty, avg_price=price).insert()
            imported += 1
        except (ValueError, KeyError):
            skipped += 1

    return StandardResponse.ok(ImportResult(broker=broker, imported=imported, skipped=skipped))


def categorize_mf(name: str) -> tuple[str, int]:
    """Categorize mutual fund by name and return expected benchmark return."""
    name = name.upper()
    if any(x in name for x in ["LIQUID", "OVERNIGHT"]):
        return "Liquid", 6
    if any(x in name for x in ["DEBT", "BOND"]):
        return "Debt", 7
    if "SMALL" in name:
        return "Small Cap", 15
    if "MID" in name:
        return "Mid Cap", 14
    if any(x in name for x in ["LARGE", "BLUECHIP"]):
        return "Large Cap", 12
    if any(x in name for x in ["INDEX", "NIFTY"]):
        return "Index", 12
    return "Equity", 12


@router.get("/mf/health", summary="MF health check", description="Analyze mutual fund performance and health")
async def mf_health_check(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Analyze mutual fund holdings for performance and health."""
    holdings = await get_user_holdings(current_user["_id"])
    mf_holdings = [h for h in holdings if h.holding_type == "MF"]
    if not mf_holdings:
        return StandardResponse.ok({"funds": [], "total_mf_value": 0, "health_score": 100})

    prices = await get_prices_for_holdings(mf_holdings)
    analysis: list = []
    issues: list = []
    total_value = 0.0

    for h in mf_holdings:
        p = prices.get(h.symbol, {})
        curr_price = p.get("current_price") or h.avg_price
        value = h.quantity * curr_price
        total_value += value
        expense_ratio = 0.2 if "INDEX" in h.name.upper() else 1.5
        category, benchmark = categorize_mf(h.name)
        inv = h.quantity * h.avg_price
        returns_pct = ((value - inv) / inv * 100) if inv > 0 else 0
        status = "Underperforming" if returns_pct < benchmark - 5 else "On Track"

        analysis.append({"symbol": h.symbol, "name": h.name, "category": category, "value": round(value, 2),
                         "returns_pct": round(returns_pct, 2), "expense_ratio": expense_ratio, "status": status})

    return StandardResponse.ok({"total_mf_value": round(total_value, 2), "funds": analysis, "issues": issues, "health_score": 100 - len(issues) * 10})
