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
    """Search stocks - filters out MF codes, prioritizes NSE"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"{YAHOO_SEARCH_URL}?q={query}&quotesCount=20"
            resp = await _rate_limited_get(client, url)
            if resp.status_code == 200:
                data = resp.json()
                nse_results = []
                bse_results = []
                for q in data.get("quotes", []):
                    symbol = q.get("symbol", "")
                    name = q.get("shortname") or q.get("longname") or symbol
                    # Skip MF codes (start with 0P or contain only alphanumeric gibberish)
                    base_symbol = symbol.replace(".NS", "").replace(".BO", "")
                    if base_symbol.startswith("0P") or not any(c.isalpha() for c in base_symbol[:3]):
                        continue
                    if ".NS" in symbol:
                        nse_results.append({"symbol": base_symbol, "name": name, "exchange": "NSE"})
                    elif ".BO" in symbol:
                        bse_results.append({"symbol": base_symbol, "name": name, "exchange": "BSE"})
                # Prioritize NSE, then BSE
                return (nse_results + bse_results)[:10]
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.error(f"Error searching {query}: {e}")
    return []


async def get_historical_data(symbol: str, exchange: str = "NSE", period: str = "1y") -> List[Dict]:
    """Fetch historical OHLCV data from Yahoo Finance."""
    symbol = sanitize_symbol(symbol)
    if not symbol:
        return []

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            ticker = f"{symbol}.NS" if exchange == "NSE" else f"{symbol}.BO"
            resp = await _rate_limited_get(client, f"{YAHOO_CHART_URL}/{ticker}?interval=1d&range={period}")
            if resp.status_code == 200:
                result = resp.json().get("chart", {}).get("result", [{}])[0]
                timestamps = result.get("timestamp", [])
                quote = result.get("indicators", {}).get("quote", [{}])[0]
                return [
                    {
                        "date": datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),
                        "open": round(quote["open"][i], 2) if quote["open"][i] else None,
                        "high": round(quote["high"][i], 2) if quote["high"][i] else None,
                        "low": round(quote["low"][i], 2) if quote["low"][i] else None,
                        "close": round(quote["close"][i], 2) if quote["close"][i] else None,
                        "volume": quote["volume"][i] or 0,
                    }
                    for i, ts in enumerate(timestamps)
                    if quote.get("close") and quote["close"][i]
                ]
    except (httpx.HTTPError, KeyError, ValueError, IndexError) as e:
        logger.error(f"Historical data error for {symbol}: {e}")
    return []


# AMFI NAV data for Mutual Funds
AMFI_NAV_URL = "https://www.amfiindia.com/spages/NAVAll.txt"

# Map custom MF symbols to AMFI scheme codes
MF_SCHEME_CODES = {
    "PPFAS": "122639",  # Parag Parikh Flexi Cap Fund Direct Growth
    "BANDHAN-SC": "145455",  # Bandhan Small Cap Fund Direct Growth
    "KOTAK-LM": "120503",  # Kotak Large & Midcap Fund Direct Growth
    "HDFC-MC": "101762",  # HDFC Mid Cap Fund Direct Growth
    "AXIS-LIQ": "119064",  # Axis Liquid Direct Fund Growth
    "MOTILAL-MC": "147622",  # Motilal Oswal Midcap Fund Direct Growth
    "PGIM-USD": "149295",  # PGIM India Ultra Short Duration Direct Growth
}


async def get_bulk_mf_nav(symbols: List[str]) -> Dict[str, Dict]:
    """Get NAV for multiple mutual funds from AMFI."""
    if not symbols:
        return {}

    # Check Redis cache for all NAVs
    cache_key = "amfi:navs"
    cached = await cache_get(cache_key)

    if not cached:
        # Fetch from AMFI
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(AMFI_NAV_URL)
                if resp.status_code == 200:
                    cached = {}
                    for line in resp.text.split("\n"):
                        parts = line.strip().split(";")
                        if len(parts) >= 5 and parts[0].isdigit():
                            cached[parts[0]] = float(parts[4]) if parts[4] else 0
                    await cache_set(cache_key, cached, 3600)  # Cache 1 hour
        except Exception as e:
            logger.error(f"AMFI NAV fetch error: {e}")
            return {}

    if not cached:
        return {}

    # Map symbols to NAVs
    results = {}
    for symbol in symbols:
        scheme_code = MF_SCHEME_CODES.get(symbol.upper())
        if scheme_code and scheme_code in cached:
            results[symbol] = {"nav": cached[scheme_code]}
    return results
