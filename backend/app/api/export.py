from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from datetime import datetime
from beanie import PydanticObjectId
from io import StringIO
import csv

from ..models.documents import Holding, Dividend
from ..api.auth import get_current_user
from ..services.price_service import get_bulk_prices

router = APIRouter()


async def get_user_holdings(user_id: str):
    return await Holding.find(Holding.user_id == PydanticObjectId(user_id)).to_list()


async def get_prices_for_holdings(holdings):
    symbols = [h.symbol for h in holdings if h.holding_type != "MF"]
    return await get_bulk_prices(symbols) if symbols else {}


@router.get("/holdings/csv")
async def export_holdings_csv(current_user: dict = Depends(get_current_user)):
    holdings = await get_user_holdings(current_user["_id"])
    prices = await get_prices_for_holdings(holdings)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Symbol", "Name", "Qty", "Avg Price", "Current Price", "Investment", "Current Value", "P&L", "P&L %"])

    for h in holdings:
        curr = prices.get(h.symbol, {}).get("current_price") or h.current_price or h.avg_price
        inv = h.quantity * h.avg_price
        val = h.quantity * curr
        pnl = val - inv
        writer.writerow([h.symbol, h.name, h.quantity, h.avg_price, round(curr, 2), round(inv, 2), round(val, 2), round(pnl, 2), round(pnl / inv * 100 if inv else 0, 2)])

    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=holdings_{datetime.now().strftime('%Y%m%d')}.csv"})


@router.get("/transactions/csv")
async def export_transactions_csv(current_user: dict = Depends(get_current_user)):
    holdings = await get_user_holdings(current_user["_id"])

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Symbol", "Type", "Qty", "Price", "Value", "Notes"])

    txns = []
    for h in holdings:
        for t in h.transactions:
            txns.append({"symbol": h.symbol, **t.model_dump()})
    txns.sort(key=lambda x: x.get("date", ""), reverse=True)

    for t in txns:
        writer.writerow([t.get("date", ""), t["symbol"], t["type"], t["quantity"], t["price"], round(t["quantity"] * t["price"], 2), t.get("notes", "")])

    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=transactions_{datetime.now().strftime('%Y%m%d')}.csv"})


@router.get("/dividends/csv")
async def export_dividends_csv(current_user: dict = Depends(get_current_user)):
    dividends = await Dividend.find(Dividend.user_id == PydanticObjectId(current_user["_id"])).sort(-Dividend.ex_date).to_list()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Ex-Date", "Symbol", "Per Share", "Qty", "Total", "Payment Date"])

    for d in dividends:
        writer.writerow([d.ex_date, d.symbol, d.amount, d.quantity, d.total, d.payment_date or ""])

    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=dividends_{datetime.now().strftime('%Y%m%d')}.csv"})


@router.get("/summary/csv")
async def export_summary_csv(current_user: dict = Depends(get_current_user)):
    user_id = PydanticObjectId(current_user["_id"])
    holdings = await Holding.find(Holding.user_id == user_id).to_list()
    dividends = await Dividend.find(Dividend.user_id == user_id).to_list()
    prices = await get_prices_for_holdings(holdings)

    total_inv = sum(h.quantity * h.avg_price for h in holdings)
    total_val = sum(h.quantity * (prices.get(h.symbol, {}).get("current_price") or h.avg_price) for h in holdings)
    total_div = sum(d.total for d in dividends)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["PORTFOLIO SUMMARY", f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"])
    writer.writerow([])
    writer.writerow(["Total Investment", round(total_inv, 2)])
    writer.writerow(["Current Value", round(total_val, 2)])
    writer.writerow(["Total P&L", round(total_val - total_inv, 2)])
    writer.writerow(["P&L %", round((total_val - total_inv) / total_inv * 100 if total_inv else 0, 2)])
    writer.writerow(["Total Dividends", round(total_div, 2)])
    writer.writerow([])
    writer.writerow(["HOLDINGS"])
    writer.writerow(["Symbol", "Qty", "Avg", "LTP", "Investment", "Value", "P&L", "P&L %"])

    for h in holdings:
        curr = prices.get(h.symbol, {}).get("current_price") or h.avg_price
        inv = h.quantity * h.avg_price
        val = h.quantity * curr
        pnl = val - inv
        writer.writerow([h.symbol, h.quantity, h.avg_price, round(curr, 2), round(inv, 2), round(val, 2), round(pnl, 2), round(pnl / inv * 100 if inv else 0, 2)])

    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=portfolio_summary_{datetime.now().strftime('%Y%m%d')}.csv"})
