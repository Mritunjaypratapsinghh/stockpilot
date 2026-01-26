"""
Smart Portfolio Advisor - Automated Buy/Sell/Hold recommendations
Analyzes portfolio holdings and sends actionable alerts
"""
from ..database import get_db
from ..services.notification_service import send_email
from ..config import get_settings
from ..services.price_service import is_market_open
from datetime import datetime
import httpx
import asyncio

settings = get_settings()

# Cache for stock data (symbol -> (data, timestamp))
_advisor_cache = {}
_CACHE_TTL = 3600  # 1 hour


async def get_stock_data(symbol: str):
    """Fetch comprehensive stock data with caching"""
    import time
    
    # Check cache
    if symbol in _advisor_cache:
        data, ts = _advisor_cache[symbol]
        if time.time() - ts < _CACHE_TTL:
            return data
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS?interval=1d&range=1y",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            if resp.status_code != 200:
                return None
            
            result = resp.json()["chart"]["result"][0]
            meta = result["meta"]
            quotes = result["indicators"]["quote"][0]
            
            closes = [c for c in quotes["close"] if c]
            highs = [h for h in quotes["high"] if h]
            lows = [l for l in quotes["low"] if l]
            volumes = [v for v in quotes["volume"] if v]
            
            if len(closes) < 50:
                return None
            
            data = {
                "symbol": symbol,
                "current_price": meta.get("regularMarketPrice", closes[-1]),
                "prev_close": meta.get("previousClose", closes[-2]),
                "closes": closes,
                "highs": highs,
                "lows": lows,
                "volumes": volumes
            }
            _advisor_cache[symbol] = (data, time.time())
            return data
    except:
        return None


async def fetch_stock_news(symbol: str) -> list:
    """Fetch recent news for a stock"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://query1.finance.yahoo.com/v1/finance/search?q={symbol}&newsCount=3",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            if resp.status_code == 200:
                news = resp.json().get("news", [])
                return [{"title": n.get("title", ""), "publisher": n.get("publisher", "")} for n in news[:2]]
    except:
        pass
    return []


async def get_bulk_stock_data(symbols: list):
    """Fetch stock data for multiple symbols concurrently"""
    results = await asyncio.gather(*[get_stock_data(s) for s in symbols], return_exceptions=True)
    return {s: r for s, r in zip(symbols, results) if r and not isinstance(r, Exception)}


def calculate_indicators(data: dict):
    """Calculate all technical indicators"""
    closes = data["closes"]
    volumes = data["volumes"]
    current = data["current_price"]
    prev = data["prev_close"]
    
    # Moving averages
    sma_5 = sum(closes[-5:]) / 5
    sma_20 = sum(closes[-20:]) / 20
    sma_50 = sum(closes[-50:]) / 50
    sma_200 = sum(closes[-200:]) / 200 if len(closes) >= 200 else None
    
    # RSI (14-day)
    gains, losses = [], []
    for i in range(1, 15):
        diff = closes[-i] - closes[-i-1]
        gains.append(max(diff, 0))
        losses.append(abs(min(diff, 0)))
    avg_gain = sum(gains) / 14
    avg_loss = sum(losses) / 14 if sum(losses) > 0 else 0.001
    rsi = 100 - (100 / (1 + avg_gain / avg_loss))
    
    # MACD
    ema_12 = sum(closes[-12:]) / 12  # Simplified
    ema_26 = sum(closes[-26:]) / 26
    macd = ema_12 - ema_26
    
    # Volume analysis
    avg_vol = sum(volumes[-20:]) / 20
    curr_vol = volumes[-1] if volumes else 0
    vol_ratio = curr_vol / avg_vol if avg_vol > 0 else 1
    
    # 52-week high/low
    high_52w = max(data["highs"][-252:]) if len(data["highs"]) >= 252 else max(data["highs"])
    low_52w = min(data["lows"][-252:]) if len(data["lows"]) >= 252 else min(data["lows"])
    
    # Price position in 52w range (0-100)
    range_position = ((current - low_52w) / (high_52w - low_52w) * 100) if high_52w != low_52w else 50
    
    # Day change
    day_change = ((current - prev) / prev * 100) if prev else 0
    
    # Trend (price vs SMAs)
    above_sma20 = current > sma_20
    above_sma50 = current > sma_50
    above_sma200 = current > sma_200 if sma_200 else None
    
    # Support/Resistance
    support = min(closes[-20:])
    resistance = max(closes[-20:])
    
    return {
        "current": current,
        "sma_5": sma_5,
        "sma_20": sma_20,
        "sma_50": sma_50,
        "sma_200": sma_200,
        "rsi": rsi,
        "macd": macd,
        "vol_ratio": vol_ratio,
        "high_52w": high_52w,
        "low_52w": low_52w,
        "range_position": range_position,
        "day_change": day_change,
        "above_sma20": above_sma20,
        "above_sma50": above_sma50,
        "above_sma200": above_sma200,
        "support": support,
        "resistance": resistance
    }


def generate_recommendation(symbol: str, avg_price: float, quantity: float, indicators: dict):
    """Generate actionable recommendation for a holding"""
    current = indicators["current"]
    rsi = indicators["rsi"]
    pnl_pct = ((current - avg_price) / avg_price * 100) if avg_price > 0 else 0
    
    action = None
    reasons = []
    detailed_reasons = []
    target = None
    stop_loss = None
    
    # === STRONG BUY CONDITIONS ===
    if rsi < 25 and indicators["range_position"] < 15:
        action = "STRONG BUY"
        reasons.append("Stock has fallen sharply and looks very cheap")
        reasons.append("Trading near its lowest price in a year - good entry point")
        detailed_reasons.append(f"RSI is at {rsi:.1f} (below 25 = extremely oversold). RSI measures momentum on a 0-100 scale. Below 25 means the stock has been heavily sold and may be due for a bounce as selling pressure exhausts.")
        detailed_reasons.append(f"Stock is in the bottom {indicators['range_position']:.0f}% of its 52-week range. This means it's trading very close to its yearly low of ₹{indicators.get('low_52w', current * 0.9):.2f}. Historically, buying near 52-week lows can offer good risk-reward if the company's fundamentals are intact.")
        target = indicators["sma_20"]
    
    # === BUY / ACCUMULATE CONDITIONS ===
    elif rsi < 35 and indicators["above_sma200"] != False:
        action = "BUY MORE"
        reasons.append("Stock is oversold - price dropped faster than usual")
        detailed_reasons.append(f"RSI is at {rsi:.1f} (below 35 = oversold zone). This indicates the stock has fallen rapidly and may be undervalued in the short term. The 200-day moving average support suggests the long-term trend is still intact.")
        if pnl_pct < -10:
            reasons.append(f"Good chance to lower your average cost (currently down {abs(pnl_pct):.1f}%)")
            detailed_reasons.append(f"Your current position is down {abs(pnl_pct):.1f}%. Buying more at lower prices reduces your average cost per share (called 'averaging down'). For example, if you bought at ₹{avg_price:.2f} and buy more at ₹{current:.2f}, your new average will be lower, meaning you need a smaller recovery to break even.")
        target = indicators["sma_50"]
    
    elif indicators["day_change"] < -4 and rsi < 45 and indicators["vol_ratio"] > 1.5:
        action = "BUY MORE"
        reasons.append(f"Stock dropped {abs(indicators['day_change']):.1f}% today with heavy trading")
        reasons.append("Could bounce back soon - potential buying opportunity")
        detailed_reasons.append(f"Stock fell {abs(indicators['day_change']):.1f}% today with {indicators['vol_ratio']:.1f}x normal volume. Large single-day drops often trigger a technical bounce as bargain hunters step in. The high volume suggests this move is significant and may have flushed out weak holders.")
        detailed_reasons.append(f"RSI at {rsi:.1f} is not yet oversold, meaning there's room for further decline, but the sharp drop creates a potential entry point. Consider buying in tranches rather than all at once.")
        target = indicators["sma_20"]
    
    # === SELL CONDITIONS ===
    elif rsi > 75 and indicators["range_position"] > 90:
        action = "SELL"
        reasons.append("Stock has risen too fast, too quickly - may correct soon")
        reasons.append("Trading near its highest price in a year")
        detailed_reasons.append(f"RSI is at {rsi:.1f} (above 75 = extremely overbought). This means buying pressure has been intense and the stock may be due for a pullback. Overbought conditions don't mean the stock will crash, but the risk of a correction increases significantly.")
        detailed_reasons.append(f"Stock is in the top {100 - indicators['range_position']:.0f}% of its 52-week range, near its yearly high. The 52-week high often acts as psychological resistance where many investors choose to take profits.")
        if pnl_pct > 20:
            reasons.append(f"You're up {pnl_pct:.1f}% - good time to book profits")
            detailed_reasons.append(f"You have a {pnl_pct:.1f}% profit on this position. The old saying 'no one ever went broke taking profits' applies here. Even if the stock continues higher, locking in gains protects you from potential reversals.")
    
    elif rsi > 70 and pnl_pct > 30:
        action = "PARTIAL SELL"
        reasons.append("Stock is overheated - risen faster than normal")
        reasons.append(f"You're up {pnl_pct:.1f}% - consider selling some to lock in gains")
        detailed_reasons.append(f"RSI at {rsi:.1f} indicates overbought conditions. Combined with your {pnl_pct:.1f}% profit, this is an ideal time for partial profit booking. Consider selling 25-50% of your position to lock in gains while keeping exposure for further upside.")
        detailed_reasons.append("Partial selling is a risk management strategy - you secure profits while maintaining a position if the stock continues to rise. This removes the emotional stress of timing the exact top.")
    
    elif pnl_pct > 50 and indicators["day_change"] > 5:
        action = "PARTIAL SELL"
        reasons.append(f"Excellent profit of {pnl_pct:.1f}% - don't let it slip away")
        reasons.append(f"Stock jumped {indicators['day_change']:.1f}% today - good exit point")
        detailed_reasons.append(f"Your position has gained {pnl_pct:.1f}%, which is an exceptional return. Today's {indicators['day_change']:.1f}% jump provides liquidity and a strong price to sell into. Large single-day gains often see partial reversals in subsequent days.")
        detailed_reasons.append("The principle of 'selling into strength' suggests taking profits when the stock is rising strongly, rather than waiting for weakness. This ensures you get good execution prices.")
    
    # === HOLD CONDITIONS ===
    elif 40 <= rsi <= 60 and indicators["above_sma50"]:
        action = "HOLD"
        reasons.append("Stock is in a healthy uptrend")
        reasons.append("No action needed - let your profits grow")
        detailed_reasons.append(f"RSI at {rsi:.1f} is in the neutral zone (40-60), indicating balanced buying and selling pressure. This is healthy - not overbought or oversold. The stock is trading above its 50-day moving average, confirming the uptrend is intact.")
        detailed_reasons.append(f"Target: ₹{indicators['resistance']:.2f} (resistance level). Stop-loss: ₹{indicators['support']:.2f} (support level). These levels are calculated from recent price action and represent where the stock has previously found buyers (support) or sellers (resistance).")
        target = indicators["resistance"]
        stop_loss = indicators["support"]
    
    # === WAIT / WATCH CONDITIONS ===
    elif not indicators["above_sma20"] and not indicators["above_sma50"]:
        if pnl_pct > 0:
            action = "HOLD - WATCH"
            reasons.append("Stock is weakening - falling below its recent averages")
            reasons.append("Set a stop-loss to protect your gains")
            detailed_reasons.append(f"Stock is trading below both its 20-day (₹{indicators['sma_20']:.2f}) and 50-day (₹{indicators['sma_50']:.2f}) moving averages. This pattern indicates weakening momentum - the recent trend has turned negative. However, you're still in profit.")
            detailed_reasons.append(f"Recommended stop-loss: ₹{indicators['support']:.2f}. A stop-loss is a pre-set price at which you'll sell to limit losses. Setting it at support level means you exit if the stock breaks below a key price where buyers previously stepped in.")
            stop_loss = indicators["support"]
        else:
            action = "WAIT"
            reasons.append("Stock is in a downtrend - not a good time to buy more")
            reasons.append("Wait for it to become cheaper before adding")
            detailed_reasons.append(f"Stock is below both moving averages (20-day: ₹{indicators['sma_20']:.2f}, 50-day: ₹{indicators['sma_50']:.2f}), indicating a downtrend. The phrase 'don't catch a falling knife' applies - buying during a downtrend often leads to further losses.")
            detailed_reasons.append("Wait for either: (1) RSI to drop below 30 (oversold), or (2) price to reclaim the 20-day moving average. These would signal the selling pressure is exhausting or the trend is reversing.")
    
    # === EXIT CONDITIONS ===
    elif pnl_pct < -20 and not indicators["above_sma50"] and rsi > 50:
        action = "EXIT"
        reasons.append(f"Stock is down {abs(pnl_pct):.1f}% with no signs of recovery")
        reasons.append("Consider selling and investing elsewhere")
        detailed_reasons.append(f"Your position is down {abs(pnl_pct):.1f}%, the stock is below its 50-day average, and RSI at {rsi:.1f} shows no oversold bounce is imminent. This combination suggests the stock may continue to underperform.")
        detailed_reasons.append("Consider the 'opportunity cost' - money stuck in a losing position could be invested elsewhere with better prospects. Selling a loser is not admitting defeat; it's reallocating capital to better opportunities. Tax-loss harvesting can also offset gains elsewhere.")
    
    # Default
    if not action:
        action = "HOLD"
        reasons.append("No clear signal right now - continue holding")
        detailed_reasons.append(f"Current indicators (RSI: {rsi:.1f}, Price: ₹{current:.2f}) don't show strong buy or sell signals. The stock is in a neutral zone. Continue holding and monitor for changes in trend or momentum.")
    
    return {
        "symbol": symbol,
        "action": action,
        "reasons": reasons,
        "detailed_reasons": detailed_reasons,
        "current_price": current,
        "avg_price": avg_price,
        "pnl_pct": pnl_pct,
        "quantity": quantity,
        "target": round(target, 2) if target else None,
        "stop_loss": round(stop_loss, 2) if stop_loss else None,
        "rsi": round(rsi, 1)
    }


async def analyze_ipo_opportunities():
    """Analyze IPOs based on GMP and recommend"""
    db = get_db()
    ipos = await db.ipos.find({"status": {"$in": ["UPCOMING", "OPEN"]}}).to_list(20)
    
    recommendations = []
    for ipo in ipos:
        gmp = ipo.get("gmp", 0)
        price_high = ipo.get("price_band", {}).get("high", 0)
        
        if not price_high:
            continue
        
        gmp_pct = (gmp / price_high * 100) if price_high else 0
        
        rec = {
            "name": ipo["name"],
            "price_band": f"₹{round(ipo.get('price_band', {}).get('low', 0))}-{round(price_high)}",
            "gmp": gmp,
            "gmp_pct": gmp_pct,
            "lot_size": ipo.get("lot_size", 0),
            "dates": ipo.get("dates", {}),
            "action": None,
            "reasons": []
        }
        
        # IPO recommendation logic
        if gmp_pct > 30:
            rec["action"] = "APPLY"
            rec["reasons"].append(f"Strong GMP of ₹{gmp} ({gmp_pct:.0f}%)")
            rec["reasons"].append("High listing gain expected")
        elif gmp_pct > 15:
            rec["action"] = "APPLY"
            rec["reasons"].append(f"Good GMP of ₹{gmp} ({gmp_pct:.0f}%)")
        elif gmp_pct > 5:
            rec["action"] = "RISKY"
            rec["reasons"].append(f"Moderate GMP ({gmp_pct:.0f}%)")
            rec["reasons"].append("Apply only if fundamentals are strong")
        elif gmp_pct <= 0:
            rec["action"] = "AVOID"
            rec["reasons"].append(f"Negative/Zero GMP")
            rec["reasons"].append("High risk of listing loss")
        else:
            rec["action"] = "WAIT"
            rec["reasons"].append("Low GMP - wait for better opportunity")
        
        recommendations.append(rec)
    
    return recommendations


async def run_portfolio_advisor():
    """Main function - analyze all users' portfolios and send recommendations"""
    db = get_db()
    users = await db.users.find({"settings.alerts_enabled": {"$ne": False}}).to_list(500)
    
    # Get IPO recommendations (same for all users)
    ipo_recs = await analyze_ipo_opportunities()
    
    for user in users:
        holdings = await db.holdings.find({"user_id": user["_id"]}).to_list(100)
        if not holdings:
            continue
        
        recommendations = []
        
        for h in holdings:
            # Skip mutual funds
            if h.get("holding_type") == "MF":
                continue
            
            data = await get_stock_data(h["symbol"])
            if not data:
                continue
            
            indicators = calculate_indicators(data)
            rec = generate_recommendation(
                h["symbol"],
                h["avg_price"],
                h["quantity"],
                indicators
            )
            
            # Fetch news for actionable recommendations
            if rec["action"] not in ["HOLD"]:
                news = await fetch_stock_news(h["symbol"])
                if news and news[0].get("title"):
                    rec["news"] = news
                    # Add news to detailed reasons
                    if rec.get("detailed_reasons"):
                        rec["detailed_reasons"].append(f"📰 Recent news: {news[0]['title']} (Source: {news[0].get('publisher', 'News')})")
                recommendations.append(rec)
        
        # Check if we already sent today
        today = datetime.utcnow().date().isoformat()
        existing = await db.advisor_history.find_one({"user_id": user["_id"], "date": today})
        
        if existing:
            continue
        
        # Send if there are recommendations
        if recommendations or ipo_recs:
            await send_advisor_alert(user, recommendations, ipo_recs)
            await db.advisor_history.insert_one({
                "user_id": user["_id"],
                "date": today,
                "recommendations": len(recommendations),
                "created_at": datetime.utcnow()
            })


async def send_advisor_alert(user: dict, stock_recs: list, ipo_recs: list):
    """Send portfolio advisor alert"""
    
    # Build Telegram message
    msg = "🤖 *StockPilot Daily Advisory*\n"
    msg += f"_{datetime.now().strftime('%d %b %Y, %I:%M %p')}_\n\n"
    
    if stock_recs:
        msg += "📊 *PORTFOLIO ACTIONS*\n\n"
        
        # Group by action
        for action in ["STRONG BUY", "BUY MORE", "PARTIAL SELL", "SELL", "EXIT", "WAIT", "HOLD - WATCH"]:
            action_recs = [r for r in stock_recs if r["action"] == action]
            if not action_recs:
                continue
            
            emoji = {"STRONG BUY": "🟢", "BUY MORE": "🟢", "PARTIAL SELL": "🟡", "SELL": "🔴", "EXIT": "🔴", "WAIT": "⏳", "HOLD - WATCH": "👀"}.get(action, "•")
            
            for r in action_recs:
                pnl_emoji = "📈" if r["pnl_pct"] >= 0 else "📉"
                msg += f"{emoji} *{action}: {r['symbol']}*\n"
                msg += f"   CMP: ₹{r['current_price']:.2f} | Avg: ₹{r['avg_price']:.2f}\n"
                msg += f"   {pnl_emoji} P&L: {r['pnl_pct']:+.1f}% | RSI: {r['rsi']}\n"
                for reason in r["reasons"][:2]:
                    msg += f"   • {reason}\n"
                if r["target"]:
                    msg += f"   🎯 Target: ₹{r['target']}\n"
                if r["stop_loss"]:
                    msg += f"   🛑 Stop Loss: ₹{r['stop_loss']}\n"
                msg += "\n"
    
    # IPO recommendations
    actionable_ipos = [i for i in ipo_recs if i["action"] in ["APPLY", "AVOID"]]
    if actionable_ipos:
        msg += "📋 *IPO RECOMMENDATIONS*\n\n"
        for ipo in actionable_ipos:
            emoji = "✅" if ipo["action"] == "APPLY" else "❌"
            msg += f"{emoji} *{ipo['action']}: {ipo['name']}*\n"
            msg += f"   Price: {ipo['price_band']} | GMP: ₹{ipo['gmp']} ({ipo['gmp_pct']:.0f}%)\n"
            for reason in ipo["reasons"][:2]:
                msg += f"   • {reason}\n"
            msg += "\n"
    
    if not stock_recs and not actionable_ipos:
        msg += "✨ No actions needed today. Your portfolio is on track!\n"
    
    msg += "\n_⚠️ Not financial advice. Do your own research._"
    
    # Send Telegram
    if user.get("telegram_chat_id") and settings.telegram_bot_token:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                    json={"chat_id": user["telegram_chat_id"], "text": msg, "parse_mode": "Markdown"}
                )
        except Exception as e:
            print(f"Telegram error: {e}")
    
    # Send Email
    if user.get("email"):
        html = f"""
        <div style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #3b82f6;">🤖 StockPilot Daily Advisory</h2>
            <p style="color: #666;">{datetime.now().strftime('%d %b %Y, %I:%M %p')}</p>
        """
        
        if stock_recs:
            html += "<h3>📊 Portfolio Actions</h3>"
            for r in stock_recs:
                color = "#22c55e" if "BUY" in r["action"] else "#ef4444" if r["action"] in ["SELL", "EXIT"] else "#f59e0b"
                html += f"""
                <div style="border-left: 4px solid {color}; padding: 12px; margin: 10px 0; background: #f8f9fa;">
                    <strong style="color: {color};">{r['action']}: {r['symbol']}</strong><br>
                    <span>CMP: ₹{r['current_price']:.2f} | Avg: ₹{r['avg_price']:.2f} | P&L: {r['pnl_pct']:+.1f}%</span><br>
                    <ul style="margin: 5px 0; padding-left: 20px;">
                        {''.join(f'<li>{reason}</li>' for reason in r['reasons'][:2])}
                    </ul>
                    {f"<span>🎯 Target: ₹{r['target']}</span><br>" if r['target'] else ""}
                    {f"<span>🛑 Stop Loss: ₹{r['stop_loss']}</span>" if r['stop_loss'] else ""}
                </div>
                """
        
        if actionable_ipos:
            html += "<h3>📋 IPO Recommendations</h3>"
            for ipo in actionable_ipos:
                color = "#22c55e" if ipo["action"] == "APPLY" else "#ef4444"
                html += f"""
                <div style="border-left: 4px solid {color}; padding: 12px; margin: 10px 0; background: #f8f9fa;">
                    <strong style="color: {color};">{ipo['action']}: {ipo['name']}</strong><br>
                    <span>Price: {ipo['price_band']} | GMP: ₹{ipo['gmp']} ({ipo['gmp_pct']:.0f}%)</span><br>
                    <ul style="margin: 5px 0; padding-left: 20px;">
                        {''.join(f'<li>{reason}</li>' for reason in ipo['reasons'][:2])}
                    </ul>
                </div>
                """
        
        html += """
            <p style="color: #999; font-size: 12px; margin-top: 20px;">
                ⚠️ This is not financial advice. Please do your own research before making investment decisions.
            </p>
        </div>
        """
        
        await send_email(user["email"], "StockPilot Daily Advisory", html)
