"""Shared mutual fund service for fetching MF holdings."""

import httpx

from ..cache import cache_get, cache_set


async def fetch_mf_holdings(scheme_name: str) -> list:
    """Fetch top holdings for a MF from Groww API.

    Args:
        scheme_name: Mutual fund scheme name

    Returns:
        List of tuples: [(stock_symbol, weight_pct), ...]
    """
    # Use full name hash to avoid collisions
    cache_key = f"mf_holdings:{hash(scheme_name) % 10**8}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            # Search for scheme on Groww
            search_term = scheme_name.split()[0]
            groww_url = (
                f"https://groww.in/v1/api/search/v1/entity?app=false&entity_type=scheme&page=0&q={search_term}&size=1"
            )
            groww_resp = await client.get(groww_url, headers={"User-Agent": "Mozilla/5.0"})

            if groww_resp.status_code != 200:
                return []

            data = groww_resp.json()
            if not data.get("content"):
                return []

            scheme_code = data["content"][0].get("search_id", "")
            if not scheme_code:
                return []

            detail_url = f"https://groww.in/v1/api/data/mf/web/v1/scheme/{scheme_code}"
            detail_resp = await client.get(detail_url, headers={"User-Agent": "Mozilla/5.0"})

            if detail_resp.status_code != 200:
                return []

            detail = detail_resp.json()
            holdings = detail.get("holdings", [])[:10]
            result = []
            for h in holdings:
                if h.get("corpus_per", 0) > 0:
                    name = h.get("company_name", "").upper().replace(" LTD", "").replace(" LIMITED", "")
                    result.append((name.split()[0], h.get("corpus_per", 0)))

            if result:
                await cache_set(cache_key, result, ttl=86400)  # 24hr cache
            return result
    except Exception:
        return []
