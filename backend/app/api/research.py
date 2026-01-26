from fastapi import APIRouter, Depends
import httpx
import asyncio
from datetime import datetime
from bson import ObjectId
from bs4 import BeautifulSoup
from ..database import get_db
from ..api.auth import get_current_user
from ..services.enhanced_analysis import get_combined_analysis

router = APIRouter()
_cache = {}

@router.get("/enhanced/{symbol}")
async def get_enhanced_analysis(symbol: str, exchange: str = "NSE"):
    """
    Get comprehensive analysis from multiple sources:
    - Yahoo Finance (price data)
    - NSEpy (NSE official data with VWAP, delivery %)
    - Screener.in (fundamentals: P/E, P/B, Market Cap)
    - MoneyControl (news)
    """
    return await get_combined_analysis(symbol.upper(), exchange)

@router.get("/news/{symbol}")
async def get_stock_news(symbol: str):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"https://query1.finance.yahoo.com/v1/finance/search?q={symbol}", headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                data = resp.json()
                return {"symbol": symbol, "news": data.get("news", [])[:5]}
    except:
        pass
    return {"symbol": symbol, "news": []}

@router.get("/chart/{symbol}")
async def get_chart_data(symbol: str, range: str = "6mo", interval: str = "1d"):
    """Get OHLCV data for charts"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS?interval={interval}&range={range}",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            if resp.status_code == 200:
                result = resp.json()["chart"]["result"][0]
                timestamps = result.get("timestamp", [])
                quote = result["indicators"]["quote"][0]
                
                candles = []
                for i, ts in enumerate(timestamps):
                    if quote["open"][i] and quote["close"][i]:
                        candles.append({
                            "time": ts,
                            "open": round(quote["open"][i], 2),
                            "high": round(quote["high"][i], 2),
                            "low": round(quote["low"][i], 2),
                            "close": round(quote["close"][i], 2),
                            "volume": quote["volume"][i] or 0
                        })
                
                meta = result.get("meta", {})
                return {
                    "symbol": symbol,
                    "name": meta.get("shortName", symbol),
                    "currency": meta.get("currency", "INR"),
                    "candles": candles
                }
    except Exception as e:
        return {"symbol": symbol, "error": str(e), "candles": []}
    return {"symbol": symbol, "candles": []}

@router.get("/analysis/{symbol}")
async def get_technical_analysis(symbol: str, exchange: str = "NSE"):
    """Get technical analysis with automatic NSE->BSE fallback"""
    try:
        suffix = ".NS" if exchange == "NSE" else ".BO"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}{suffix}?interval=1d&range=6mo", headers={"User-Agent": "Mozilla/5.0"})
            
            # If NSE fails, try BSE automatically
            if resp.status_code != 200 and exchange == "NSE":
                resp = await client.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.BO?interval=1d&range=6mo", headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    exchange = "BSE"  # Update exchange for response
            
            if resp.status_code == 200:
                result = resp.json()["chart"]["result"][0]
                closes = result["indicators"]["quote"][0]["close"]
                highs = result["indicators"]["quote"][0]["high"]
                lows = result["indicators"]["quote"][0]["low"]
                closes = [c for c in closes if c]
                highs = [h for h in highs if h]
                lows = [l for l in lows if l]
                
                if len(closes) < 2:
                    return {"symbol": symbol, "error": "Insufficient data - stock may be newly listed or illiquid", "data_points": len(closes)}
                
                current = closes[-1]
                
                # Adjust calculations based on available data
                sma_period = min(20, len(closes))
                sma_20 = sum(closes[-sma_period:]) / sma_period
                sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else None
                sma_200 = sum(closes[-200:]) / 200 if len(closes) >= 200 else None
                
                # RSI (adjust period based on available data)
                if len(closes) >= 3:
                    rsi_period = min(14, len(closes) - 1)
                    gains, losses = [], []
                    for i in range(1, rsi_period + 1):
                        if i >= len(closes):
                            break
                        diff = closes[-i] - closes[-i-1]
                        if diff > 0:
                            gains.append(diff)
                        else:
                            losses.append(abs(diff))
                    avg_gain = sum(gains) / rsi_period if gains else 0
                    avg_loss = sum(losses) / rsi_period if losses else 0.001
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                else:
                    rsi = 50  # Neutral for very limited data
                
                trend = "BULLISH" if current > sma_20 else "BEARISH"
                
                # Support/Resistance (use all available data)
                support = min(closes)
                resistance = max(closes)
                
                # Pattern detection only if enough data
                pattern = detect_pattern(closes, highs, lows) if len(closes) >= 5 else "INSUFFICIENT_DATA"
                
                return {
                    "symbol": symbol,
                    "exchange": exchange,  # Return actual exchange used
                    "current_price": round(current, 2),
                    "sma_20": round(sma_20, 2),
                    "sma_50": round(sma_50, 2) if sma_50 else None,
                    "sma_200": round(sma_200, 2) if sma_200 else None,
                    "rsi": round(rsi, 2),
                    "trend": trend,
                    "rsi_signal": "OVERSOLD" if rsi < 30 else "OVERBOUGHT" if rsi > 70 else "NEUTRAL",
                    "support": round(support, 2),
                    "resistance": round(resistance, 2),
                    "pattern": pattern
                }
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}

def detect_pattern(closes, highs, lows):
    """Detect basic chart patterns"""
    if len(closes) < 10:
        return None
    
    recent = closes[-10:]
    
    # Higher highs and higher lows = Uptrend
    hh = all(recent[i] >= recent[i-1] for i in range(1, len(recent)))
    ll = all(recent[i] <= recent[i-1] for i in range(1, len(recent)))
    
    if hh:
        return "UPTREND"
    if ll:
        return "DOWNTREND"
    
    # Double bottom (W pattern)
    mid = len(recent) // 2
    first_half_min = min(recent[:mid])
    second_half_min = min(recent[mid:])
    if abs(first_half_min - second_half_min) / first_half_min < 0.03 and recent[-1] > max(first_half_min, second_half_min) * 1.02:
        return "DOUBLE_BOTTOM"
    
    # Double top (M pattern)
    first_half_max = max(recent[:mid])
    second_half_max = max(recent[mid:])
    if abs(first_half_max - second_half_max) / first_half_max < 0.03 and recent[-1] < min(first_half_max, second_half_max) * 0.98:
        return "DOUBLE_TOP"
    
    # Consolidation
    price_range = (max(recent) - min(recent)) / min(recent)
    if price_range < 0.05:
        return "CONSOLIDATION"
    
    return None

@router.get("/peers/{symbol}")
async def get_peer_comparison(symbol: str):
    # Sector mapping for common stocks
    sector_peers = {
        "HDFCBANK": ["ICICIBANK", "KOTAKBANK", "SBIN", "AXISBANK"],
        "ICICIBANK": ["HDFCBANK", "KOTAKBANK", "SBIN", "AXISBANK"],
        "RELIANCE": ["TCS", "INFY", "HDFCBANK", "ICICIBANK"],
        "TCS": ["INFY", "WIPRO", "HCLTECH", "TECHM"],
        "INFY": ["TCS", "WIPRO", "HCLTECH", "TECHM"],
    }
    peers = sector_peers.get(symbol.upper(), ["RELIANCE", "TCS", "HDFCBANK", "INFY"])[:4]
    
    from ..services.price_service import get_bulk_prices
    all_symbols = [symbol.upper()] + peers
    prices = await get_bulk_prices(all_symbols)
    
    result = []
    for s in all_symbols:
        p = prices.get(s, {})
        result.append({"symbol": s, "price": p.get("current_price"), "day_change_pct": p.get("day_change_pct", 0)})
    return {"symbol": symbol.upper(), "peers": result}

@router.get("/market-summary")
async def get_market_summary():
    from ..services.price_service import is_market_open
    
    indices = {"NIFTY50": "^NSEI", "SENSEX": "^BSESN", "BANKNIFTY": "^NSEBANK"}
    top_stocks = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]
    
    # Check cache first during off-market hours
    cache_key = "market_summary"
    if not is_market_open() and cache_key in _cache and (datetime.utcnow() - _cache[cache_key]["time"]).seconds < 3600:
        return _cache[cache_key]["data"]
    
    result = {"indices": {}, "top_movers": []}
    
    async def fetch_quote(client, symbol, is_index=False):
        try:
            yf_symbol = symbol if is_index else f"{symbol}.NS"
            resp = await client.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_symbol}", headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                meta = resp.json()["chart"]["result"][0]["meta"]
                price = meta.get("regularMarketPrice", 0)
                prev = meta.get("previousClose", price)
                change_pct = round((price - prev) / prev * 100, 2) if prev else 0
                return {"symbol": symbol, "price": round(price, 2), "change": round(price - prev, 2), "change_pct": change_pct, "is_index": is_index}
        except:
            pass
        return None
    
    async with httpx.AsyncClient(timeout=10) as client:
        tasks = [fetch_quote(client, sym, True) for sym in indices.values()]
        tasks += [fetch_quote(client, sym, False) for sym in top_stocks]
        results = await asyncio.gather(*tasks)
    
    idx_names = list(indices.keys())
    for i, r in enumerate(results[:3]):
        if r:
            result["indices"][idx_names[i]] = {"price": r["price"], "change": r["change"], "change_pct": r["change_pct"]}
    
    for r in results[3:]:
        if r:
            result["top_movers"].append({"symbol": r["symbol"], "price": r["price"], "change_pct": r["change_pct"]})
    
    result["top_movers"] = sorted(result["top_movers"], key=lambda x: abs(x["change_pct"]), reverse=True)
    
    _cache[cache_key] = {"data": result, "time": datetime.utcnow()}
    return result

@router.get("/fii-dii")
async def get_fii_dii_activity():
    """Get FII/DII activity data from NSE"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get("https://www.nseindia.com/api/fiidiiTradeReact", 
                headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
            if resp.status_code == 200:
                return resp.json()
    except:
        pass
    # Return sample structure if API fails
    return {
        "fii": {"buy": 0, "sell": 0, "net": 0},
        "dii": {"buy": 0, "sell": 0, "net": 0},
        "note": "Live data unavailable - NSE API requires browser session"
    }

@router.get("/insider-trades/{symbol}")
async def get_insider_trades(symbol: str):
    """Get insider trading data"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}.NS?modules=insiderTransactions",
                headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                data = resp.json()["quoteSummary"]["result"][0].get("insiderTransactions", {})
                transactions = data.get("transactions", [])
                return {"symbol": symbol, "trades": [{"name": t.get("filerName", ""), "relation": t.get("filerRelation", ""), "shares": t.get("shares", {}).get("raw", 0), "value": t.get("value", {}).get("raw", 0), "date": t.get("startDate", {}).get("fmt", "")} for t in transactions[:10]]}
    except:
        pass
    return {"symbol": symbol, "trades": []}

@router.get("/analyst-ratings/{symbol}")
async def get_analyst_ratings(symbol: str):
    """Get analyst ratings and recommendations"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}.NS?modules=recommendationTrend,financialData",
                headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                result = resp.json()["quoteSummary"]["result"][0]
                trend = result.get("recommendationTrend", {}).get("trend", [{}])[0]
                fin = result.get("financialData", {})
                return {
                    "symbol": symbol,
                    "recommendation": fin.get("recommendationKey", ""),
                    "target_price": fin.get("targetMeanPrice", {}).get("raw"),
                    "analyst_count": fin.get("numberOfAnalystOpinions", {}).get("raw", 0),
                    "ratings": {"strongBuy": trend.get("strongBuy", 0), "buy": trend.get("buy", 0), "hold": trend.get("hold", 0), "sell": trend.get("sell", 0), "strongSell": trend.get("strongSell", 0)}
                }
    except:
        pass
    return {"symbol": symbol, "recommendation": "", "ratings": {}}

@router.get("/signals/{symbol}")
async def get_stock_signals(symbol: str):
    """Get buy/sell signals for a stock"""
    from ..tasks.portfolio_advisor import get_stock_data, calculate_indicators, generate_recommendation
    
    data = await get_stock_data(symbol.upper())
    if not data:
        return {"symbol": symbol, "error": "Could not fetch data"}
    
    indicators = calculate_indicators(data)
    rec = generate_recommendation(symbol.upper(), indicators["current"], 0, indicators)
    
    return {
        "symbol": symbol.upper(),
        "price": indicators["current"],
        "action": rec["action"],
        "reasons": rec["reasons"],
        "rsi": rec["rsi"],
        "target": rec["target"],
        "stop_loss": rec["stop_loss"],
        "indicators": {
            "sma_20": round(indicators["sma_20"], 2),
            "sma_50": round(indicators["sma_50"], 2),
            "range_position": round(indicators["range_position"], 1),
            "day_change": round(indicators["day_change"], 2)
        }
    }

@router.post("/advisor/run")
async def run_advisor_now(current_user: dict = Depends(get_current_user)):
    """Manually trigger portfolio advisor for current user"""
    from ..tasks.portfolio_advisor import get_bulk_stock_data, calculate_indicators, generate_recommendation, analyze_ipo_opportunities
    
    db = get_db()
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    
    # Get equity symbols only
    equity_holdings = [h for h in holdings if h.get("holding_type") != "MF"]
    symbols = [h["symbol"] for h in equity_holdings]
    
    # Fetch all stock data concurrently
    stock_data = await get_bulk_stock_data(symbols)
    
    recommendations = []
    for h in equity_holdings:
        data = stock_data.get(h["symbol"])
        if not data:
            continue
        
        indicators = calculate_indicators(data)
        rec = generate_recommendation(h["symbol"], h["avg_price"], h["quantity"], indicators)
        recommendations.append(rec)
    
    ipo_recs = await analyze_ipo_opportunities()
    
    return {
        "portfolio": recommendations,
        "ipos": ipo_recs
    }
