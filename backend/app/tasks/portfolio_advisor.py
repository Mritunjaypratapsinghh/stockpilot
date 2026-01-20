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
    target = None
    stop_loss = None
    
    # === STRONG BUY CONDITIONS ===
    if rsi < 25 and indicators["range_position"] < 15:
        action = "STRONG BUY"
        reasons.append("Stock has fallen sharply and looks very cheap")
        reasons.append("Trading near its lowest price in a year - good entry point")
        target = indicators["sma_20"]
    
    # === BUY / ACCUMULATE CONDITIONS ===
    elif rsi < 35 and indicators["above_sma200"] != False:
        action = "BUY MORE"
        reasons.append("Stock is oversold - price dropped faster than usual")
        if pnl_pct < -10:
            reasons.append(f"Good chance to lower your average cost (currently down {abs(pnl_pct):.1f}%)")
        target = indicators["sma_50"]
    
    elif indicators["day_change"] < -4 and rsi < 45 and indicators["vol_ratio"] > 1.5:
        action = "BUY MORE"
        reasons.append(f"Stock dropped {abs(indicators['day_change']):.1f}% today with heavy trading")
        reasons.append("Could bounce back soon - potential buying opportunity")
        target = indicators["sma_20"]
    
    # === SELL CONDITIONS ===
    elif rsi > 75 and indicators["range_position"] > 90:
        action = "SELL"
        reasons.append("Stock has risen too fast, too quickly - may correct soon")
        reasons.append("Trading near its highest price in a year")
        if pnl_pct > 20:
            reasons.append(f"You're up {pnl_pct:.1f}% - good time to book profits")
    
    elif rsi > 70 and pnl_pct > 30:
        action = "PARTIAL SELL"
        reasons.append("Stock is overheated - risen faster than normal")
        reasons.append(f"You're up {pnl_pct:.1f}% - consider selling some to lock in gains")
    
    elif pnl_pct > 50 and indicators["day_change"] > 5:
        action = "PARTIAL SELL"
        reasons.append(f"Excellent profit of {pnl_pct:.1f}% - don't let it slip away")
        reasons.append(f"Stock jumped {indicators['day_change']:.1f}% today - good exit point")
    
    # === HOLD CONDITIONS ===
    elif 40 <= rsi <= 60 and indicators["above_sma50"]:
        action = "HOLD"
        reasons.append("Stock is in a healthy uptrend")
        reasons.append("No action needed - let your profits grow")
        target = indicators["resistance"]
        stop_loss = indicators["support"]
    
    # === WAIT / WATCH CONDITIONS ===
    elif not indicators["above_sma20"] and not indicators["above_sma50"]:
        if pnl_pct > 0:
            action = "HOLD - WATCH"
            reasons.append("Stock is weakening - falling below its recent averages")
            reasons.append("Set a stop-loss to protect your gains")
            stop_loss = indicators["support"]
        else:
            action = "WAIT"
            reasons.append("Stock is in a downtrend - not a good time to buy more")
            reasons.append("Wait for it to become cheaper before adding")
    
    # === EXIT CONDITIONS ===
    elif pnl_pct < -20 and not indicators["above_sma50"] and rsi > 50:
        action = "EXIT"
        reasons.append(f"Stock is down {abs(pnl_pct):.1f}% with no signs of recovery")
        reasons.append("Consider selling and investing elsewhere")
    
    # Default
    if not action:
        action = "HOLD"
        reasons.append("No clear signal right now - continue holding")
    
    return {
        "symbol": symbol,
        "action": action,
        "reasons": reasons,
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
            
            # Only include actionable recommendations (not plain HOLD)
            if rec["action"] not in ["HOLD"]:
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
