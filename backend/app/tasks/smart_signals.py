from ..models.documents import User, Holding, WatchlistItem, SignalHistory
from ..services.notification.service import send_email
from ..core.config import settings
from ..utils.logger import logger
from datetime import datetime
import httpx


async def fetch_stock_news(symbol: str, client: httpx.AsyncClient) -> list:
    """Fetch recent news for a stock from Yahoo Finance"""
    try:
        resp = await client.get(
            f"https://query1.finance.yahoo.com/v1/finance/search?q={symbol}&newsCount=5",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        if resp.status_code == 200:
            data = resp.json()
            news = data.get("news", [])
            return [{"title": n.get("title", ""), "publisher": n.get("publisher", ""), "link": n.get("link", "")} for n in news[:3]]
    except (httpx.HTTPError, KeyError, ValueError):
        pass
    return []


async def analyze_stock(symbol: str):
    """Analyze stock and return buy/sell signals"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS?interval=1d&range=6mo",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            if resp.status_code != 200:
                return None
            
            result = resp.json()["chart"]["result"][0]
            meta = result["meta"]
            closes = [c for c in result["indicators"]["quote"][0]["close"] if c]
            volumes = [v for v in result["indicators"]["quote"][0]["volume"] if v]
            
            if len(closes) < 50:
                return None
            
            current_price = meta.get("regularMarketPrice", closes[-1])
            prev_close = meta.get("previousClose", closes[-2])
            
            # Fetch news
            news = await fetch_stock_news(symbol, client)
            
            # Calculate indicators
            sma_20 = sum(closes[-20:]) / 20
            sma_50 = sum(closes[-50:]) / 50
            
            # RSI
            gains, losses = [], []
            for i in range(1, 15):
                diff = closes[-i] - closes[-i-1]
                if diff > 0:
                    gains.append(diff)
                else:
                    losses.append(abs(diff))
            avg_gain = sum(gains) / 14 if gains else 0
            avg_loss = sum(losses) / 14 if losses else 0.001
            rsi = 100 - (100 / (1 + avg_gain / avg_loss))
            
            # Volume spike
            avg_volume = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else 0
            current_volume = volumes[-1] if volumes else 0
            volume_spike = (current_volume / avg_volume) if avg_volume > 0 else 1
            
            # Day change
            day_change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
            
            # 52-week high/low
            high_52w = max(closes)
            low_52w = min(closes)
            near_52w_high = current_price >= high_52w * 0.98
            near_52w_low = current_price <= low_52w * 1.02
            
            # Generate signals
            signals = []
            
            # RSI signals
            if rsi < 30:
                signals.append({
                    "type": "BUY",
                    "strength": "STRONG",
                    "reason": "Stock is oversold - price dropped too fast, may bounce back",
                    "detailed_reason": f"RSI (Relative Strength Index) is at {rsi:.1f}, which is below 30. RSI measures how fast a stock's price has moved recently on a scale of 0-100. When RSI drops below 30, it means the stock has fallen sharply in a short time and sellers may be exhausted. Historically, oversold stocks often see a price recovery as bargain hunters step in."
                })
            elif rsi < 40:
                signals.append({
                    "type": "BUY",
                    "strength": "MODERATE",
                    "reason": "Stock is getting cheap - could be a buying opportunity",
                    "detailed_reason": f"RSI is at {rsi:.1f}, approaching oversold territory (below 30). RSI tracks the speed of recent price changes - lower values suggest selling pressure is high. At this level, the stock is not extremely oversold but is showing weakness that could present a buying opportunity if fundamentals are strong."
                })
            elif rsi > 70:
                signals.append({
                    "type": "SELL",
                    "strength": "STRONG",
                    "reason": "Stock is overheated - risen too fast, may correct soon",
                    "detailed_reason": f"RSI is at {rsi:.1f}, which is above 70 (overbought zone). This means the stock price has risen very quickly recently. When RSI exceeds 70, it often indicates that buyers have pushed the price too high too fast, and a pullback or correction becomes more likely as profit-taking kicks in."
                })
            elif rsi > 60:
                signals.append({
                    "type": "SELL",
                    "strength": "MODERATE",
                    "reason": "Stock is getting expensive - consider booking profits",
                    "detailed_reason": f"RSI is at {rsi:.1f}, moving toward overbought territory (above 70). The stock has been rising steadily and momentum is strong. While not extremely overbought, this is often a good time to consider booking partial profits, especially if you've made significant gains."
                })
            
            # Moving average crossover
            if current_price > sma_20 > sma_50:
                signals.append({
                    "type": "BUY",
                    "strength": "MODERATE",
                    "reason": "Stock is in an uptrend - price above key averages",
                    "detailed_reason": f"Current price ₹{current_price:.2f} is above both the 20-day average (₹{sma_20:.2f}) and 50-day average (₹{sma_50:.2f}). Moving averages smooth out daily price fluctuations to show the overall trend. When price stays above these averages and the shorter average is above the longer one, it confirms the stock is in a healthy uptrend with sustained buying interest."
                })
            elif current_price < sma_20 < sma_50:
                signals.append({
                    "type": "SELL",
                    "strength": "MODERATE",
                    "reason": "Stock is in a downtrend - price below key averages",
                    "detailed_reason": f"Current price ₹{current_price:.2f} is below both the 20-day average (₹{sma_20:.2f}) and 50-day average (₹{sma_50:.2f}). This pattern indicates a downtrend - the stock has been falling consistently and hasn't recovered to its recent average prices. This suggests continued selling pressure and weak investor sentiment."
                })
            
            # Golden cross / Death cross
            prev_sma_20 = sum(closes[-21:-1]) / 20
            prev_sma_50 = sum(closes[-51:-1]) / 50
            if prev_sma_20 < prev_sma_50 and sma_20 > sma_50:
                signals.append({
                    "type": "BUY",
                    "strength": "STRONG",
                    "reason": "Bullish signal - short-term trend turning positive",
                    "detailed_reason": f"A 'Golden Cross' just occurred - the 20-day moving average (₹{sma_20:.2f}) crossed above the 50-day average (₹{sma_50:.2f}). This is a classic bullish signal used by traders worldwide. It means recent prices are now higher than the longer-term average, suggesting momentum is shifting from sellers to buyers and a new uptrend may be starting."
                })
            elif prev_sma_20 > prev_sma_50 and sma_20 < sma_50:
                signals.append({
                    "type": "SELL",
                    "strength": "STRONG",
                    "reason": "Bearish signal - short-term trend turning negative",
                    "detailed_reason": f"A 'Death Cross' just occurred - the 20-day moving average (₹{sma_20:.2f}) crossed below the 50-day average (₹{sma_50:.2f}). This is a widely-watched bearish signal. It indicates that recent prices have fallen below the longer-term trend, suggesting selling pressure is increasing and the stock may continue to decline."
                })
            
            # Volume spike with price movement
            if volume_spike > 2:
                if day_change_pct > 3:
                    signals.append({
                        "type": "BUY",
                        "strength": "STRONG",
                        "reason": f"Heavy buying today - stock up {day_change_pct:.1f}% with {volume_spike:.1f}x normal volume",
                        "detailed_reason": f"Today's trading volume is {volume_spike:.1f}x higher than the 20-day average, and the stock is up {day_change_pct:.1f}%. High volume confirms that the price move is backed by strong participation - many buyers are actively accumulating. This combination of rising price + high volume often signals institutional buying or positive news that could drive further gains."
                    })
                elif day_change_pct < -3:
                    signals.append({
                        "type": "SELL",
                        "strength": "STRONG",
                        "reason": f"Heavy selling today - stock down {abs(day_change_pct):.1f}% with {volume_spike:.1f}x normal volume",
                        "detailed_reason": f"Today's trading volume is {volume_spike:.1f}x higher than the 20-day average, and the stock is down {abs(day_change_pct):.1f}%. High volume on a down day indicates strong selling pressure - large investors may be exiting their positions. This pattern often precedes further declines as negative sentiment spreads."
                    })
            
            # 52-week levels
            if near_52w_low:
                signals.append({
                    "type": "BUY",
                    "strength": "MODERATE",
                    "reason": f"Near yearly low of ₹{low_52w:.0f} - potential value buy",
                    "detailed_reason": f"Stock is trading near its 52-week low of ₹{low_52w:.2f} (current: ₹{current_price:.2f}). The 52-week low represents the cheapest the stock has been in a year. While this could indicate problems, it can also be a value opportunity if the company's fundamentals remain strong. Many successful investors look for quality stocks trading near yearly lows."
                })
            if near_52w_high:
                signals.append({
                    "type": "SELL",
                    "strength": "MODERATE",
                    "reason": f"Near yearly high of ₹{high_52w:.0f} - consider booking profits",
                    "detailed_reason": f"Stock is trading near its 52-week high of ₹{high_52w:.2f} (current: ₹{current_price:.2f}). While stocks can break through to new highs, the 52-week high often acts as a resistance level where many investors choose to sell. If you have profits, this could be a good time to book some gains, as pullbacks from yearly highs are common."
                })
            
            # Big daily moves
            if day_change_pct < -5:
                signals.append({
                    "type": "BUY",
                    "strength": "MODERATE",
                    "reason": f"Big drop of {abs(day_change_pct):.1f}% today - could bounce back",
                    "detailed_reason": f"Stock fell {abs(day_change_pct):.1f}% in a single day, which is a significant move. Large single-day drops often trigger a 'dead cat bounce' - a temporary recovery as bargain hunters buy the dip. However, verify there's no negative news (earnings miss, scandal, etc.) before buying, as some drops are justified."
                })
            elif day_change_pct > 5:
                signals.append({
                    "type": "SELL",
                    "strength": "MODERATE",
                    "reason": f"Big jump of {day_change_pct:.1f}% today - good time to book profits",
                    "detailed_reason": f"Stock jumped {day_change_pct:.1f}% in a single day. Large single-day gains often see partial reversals in the following days as short-term traders book profits. If you're sitting on gains, this spike could be a good opportunity to sell some shares. The saying 'sell into strength' applies here."
                })
            
            # Add news context to signals if available
            news_context = None
            if news:
                news_context = f"Recent news: {news[0]['title']}" if news[0]['title'] else None
                for sig in signals:
                    if news_context:
                        sig["detailed_reason"] += f"\n\n📰 {news_context} (Source: {news[0].get('publisher', 'News')})"
            
            return {
                "symbol": symbol,
                "price": current_price,
                "rsi": rsi,
                "sma_20": sma_20,
                "sma_50": sma_50,
                "day_change_pct": day_change_pct,
                "signals": signals,
                "news": news
            }
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        return None


async def check_smart_signals():
    """Check all user holdings for buy/sell signals and notify"""
    users = await User.find(User.settings.alerts_enabled != False).to_list()
    
    for user in users:
        holdings = await Holding.find(Holding.user_id == user.id).to_list()
        if not holdings:
            continue
        
        watchlist = await WatchlistItem.find(WatchlistItem.user_id == user.id).to_list()
        
        symbols = list(set([h.symbol for h in holdings] + [w.symbol for w in watchlist]))
        
        alerts_to_send = []
        
        for symbol in symbols:
            holding = next((h for h in holdings if h.symbol == symbol), None)
            if holding and holding.holding_type == "MF":
                continue
            
            analysis = await analyze_stock(symbol)
            if not analysis or not analysis["signals"]:
                continue
            
            strong_signals = [s for s in analysis["signals"] if s["strength"] == "STRONG"]
            buy_signals = [s for s in analysis["signals"] if s["type"] == "BUY"]
            sell_signals = [s for s in analysis["signals"] if s["type"] == "SELL"]
            
            today = datetime.utcnow().date().isoformat()
            existing = await SignalHistory.find_one(
                SignalHistory.user_id == user.id,
                SignalHistory.symbol == symbol,
                SignalHistory.date == today
            )
            if existing:
                continue
            
            if strong_signals or len(buy_signals) >= 2 or len(sell_signals) >= 2:
                if len(buy_signals) > len(sell_signals):
                    signal_type = "🟢 BUY"
                    reasons = [s["reason"] for s in buy_signals]
                elif len(sell_signals) > len(buy_signals):
                    signal_type = "🔴 SELL"
                    reasons = [s["reason"] for s in sell_signals]
                else:
                    continue
                
                alerts_to_send.append({
                    "symbol": symbol,
                    "price": analysis["price"],
                    "signal": signal_type,
                    "reasons": reasons[:3]
                })
                
                await SignalHistory(
                    user_id=user.id,
                    symbol=symbol,
                    date=today,
                    signal=signal_type,
                    created_at=datetime.utcnow()
                ).insert()
        
        if alerts_to_send:
            await send_smart_alert({"telegram_chat_id": user.telegram_chat_id, "email": user.email}, alerts_to_send)


async def send_smart_alert(user: dict, alerts: list):
    """Send smart signal alert to user"""
    
    msg = "📊 *Smart Signals Alert*\n\n"
    for a in alerts:
        msg += f"{a['signal']} *{a['symbol']}* @ ₹{a['price']:.2f}\n"
        for r in a['reasons']:
            msg += f"  • {r}\n"
        msg += "\n"
    
    msg += "_This is not financial advice. Do your own research._"
    
    # Telegram
    if user.get("telegram_chat_id") and settings.telegram_bot_token:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                    json={"chat_id": user["telegram_chat_id"], "text": msg, "parse_mode": "Markdown"}
                )
        except Exception as e:
            logger.error(f"Telegram error: {e}")
    
    # Email
    if user.get("email"):
        html = "<h2>📊 Smart Signals Alert</h2>"
        for a in alerts:
            color = "#22c55e" if "BUY" in a["signal"] else "#ef4444"
            html += f"<div style='margin-bottom:20px;padding:15px;border-left:4px solid {color};background:#f8f9fa'>"
            html += f"<h3 style='margin:0;color:{color}'>{a['signal']} {a['symbol']}</h3>"
            html += f"<p style='margin:5px 0;font-size:18px'>₹{a['price']:.2f}</p>"
            html += "<ul style='margin:10px 0;padding-left:20px'>"
            for r in a['reasons']:
                html += f"<li>{r}</li>"
            html += "</ul></div>"
        html += "<p style='color:#666;font-size:12px'><em>This is not financial advice. Do your own research.</em></p>"
        
        await send_email(user["email"], "StockPilot: Smart Signals Alert", html)
