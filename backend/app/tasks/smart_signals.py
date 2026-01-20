from ..database import get_db
from ..services.notification_service import send_email
from ..config import get_settings
from datetime import datetime
import httpx

settings = get_settings()

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
                signals.append({"type": "BUY", "reason": "Stock is oversold - price dropped too fast, may bounce back", "strength": "STRONG"})
            elif rsi < 40:
                signals.append({"type": "BUY", "reason": "Stock is getting cheap - could be a buying opportunity", "strength": "MODERATE"})
            elif rsi > 70:
                signals.append({"type": "SELL", "reason": "Stock is overheated - risen too fast, may correct soon", "strength": "STRONG"})
            elif rsi > 60:
                signals.append({"type": "SELL", "reason": "Stock is getting expensive - consider booking profits", "strength": "MODERATE"})
            
            # Moving average crossover
            if current_price > sma_20 > sma_50:
                signals.append({"type": "BUY", "reason": "Stock is in an uptrend - price above key averages", "strength": "MODERATE"})
            elif current_price < sma_20 < sma_50:
                signals.append({"type": "SELL", "reason": "Stock is in a downtrend - price below key averages", "strength": "MODERATE"})
            
            # Golden cross / Death cross (SMA20 crossing SMA50)
            prev_sma_20 = sum(closes[-21:-1]) / 20
            prev_sma_50 = sum(closes[-51:-1]) / 50
            if prev_sma_20 < prev_sma_50 and sma_20 > sma_50:
                signals.append({"type": "BUY", "reason": "Bullish signal - short-term trend turning positive", "strength": "STRONG"})
            elif prev_sma_20 > prev_sma_50 and sma_20 < sma_50:
                signals.append({"type": "SELL", "reason": "Bearish signal - short-term trend turning negative", "strength": "STRONG"})
            
            # Volume spike with price movement
            if volume_spike > 2:
                if day_change_pct > 3:
                    signals.append({"type": "BUY", "reason": f"Heavy buying today - stock up {day_change_pct:.1f}% with {volume_spike:.1f}x normal volume", "strength": "STRONG"})
                elif day_change_pct < -3:
                    signals.append({"type": "SELL", "reason": f"Heavy selling today - stock down {abs(day_change_pct):.1f}% with {volume_spike:.1f}x normal volume", "strength": "STRONG"})
            
            # 52-week levels
            if near_52w_low:
                signals.append({"type": "BUY", "reason": f"Near yearly low of ₹{low_52w:.0f} - potential value buy", "strength": "MODERATE"})
            if near_52w_high:
                signals.append({"type": "SELL", "reason": f"Near yearly high of ₹{high_52w:.0f} - consider booking profits", "strength": "MODERATE"})
            
            # Big daily moves
            if day_change_pct < -5:
                signals.append({"type": "BUY", "reason": f"Big drop of {abs(day_change_pct):.1f}% today - could bounce back", "strength": "MODERATE"})
            elif day_change_pct > 5:
                signals.append({"type": "SELL", "reason": f"Big jump of {day_change_pct:.1f}% today - good time to book profits", "strength": "MODERATE"})
            
            return {
                "symbol": symbol,
                "price": current_price,
                "rsi": rsi,
                "sma_20": sma_20,
                "sma_50": sma_50,
                "day_change_pct": day_change_pct,
                "signals": signals
            }
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None


async def check_smart_signals():
    """Check all user holdings for buy/sell signals and notify"""
    db = get_db()
    
    # Get all users with alerts enabled
    users = await db.users.find({"settings.alerts_enabled": {"$ne": False}}).to_list(500)
    
    for user in users:
        # Get user's holdings
        holdings = await db.holdings.find({"user_id": user["_id"]}).to_list(100)
        if not holdings:
            continue
        
        # Get watchlist too
        watchlist = await db.watchlist.find({"user_id": user["_id"]}).to_list(50)
        
        # Combine symbols
        symbols = list(set([h["symbol"] for h in holdings] + [w["symbol"] for w in watchlist]))
        
        alerts_to_send = []
        
        for symbol in symbols:
            # Skip MFs
            holding = next((h for h in holdings if h["symbol"] == symbol), None)
            if holding and holding.get("holding_type") == "MF":
                continue
            
            analysis = await analyze_stock(symbol)
            if not analysis or not analysis["signals"]:
                continue
            
            # Only send strong signals or multiple moderate signals
            strong_signals = [s for s in analysis["signals"] if s["strength"] == "STRONG"]
            buy_signals = [s for s in analysis["signals"] if s["type"] == "BUY"]
            sell_signals = [s for s in analysis["signals"] if s["type"] == "SELL"]
            
            # Check if we already sent this signal today
            today = datetime.utcnow().date().isoformat()
            existing = await db.signal_history.find_one({
                "user_id": user["_id"],
                "symbol": symbol,
                "date": today
            })
            if existing:
                continue
            
            if strong_signals or len(buy_signals) >= 2 or len(sell_signals) >= 2:
                # Determine overall signal
                if len(buy_signals) > len(sell_signals):
                    signal_type = "🟢 BUY"
                    reasons = [s["reason"] for s in buy_signals]
                elif len(sell_signals) > len(buy_signals):
                    signal_type = "🔴 SELL"
                    reasons = [s["reason"] for s in sell_signals]
                else:
                    continue  # Mixed signals, skip
                
                alerts_to_send.append({
                    "symbol": symbol,
                    "price": analysis["price"],
                    "signal": signal_type,
                    "reasons": reasons[:3]  # Top 3 reasons
                })
                
                # Record that we sent this signal
                await db.signal_history.insert_one({
                    "user_id": user["_id"],
                    "symbol": symbol,
                    "date": today,
                    "signal": signal_type,
                    "created_at": datetime.utcnow()
                })
        
        # Send consolidated alert
        if alerts_to_send:
            await send_smart_alert(user, alerts_to_send)


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
            print(f"Telegram error: {e}")
    
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
