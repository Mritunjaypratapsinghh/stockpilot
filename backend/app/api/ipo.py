from fastapi import APIRouter
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
import re

router = APIRouter()

def parse_ipo_dates(dates_str):
    """Parse date string and check if IPO is still open"""
    if not dates_str:
        return None, None, "UPCOMING"
    
    # Extract dates like "13-16 Jan" or "13 Jan - 16 Jan"
    today = datetime.now()
    current_year = today.year
    
    try:
        # Match patterns like "13-16 Jan", "13 Jan-16 Jan", "13-16 January"
        match = re.search(r'(\d{1,2})[-–](\d{1,2})\s*(\w+)', dates_str)
        if match:
            start_day = int(match.group(1))
            end_day = int(match.group(2))
            month_str = match.group(3)[:3]
            
            months = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                      'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
            month = months.get(month_str.lower(), today.month)
            
            # Handle year rollover
            year = current_year
            if month < today.month - 1:  # If month is way before current, it's likely past
                year = current_year  # Keep same year for comparison
            
            end_date = datetime(year, month, end_day)
            start_date = datetime(year, month, start_day)
            
            if end_date.date() < today.date():
                return start_date, end_date, "CLOSED"
            elif start_date.date() > today.date():
                return start_date, end_date, "UPCOMING"
            else:
                return start_date, end_date, "OPEN"
    except:
        pass
    
    return None, None, "UNKNOWN"

async def fetch_live_ipos():
    """Fetch live IPO GMP data from ipowatch.in"""
    ipos = []
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(
                "https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                tables = soup.find_all("table")
                
                if tables:
                    table = tables[0]
                    rows = table.find_all("tr")[1:]
                    
                    for row in rows[:30]:
                        cols = row.find_all("td")
                        if len(cols) >= 5:
                            name = cols[0].get_text(strip=True)
                            gmp_text = cols[1].get_text(strip=True).replace("₹", "").replace(",", "").strip()
                            price_text = cols[2].get_text(strip=True).replace("₹", "").replace(",", "").strip()
                            gain_text = cols[3].get_text(strip=True).replace("%", "").strip()
                            review = cols[4].get_text(strip=True) if len(cols) > 4 else ""
                            dates = cols[5].get_text(strip=True) if len(cols) > 5 else ""
                            
                            # Parse dates and determine status
                            _, _, status = parse_ipo_dates(dates)
                            
                            # Skip closed IPOs
                            if status == "CLOSED":
                                continue
                            
                            try:
                                gmp = float(gmp_text) if gmp_text and gmp_text != "-" else 0
                            except:
                                gmp = 0
                            
                            try:
                                price = float(price_text) if price_text and price_text != "-" else 0
                            except:
                                price = 0
                            
                            try:
                                gain_pct = float(gain_text) if gain_text and gain_text != "-" else 0
                            except:
                                gain_pct = (gmp / price * 100) if price > 0 else 0
                            
                            ipo_type = "SME" if "SME" in name.upper() or price < 200 else "Mainboard"
                            
                            if ipo_type == "SME":
                                lot_size = max(1, int(100000 / price)) if price > 0 else 1600
                            else:
                                lot_size = max(1, int(15000 / price)) if price > 0 else 13
                            
                            min_investment = lot_size * price
                            
                            if gain_pct > 15:
                                action = "APPLY"
                            elif gain_pct > 5:
                                action = "MAY APPLY"
                            elif gain_pct > 0:
                                action = "RISKY"
                            else:
                                action = "AVOID"
                            
                            ipos.append({
                                "name": name,
                                "type": ipo_type,
                                "price": price,
                                "lot_size": lot_size,
                                "min_investment": round(min_investment, 0),
                                "gmp": gmp,
                                "gmp_pct": round(gain_pct, 2),
                                "estimated_listing": round(price + gmp, 2) if price > 0 else 0,
                                "review": review,
                                "dates": dates,
                                "action": action,
                                "status": status
                            })
    except Exception as e:
        print(f"Error fetching IPOs: {e}")
    
    return ipos

@router.get("/upcoming")
async def get_upcoming_ipos():
    return await get_ipos_from_db()

@router.get("/gmp")
async def get_gmp_tracker():
    return await get_ipos_from_db()

@router.post("/refresh")
async def refresh_ipo_data():
    """Manually trigger IPO data refresh"""
    from ..tasks.ipo_tracker import scrape_ipo_data
    await scrape_ipo_data()
    return {"message": "IPO data refreshed"}

@router.get("/all")
async def get_all_ipos():
    ipos = await get_ipos_from_db()
    mainboard = [i for i in ipos if i["type"] == "MAINBOARD"]
    sme = [i for i in ipos if i["type"] == "SME"]
    return {
        "mainboard": mainboard,
        "sme": sme,
        "all": ipos,
        "count": len(ipos),
        "updated_at": datetime.utcnow().isoformat()
    }

async def get_ipos_from_db():
    """Get IPO data from database"""
    from ..models.documents import IPO
    ipos = await IPO.find(IPO.status.is_in(["OPEN", "UPCOMING"])).to_list()
    
    result = []
    for ipo in ipos:
        price = ipo.price_band.get("high", 0) if ipo.price_band else 0
        if price <= 0:
            continue
        gmp = ipo.gmp or 0
        gmp_pct = (gmp / price * 100) if price > 0 else 0
        
        if gmp_pct > 15:
            action = "APPLY"
        elif gmp_pct > 5:
            action = "MAY APPLY"
        elif gmp_pct > 0:
            action = "RISKY"
        else:
            action = "AVOID"
        
        dates_str = ipo.date_range or ""
        
        result.append({
            "name": ipo.name,
            "type": ipo.ipo_type,
            "price": price,
            "lot_size": ipo.lot_size,
            "min_investment": ipo.lot_size * price,
            "gmp": gmp,
            "gmp_pct": round(gmp_pct, 2),
            "estimated_listing": round(price + gmp, 2) if price > 0 else 0,
            "dates": dates_str,
            "action": action,
            "status": ipo.status
        })
    
    return result
