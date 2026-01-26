from fastapi import APIRouter, Depends, Query
from typing import Optional, List
import yfinance as yf
import asyncio
from concurrent.futures import ThreadPoolExecutor
from ..api.auth import get_current_user
from ..logger import logger
import time

router = APIRouter()
executor = ThreadPoolExecutor(max_workers=8)

# Cache for stock data (symbol -> (data, timestamp))
_cache = {}
CACHE_TTL = 300  # 5 minutes

# Pre-built screens
SCREENS = {
    "undervalued": {"pe_max": 15, "pb_max": 2, "roe_min": 15},
    "high_dividend": {"dividend_yield_min": 3},
    "large_cap": {"market_cap_min": 50000},
    "mid_cap": {"market_cap_min": 10000, "market_cap_max": 50000},
    "small_cap": {"market_cap_max": 10000},
    "momentum": {"change_52w_min": 20},
    "low_debt": {"debt_equity_max": 0.5},
}

# Popular NSE stocks for screening
STOCK_UNIVERSE = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR", "SBIN", "BHARTIARTL",
    "KOTAKBANK", "LT", "AXISBANK", "ITC", "BAJFINANCE", "ASIANPAINT", "MARUTI", "TITAN",
    "SUNPHARMA", "ULTRACEMCO", "WIPRO", "HCLTECH", "NTPC", "POWERGRID", "ONGC", "TATASTEEL",
    "JSWSTEEL", "TATAMOTORS", "M&M", "ADANIENT", "ADANIPORTS", "COALINDIA", "BAJAJFINSV",
    "TECHM", "DRREDDY", "CIPLA", "DIVISLAB", "BRITANNIA", "NESTLEIND", "GRASIM", "HINDALCO",
    "EICHERMOT", "HEROMOTOCO", "BPCL", "IOC", "INDUSINDBK", "SBILIFE", "HDFCLIFE", "TATACONSUM"
]

# Sample data fallback when Yahoo is rate-limited
SAMPLE_DATA = {
    "RELIANCE": {"name": "Reliance Industries", "price": 1387, "market_cap": 940000, "pe": 24.5, "pb": 2.1, "roe": 9.2, "dividend_yield": 0.4, "debt_equity": 42, "change_52w": -8},
    "TCS": {"name": "Tata Consultancy", "price": 3157, "market_cap": 1140000, "pe": 28.2, "pb": 13.5, "roe": 52, "dividend_yield": 1.5, "debt_equity": 0, "change_52w": -12},
    "HDFCBANK": {"name": "HDFC Bank", "price": 1650, "market_cap": 1260000, "pe": 18.5, "pb": 2.8, "roe": 16.5, "dividend_yield": 1.2, "debt_equity": None, "change_52w": 5},
    "INFY": {"name": "Infosys", "price": 1672, "market_cap": 695000, "pe": 24.8, "pb": 8.2, "roe": 32, "dividend_yield": 2.5, "debt_equity": 0, "change_52w": -5},
    "ICICIBANK": {"name": "ICICI Bank", "price": 1280, "market_cap": 900000, "pe": 18.2, "pb": 3.2, "roe": 18, "dividend_yield": 0.8, "debt_equity": None, "change_52w": 22},
    "SBIN": {"name": "State Bank of India", "price": 780, "market_cap": 696000, "pe": 10.5, "pb": 1.8, "roe": 18, "dividend_yield": 1.8, "debt_equity": None, "change_52w": 28},
    "ITC": {"name": "ITC Limited", "price": 465, "market_cap": 580000, "pe": 28, "pb": 7.5, "roe": 28, "dividend_yield": 3.2, "debt_equity": 0, "change_52w": 8},
    "BHARTIARTL": {"name": "Bharti Airtel", "price": 1680, "market_cap": 1010000, "pe": 85, "pb": 7.8, "roe": 9.5, "dividend_yield": 0.5, "debt_equity": 180, "change_52w": 45},
    "KOTAKBANK": {"name": "Kotak Mahindra Bank", "price": 1850, "market_cap": 368000, "pe": 19.5, "pb": 3.1, "roe": 14, "dividend_yield": 0.1, "debt_equity": None, "change_52w": -2},
    "LT": {"name": "Larsen & Toubro", "price": 3450, "market_cap": 475000, "pe": 32, "pb": 5.2, "roe": 15, "dividend_yield": 0.9, "debt_equity": 85, "change_52w": 12},
    "HINDUNILVR": {"name": "Hindustan Unilever", "price": 2380, "market_cap": 559000, "pe": 55, "pb": 11, "roe": 20, "dividend_yield": 1.6, "debt_equity": 0, "change_52w": -8},
    "AXISBANK": {"name": "Axis Bank", "price": 1120, "market_cap": 346000, "pe": 13.5, "pb": 2.2, "roe": 17, "dividend_yield": 0.1, "debt_equity": None, "change_52w": 15},
    "BAJFINANCE": {"name": "Bajaj Finance", "price": 6850, "market_cap": 424000, "pe": 30, "pb": 6.5, "roe": 22, "dividend_yield": 0.4, "debt_equity": 320, "change_52w": -5},
    "MARUTI": {"name": "Maruti Suzuki", "price": 12200, "market_cap": 384000, "pe": 26, "pb": 4.8, "roe": 18, "dividend_yield": 0.8, "debt_equity": 0, "change_52w": 18},
    "TITAN": {"name": "Titan Company", "price": 3280, "market_cap": 291000, "pe": 85, "pb": 18, "roe": 25, "dividend_yield": 0.3, "debt_equity": 45, "change_52w": -2},
    "SUNPHARMA": {"name": "Sun Pharma", "price": 1820, "market_cap": 437000, "pe": 38, "pb": 5.5, "roe": 15, "dividend_yield": 0.6, "debt_equity": 12, "change_52w": 42},
    "NTPC": {"name": "NTPC Limited", "price": 355, "market_cap": 344000, "pe": 15.5, "pb": 2.1, "roe": 14, "dividend_yield": 2.5, "debt_equity": 145, "change_52w": 35},
    "POWERGRID": {"name": "Power Grid Corp", "price": 310, "market_cap": 288000, "pe": 14, "pb": 2.5, "roe": 18, "dividend_yield": 4.2, "debt_equity": 210, "change_52w": 28},
    "ONGC": {"name": "ONGC", "price": 265, "market_cap": 333000, "pe": 7.5, "pb": 0.9, "roe": 12, "dividend_yield": 4.5, "debt_equity": 35, "change_52w": 15},
    "COALINDIA": {"name": "Coal India", "price": 395, "market_cap": 243000, "pe": 6.8, "pb": 2.8, "roe": 52, "dividend_yield": 5.5, "debt_equity": 0, "change_52w": -12},
    "TATASTEEL": {"name": "Tata Steel", "price": 142, "market_cap": 177000, "pe": None, "pb": 1.2, "roe": -2, "dividend_yield": 2.5, "debt_equity": 85, "change_52w": -18},
    "IOC": {"name": "Indian Oil Corp", "price": 135, "market_cap": 190000, "pe": 12, "pb": 1.1, "roe": 9, "dividend_yield": 8.5, "debt_equity": 95, "change_52w": -5},
    "BPCL": {"name": "Bharat Petroleum", "price": 295, "market_cap": 128000, "pe": 8.5, "pb": 1.5, "roe": 18, "dividend_yield": 5.8, "debt_equity": 65, "change_52w": 8},
}

def _fetch_yf_data(symbol: str) -> dict:
    """Fetch stock data using yfinance, fallback to sample data"""
    # Check cache
    if symbol in _cache:
        data, ts = _cache[symbol]
        if time.time() - ts < CACHE_TTL:
            return data
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        info = ticker.info
        if info and info.get("regularMarketPrice"):
            data = {
                "symbol": symbol,
                "name": info.get("shortName", symbol),
                "price": info.get("regularMarketPrice", 0),
                "change_pct": round((info.get("regularMarketChangePercent", 0) or 0) * 100, 2),
                "market_cap": round(info.get("marketCap", 0) / 10000000, 0),
                "pe": round(info.get("trailingPE", 0), 2) if info.get("trailingPE") else None,
                "pb": round(info.get("priceToBook", 0), 2) if info.get("priceToBook") else None,
                "dividend_yield": round((info.get("dividendYield", 0) or 0) * 100, 2),
                "roe": round((info.get("returnOnEquity", 0) or 0) * 100, 2) if info.get("returnOnEquity") else None,
                "debt_equity": round(info.get("debtToEquity", 0), 2) if info.get("debtToEquity") else None,
                "change_52w": round((info.get("52WeekChange", 0) or 0) * 100, 2),
                "high_52w": info.get("fiftyTwoWeekHigh"),
                "low_52w": info.get("fiftyTwoWeekLow"),
            }
            _cache[symbol] = (data, time.time())
            return data
    except Exception as e:
        logger.warning(f"yfinance error for {symbol}: {e}")
    
    # Fallback to sample data
    if symbol in SAMPLE_DATA:
        sample = SAMPLE_DATA[symbol]
        return {"symbol": symbol, **sample, "change_pct": 0, "high_52w": None, "low_52w": None}
    return None

async def fetch_stock_data(symbol: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _fetch_yf_data, symbol)

def apply_filters(stock: dict, filters: dict) -> bool:
    """Check if stock passes all filters"""
    if not stock:
        return False
    
    for key, value in filters.items():
        field = key.replace("_min", "").replace("_max", "")
        stock_val = stock.get(field)
        
        if stock_val is None:
            continue
            
        if key.endswith("_min") and stock_val < value:
            return False
        if key.endswith("_max") and stock_val > value:
            return False
    
    return True

@router.get("/screens")
async def get_screens():
    """Get list of pre-built screens"""
    return {
        "screens": [
            {"id": "undervalued", "name": "Undervalued Stocks", "description": "PE < 15, PB < 2, ROE > 15%"},
            {"id": "high_dividend", "name": "High Dividend Yield", "description": "Dividend yield > 3%"},
            {"id": "large_cap", "name": "Large Cap", "description": "Market cap > ₹50,000 Cr"},
            {"id": "mid_cap", "name": "Mid Cap", "description": "Market cap ₹10,000-50,000 Cr"},
            {"id": "small_cap", "name": "Small Cap", "description": "Market cap < ₹10,000 Cr"},
            {"id": "momentum", "name": "Momentum", "description": "52-week return > 20%"},
            {"id": "low_debt", "name": "Low Debt", "description": "Debt/Equity < 0.5"},
        ]
    }

@router.get("/run/{screen_id}")
async def run_screen(screen_id: str, limit: int = 20, current_user: dict = Depends(get_current_user)):
    """Run a pre-built screen"""
    if screen_id not in SCREENS:
        return {"error": "Invalid screen"}
    
    filters = SCREENS[screen_id]
    results = []
    
    # Fetch data for universe (in batches for speed)
    import asyncio
    tasks = [fetch_stock_data(s) for s in STOCK_UNIVERSE[:30]]  # Limit for speed
    stocks = await asyncio.gather(*tasks)
    
    for stock in stocks:
        if apply_filters(stock, filters):
            results.append(stock)
    
    # Sort by market cap
    results.sort(key=lambda x: x.get("market_cap", 0), reverse=True)
    
    return {"screen": screen_id, "filters": filters, "count": len(results), "results": results[:limit]}

@router.get("/custom")
async def custom_screen(
    pe_min: Optional[float] = None, pe_max: Optional[float] = None,
    pb_min: Optional[float] = None, pb_max: Optional[float] = None,
    roe_min: Optional[float] = None, roe_max: Optional[float] = None,
    dividend_yield_min: Optional[float] = None,
    market_cap_min: Optional[float] = None, market_cap_max: Optional[float] = None,
    debt_equity_max: Optional[float] = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Run custom screen with user-defined filters"""
    filters = {}
    if pe_min: filters["pe_min"] = pe_min
    if pe_max: filters["pe_max"] = pe_max
    if pb_min: filters["pb_min"] = pb_min
    if pb_max: filters["pb_max"] = pb_max
    if roe_min: filters["roe_min"] = roe_min
    if roe_max: filters["roe_max"] = roe_max
    if dividend_yield_min: filters["dividend_yield_min"] = dividend_yield_min
    if market_cap_min: filters["market_cap_min"] = market_cap_min
    if market_cap_max: filters["market_cap_max"] = market_cap_max
    if debt_equity_max: filters["debt_equity_max"] = debt_equity_max
    
    if not filters:
        return {"error": "No filters provided"}
    
    import asyncio
    tasks = [fetch_stock_data(s) for s in STOCK_UNIVERSE[:30]]
    stocks = await asyncio.gather(*tasks)
    
    results = [s for s in stocks if apply_filters(s, filters)]
    results.sort(key=lambda x: x.get("market_cap", 0), reverse=True)
    
    return {"filters": filters, "count": len(results), "results": results[:limit]}
