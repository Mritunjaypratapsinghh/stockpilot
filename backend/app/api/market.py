from fastapi import APIRouter, HTTPException, Depends
from ..services.price_service import get_stock_price, search_stock
from ..middleware.rate_limit import rate_limit

router = APIRouter()

@router.get("/quote/{symbol}")
async def get_quote(symbol: str, exchange: str = "NSE"):
    price_data = await get_stock_price(symbol.upper(), exchange)
    if not price_data:
        raise HTTPException(status_code=404, detail="Stock not found")
    return price_data

@router.get("/search", dependencies=[Depends(rate_limit("search"))])
async def search(q: str):
    results = await search_stock(q)
    return results

@router.get("/indices")
async def get_indices():
    import httpx
    indices = {"NIFTY50": "^NSEI", "SENSEX": "^BSESN", "BANKNIFTY": "^NSEBANK"}
    result = {}
    async with httpx.AsyncClient(timeout=10) as client:
        for name, symbol in indices.items():
            try:
                resp = await client.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}", headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    meta = resp.json()["chart"]["result"][0]["meta"]
                    price = meta.get("regularMarketPrice", 0)
                    prev = meta.get("previousClose", price)
                    result[name] = {"price": round(price, 2), "change": round(price - prev, 2), "change_pct": round((price - prev) / prev * 100, 2) if prev else 0}
            except:
                pass
    return result

@router.get("/quotes")
async def get_bulk_quotes(symbols: str):
    from ..services.price_service import get_bulk_prices
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    return await get_bulk_prices(symbol_list)
