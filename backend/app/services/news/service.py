"""Shared news service for fetching stock news via Google News RSS."""

import xml.etree.ElementTree as ET

import httpx

from ...core.constants import COMPANY_NAMES


async def fetch_stock_news(symbol: str, client: httpx.AsyncClient | None = None, limit: int = 3) -> list:
    """Fetch recent news for a stock via Google News RSS.

    Args:
        symbol: Stock symbol (e.g., 'RELIANCE')
        client: Optional httpx client for connection reuse
        limit: Max news items to return

    Returns:
        List of dicts with title, publisher, link keys
    """
    company = COMPANY_NAMES.get(symbol, symbol)
    url = f"https://news.google.com/rss/search?q={company}+stock+NSE&hl=en-IN&gl=IN&ceid=IN:en"

    async def _fetch(c: httpx.AsyncClient) -> list:
        try:
            resp = await c.get(url, follow_redirects=True)
            if resp.status_code != 200:
                return []
            try:
                root = ET.fromstring(resp.text)
            except ET.ParseError:
                return []
            items = root.findall(".//item")[:limit]
            news = []
            for item in items:
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                parts = title.rsplit(" - ", 1)
                news.append({"title": parts[0], "publisher": parts[1] if len(parts) > 1 else "", "link": link})
            return news
        except Exception:
            return []

    if client:
        return await _fetch(client)
    async with httpx.AsyncClient(timeout=10, headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True) as c:
        return await _fetch(c)
