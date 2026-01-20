import httpx
import asyncio
import time
from typing import Optional, Dict, List
from datetime import datetime
from ..logger import logger
from ..config import YAHOO_CHART_URL, YAHOO_SEARCH_URL

# Rate limiter: max 2 requests/sec to Yahoo Finance
_last_request_time = 0
_rate_lock = asyncio.Lock()
_cache: Dict[str, tuple] = {}  # symbol -> (data, timestamp)

def is_market_open() -> bool:
    """Check if Indian stock market is open (NSE/BSE)"""
    now = datetime.now()
    # Market closed on weekends
    if now.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    # Market hours: 9:15 AM - 3:30 PM IST
    market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_start <= now <= market_end

def get_cache_ttl() -> int:
    """Return cache TTL based on market hours"""
    if is_market_open():
        return 60  # 1 minute during market hours
    else:
        return 3600  # 1 hour when market is closed

async def _rate_limited_get(client: httpx.AsyncClient, url: str) -> httpx.Response:
    global _last_request_time
    async with _rate_lock:
        now = time.time()
        wait = max(0, 0.1 - (now - _last_request_time))  # 10 req/sec max
        if wait:
            await asyncio.sleep(wait)
        _last_request_time = time.time()
    return await client.get(url, headers={"User-Agent": "Mozilla/5.0"})

async def get_stock_price(symbol: str, exchange: str = "NSE") -> Optional[Dict]:
    """Fetch stock price from Yahoo Finance with caching and rate limiting"""
    cache_key = f"{symbol}:{exchange}"
    cache_ttl = get_cache_ttl()
    
    # Check cache
    if cache_key in _cache:
        data, ts = _cache[cache_key]
        if time.time() - ts < cache_ttl:
            return data
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            ticker = f"{symbol}.NS" if exchange == "NSE" else f"{symbol}.BO"
            url = f"'${YAHOO_CHART_URL}'/{ticker}"
            resp = await _rate_limited_get(client, url)
            
            if resp.status_code == 200:
                data = resp.json()
                result = data.get("chart", {}).get("result", [{}])[0]
                meta = result.get("meta", {})
                
                current = meta.get("regularMarketPrice", 0)
                prev_close = meta.get("previousClose", current)
                
                price_data = {
                    "symbol": symbol,
                    "name": meta.get("shortName", symbol),
                    "exchange": exchange,
                    "current_price": current,
                    "previous_close": prev_close,
                    "day_open": meta.get("regularMarketOpen", current),
                    "day_high": meta.get("regularMarketDayHigh", current),
                    "day_low": meta.get("regularMarketDayLow", current),
                    "day_change": round(current - prev_close, 2),
                    "day_change_pct": round(((current - prev_close) / prev_close * 100) if prev_close else 0, 2),
                    "volume": meta.get("regularMarketVolume", 0)
                }
                _cache[cache_key] = (price_data, time.time())
                return price_data
            else:
                logger.warning(f"Yahoo API returned {resp.status_code} for {symbol}")
    except Exception as e:
        logger.error(f"Error fetching {symbol}: {e}")
    return None

async def get_bulk_prices(symbols: List[str], exchange: str = "NSE") -> Dict[str, Dict]:
    """Fetch prices for multiple symbols - skips API during off-market hours"""
    if not symbols or not is_market_open():
        return {}  # Return empty - use stored prices during off-market
    
    # Check cache first
    cache_ttl = get_cache_ttl()
    prices = {}
    uncached = []
    
    for symbol in symbols:
        cache_key = f"{symbol}:{exchange}"
        if cache_key in _cache:
            data, ts = _cache[cache_key]
            if time.time() - ts < cache_ttl:
                prices[symbol] = data
                continue
        uncached.append(symbol)
    
    if not uncached:
        return prices
    
    # Fetch all uncached symbols with single shared client
    async with httpx.AsyncClient(timeout=10) as client:
        async def fetch_one(symbol: str) -> tuple:
            try:
                ticker = f"{symbol}.NS" if exchange == "NSE" else f"{symbol}.BO"
                url = f"'${YAHOO_CHART_URL}'/{ticker}"
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    data = resp.json()
                    result = data.get("chart", {}).get("result", [{}])[0]
                    meta = result.get("meta", {})
                    current = meta.get("regularMarketPrice", 0)
                    prev_close = meta.get("previousClose", current)
                    price_data = {
                        "symbol": symbol,
                        "current_price": current,
                        "previous_close": prev_close,
                        "day_change_pct": round(((current - prev_close) / prev_close * 100) if prev_close else 0, 2),
                    }
                    _cache[f"{symbol}:{exchange}"] = (price_data, time.time())
                    return symbol, price_data
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
            return symbol, None
        
        results = await asyncio.gather(*[fetch_one(s) for s in uncached])
        for symbol, data in results:
            if data:
                prices[symbol] = data
    
    return prices

async def search_stock(query: str) -> List[Dict]:
    """Search stocks"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"{YAHOO_SEARCH_URL}?q={query}&quotesCount=5"
            resp = await _rate_limited_get(client, url)
            if resp.status_code == 200:
                data = resp.json()
                return [{"symbol": q["symbol"].replace(".NS", ""), "name": q.get("shortname", q["symbol"]), "exchange": "NSE"} 
                        for q in data.get("quotes", []) if ".NS" in q.get("symbol", "")]
    except Exception as e:
        logger.error(f"Error searching {query}: {e}")
    return []
