from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from datetime import datetime, timezone
from beanie import PydanticObjectId
import csv
import io

from ..models.documents import Holding
from ..models.documents.holding import EmbeddedTransaction
from ..api.auth import get_current_user

router = APIRouter()

BROKER_FORMATS = {
    "zerodha": {"markers": ["trade_type", "trade_date", "tradebook"], "type": "tradebook"},
    "groww": {"markers": ["avg cost", "company name"], "type": "holdings"},
    "upstox": {"markers": ["scrip", "net_qty", "buy_avg"], "type": "holdings"},
    "angelone": {"markers": ["scrip name", "net qty", "avg price"], "type": "holdings"},
    "kite": {"markers": ["instrument", "qty.", "avg. cost"], "type": "holdings"},
}


def detect_broker(headers: list, content: str = "") -> tuple:
    headers_lower = [h.lower().strip() for h in headers]
    content_lower = content.lower()
    for broker, config in BROKER_FORMATS.items():
        if sum(1 for m in config["markers"] if m in headers_lower or m in content_lower) >= 2:
            return broker, config["type"]
    if "trade_type" in headers_lower:
        return "zerodha", "tradebook"
    if "avg cost" in headers_lower:
        return "generic", "holdings"
    return "unknown", "unknown"


def parse_zerodha(row: dict) -> dict:
    return {"symbol": row.get("symbol", row.get("tradingsymbol", "")).split("-")[0].strip().upper(), "type": "BUY" if row.get("trade_type", "").lower() == "buy" else "SELL", "quantity": float(row.get("quantity", row.get("qty", 0))), "price": float(row.get("price", row.get("trade_price", 0))), "date": row.get("trade_date", row.get("order_execution_time", "")).split(" ")[0]}


def parse_holdings(row: dict) -> dict:
    symbol = qty = avg = ""
    for k, v in row.items():
        kl = k.lower()
        if "symbol" in kl or "scrip" in kl or "instrument" in kl:
            symbol = str(v).split()[0].strip().upper()
        elif "qty" in kl or "quantity" in kl:
            qty = float(str(v).replace(",", "") or 0)
        elif "avg" in kl or "cost" in kl:
            try:
                avg = float(str(v).replace(",", "") or 0)
            except:
                pass
    return {"symbol": symbol, "name": symbol, "quantity": qty, "avg_price": avg}


@router.post("/import")
async def import_holdings(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files supported")

    text = (await file.read()).decode("utf-8")
    try:
        rows = list(csv.DictReader(io.StringIO(text)))
    except:
        raise HTTPException(status_code=400, detail="Invalid CSV format")

    if not rows:
        raise HTTPException(status_code=400, detail="Empty CSV file")

    broker, import_type = detect_broker(list(rows[0].keys()), text)
    if broker == "unknown":
        raise HTTPException(status_code=400, detail="Unsupported CSV format")

    user_id = PydanticObjectId(current_user["_id"])
    imported = skipped = 0

    if import_type == "tradebook":
        holdings_map = {}
        for row in rows:
            try:
                p = parse_zerodha(row)
                if not p["symbol"] or p["quantity"] <= 0:
                    skipped += 1
                    continue
                if p["symbol"] not in holdings_map:
                    holdings_map[p["symbol"]] = {"qty": 0, "cost": 0, "txns": []}
                if p["type"] == "BUY":
                    holdings_map[p["symbol"]]["qty"] += p["quantity"]
                    holdings_map[p["symbol"]]["cost"] += p["quantity"] * p["price"]
                else:
                    holdings_map[p["symbol"]]["qty"] -= p["quantity"]
                holdings_map[p["symbol"]]["txns"].append(EmbeddedTransaction(type=p["type"], quantity=p["quantity"], price=p["price"], date=p["date"]))
            except:
                skipped += 1

        for symbol, data in holdings_map.items():
            if data["qty"] <= 0:
                continue
            existing = await Holding.find_one(Holding.user_id == user_id, Holding.symbol == symbol)
            if existing:
                skipped += 1
                continue
            await Holding(user_id=user_id, symbol=symbol, name=symbol, quantity=data["qty"], avg_price=round(data["cost"] / data["qty"], 2), transactions=data["txns"]).insert()
            imported += 1
    else:
        for row in rows:
            try:
                p = parse_holdings(row)
                if not p["symbol"] or p["quantity"] <= 0:
                    skipped += 1
                    continue
                existing = await Holding.find_one(Holding.user_id == user_id, Holding.symbol == p["symbol"])
                if existing:
                    skipped += 1
                    continue
                await Holding(user_id=user_id, symbol=p["symbol"], name=p["name"], quantity=p["quantity"], avg_price=p["avg_price"]).insert()
                imported += 1
            except:
                skipped += 1

    return {"broker": broker, "imported": imported, "skipped": skipped, "message": f"Imported {imported} holdings from {broker.title()}"}
