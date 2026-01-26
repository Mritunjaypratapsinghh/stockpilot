import asyncio
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import httpx

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_DB = os.getenv("MONGODB_DB", "stockpilot")

db = None

async def init_db():
    global db
    if MONGODB_URI:
        client = AsyncIOMotorClient(MONGODB_URI)
        db = client[MONGODB_DB]

async def get_user_by_telegram(chat_id: str):
    if db:
        return await db.users.find_one({"telegram_chat_id": str(chat_id)})
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 *Welcome to StockPilot Bot!*\n\n"
        "Commands:\n"
        "/portfolio - View your portfolio\n"
        "/alerts - View active alerts\n"
        "/quote SYMBOL - Get stock price\n"
        "/link EMAIL - Link your account\n"
        "/help - Show help",
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*StockPilot Commands*\n\n"
        "/portfolio - Portfolio summary with P&L\n"
        "/holdings - List all holdings\n"
        "/alerts - Active price alerts\n"
        "/quote HDFCBANK - Get live price\n"
        "/link user@email.com - Link account",
        parse_mode="Markdown"
    )

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = await get_user_by_telegram(update.effective_chat.id)
        if not user:
            await update.message.reply_text("❌ Account not linked. Use /link EMAIL")
            return
        
        # Fix: Query with ObjectId, not string
        holdings = await db.holdings.find({"user_id": ObjectId(user["_id"])}).to_list(50)
        if not holdings:
            await update.message.reply_text("📭 No holdings found. Add via web app.")
            return
        
        total_inv = sum(h["quantity"] * h["avg_price"] for h in holdings)
        msg = "📊 *Your Portfolio*\n\n"
        total_val = 0
        
        for h in holdings:
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    ticker = f"{h['symbol']}.NS"
                    resp = await client.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}", 
                                            headers={"User-Agent": "Mozilla/5.0"})
                    price = resp.json()["chart"]["result"][0]["meta"].get("regularMarketPrice", h["avg_price"]) if resp.status_code == 200 else h["avg_price"]
            except:
                price = h["avg_price"]
            
            val = h["quantity"] * price
            inv = h["quantity"] * h["avg_price"]
            pnl = val - inv
            pnl_pct = (pnl / inv * 100) if inv > 0 else 0
            total_val += val
            
            emoji = "🟢" if pnl >= 0 else "🔴"
            msg += f"{emoji} *{h['symbol']}*\n   {h['quantity']} × ₹{price:.2f} = ₹{val:,.0f}\n   P&L: ₹{pnl:,.0f} ({pnl_pct:+.1f}%)\n\n"
        
        total_pnl = total_val - total_inv
        total_pnl_pct = (total_pnl / total_inv * 100) if total_inv > 0 else 0
        emoji = "🟢" if total_pnl >= 0 else "🔴"
        
        msg += f"━━━━━━━━━━━━━━━\n💰 *Total Value:* ₹{total_val:,.0f}\n📈 *Invested:* ₹{total_inv:,.0f}\n{emoji} *P&L:* ₹{total_pnl:,.0f} ({total_pnl_pct:+.1f}%)"
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user_by_telegram(update.effective_chat.id)
    if not user:
        await update.message.reply_text("❌ Account not linked. Use /link EMAIL")
        return
    
    # Fix: Query with ObjectId, not string
    alerts_list = await db.alerts.find({"user_id": ObjectId(user["_id"]), "is_active": True}).to_list(20)
    if not alerts_list:
        await update.message.reply_text("🔕 No active alerts.")
        return
    
    msg = "🔔 *Active Alerts*\n\n"
    for a in alerts_list:
        alert_type = "📈" if "ABOVE" in a["alert_type"] else "📉"
        msg += f"{alert_type} {a['symbol']} {a['alert_type'].replace('_', ' ')} ₹{a['target_value']}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /quote HDFCBANK")
        return
    
    symbol = context.args[0].upper()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS",
                                    headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                meta = resp.json()["chart"]["result"][0]["meta"]
                price = meta.get("regularMarketPrice", 0)
                prev = meta.get("previousClose", price)
                change = price - prev
                change_pct = (change / prev * 100) if prev else 0
                
                emoji = "🟢" if change >= 0 else "🔴"
                msg = f"📊 *{symbol}*\n\n💰 Price: ₹{price:.2f}\n{emoji} Change: ₹{change:.2f} ({change_pct:+.2f}%)\n📈 High: ₹{meta.get('regularMarketDayHigh', price):.2f}\n📉 Low: ₹{meta.get('regularMarketDayLow', price):.2f}"
                await update.message.reply_text(msg, parse_mode="Markdown")
            else:
                await update.message.reply_text(f"❌ Stock {symbol} not found")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /link your@email.com")
        return
    
    email = context.args[0].lower()
    user = await db.users.find_one({"email": email})
    if not user:
        await update.message.reply_text(f"❌ No account found for {email}")
        return
    
    await db.users.update_one({"email": email}, {"$set": {"telegram_chat_id": str(update.effective_chat.id)}})
    await update.message.reply_text(f"✅ Linked to {email}!\n\nTry /portfolio")

async def main():
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set")
        return
    
    await init_db()
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("holdings", portfolio))
    app.add_handler(CommandHandler("alerts", alerts))
    app.add_handler(CommandHandler("quote", quote))
    app.add_handler(CommandHandler("q", quote))
    app.add_handler(CommandHandler("link", link))
    
    print("🤖 StockPilot Bot started!")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
