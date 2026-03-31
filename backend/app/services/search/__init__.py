"""Web search service for AI chat using DuckDuckGo (no API key needed)."""

import httpx


async def web_search(query: str, max_results: int = 3) -> list[dict]:
    """Search the web using DuckDuckGo HTML.

    Args:
        query: Search query
        max_results: Maximum results to return

    Returns:
        List of dicts with title, snippet, url keys
    """
    url = "https://html.duckduckgo.com/html/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.post(url, data={"q": query}, headers=headers)
            if resp.status_code != 200:
                return []

            html = resp.text
            results = []

            # Parse results from HTML (simple extraction)
            import re

            # Find result blocks
            blocks = re.findall(
                r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>(.+?)</a>.*?'
                r'<a class="result__snippet"[^>]*>(.+?)</a>',
                html,
                re.DOTALL,
            )

            for href, title, snippet in blocks[:max_results]:
                # Clean HTML tags
                title = re.sub(r"<[^>]+>", "", title).strip()
                snippet = re.sub(r"<[^>]+>", "", snippet).strip()
                results.append({"title": title, "snippet": snippet, "url": href})

            return results
    except Exception:
        return []


async def search_company_info(company_name: str) -> str:
    """Search for company information and format for AI context.

    Args:
        company_name: Company or stock name to search

    Returns:
        Formatted string with search results for AI context
    """
    query = f"{company_name} company India stock"
    results = await web_search(query, max_results=3)

    if not results:
        return ""

    lines = [f"WEB SEARCH RESULTS for '{company_name}':"]
    for r in results:
        lines.append(f"- {r['title']}: {r['snippet']}")

    return "\n".join(lines)
