"""
Enhanced stock analysis combining multiple data sources:
- Yahoo Finance (primary for price data)
- NSEpy (NSE official data)
- Screener.in (fundamentals)
"""

import httpx
from datetime import date, timedelta
from typing import Optional, Dict
from bs4 import BeautifulSoup
from ...utils.logger import logger

async def get_nse_data(symbol: str) -> Optional[Dict]:
    """Get data from NSE using nsepy"""
    try:
        from nsepy import get_history
        
        end_date = date.today()
        start_date = end_date - timedelta(days=180)
        
        # Fetch NSE data
        df = get_history(
            symbol=symbol.upper(),
            start=start_date,
            end=end_date,
            index=False
        )
        
        if df is None or df.empty:
            return None
        
        # Convert to dict
        latest = df.iloc[-1]
        
        return {
            "symbol": symbol,
            "close": float(latest['Close']),
            "open": float(latest['Open']),
            "high": float(latest['High']),
            "low": float(latest['Low']),
            "volume": int(latest['Volume']),
            "vwap": float(latest.get('VWAP', 0)) if 'VWAP' in df.columns else None,
            "delivery_pct": float(latest.get('Deliverable Volume', 0) / latest['Volume'] * 100) if 'Deliverable Volume' in df.columns else None,
            "historical_data": df.to_dict('records')[-60:]  # Last 60 days
        }
    except Exception as e:
        logger.error(f"NSEpy error for {symbol}: {e}")
        return None

async def get_screener_fundamentals(symbol: str) -> Optional[Dict]:
    """Scrape fundamental data from Screener.in"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            url = f"https://www.screener.in/company/{symbol}/consolidated/"
            resp = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # Extract key metrics
            data = {"symbol": symbol}
            
            # Market Cap, P/E, etc.
            ratios = soup.find_all('li', class_='flex flex-space-between')
            for ratio in ratios:
                name = ratio.find('span', class_='name')
                value = ratio.find('span', class_='number')
                if name and value:
                    key = name.text.strip().lower().replace(' ', '_')
                    val = value.text.strip()
                    data[key] = val
            
            # Company name
            name_tag = soup.find('h1')
            if name_tag:
                data['company_name'] = name_tag.text.strip()
            
            return data
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.error(f"Screener scraping error for {symbol}: {e}")
        return None

async def get_moneycontrol_news(symbol: str) -> list:
    """Scrape news from MoneyControl"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Search for company
            search_url = f"https://www.moneycontrol.com/stocks/cptmarket/compsearchnew.php?search_data=&cid=&mbsearch_str={symbol}&topsearch_type=1"
            resp = await client.get(search_url, headers={
                "User-Agent": "Mozilla/5.0"
            })
            
            if resp.status_code != 200:
                return []
            
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # Extract news items
            news = []
            news_items = soup.find_all('li', class_='clearfix')[:5]
            
            for item in news_items:
                title_tag = item.find('a')
                time_tag = item.find('span', class_='ago')
                
                if title_tag:
                    news.append({
                        "title": title_tag.text.strip(),
                        "link": title_tag.get('href', ''),
                        "time": time_tag.text.strip() if time_tag else ''
                    })
            
            return news
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.error(f"MoneyControl scraping error for {symbol}: {e}")
        return []

async def get_combined_analysis(symbol: str, exchange: str = "NSE") -> Dict:
    """
    Combine data from multiple sources for comprehensive analysis
    Auto-fallback from NSE to BSE if data not available
    """
    from ..market.price_service import get_stock_price
    
    result = {
        "symbol": symbol,
        "exchange": exchange,
        "sources": {}
    }
    
    # 1. Yahoo Finance (primary - already implemented)
    try:
        yahoo_data = await get_stock_price(symbol, exchange)
        
        # If NSE fails, try BSE
        if not yahoo_data and exchange == "NSE":
            yahoo_data = await get_stock_price(symbol, "BSE")
            if yahoo_data:
                exchange = "BSE"
                result["exchange"] = "BSE"
        
        if yahoo_data:
            result["sources"]["yahoo"] = yahoo_data
            result["current_price"] = yahoo_data.get("current_price")
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.error(f"Yahoo Finance error: {e}")
    
    # 2. NSE Data (if NSE exchange)
    if exchange == "NSE":
        nse_data = await get_nse_data(symbol)
        if nse_data:
            result["sources"]["nse"] = {
                "vwap": nse_data.get("vwap"),
                "delivery_pct": nse_data.get("delivery_pct"),
                "volume": nse_data.get("volume")
            }
            # Use NSE price if Yahoo failed
            if not result.get("current_price"):
                result["current_price"] = nse_data.get("close")
    
    # 3. Fundamentals from Screener
    fundamentals = await get_screener_fundamentals(symbol)
    if fundamentals:
        result["sources"]["fundamentals"] = fundamentals
        result["market_cap"] = fundamentals.get("market_cap")
        result["pe_ratio"] = fundamentals.get("stock_p/e")
        result["pb_ratio"] = fundamentals.get("price_to_book_value")
        result["roe"] = fundamentals.get("roe")
        result["roce"] = fundamentals.get("roce")
    
    # 4. News from MoneyControl
    news = await get_moneycontrol_news(symbol)
    if news:
        result["sources"]["news"] = news
        result["news_count"] = len(news)
    
    # Calculate data quality score
    sources_available = len([k for k, v in result["sources"].items() if v])
    result["data_quality"] = f"{sources_available}/4 sources"
    result["recommendation"] = generate_recommendation(result)
    
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
