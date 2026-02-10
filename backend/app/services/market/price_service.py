import asyncio
import re
import time
from datetime import datetime
from typing import Dict, List, Optional

import httpx

from ...core.constants import YAHOO_CHART_URL, YAHOO_SEARCH_URL
from ...utils.logger import logger
from ..cache import cache_get, cache_mget, cache_mset, cache_set

# Rate limiter: max 10 requests/sec
_last_request_time = 0
_rate_lock = asyncio.Lock()

# Input validation pattern - alphanumeric, dash, ampersand only
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9&-]{1,20}$")
CACHE_PREFIX = "price:"


def sanitize_symbol(symbol: str) -> Optional[str]:
    """Sanitize and validate stock symbol input."""
    if not symbol:
        return None
    cleaned = symbol.strip().upper().replace(" ", "")
    if not SYMBOL_PATTERN.match(cleaned):
        logger.warning(f"Invalid symbol rejected: {symbol}")
        return None
    return cleaned


def is_market_open() -> bool:
    """Check if Indian stock market is open (NSE/BSE)"""
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_start <= now <= market_end


def get_cache_ttl() -> int:
    return 60 if is_market_open() else 3600


async def _rate_limited_get(client: httpx.AsyncClient, url: str) -> httpx.Response:
    global _last_request_time
    async with _rate_lock:
        wait = max(0, 0.1 - (time.time() - _last_request_time))
        if wait:
            await asyncio.sleep(wait)
        _last_request_time = time.time()
    return await client.get(url, headers={"User-Agent": "Mozilla/5.0"})


async def _fetch_yahoo(symbol: str, exchange: str) -> Optional[Dict]:
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            ticker = f"{symbol}.NS" if exchange == "NSE" else f"{symbol}.BO"
            resp = await _rate_limited_get(client, f"{YAHOO_CHART_URL}/{ticker}")
            if resp.status_code == 200:
                meta = resp.json().get("chart", {}).get("result", [{}])[0].get("meta", {})
                if meta.get("regularMarketPrice"):
                    current = meta["regularMarketPrice"]
                    prev = meta.get("previousClose", current)
                    return {
                        "symbol": symbol,
                        "name": meta.get("shortName", symbol),
                        "exchange": exchange,
                        "current_price": current,
                        "previous_close": prev,
                        "day_open": meta.get("regularMarketOpen"),
                        "day_high": meta.get("regularMarketDayHigh"),
                        "day_low": meta.get("regularMarketDayLow"),
                        "day_change": round(current - prev, 2),
                        "day_change_pct": round((current - prev) / prev * 100, 2) if prev else 0,
                        "volume": meta.get("regularMarketVolume"),
                        "source": "yahoo",
                    }
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.debug(f"Yahoo failed for {symbol}: {e}")
    return None


async def _fetch_moneycontrol(symbol: str) -> Optional[Dict]:
    MC_CODES = {
        "RELIANCE": "RI",
        "TCS": "TCS",
        "HDFCBANK": "HDF01",
        "INFY": "IT",
        "ICICIBANK": "ICI02",
        "SBIN": "SBI",
        "BHARTIARTL": "BA08",
        "ITC": "ITC",
        "KOTAKBANK": "KMB",
        "LT": "LT",
        "AXISBANK": "AB16",
        "HINDUNILVR": "HU",
        "BAJFINANCE": "BAF",
        "MARUTI": "MS24",
        "TITAN": "TI01",
        "SUNPHARMA": "SU12",
        "WIPRO": "W",
        "HCLTECH": "HCL02",
        "NTPC": "NTP",
        "POWERGRID": "PGC",
        "ONGC": "ONG",
        "TATASTEEL": "TIS",
        "TATAMOTORS": "TM03",
        "COALINDIA": "CI11",
        "ASIANPAINT": "AP31",
        "ULTRACEMCO": "UC",
        "TECHM": "TM4",
        "DRREDDY": "DRR",
        "CIPLA": "C",
        "DIVISLAB": "DL03",
        "BRITANNIA": "BI01",
        "NESTLEIND": "NI15",
    }
    mc_code = MC_CODES.get(symbol.upper())
    if not mc_code:
        return None
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(f"https://priceapi.moneycontrol.com/pricefeed/nse/equitycash/{mc_code}")
            if resp.status_code == 200:
                d = resp.json().get("data", {})
                if d.get("pricecurrent"):
                    current = float(d["pricecurrent"])
                    prev = float(d.get("priceclose", current))
                    return {
                        "symbol": symbol,
                        "name": d.get("SC_FULLNM", symbol),
                        "exchange": "NSE",
                        "current_price": current,
                        "previous_close": prev,
                        "day_open": float(d["priceopen"]) if d.get("priceopen") else None,
                        "day_high": float(d["pricehigh"]) if d.get("pricehigh") else None,
                        "day_low": float(d["pricelow"]) if d.get("pricelow") else None,
                        "day_change": round(current - prev, 2),
                        "day_change_pct": round((current - prev) / prev * 100, 2) if prev else 0,
                        "volume": int(d["VOL"]) if d.get("VOL") else None,
                        "source": "moneycontrol",
                    }
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.debug(f"MoneyControl failed for {symbol}: {e}")
    return None


async def _fetch_google(symbol: str) -> Optional[Dict]:
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                f"https://www.google.com/finance/quote/{symbol}:NSE",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if resp.status_code == 200:
                price_match = re.search(r'data-last-price="([\d.]+)"', resp.text)
                prev_match = re.search(r'data-previous-close="([\d.]+)"', resp.text)
                if price_match:
                    current = float(price_match.group(1))
                    prev = float(prev_match.group(1)) if prev_match else current
                    return {
                        "symbol": symbol,
                        "name": symbol,
                        "exchange": "NSE",
                        "current_price": current,
                        "previous_close": prev,
                        "day_change": round(current - prev, 2),
                        "day_change_pct": round((current - prev) / prev * 100, 2) if prev else 0,
                        "source": "google",
                    }
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.debug(f"Google failed for {symbol}: {e}")
    return None


async def get_stock_price(symbol: str, exchange: str = "NSE") -> Optional[Dict]:
    """Fetch stock price with Redis caching and multi-source fallback."""
    symbol = sanitize_symbol(symbol)
    if not symbol:
        return None

    cache_key = f"{CACHE_PREFIX}{symbol}:{exchange}"
    cache_ttl = get_cache_ttl()

    # Check Redis cache
    cached = await cache_get(cache_key)
    if cached:
        return cached

    # Try sources in order: Yahoo -> MoneyControl -> Google
    data = await _fetch_yahoo(symbol, exchange)
    if not data:
        data = await _fetch_moneycontrol(symbol)
    if not data:
        data = await _fetch_google(symbol)

    if data:
        await cache_set(cache_key, data, cache_ttl)
        return data

    logger.warning(f"All sources failed for {symbol}")
    return None


async def get_bulk_prices(symbols: List[str], exchange: str = "NSE") -> Dict[str, Dict]:
    """Fetch prices for multiple symbols with Redis caching."""
    symbols = [s for s in (sanitize_symbol(s) for s in symbols) if s]
    if not symbols:
        return {}

    cache_ttl = get_cache_ttl()
    cache_keys = [f"{CACHE_PREFIX}{s}:{exchange}" for s in symbols]

    # Batch get from Redis
    cached = await cache_mget(cache_keys)
    prices = {}
    uncached = []

    for symbol, key in zip(symbols, cache_keys):
        if cached.get(key):
            prices[symbol] = cached[key]
        else:
            uncached.append(symbol)

    if not uncached:
        return prices

    # Fetch uncached symbols concurrently
    tasks = [get_stock_price(s, exchange) for s in uncached]
    results = await asyncio.gather(*tasks)

    # Batch set to Redis
    to_cache = {}
    for symbol, data in zip(uncached, results):
        if data:
            prices[symbol] = data
            to_cache[f"{CACHE_PREFIX}{symbol}:{exchange}"] = data

    if to_cache:
        await cache_mset(to_cache, cache_ttl)

    return prices


async def search_stock(query: str) -> List[Dict]:
    """Search stocks"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"{YAHOO_SEARCH_URL}?q={query}&quotesCount=10"
            resp = await _rate_limited_get(client, url)
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for q in data.get("quotes", []):
                    symbol = q.get("symbol", "")
                    if ".NS" in symbol:
                        results.append(
                            {
                                "symbol": symbol.replace(".NS", ""),
                                "name": q.get("shortname", symbol),
                                "exchange": "NSE",
                            }
                        )
                    elif ".BO" in symbol:
                        results.append(
                            {
                                "symbol": symbol.replace(".BO", ""),
                                "name": q.get("shortname", symbol),
                                "exchange": "BSE",
                            }
                        )
                return results
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.error(f"Error searching {query}: {e}")
    return []
