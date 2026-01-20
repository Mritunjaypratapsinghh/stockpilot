from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from datetime import datetime
from bson import ObjectId
from io import BytesIO, StringIO
import csv
from ..database import get_db
from ..api.auth import get_current_user
from ..services.price_service import get_bulk_prices

router = APIRouter()

@router.get("/holdings/csv")
async def export_holdings_csv(current_user: dict = Depends(get_current_user)):
    """Export holdings as CSV"""
    db = get_db()
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    symbols = [h["symbol"] for h in holdings if h.get("holding_type") != "MF"]
    prices = await get_bulk_prices(symbols) if symbols else {}
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Symbol", "Name", "Qty", "Avg Price", "Current Price", "Investment", "Current Value", "P&L", "P&L %"])
    
    for h in holdings:
        p = prices.get(h["symbol"], {})
        curr = p.get("current_price") or h.get("current_price") or h["avg_price"]
        inv = h["quantity"] * h["avg_price"]
        val = h["quantity"] * curr
        pnl = val - inv
        writer.writerow([h["symbol"], h.get("name", ""), h["quantity"], h["avg_price"], round(curr, 2), round(inv, 2), round(val, 2), round(pnl, 2), round(pnl / inv * 100 if inv else 0, 2)])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=holdings_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@router.get("/transactions/csv")
async def export_transactions_csv(current_user: dict = Depends(get_current_user)):
    """Export transactions as CSV"""
    db = get_db()
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Symbol", "Type", "Qty", "Price", "Value", "Notes"])
    
    txns = []
    for h in holdings:
        for t in h.get("transactions", []):
            txns.append({"symbol": h["symbol"], **t})
    txns.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    for t in txns:
        writer.writerow([t.get("date", ""), t["symbol"], t["type"], t["quantity"], t["price"], round(t["quantity"] * t["price"], 2), t.get("notes", "")])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=transactions_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@router.get("/dividends/csv")
async def export_dividends_csv(current_user: dict = Depends(get_current_user)):
    """Export dividends as CSV"""
    db = get_db()
    dividends = await db.dividends.find({"user_id": ObjectId(current_user["_id"])}).sort("ex_date", -1).to_list(500)
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Ex-Date", "Symbol", "Per Share", "Qty", "Total", "Payment Date"])
    
    for d in dividends:
        writer.writerow([d.get("ex_date", ""), d["symbol"], d["amount"], d["quantity"], d["total"], d.get("payment_date", "")])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=dividends_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@router.get("/summary/csv")
async def export_summary_csv(current_user: dict = Depends(get_current_user)):
    """Export complete portfolio summary as CSV"""
    db = get_db()
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    dividends = await db.dividends.find({"user_id": ObjectId(current_user["_id"])}).to_list(500)
    symbols = [h["symbol"] for h in holdings if h.get("holding_type") != "MF"]
    prices = await get_bulk_prices(symbols) if symbols else {}
    
    total_inv = sum(h["quantity"] * h["avg_price"] for h in holdings)
    total_val = sum(h["quantity"] * (prices.get(h["symbol"], {}).get("current_price") or h["avg_price"]) for h in holdings)
    total_div = sum(d["total"] for d in dividends)
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["PORTFOLIO SUMMARY", f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"])
    writer.writerow([])
    writer.writerow(["Total Investment", round(total_inv, 2)])
    writer.writerow(["Current Value", round(total_val, 2)])
    writer.writerow(["Total P&L", round(total_val - total_inv, 2)])
    writer.writerow(["P&L %", round((total_val - total_inv) / total_inv * 100 if total_inv else 0, 2)])
    writer.writerow(["Total Dividends", round(total_div, 2)])
    writer.writerow(["Dividend Yield %", round(total_div / total_inv * 100 if total_inv else 0, 2)])
    writer.writerow([])
    writer.writerow(["HOLDINGS"])
    writer.writerow(["Symbol", "Qty", "Avg", "LTP", "Investment", "Value", "P&L", "P&L %"])
    
    for h in holdings:
        p = prices.get(h["symbol"], {})
        curr = p.get("current_price") or h["avg_price"]
        inv = h["quantity"] * h["avg_price"]
        val = h["quantity"] * curr
        pnl = val - inv
        writer.writerow([h["symbol"], h["quantity"], h["avg_price"], round(curr, 2), round(inv, 2), round(val, 2), round(pnl, 2), round(pnl / inv * 100 if inv else 0, 2)])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=portfolio_summary_{datetime.now().strftime('%Y%m%d')}.csv"}
    )
