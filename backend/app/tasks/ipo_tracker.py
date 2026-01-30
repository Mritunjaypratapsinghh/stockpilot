from ..models.documents import IPO, User
from ..core.config import settings
from ..utils.logger import logger
from datetime import datetime
import httpx
import re


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
    except (ValueError, AttributeError) as e:
        logger.debug(f"Date parse error: {e}")
    return None, None


async def scrape_ipo_data():
    """Scrape IPO data from ipowatch.in and insert/update IPOs"""
    # Mark old IPOs as CLOSED
    old_ipos = await IPO.find(
        IPO.status.is_in(["OPEN", "UPCOMING"])
    ).to_list()
    
    for ipo in old_ipos:
        if ipo.dates and ipo.dates.get("close") and ipo.dates["close"] < datetime.utcnow():
            ipo.status = "CLOSED"
            ipo.updated_at = datetime.utcnow()
            await ipo.save()
    
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
                            except ValueError:
                                price = 0
                            if price == 0:
                                continue
                            try:
                                gmp = float(gmp_text) if gmp_text and gmp_text != "-" else 0
                            except ValueError:
                                gmp = 0
                            
                            open_date, close_date = await parse_date_range(date_text)
                            
                            today = datetime.utcnow().date()
                            if close_date and close_date.date() < today:
                                status = "CLOSED"
                            elif open_date and open_date.date() <= today <= close_date.date():
                                status = "OPEN"
                            else:
                                status = "UPCOMING"
                            
                            ipo_type = "SME" if "SME" in type_text.upper() else "MAINBOARD"
                            lot_size = max(1, int(100000 / price)) if ipo_type == "SME" and price > 0 else max(1, int(15000 / price)) if price > 0 else 1
                            
                            existing = await IPO.find_one(IPO.name == name)
                            if existing:
                                existing.ipo_type = ipo_type
                                existing.price_band = {"low": price * 0.95, "high": price}
                                existing.lot_size = lot_size
                                existing.gmp = gmp
                                existing.date_range = date_text
                                existing.dates = {"open": open_date, "close": close_date}
                                existing.status = status
                                existing.updated_at = datetime.utcnow()
                                await existing.save()
                            else:
                                await IPO(
                                    name=name, ipo_type=ipo_type,
                                    price_band={"low": price * 0.95, "high": price},
                                    lot_size=lot_size, gmp=gmp, date_range=date_text,
                                    dates={"open": open_date, "close": close_date},
                                    status=status, created_at=datetime.utcnow(), updated_at=datetime.utcnow()
                                ).insert()
    except Exception as e:
        logger.error(f"IPO scrape error: {e}")


async def check_ipo_alerts():
    """Check for IPO-related alerts (allotment, listing)"""
    today = datetime.utcnow().date()
    
    ipos = await IPO.find().to_list()
    relevant_ipos = [
        ipo for ipo in ipos
        if ipo.dates and (
            (ipo.dates.get("allotment") and ipo.dates["allotment"].date() == today) or
            (ipo.dates.get("listing") and ipo.dates["listing"].date() == today)
        )
    ]
    
    if not relevant_ipos:
        return
    
    users = await User.find(User.settings.alerts_enabled == True).to_list()
    
    for ipo in relevant_ipos:
        is_allotment = ipo.dates.get("allotment") and ipo.dates["allotment"].date() == today
        is_listing = ipo.dates.get("listing") and ipo.dates["listing"].date() == today
        
        if is_allotment:
            msg = f"📋 IPO Allotment Today: {ipo.name}\nCheck your allotment status!"
        elif is_listing:
            msg = f"🔔 IPO Listing Today: {ipo.name}\nGMP: ₹{ipo.gmp or 0}"
        else:
            continue
        
        for user in users:
            if user.telegram_chat_id and settings.telegram_bot_token:
                try:
                    async with httpx.AsyncClient() as client:
                        await client.post(f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                            json={"chat_id": user.telegram_chat_id, "text": msg})
                except httpx.HTTPError as e:
                    logger.warning(f"Telegram notification error: {e}")
