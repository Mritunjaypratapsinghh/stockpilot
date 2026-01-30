from fastapi import APIRouter
from datetime import datetime
import re
from ....utils.logger import logger
from ....core.response_handler import StandardResponse

router = APIRouter()


def parse_ipo_dates(dates_str):
    if not dates_str:
        return None, None, "UPCOMING"
    
    today = datetime.now()
    current_year = today.year
    
    try:
        match = re.search(r'(\d{1,2})[-–](\d{1,2})\s*(\w+)', dates_str)
        if match:
            start_day = int(match.group(1))
            end_day = int(match.group(2))
            month_str = match.group(3)[:3]
            
            months = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                      'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
            month = months.get(month_str.lower(), today.month)
            year = current_year
            
            end_date = datetime(year, month, end_day)
            start_date = datetime(year, month, start_day)
            
            if end_date.date() < today.date():
                return start_date, end_date, "CLOSED"
            elif start_date.date() > today.date():
                return start_date, end_date, "UPCOMING"
            else:
                return start_date, end_date, "OPEN"
    except (ValueError, AttributeError):
        pass
    
    return None, None, "UNKNOWN"


async def get_ipos_from_db():
    from ....models.documents import IPO
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
        
        result.append({
            "name": ipo.name, "type": ipo.ipo_type, "price": price, "lot_size": ipo.lot_size,
            "min_investment": ipo.lot_size * price, "gmp": gmp, "gmp_pct": round(gmp_pct, 2),
            "estimated_listing": round(price + gmp, 2) if price > 0 else 0,
            "dates": ipo.date_range or "", "action": action, "status": ipo.status
        })
    
    return result


@router.get("/upcoming")
async def get_upcoming_ipos():
    return StandardResponse.ok(await get_ipos_from_db())


@router.get("/gmp")
async def get_gmp_tracker():
    return StandardResponse.ok(await get_ipos_from_db())


@router.post("/refresh")
async def refresh_ipo_data():
    from ....tasks.ipo_tracker import scrape_ipo_data
    await scrape_ipo_data()
    return StandardResponse.ok(message="IPO data refreshed")


@router.get("/all")
async def get_all_ipos():
    ipos = await get_ipos_from_db()
    mainboard = [i for i in ipos if i["type"] == "MAINBOARD"]
    sme = [i for i in ipos if i["type"] == "SME"]
    return StandardResponse.ok({
        "mainboard": mainboard, "sme": sme, "all": ipos,
        "count": len(ipos), "updated_at": datetime.utcnow().isoformat()
    })
