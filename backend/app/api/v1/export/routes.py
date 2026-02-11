"""Export routes - CSV exports for holdings, transactions, summary, dividends."""

import csv
from datetime import datetime
from io import StringIO

from app.core.security import get_current_user
from app.models.documents import Holding, Transaction
from app.services.market.price_service import get_bulk_prices
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

router = APIRouter()


async def get_user_holdings(user_id: str) -> list:
    """Get holdings for user."""
    return await Holding.find(Holding.user_id == user_id).to_list()


async def get_prices_for_holdings(holdings: list) -> dict:
    """Get current prices for holdings."""
    symbols = [h.symbol for h in holdings if not h.symbol.startswith("0P")]
    return await get_bulk_prices(symbols) if symbols else {}


@router.get("/holdings/csv")
async def export_holdings_csv(current_user: dict = Depends(get_current_user)):
    """Export holdings to CSV."""
    holdings = await get_user_holdings(current_user["_id"])
    prices = await get_prices_for_holdings(holdings)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Symbol",
            "Name",
            "Type",
            "Quantity",
            "Avg Price",
            "Current Price",
            "Investment",
            "Current Value",
            "P&L",
            "P&L %",
        ]
    )

    for h in holdings:
        curr_price = prices.get(h.symbol, {}).get("current_price") or h.current_price or h.avg_price
        inv = h.quantity * h.avg_price
        val = h.quantity * curr_price
        pnl = val - inv
        writer.writerow(
            [
                h.symbol,
                h.name,
                h.holding_type,
                round(h.quantity, 4),
                round(h.avg_price, 2),
                round(curr_price, 2),
                round(inv, 2),
                round(val, 2),
                round(pnl, 2),
                round(pnl / inv * 100, 2) if inv > 0 else 0,
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=holdings_{datetime.now().strftime('%Y%m%d')}.csv"},
    )


@router.get("/transactions/csv")
async def export_transactions_csv(current_user: dict = Depends(get_current_user)):
    """Export transactions to CSV."""
    transactions = await Transaction.find(Transaction.user_id == current_user["_id"]).sort(-Transaction.date).to_list()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Symbol", "Type", "Quantity", "Price", "Amount", "Notes"])

    for t in transactions:
        writer.writerow(
            [
                t.date.strftime("%Y-%m-%d") if t.date else "",
                t.symbol,
                t.transaction_type,
                round(t.quantity, 4),
                round(t.price, 2),
                round(t.quantity * t.price, 2),
                t.notes or "",
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=transactions_{datetime.now().strftime('%Y%m%d')}.csv"},
    )


@router.get("/summary/csv")
async def export_summary_csv(current_user: dict = Depends(get_current_user)):
    """Export portfolio summary to CSV."""
    holdings = await get_user_holdings(current_user["_id"])
    prices = await get_prices_for_holdings(holdings)

    total_investment = 0
    total_value = 0
    by_type = {}

    for h in holdings:
        curr_price = prices.get(h.symbol, {}).get("current_price") or h.current_price or h.avg_price
        inv = h.quantity * h.avg_price
        val = h.quantity * curr_price
        total_investment += inv
        total_value += val

        htype = h.holding_type or "Stock"
        if htype not in by_type:
            by_type[htype] = {"investment": 0, "value": 0, "count": 0}
        by_type[htype]["investment"] += inv
        by_type[htype]["value"] += val
        by_type[htype]["count"] += 1

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Portfolio Summary", f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"])
    writer.writerow([])
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Total Investment", round(total_investment, 2)])
    writer.writerow(["Current Value", round(total_value, 2)])
    writer.writerow(["Total P&L", round(total_value - total_investment, 2)])
    writer.writerow(
        [
            "Total P&L %",
            round((total_value - total_investment) / total_investment * 100, 2) if total_investment > 0 else 0,
        ]
    )
    writer.writerow(["Total Holdings", len(holdings)])
    writer.writerow([])
    writer.writerow(["By Type", "Count", "Investment", "Value", "P&L"])
    for htype, data in by_type.items():
        pnl = data["value"] - data["investment"]
        writer.writerow([htype, data["count"], round(data["investment"], 2), round(data["value"], 2), round(pnl, 2)])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=summary_{datetime.now().strftime('%Y%m%d')}.csv"},
    )


@router.get("/dividends/csv")
async def export_dividends_csv(current_user: dict = Depends(get_current_user)):
    """Export dividend history to CSV."""
    from app.models.documents import Dividend

    dividends = await Dividend.find(Dividend.user_id == current_user["_id"]).to_list()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Ex-Date", "Symbol", "Amount Per Share", "Quantity", "Total"])

    for d in dividends:
        writer.writerow(
            [
                d.ex_date or "",
                d.symbol,
                round(d.amount, 2) if d.amount else 0,
                round(d.quantity, 4) if d.quantity else 0,
                round(d.total, 2) if d.total else 0,
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=dividends_{datetime.now().strftime('%Y%m%d')}.csv"},
    )
