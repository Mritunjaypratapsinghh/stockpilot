from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from datetime import datetime
from bson import ObjectId
import csv
import io
import re
from ..database import get_db
from ..api.auth import get_current_user
from ..logger import logger

router = APIRouter()

# Broker CSV formats
BROKER_FORMATS = {
    "zerodha": {"markers": ["trade_type", "trade_date", "tradebook"], "type": "tradebook"},
    "groww": {"markers": ["avg cost", "company name"], "type": "holdings"},
    "upstox": {"markers": ["scrip", "net_qty", "buy_avg"], "type": "holdings"},
    "angelone": {"markers": ["scrip name", "net qty", "avg price"], "type": "holdings"},
    "kite": {"markers": ["instrument", "qty.", "avg. cost"], "type": "holdings"},
    "icici": {"markers": ["stock symbol", "quantity", "average price"], "type": "holdings"},
}

def detect_broker(headers: list, content: str = "") -> tuple:
    """Detect broker from CSV headers"""
    headers_lower = [h.lower().strip() for h in headers]
    content_lower = content.lower()
    
    # Check each broker's markers
    for broker, config in BROKER_FORMATS.items():
        matches = sum(1 for m in config["markers"] if m in headers_lower or m in content_lower)
        if matches >= 2:
            return broker, config["type"]
    
    # Fallback detection
    if "trade_type" in headers_lower:
        return "zerodha", "tradebook"
    if "avg cost" in headers_lower or "average" in headers_lower:
        return "generic", "holdings"
    
    return "unknown", "unknown"

def parse_zerodha_tradebook(row: dict) -> dict:
    return {
        "symbol": row.get("symbol", row.get("tradingsymbol", "")).split("-")[0].strip().upper(),
        "type": "BUY" if row.get("trade_type", "").lower() == "buy" else "SELL",
        "quantity": float(row.get("quantity", row.get("qty", 0))),
        "price": float(row.get("price", row.get("trade_price", 0))),
        "date": row.get("trade_date", row.get("order_execution_time", "")).split(" ")[0],
        "exchange": row.get("exchange", "NSE").upper()
    }

def parse_groww_holdings(row: dict) -> dict:
    return {
        "symbol": row.get("Symbol", row.get("symbol", "")).strip().upper(),
        "name": row.get("Company Name", row.get("company_name", "")),
        "quantity": float(str(row.get("Quantity", row.get("quantity", 0))).replace(",", "")),
        "avg_price": float(str(row.get("Avg Cost", row.get("avg_cost", row.get("Average Cost", 0)))).replace(",", ""))
    }

def parse_upstox_holdings(row: dict) -> dict:
    return {
        "symbol": row.get("scrip", row.get("Scrip", "")).strip().upper(),
        "name": row.get("scrip", ""),
        "quantity": float(str(row.get("net_qty", row.get("Net Qty", 0))).replace(",", "")),
        "avg_price": float(str(row.get("buy_avg", row.get("Buy Avg", 0))).replace(",", ""))
    }

def parse_angelone_holdings(row: dict) -> dict:
    return {
        "symbol": row.get("Scrip Name", row.get("scrip_name", "")).split()[0].strip().upper(),
        "name": row.get("Scrip Name", ""),
        "quantity": float(str(row.get("Net Qty", row.get("net_qty", 0))).replace(",", "")),
        "avg_price": float(str(row.get("Avg Price", row.get("avg_price", 0))).replace(",", ""))
    }

def parse_kite_holdings(row: dict) -> dict:
    return {
        "symbol": row.get("Instrument", row.get("instrument", "")).strip().upper(),
        "name": row.get("Instrument", ""),
        "quantity": float(str(row.get("Qty.", row.get("qty", 0))).replace(",", "")),
        "avg_price": float(str(row.get("Avg. cost", row.get("avg_cost", 0))).replace(",", ""))
    }

def parse_generic_holdings(row: dict) -> dict:
    """Generic parser for unknown formats"""
    # Try common column names
    symbol = ""
    quantity = 0
    avg_price = 0
    
    for key, val in row.items():
        key_lower = key.lower()
        if "symbol" in key_lower or "scrip" in key_lower or "stock" in key_lower:
            symbol = str(val).split()[0].strip().upper()
        elif "qty" in key_lower or "quantity" in key_lower or "units" in key_lower:
            quantity = float(str(val).replace(",", "") or 0)
        elif "avg" in key_lower or "cost" in key_lower or "price" in key_lower:
            try:
                avg_price = float(str(val).replace(",", "") or 0)
            except:
                pass
    
    return {"symbol": symbol, "name": symbol, "quantity": quantity, "avg_price": avg_price}

PARSERS = {
    "zerodha": parse_zerodha_tradebook,
    "groww": parse_groww_holdings,
    "upstox": parse_upstox_holdings,
    "angelone": parse_angelone_holdings,
    "kite": parse_kite_holdings,
    "generic": parse_generic_holdings,
}

@router.post("/import")
async def import_holdings(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Import holdings from broker CSV (Zerodha, Groww, Upstox, Angel One, ICICI Direct)"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files supported")
    
    content = await file.read()
    text = content.decode("utf-8")
    
    # Handle different CSV dialects
    try:
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
    except:
        raise HTTPException(status_code=400, detail="Invalid CSV format")
    
    if not rows:
        raise HTTPException(status_code=400, detail="Empty CSV file")
    
    broker, import_type = detect_broker(list(rows[0].keys()), text)
    if broker == "unknown":
        raise HTTPException(status_code=400, detail="Unsupported CSV format. Supported: Zerodha, Groww, Upstox, Angel One")
    
    parser = PARSERS.get(broker, parse_generic_holdings)
    db = get_db()
    user_id = ObjectId(current_user["_id"])
    imported = 0
    skipped = 0
    errors = []
    
    if import_type == "tradebook":
        # Process transactions to build holdings (Zerodha tradebook)
        holdings_map = {}
        for row in rows:
            try:
                parsed = parser(row)
                if not parsed["symbol"] or parsed["quantity"] <= 0:
                    skipped += 1
                    continue
                
                symbol = parsed["symbol"]
                if symbol not in holdings_map:
                    holdings_map[symbol] = {"qty": 0, "cost": 0, "txns": []}
                
                if parsed["type"] == "BUY":
                    holdings_map[symbol]["qty"] += parsed["quantity"]
                    holdings_map[symbol]["cost"] += parsed["quantity"] * parsed["price"]
                else:
                    holdings_map[symbol]["qty"] -= parsed["quantity"]
                
                holdings_map[symbol]["txns"].append({
                    "type": parsed["type"],
                    "quantity": parsed["quantity"],
                    "price": parsed["price"],
                    "date": parsed["date"]
                })
            except Exception as e:
                errors.append(str(e))
                skipped += 1
        
        # Create holdings from aggregated data
        for symbol, data in holdings_map.items():
            if data["qty"] <= 0:
                continue
            
            existing = await db.holdings.find_one({"user_id": user_id, "symbol": symbol})
            if existing:
                skipped += 1
                continue
            
            avg_price = data["cost"] / data["qty"] if data["qty"] > 0 else 0
            await db.holdings.insert_one({
                "user_id": user_id,
                "symbol": symbol,
                "name": symbol,
                "exchange": "NSE",
                "holding_type": "EQUITY",
                "quantity": data["qty"],
                "avg_price": round(avg_price, 2),
                "transactions": data["txns"],
                "created_at": datetime.utcnow()
            })
            imported += 1
    
    else:
        # Direct holdings import (Groww, Upstox, etc.)
        for row in rows:
            try:
                parsed = parser(row)
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
                    "name": parsed.get("name") or parsed["symbol"],
                    "exchange": "NSE",
                    "holding_type": "EQUITY",
                    "quantity": parsed["quantity"],
                    "avg_price": parsed["avg_price"],
                    "transactions": [],
                    "created_at": datetime.utcnow()
                })
                imported += 1
            except Exception as e:
                errors.append(str(e))
                skipped += 1
    
    return {
        "broker": broker,
        "imported": imported,
        "skipped": skipped,
        "errors": errors[:5] if errors else None,
        "message": f"Imported {imported} holdings from {broker.title()}"
    }
