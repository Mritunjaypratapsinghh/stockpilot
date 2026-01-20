from ..database import get_db
from ..services.notification_service import send_email
from ..config import get_settings
from datetime import datetime, timedelta
import httpx
import re

settings = get_settings()

async def parse_date_range(date_text):
    """Parse date range like '13-16 Jan' into open/close dates"""
    if not date_text:
        return None, None
    try:
        match = re.search(r'(\d{1,2})[-–](\d{1,2})\s*(\w+)', date_text)
        if match:
            start_day, end_day = int(match.group(1)), int(match.group(2))
            month_str = match.group(3)[:3].lower()
            months = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                      'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
            month = months.get(month_str)
            if month:
                year = datetime.utcnow().year
                return datetime(year, month, start_day), datetime(year, month, end_day)
    except:
        pass
    return None, None

async def scrape_ipo_data():
    """Scrape IPO data from ipowatch.in and insert/update IPOs"""
    db = get_db()
    
    # Mark old IPOs as CLOSED
    await db.ipos.update_many(
        {"dates.close": {"$lt": datetime.utcnow()}, "status": {"$in": ["OPEN", "UPCOMING"]}},
        {"$set": {"status": "CLOSED", "updated_at": datetime.utcnow()}}
    )
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get("https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/", 
                headers={"User-Agent": "Mozilla/5.0"})
            
            if resp.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                table = soup.find("table")
                
                if table:
                    rows = table.find_all("tr")[1:]
                    for row in rows[:20]:
                        cols = row.find_all("td")
                        if len(cols) >= 6:
                            name = cols[0].get_text(strip=True)
                            gmp_text = cols[1].get_text(strip=True).replace("₹", "").replace(",", "")
                            price_text = cols[2].get_text(strip=True).replace("₹", "").replace(",", "")
                            date_text = cols[5].get_text(strip=True) if len(cols) > 5 else ""
                            type_text = cols[6].get_text(strip=True) if len(cols) > 6 else ""
                            
                            try:
                                price = float(price_text) if price_text and price_text != "-" else 0
                            except:
                                price = 0
                            if price == 0:
                                continue
                            try:
                                gmp = float(gmp_text) if gmp_text and gmp_text != "-" else 0
                            except:
                                gmp = 0
                            
                            open_date, close_date = await parse_date_range(date_text)
                            
                            # Determine status based on dates
                            today = datetime.utcnow().date()
                            if close_date and close_date.date() < today:
                                status = "CLOSED"
                            elif open_date and open_date.date() <= today <= close_date.date():
                                status = "OPEN"
                            else:
                                status = "UPCOMING"
                            
                            ipo_type = "SME" if "SME" in type_text.upper() else "MAINBOARD"
                            lot_size = max(1, int(100000 / price)) if ipo_type == "SME" and price > 0 else max(1, int(15000 / price)) if price > 0 else 1
                            
                            await db.ipos.update_one(
                                {"name": name},
                                {"$set": {
                                    "name": name,
                                    "ipo_type": ipo_type,
                                    "price_band": {"low": price * 0.95, "high": price},
                                    "lot_size": lot_size,
                                    "gmp": gmp,
                                    "date_range": date_text,
                                    "dates": {"open": open_date, "close": close_date},
                                    "status": status,
                                    "updated_at": datetime.utcnow()
                                }, "$setOnInsert": {
                                    "created_at": datetime.utcnow()
                                }},
                                upsert=True
                            )
    except Exception as e:
        print(f"IPO scrape error: {e}")

async def check_ipo_alerts():
    """Check for IPO-related alerts (allotment, listing)"""
    db = get_db()
    today = datetime.utcnow().date()
    
    # Find IPOs with allotment or listing today
    ipos = await db.ipos.find({
        "$or": [
            {"dates.allotment": {"$gte": datetime.combine(today, datetime.min.time()), "$lt": datetime.combine(today, datetime.max.time())}},
            {"dates.listing": {"$gte": datetime.combine(today, datetime.min.time()), "$lt": datetime.combine(today, datetime.max.time())}}
        ]
    }).to_list(20)
    
    if not ipos:
        return
    
    # Notify all users with daily_digest enabled
    users = await db.users.find({"settings.alerts_enabled": True}).to_list(500)
    
    for ipo in ipos:
        is_allotment = ipo.get("dates", {}).get("allotment") and ipo["dates"]["allotment"].date() == today
        is_listing = ipo.get("dates", {}).get("listing") and ipo["dates"]["listing"].date() == today
        
        if is_allotment:
            msg = f"📋 IPO Allotment Today: {ipo['name']}\nCheck your allotment status!"
        elif is_listing:
            gmp = ipo.get("gmp", 0)
            msg = f"🔔 IPO Listing Today: {ipo['name']}\nGMP: ₹{gmp}"
        else:
            continue
        
        for user in users:
            if user.get("telegram_chat_id") and settings.telegram_bot_token:
                try:
                    async with httpx.AsyncClient() as client:
                        await client.post(f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                            json={"chat_id": user["telegram_chat_id"], "text": msg})
                except:
                    pass
