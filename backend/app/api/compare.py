from fastapi import APIRouter, Depends, Query
from typing import List
import yfinance as yf
import asyncio
from concurrent.futures import ThreadPoolExecutor
from ..api.auth import get_current_user
from ..services.price_service import get_stock_price
from ..logger import logger

router = APIRouter()
executor = ThreadPoolExecutor(max_workers=4)

def _fetch_yf_data(symbol: str) -> dict:
    """Fetch stock data using yfinance"""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        info = ticker.info
        if not info or info.get("regularMarketPrice") is None:
            return None
        return {
            "symbol": symbol,
            "name": info.get("shortName", symbol),
            "sector": info.get("sector", "N/A"),
            "price": info.get("regularMarketPrice", 0),
            "change_pct": round(info.get("regularMarketChangePercent", 0) * 100, 2) if info.get("regularMarketChangePercent") else 0,
            "market_cap": round(info.get("marketCap", 0) / 10000000, 0),
            "pe": round(info.get("trailingPE", 0), 2) if info.get("trailingPE") else None,
            "forward_pe": round(info.get("forwardPE", 0), 2) if info.get("forwardPE") else None,
            "pb": round(info.get("priceToBook", 0), 2) if info.get("priceToBook") else None,
            "ps": round(info.get("priceToSalesTrailing12Months", 0), 2) if info.get("priceToSalesTrailing12Months") else None,
            "dividend_yield": round(info.get("dividendYield", 0) * 100, 2) if info.get("dividendYield") else 0,
            "roe": round(info.get("returnOnEquity", 0) * 100, 2) if info.get("returnOnEquity") else None,
            "roce": round(info.get("returnOnAssets", 0) * 100, 2) if info.get("returnOnAssets") else None,
            "debt_equity": round(info.get("debtToEquity", 0), 2) if info.get("debtToEquity") else None,
            "current_ratio": round(info.get("currentRatio", 0), 2) if info.get("currentRatio") else None,
            "profit_margin": round(info.get("profitMargins", 0) * 100, 2) if info.get("profitMargins") else None,
            "operating_margin": round(info.get("operatingMargins", 0) * 100, 2) if info.get("operatingMargins") else None,
            "revenue_growth": round(info.get("revenueGrowth", 0) * 100, 2) if info.get("revenueGrowth") else None,
            "earnings_growth": round(info.get("earningsGrowth", 0) * 100, 2) if info.get("earningsGrowth") else None,
            "high_52w": info.get("fiftyTwoWeekHigh"),
            "low_52w": info.get("fiftyTwoWeekLow"),
            "avg_volume": info.get("averageVolume", 0),
            "beta": info.get("beta"),
        }
    except Exception as e:
        logger.error(f"yfinance error for {symbol}: {e}")
        return None

async def fetch_stock_fundamentals(symbol: str) -> dict:
    """Try yfinance first, fallback to price service for basic data"""
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(executor, _fetch_yf_data, symbol)
    if data:
        return data
    # Fallback to basic price data
    price_data = await get_stock_price(symbol)
    if price_data:
        return {
            "symbol": symbol,
            "name": price_data.get("name", symbol),
            "price": price_data.get("current_price", 0),
            "change_pct": price_data.get("day_change_pct", 0),
            "note": "Limited data - Yahoo rate limited"
        }
    return {"symbol": symbol, "error": "Failed to fetch data"}

async def fetch_price_history(symbol: str, period: str = "1y") -> list:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _fetch_history_sync, symbol, period)

def _fetch_history_sync(symbol: str, period: str) -> list:
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        hist = ticker.history(period=period)
        if hist.empty:
            return []
        closes = hist['Close'].tolist()
        dates = [int(d.timestamp()) for d in hist.index]
        start_price = closes[0] if closes[0] else 1
        return [
            {"date": dates[i], "price": round(closes[i], 2), "change_pct": round((closes[i] / start_price - 1) * 100, 2)}
            for i in range(0, len(dates), 5) if closes[i]
        ]
    except Exception as e:
        logger.error(f"Error fetching history for {symbol}: {e}")
        return []

@router.get("/compare")
async def compare_stocks(symbols: str = Query(..., description="Comma-separated symbols, e.g., RELIANCE,TCS,INFY"), current_user: dict = Depends(get_current_user)):
    """Compare multiple stocks side by side"""
    symbol_list = [s.strip().upper() for s in symbols.split(",")][:4]  # Max 4 stocks
    
    if len(symbol_list) < 2:
        return {"error": "Provide at least 2 symbols to compare"}
    
    # Fetch data for all symbols
    tasks = [fetch_stock_fundamentals(s) for s in symbol_list]
    stocks = await asyncio.gather(*tasks)
    
    # Determine best/worst for each metric
    metrics = ["pe", "pb", "roe", "roce", "debt_equity", "profit_margin", "revenue_growth", "dividend_yield"]
    comparison = {}
    
    for metric in metrics:
        values = [(s["symbol"], s.get(metric)) for s in stocks if s.get(metric) is not None]
        if values:
            # Lower is better for PE, PB, Debt/Equity
            if metric in ["pe", "pb", "debt_equity"]:
                best = min(values, key=lambda x: x[1])
                worst = max(values, key=lambda x: x[1])
            else:
                best = max(values, key=lambda x: x[1])
                worst = min(values, key=lambda x: x[1])
            comparison[metric] = {"best": best[0], "worst": worst[0]}
    
    return {
        "stocks": stocks,
        "comparison": comparison,
        "metrics_explanation": {
            "pe": "Price to Earnings - Lower is cheaper",
            "pb": "Price to Book - Lower is cheaper",
            "roe": "Return on Equity - Higher is better",
            "roce": "Return on Capital - Higher is better",
            "debt_equity": "Debt to Equity - Lower is safer",
            "profit_margin": "Profit Margin - Higher is better",
            "revenue_growth": "Revenue Growth - Higher is better",
            "dividend_yield": "Dividend Yield - Higher for income"
        }
    }

@router.get("/chart")
async def compare_price_chart(symbols: str = Query(...), period: str = "1y", current_user: dict = Depends(get_current_user)):
    """Get price history for chart comparison"""
    symbol_list = [s.strip().upper() for s in symbols.split(",")][:4]
    
    tasks = [fetch_price_history(s, period) for s in symbol_list]
    histories = await asyncio.gather(*tasks)
    
    result = {}
    for i, symbol in enumerate(symbol_list):
        result[symbol] = histories[i]
    
    return {"period": period, "data": result}

@router.get("/sector-peers/{symbol}")
async def get_sector_peers(symbol: str, current_user: dict = Depends(get_current_user)):
    """Get peers in the same sector for comparison"""
    # Sector peer mapping
    SECTOR_PEERS = {
        "RELIANCE": ["ONGC", "BPCL", "IOC", "GAIL"],
        "TCS": ["INFY", "WIPRO", "HCLTECH", "TECHM"],
        "HDFCBANK": ["ICICIBANK", "KOTAKBANK", "AXISBANK", "SBIN"],
        "HINDUNILVR": ["ITC", "NESTLEIND", "BRITANNIA", "DABUR"],
        "SUNPHARMA": ["DRREDDY", "CIPLA", "DIVISLAB", "LUPIN"],
        "TATAMOTORS": ["MARUTI", "M&M", "BAJAJ-AUTO", "HEROMOTOCO"],
        "TATASTEEL": ["JSWSTEEL", "HINDALCO", "VEDL", "SAIL"],
        "LT": ["ULTRACEMCO", "GRASIM", "ADANIENT", "DLF"],
    }
    
    symbol = symbol.upper()
    peers = SECTOR_PEERS.get(symbol)
    
    if not peers:
        # Try to find by checking which list contains the symbol
        for key, peer_list in SECTOR_PEERS.items():
            if symbol in peer_list:
                peers = [key] + [p for p in peer_list if p != symbol]
                break
    
    if not peers:
        return {"symbol": symbol, "peers": [], "note": "No sector peers found"}
    
    # Fetch data for symbol and peers
    all_symbols = [symbol] + peers[:3]
    tasks = [fetch_stock_fundamentals(s) for s in all_symbols]
    stocks = await asyncio.gather(*tasks)
    
    return {
        "symbol": symbol,
        "peers": peers[:4],
        "comparison": stocks
    }
