"""Multi-source price service with fallback chain"""
import httpx
import asyncio
import time
from typing import Dict, Optional, List
from ...utils.logger import logger

# Cache: symbol -> (data, timestamp)
_cache: Dict[str, tuple] = {}
CACHE_TTL = 60  # 1 minute for live data

async def _fetch_yahoo_chart(symbol: str) -> Optional[Dict]:
    """Source 1: Yahoo Finance Chart API"""
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS"
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                data = resp.json().get("chart", {}).get("result", [{}])[0]
                meta = data.get("meta", {})
                if meta.get("regularMarketPrice"):
                    return {
                        "symbol": symbol,
                        "name": meta.get("shortName", symbol),
                        "price": meta.get("regularMarketPrice"),
                        "prev_close": meta.get("previousClose"),
                        "open": meta.get("regularMarketOpen"),
                        "high": meta.get("regularMarketDayHigh"),
                        "low": meta.get("regularMarketDayLow"),
                        "volume": meta.get("regularMarketVolume"),
                        "source": "yahoo"
                    }
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.debug(f"Yahoo chart failed for {symbol}: {e}")
    return None

async def _fetch_google_finance(symbol: str) -> Optional[Dict]:
    """Source 2: Google Finance (scrape)"""
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            url = f"https://www.google.com/finance/quote/{symbol}:NSE"
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                text = resp.text
                # Extract price from data-last-price attribute
                import re
                price_match = re.search(r'data-last-price="([\d.]+)"', text)
                prev_match = re.search(r'data-previous-close="([\d.]+)"', text)
                if price_match:
                    return {
                        "symbol": symbol,
                        "name": symbol,
                        "price": float(price_match.group(1)),
                        "prev_close": float(prev_match.group(1)) if prev_match else None,
                        "source": "google"
                    }
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.debug(f"Google finance failed for {symbol}: {e}")
    return None

async def _fetch_nse_direct(symbol: str) -> Optional[Dict]:
    """Source 3: NSE India direct"""
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            # First get cookies
            await client.get("https://www.nseindia.com", headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
            resp = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json"
            })
            if resp.status_code == 200:
                data = resp.json().get("priceInfo", {})
                if data.get("lastPrice"):
                    return {
                        "symbol": symbol,
                        "name": resp.json().get("info", {}).get("companyName", symbol),
                        "price": data.get("lastPrice"),
                        "prev_close": data.get("previousClose"),
                        "open": data.get("open"),
                        "high": data.get("intraDayHighLow", {}).get("max"),
                        "low": data.get("intraDayHighLow", {}).get("min"),
                        "volume": data.get("totalTradedVolume"),
                        "source": "nse"
                    }
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.debug(f"NSE direct failed for {symbol}: {e}")
    return None

async def _fetch_moneycontrol(symbol: str) -> Optional[Dict]:
    """Source 4: MoneyControl"""
    # Map common symbols to moneycontrol codes
    MC_CODES = {
        "RELIANCE": "RI", "TCS": "TCS", "HDFCBANK": "HDF01", "INFY": "IT",
        "ICICIBANK": "ICI02", "SBIN": "SBI", "BHARTIARTL": "BA08", "ITC": "ITC",
        "KOTAKBANK": "KMB", "LT": "LT", "AXISBANK": "AB16", "HINDUNILVR": "HU",
        "BAJFINANCE": "BAF", "MARUTI": "MS24", "TITAN": "TI01", "SUNPHARMA": "SU12",
        "WIPRO": "W", "HCLTECH": "HCL02", "NTPC": "NTP", "POWERGRID": "PGC",
        "ONGC": "ONG", "TATASTEEL": "TIS", "TATAMOTORS": "TM03", "COALINDIA": "CI11"
    }
    mc_code = MC_CODES.get(symbol)
    if not mc_code:
        return None
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            url = f"https://priceapi.moneycontrol.com/pricefeed/nse/equitycash/{mc_code}"
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                if data.get("pricecurrent"):
                    return {
                        "symbol": symbol,
                        "name": data.get("SC_FULLNM", symbol),
                        "price": float(data.get("pricecurrent")),
                        "prev_close": float(data.get("priceclose")) if data.get("priceclose") else None,
                        "open": float(data.get("priceopen")) if data.get("priceopen") else None,
                        "high": float(data.get("pricehigh")) if data.get("pricehigh") else None,
                        "low": float(data.get("pricelow")) if data.get("pricelow") else None,
                        "volume": int(data.get("VOL")) if data.get("VOL") else None,
                        "source": "moneycontrol"
                    }
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.debug(f"MoneyControl failed for {symbol}: {e}")
    return None

async def get_price(symbol: str, use_cache: bool = True) -> Optional[Dict]:
    """Get stock price with multi-source fallback"""
    symbol = symbol.upper()
    
    # Check cache
    if use_cache and symbol in _cache:
        data, ts = _cache[symbol]
        if time.time() - ts < CACHE_TTL:
            return data
    
    # Try sources in order
    sources = [
        _fetch_yahoo_chart,
        _fetch_moneycontrol,
        _fetch_google_finance,
        _fetch_nse_direct,
    ]
    
    for fetch_fn in sources:
        data = await fetch_fn(symbol)
        if data:
            # Calculate change
            if data.get("prev_close") and data.get("price"):
                data["change"] = round(data["price"] - data["prev_close"], 2)
                data["change_pct"] = round((data["change"] / data["prev_close"]) * 100, 2)
            _cache[symbol] = (data, time.time())
            logger.info(f"Price for {symbol} from {data['source']}")
            return data
    
    logger.warning(f"All sources failed for {symbol}")
    return None

async def get_bulk_prices(symbols: List[str]) -> Dict[str, Dict]:
    """Get prices for multiple symbols concurrently"""
    tasks = [get_price(s) for s in symbols]
    results = await asyncio.gather(*tasks)
    return {s: r for s, r in zip(symbols, results) if r}
