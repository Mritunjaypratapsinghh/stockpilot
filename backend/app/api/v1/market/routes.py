"""Market routes - quotes, search, indices, research, screener, compare, corporate actions."""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from beanie import PydanticObjectId
import httpx

from ....services.market.price_service import get_stock_price, get_bulk_prices, search_stock
from ....services.analytics.service import get_combined_analysis
from ....models.documents import Holding
from ....core.security import get_current_user
from ....core.response_handler import StandardResponse
from ....middleware.rate_limit import rate_limit
from ....utils.logger import logger

router = APIRouter()


@router.get("/quote/{symbol}", summary="Get stock quote", description="Get real-time price for a stock")
async def get_quote(symbol: str, exchange: str = "NSE") -> StandardResponse:
    """Get real-time stock quote."""
    price_data = await get_stock_price(symbol.upper(), exchange)
    if not price_data:
        raise HTTPException(status_code=404, detail="Stock not found")
    return StandardResponse.ok(price_data)


@router.get("/search", summary="Search stocks", description="Search for stocks by name or symbol", dependencies=[Depends(rate_limit("search"))])
async def search(q: str) -> StandardResponse:
    """Search for stocks by name or symbol."""
    return StandardResponse.ok(await search_stock(q))


@router.get("/indices", summary="Get market indices", description="Get NIFTY, SENSEX, BANKNIFTY prices")
async def get_indices() -> StandardResponse:
    """Get major market indices prices."""
    indices = {"NIFTY50": "^NSEI", "SENSEX": "^BSESN", "BANKNIFTY": "^NSEBANK"}
    result: dict = {}
    async with httpx.AsyncClient(timeout=10) as client:
        for name, symbol in indices.items():
            try:
                resp = await client.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}", headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    meta = resp.json()["chart"]["result"][0]["meta"]
                    price = meta.get("regularMarketPrice", 0)
                    prev = meta.get("previousClose", price)
                    result[name] = {"price": round(price, 2), "change": round(price - prev, 2), "change_pct": round((price - prev) / prev * 100, 2) if prev else 0}
            except (httpx.HTTPError, KeyError, ValueError):
                pass
    return StandardResponse.ok(result)


@router.get("/quotes", summary="Get bulk quotes", description="Get prices for multiple stocks")
async def get_bulk_quotes(symbols: str) -> StandardResponse:
    """Get prices for multiple stocks at once."""
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    return StandardResponse.ok(await get_bulk_prices(symbol_list))


@router.get("/research/{symbol}", summary="Get stock research", description="Get detailed analysis for a stock")
async def get_enhanced_analysis(symbol: str, exchange: str = "NSE") -> StandardResponse:
    """Get detailed stock analysis and research."""
    return StandardResponse.ok(await get_combined_analysis(symbol.upper(), exchange))


@router.get("/research/{symbol}/news", summary="Get stock news", description="Get latest news for a stock")
async def get_stock_news(symbol: str) -> StandardResponse:
    """Get latest news for a stock."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"https://query1.finance.yahoo.com/v1/finance/search?q={symbol}", headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                return StandardResponse.ok({"symbol": symbol, "news": resp.json().get("news", [])[:5]})
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.warning(f"News fetch error for {symbol}: {e}")
    return StandardResponse.ok({"symbol": symbol, "news": []})


@router.get("/research/{symbol}/chart", summary="Get chart data", description="Get OHLCV candle data for charts")
async def get_chart_data(symbol: str, range: str = "6mo", interval: str = "1d") -> StandardResponse:
    """Get OHLCV chart data for a stock."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS?interval={interval}&range={range}", headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                result = resp.json()["chart"]["result"][0]
                timestamps = result.get("timestamp", [])
                quote = result["indicators"]["quote"][0]
                candles = [{"time": ts, "open": round(quote["open"][i], 2), "high": round(quote["high"][i], 2), "low": round(quote["low"][i], 2), "close": round(quote["close"][i], 2), "volume": quote["volume"][i] or 0}
                           for i, ts in enumerate(timestamps) if quote["open"][i] and quote["close"][i]]
                return StandardResponse.ok({"symbol": symbol, "candles": candles})
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.warning(f"Chart error for {symbol}: {e}")
    return StandardResponse.ok({"symbol": symbol, "candles": []})


@router.get("/screener/gainers", summary="Get top gainers/losers", description="Get top gaining and losing stocks")
async def get_top_gainers() -> StandardResponse:
    """Get top gaining and losing stocks."""
    symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "KOTAKBANK", "SBIN", "BHARTIARTL", "ITC", "LT"]
    prices = await get_bulk_prices(symbols)
    sorted_stocks = sorted([{"symbol": s, **prices.get(s, {})} for s in symbols if prices.get(s)], key=lambda x: x.get("day_change_pct", 0), reverse=True)
    return StandardResponse.ok({"gainers": sorted_stocks[:5], "losers": sorted_stocks[-5:][::-1]})


@router.get("/screener/52week", summary="Get 52-week highs/lows", description="Get stocks near 52-week high or low")
async def get_52week_highs_lows() -> StandardResponse:
    """Get stocks near 52-week high or low."""
    symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]
    result: dict = {"near_high": [], "near_low": []}
    async with httpx.AsyncClient(timeout=10) as client:
        for symbol in symbols:
            try:
                resp = await client.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS?interval=1d&range=1y", headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    data = resp.json()["chart"]["result"][0]
                    highs = [h for h in data["indicators"]["quote"][0]["high"] if h]
                    lows = [low for low in data["indicators"]["quote"][0]["low"] if low]
                    current = data["meta"].get("regularMarketPrice", 0)
                    if highs and current >= max(highs) * 0.95:
                        result["near_high"].append({"symbol": symbol, "price": current, "high_52w": max(highs)})
                    if lows and current <= min(lows) * 1.05:
                        result["near_low"].append({"symbol": symbol, "price": current, "low_52w": min(lows)})
            except (httpx.HTTPError, KeyError, ValueError):
                pass
    return StandardResponse.ok(result)


@router.get("/compare", summary="Compare stocks", description="Compare multiple stocks side by side")
async def compare_stocks(symbols: str) -> StandardResponse:
    """Compare multiple stocks side by side."""
    symbol_list = [s.strip().upper() for s in symbols.split(",")][:5]
    prices = await get_bulk_prices(symbol_list)
    stocks = [{"symbol": s, **prices.get(s, {})} for s in symbol_list if prices.get(s)]
    
    # Build comparison with best/worst for each metric
    comparison = {}
    metrics = ["price", "market_cap", "pe", "pb", "roe", "roce", "debt_equity", "profit_margin", "revenue_growth", "dividend_yield"]
    for metric in metrics:
        values = [(s["symbol"], s.get(metric, 0) or 0) for s in stocks]
        if values:
            sorted_vals = sorted(values, key=lambda x: x[1], reverse=True)
            comparison[metric] = {"best": sorted_vals[0][0], "worst": sorted_vals[-1][0]}
    
    return StandardResponse.ok({"stocks": stocks, "comparison": comparison})


@router.get("/corporate-actions", summary="Get corporate actions", description="Get dividends and splits for portfolio stocks")
async def get_corporate_actions(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get corporate actions for portfolio stocks."""
    holdings = await Holding.find(Holding.user_id == PydanticObjectId(current_user["_id"])).to_list()
    if not holdings:
        return StandardResponse.ok({"actions": [], "upcoming": []})

    symbols = [h.symbol for h in holdings if h.holding_type != "MF"][:10]
    actions: list = []
    upcoming: list = []

    async with httpx.AsyncClient(timeout=10) as client:
        for symbol in symbols:
            try:
                resp = await client.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS?interval=1d&range=1y&events=div", headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    events = resp.json().get("chart", {}).get("result", [{}])[0].get("events", {})
                    for ts, div in events.get("dividends", {}).items():
                        action = {"type": "DIVIDEND", "symbol": symbol, "date": datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d"), "value": div.get("amount", 0)}
                        actions.append(action)
                        if datetime.fromtimestamp(int(ts)) > datetime.now():
                            upcoming.append(action)
            except (httpx.HTTPError, KeyError, ValueError):
                pass

    return StandardResponse.ok({"actions": sorted(actions, key=lambda x: x["date"], reverse=True)[:20], "upcoming": upcoming})


@router.get("/market-summary", summary="Get market summary", description="Get top movers and market overview")
async def get_market_summary() -> StandardResponse:
    """Get market summary with top movers."""
    symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "KOTAKBANK", "SBIN", "BHARTIARTL", "ITC", "LT"]
    prices = await get_bulk_prices(symbols)
    movers = sorted([{"symbol": s, "price": p.get("current_price", 0), "change_pct": p.get("day_change_pct", 0)} for s, p in prices.items() if p], key=lambda x: abs(x["change_pct"]), reverse=True)
    return StandardResponse.ok({"top_movers": movers[:10]})


@router.get("/fii-dii", summary="Get FII/DII data", description="Get FII and DII activity data")
async def get_fii_dii() -> StandardResponse:
    """Get FII/DII activity data."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://www.nseindia.com/api/fiidiiTradeReact", headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
            if resp.status_code == 200:
                data = resp.json()
                return StandardResponse.ok({
                    "fii": {"buy": data.get("fpiPurchaseValue", 0), "sell": data.get("fpiSalesValue", 0), "net": data.get("fpiNetValue", 0)},
                    "dii": {"buy": data.get("diiPurchaseValue", 0), "sell": data.get("diiSalesValue", 0), "net": data.get("diiNetValue", 0)}
                })
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.warning(f"FII/DII fetch error: {e}")
    return StandardResponse.ok({"note": "FII/DII data temporarily unavailable"})


@router.get("/screener/screens", summary="Get screener screens", description="Get predefined stock screens")
async def get_screener_screens() -> StandardResponse:
    """Get predefined screens."""
    screens = [
        {"id": "gainers", "name": "Top Gainers", "description": "Stocks with highest daily gains"},
        {"id": "losers", "name": "Top Losers", "description": "Stocks with highest daily losses"},
        {"id": "52w_high", "name": "52 Week High", "description": "Stocks near 52-week high"},
        {"id": "52w_low", "name": "52 Week Low", "description": "Stocks near 52-week low"},
        {"id": "high_volume", "name": "High Volume", "description": "Stocks with unusual volume"}
    ]
    return StandardResponse.ok({"screens": screens})


@router.get("/screener/run/{screen_id}", summary="Run screener", description="Run a predefined screen")
async def run_screener(screen_id: str) -> StandardResponse:
    """Run a predefined screen."""
    symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "KOTAKBANK", "SBIN", "BHARTIARTL", "ITC", "LT"]
    prices = await get_bulk_prices(symbols)
    
    results = [{"symbol": s, "price": p.get("price", 0), "change_pct": p.get("day_change_pct", 0)} for s, p in prices.items() if p]
    
    if screen_id == "gainers":
        results = sorted(results, key=lambda x: x["change_pct"], reverse=True)[:10]
    elif screen_id == "losers":
        results = sorted(results, key=lambda x: x["change_pct"])[:10]
    
    return StandardResponse.ok({"results": results})


@router.get("/screener/custom", summary="Custom screener", description="Run custom stock screen")
async def custom_screener(pe_max: float = None, pb_max: float = None, roe_min: float = None, dividend_yield_min: float = None, market_cap_min: float = None) -> StandardResponse:
    """Run custom screen."""
    symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]
    prices = await get_bulk_prices(symbols)
    results = [{"symbol": s, "price": p.get("price", 0), "change_pct": p.get("day_change_pct", 0)} for s, p in prices.items() if p]
    return StandardResponse.ok({"results": results})
