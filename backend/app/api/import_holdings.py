from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from datetime import datetime
from bson import ObjectId
import csv
import io
from ..database import get_db
from ..api.auth import get_current_user
from ..logger import logger

router = APIRouter()

# Zerodha tradebook columns: symbol, isin, trade_date, exchange, segment, series, trade_type, auction, quantity, price, trade_id, order_id, order_execution_time
# Groww columns: Symbol, Company Name, Quantity, Avg Cost, LTP, Current Value, P&L, P&L %

def parse_zerodha_row(row: dict) -> dict:
    """Parse Zerodha tradebook CSV row"""
    return {
        "symbol": row.get("symbol", "").split("-")[0].strip().upper(),
        "type": "BUY" if row.get("trade_type", "").lower() == "buy" else "SELL",
        "quantity": float(row.get("quantity", 0)),
        "price": float(row.get("price", 0)),
        "date": row.get("trade_date", ""),
        "exchange": row.get("exchange", "NSE").upper()
    }

def parse_groww_row(row: dict) -> dict:
    """Parse Groww holdings CSV row"""
    return {
        "symbol": row.get("Symbol", "").strip().upper(),
        "name": row.get("Company Name", ""),
        "quantity": float(row.get("Quantity", 0)),
        "avg_price": float(row.get("Avg Cost", "0").replace(",", "")),
        "type": "HOLDING"
    }

def detect_broker(headers: list) -> str:
    headers_lower = [h.lower() for h in headers]
    if "trade_type" in headers_lower or "trade_date" in headers_lower:
        return "zerodha"
    if "avg cost" in headers_lower or "company name" in headers_lower:
        return "groww"
    if "isin" in headers_lower and "qty" in headers_lower:
        return "zerodha"
    return "unknown"

@router.post("/import")
async def import_holdings(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Import holdings from broker CSV (Zerodha tradebook or Groww holdings)"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files supported")
    
    content = await file.read()
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    
    if not rows:
        raise HTTPException(status_code=400, detail="Empty CSV file")
    
    broker = detect_broker(list(rows[0].keys()))
    if broker == "unknown":
        raise HTTPException(status_code=400, detail="Unsupported CSV format. Use Zerodha tradebook or Groww holdings export.")
    
    db = get_db()
    user_id = ObjectId(current_user["_id"])
    imported = 0
    skipped = 0
    
    if broker == "groww":
        # Groww: direct holdings import
        for row in rows:
            parsed = parse_groww_row(row)
            if not parsed["symbol"] or parsed["quantity"] <= 0:
                skipped += 1
                continue
            
            existing = await db.holdings.find_one({"user_id": user_id, "symbol": parsed["symbol"]})
            if existing:
                skipped += 1
                continue
            
            await db.holdings.insert_one({
                "user_id": user_id,
                "symbol": parsed["symbol"],
                "name": parsed["name"] or parsed["symbol"],
                "exchange": "NSE",
                "holding_type": "EQUITY",
                "quantity": parsed["quantity"],
                "avg_price": parsed["avg_price"],
                "transactions": [],
                "created_at": datetime.utcnow()
            })
            imported += 1
    
    else:  # zerodha
        # Zerodha: process transactions to build holdings
        holdings_map = {}
        for row in rows:
            parsed = parse_zerodha_row(row)
            if not parsed["symbol"] or parsed["quantity"] <= 0:
                skipped += 1
                continue
            
            sym = parsed["symbol"]
            if sym not in holdings_map:
                holdings_map[sym] = {"quantity": 0, "total_cost": 0, "transactions": []}
            
            h = holdings_map[sym]
            if parsed["type"] == "BUY":
                h["total_cost"] += parsed["quantity"] * parsed["price"]
                h["quantity"] += parsed["quantity"]
            else:
                h["quantity"] -= parsed["quantity"]
            
            h["transactions"].append({
                "type": parsed["type"],
                "quantity": parsed["quantity"],
                "price": parsed["price"],
                "date": parsed["date"]
            })
        
        for sym, data in holdings_map.items():
            if data["quantity"] <= 0:
                skipped += 1
                continue
            
            existing = await db.holdings.find_one({"user_id": user_id, "symbol": sym})
            if existing:
                skipped += 1
                continue
            
            avg_price = data["total_cost"] / data["quantity"] if data["quantity"] > 0 else 0
            await db.holdings.insert_one({
                "user_id": user_id,
                "symbol": sym,
                "name": sym,
                "exchange": "NSE",
                "holding_type": "EQUITY",
                "quantity": data["quantity"],
                "avg_price": round(avg_price, 2),
                "transactions": data["transactions"],
                "created_at": datetime.utcnow()
            })
            imported += 1
    
    logger.info(f"Import: user={current_user['_id']}, broker={broker}, imported={imported}, skipped={skipped}")
    return {"broker": broker, "imported": imported, "skipped": skipped}
