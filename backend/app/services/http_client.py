"""Shared httpx client — connection pooling for external API calls."""

import httpx

_client: httpx.AsyncClient | None = None


async def get_http_client() -> httpx.AsyncClient:
    """Get shared httpx client with connection pooling. Lazy-initialized."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(8.0, connect=3.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            headers={"User-Agent": "StockPilot/1.0"},
            follow_redirects=True,
        )
    return _client


async def close_http_client() -> None:
    """Close shared client on shutdown."""
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None
