"""
Enhanced stock analysis combining multiple data sources:
- Yahoo Finance (primary for price data)
- NSEpy (NSE official data)
- Screener.in (fundamentals)
"""

from datetime import date, timedelta
from typing import Dict, Optional

import httpx
from bs4 import BeautifulSoup

from ...utils.logger import logger


async def get_nse_data(symbol: str) -> Optional[Dict]:
    """Get data from NSE - disabled due to SSL issues with nsepy"""
    # nsepy library has SSL compatibility issues with NSE website
    # Returning None to skip this data source
    return None


async def get_screener_fundamentals(symbol: str) -> Optional[Dict]:
    """Scrape fundamental data from Screener.in"""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            url = f"https://www.screener.in/company/{symbol}/consolidated/"
            resp = await client.get(
                url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )

            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, "lxml")

            # Extract key metrics
            data = {"symbol": symbol}

            # Market Cap, P/E, etc.
            ratios = soup.find_all("li", class_="flex flex-space-between")
            for ratio in ratios:
                name = ratio.find("span", class_="name")
                value = ratio.find("span", class_="number")
                if name and value:
                    key = name.text.strip().lower().replace(" ", "_")
                    val = value.text.strip()
                    data[key] = val

            # Company name
            name_tag = soup.find("h1")
            if name_tag:
                data["company_name"] = name_tag.text.strip()

            return data
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.error(f"Screener scraping error for {symbol}: {e}")
        return None


async def get_moneycontrol_news(symbol: str) -> list:
    """Scrape news from MoneyControl"""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            # Search for company
            search_url = f"https://www.moneycontrol.com/stocks/cptmarket/compsearchnew.php?search_data=&cid=&mbsearch_str={symbol}&topsearch_type=1"
            resp = await client.get(search_url, headers={"User-Agent": "Mozilla/5.0"})

            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "lxml")

            # Extract news items
            news = []
            news_items = soup.find_all("li", class_="clearfix")[:5]

            for item in news_items:
                title_tag = item.find("a")
                time_tag = item.find("span", class_="ago")

                if title_tag:
                    news.append(
                        {
                            "title": title_tag.text.strip(),
                            "link": title_tag.get("href", ""),
                            "time": time_tag.text.strip() if time_tag else "",
                        }
                    )

            return news
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.error(f"MoneyControl scraping error for {symbol}: {e}")
        return []


async def get_combined_analysis(symbol: str, exchange: str = "NSE") -> Dict:
    """
    Combine data from multiple sources for comprehensive analysis.
    All external calls run in parallel for speed. Results cached in Redis.
    """
    import asyncio

    from ..cache import cache_get, cache_set
    from ..market.price_service import get_historical_data, get_stock_price

    # Check cache first (5 min TTL)
    cache_key = f"analysis:{symbol}:{exchange}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    result = {"symbol": symbol, "exchange": exchange, "sources": {}}

    # Run all fetches in parallel
    yahoo_task = get_stock_price(symbol, exchange)
    hist_task = get_historical_data(symbol, exchange, period="1y")
    fundamentals_task = get_screener_fundamentals(symbol)

    yahoo_data, hist, fundamentals = await asyncio.gather(
        yahoo_task, hist_task, fundamentals_task, return_exceptions=True
    )

    # Process Yahoo data
    if isinstance(yahoo_data, dict) and yahoo_data:
        result["sources"]["yahoo"] = yahoo_data
        result["current_price"] = yahoo_data.get("current_price")
    elif exchange == "NSE":
        # Fallback to BSE
        yahoo_data = await get_stock_price(symbol, "BSE")
        if yahoo_data:
            result["sources"]["yahoo"] = yahoo_data
            result["current_price"] = yahoo_data.get("current_price")
            result["exchange"] = "BSE"

    # Process historical data for technicals
    if isinstance(hist, list) and len(hist) >= 20:
        closes = [d["close"] for d in hist if d.get("close")]
        if len(closes) >= 20:
            result["sma_20"] = round(sum(closes[-20:]) / 20, 2)
            if len(closes) >= 50:
                result["sma_50"] = round(sum(closes[-50:]) / 50, 2)
            if len(closes) >= 200:
                result["sma_200"] = round(sum(closes[-200:]) / 200, 2)

            if len(closes) >= 15:
                changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
                gains = [c if c > 0 else 0 for c in changes[-14:]]
                losses = [-c if c < 0 else 0 for c in changes[-14:]]
                avg_gain, avg_loss = sum(gains) / 14, sum(losses) / 14
                result["rsi"] = round(100 - (100 / (1 + avg_gain / avg_loss)), 1) if avg_loss > 0 else 100
                result["rsi_signal"] = "OVERSOLD" if result["rsi"] < 30 else "OVERBOUGHT" if result["rsi"] > 70 else "NEUTRAL"

            recent = closes[-20:]
            result["support"] = round(min(recent), 2)
            result["resistance"] = round(max(recent), 2)

            if result.get("current_price") and result.get("sma_20"):
                result["trend"] = "BULLISH" if result["current_price"] > result["sma_20"] else "BEARISH"

    # Process fundamentals
    if isinstance(fundamentals, dict) and fundamentals:
        result["sources"]["fundamentals"] = fundamentals
        result["market_cap"] = fundamentals.get("market_cap")
        result["pe_ratio"] = fundamentals.get("stock_p/e")
        result["pb_ratio"] = fundamentals.get("price_to_book_value")
        result["roe"] = fundamentals.get("roe")
        result["roce"] = fundamentals.get("roce")

    sources_available = len([v for v in result["sources"].values() if v])
    result["data_quality"] = f"{sources_available}/3 sources"
    result["recommendation"] = generate_recommendation(result)

    # Cache for 5 minutes
    await cache_set(cache_key, result, 300)

    return result


def generate_recommendation(data: Dict) -> str:
    """Generate buy/hold/sell recommendation based on combined data"""
    score = 0

    # Check P/E ratio
    pe = data.get("pe_ratio")
    if pe:
        try:
            pe_val = float(pe.replace(",", ""))
            if pe_val < 15:
                score += 2
            elif pe_val < 25:
                score += 1
            elif pe_val > 40:
                score -= 2
        except ValueError:
            pass

    # Check ROE
    roe = data.get("roe")
    if roe:
        try:
            roe_val = float(roe.replace(",", ""))
            if roe_val > 15:
                score += 2
            elif roe_val > 10:
                score += 1
        except ValueError:
            pass

    # Check delivery percentage (NSE data)
    nse = data.get("sources", {}).get("nse", {})
    delivery_pct = nse.get("delivery_pct")
    if delivery_pct and delivery_pct > 60:
        score += 1

    if score >= 4:
        return "STRONG_BUY"
    elif score >= 2:
        return "BUY"
    elif score >= 0:
        return "HOLD"
    else:
        return "SELL"
