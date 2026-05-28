"""CEORater MCP Server — exposes CEORater API as MCP tools."""
import json
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

API_BASE = "https://api.ceorater.com"

mcp = FastMCP("ceorater", description="CEO performance analytics — scores, compensation, tenure, and shareholder returns for S&P 500 CEOs")


def _get_key() -> str:
    key = os.environ.get("CEORATER_API_KEY", "").strip()
    if not key:
        return ""
    return key


def _headers() -> dict:
    return {"Authorization": f"Bearer {_get_key()}"}


async def _call(path: str, params: dict | None = None) -> dict | list | str:
    key = _get_key()
    if not key:
        return "CEORATER_API_KEY not set. Get your key at https://www.ceorater.com"

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(f"{API_BASE}{path}", headers=_headers(), params=params)

    if resp.status_code == 401:
        return "Invalid API key. Check your CEORATER_API_KEY."
    if resp.status_code == 403:
        return "Subscription not active. Visit https://www.ceorater.com to subscribe."
    if resp.status_code == 404:
        return "Ticker not found in CEORater coverage."
    if resp.status_code >= 400:
        return f"API error {resp.status_code}: {resp.text}"

    return resp.json()


def _format_result(data: Any) -> str:
    if isinstance(data, str):
        return data
    return json.dumps(data, indent=2)


@mcp.tool()
async def ceo_lookup(ticker: str) -> str:
    """Look up CEO performance data for a specific stock ticker.

    Returns CEO name, founder status, CEORaterScore, AlphaScore, CompScore,
    compensation, total shareholder return, tenure, and revenue CAGR.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT, NVDA)
    """
    result = await _call(f"/v1/ceo/{ticker.upper()}", {"format": "ui"})
    return _format_result(result)


@mcp.tool()
async def ceo_search(query: str) -> str:
    """Search for CEOs by company name, CEO name, sector, or industry.

    Returns matching companies with full CEO performance metrics.

    Args:
        query: Search term (e.g., "Apple", "technology", "Jensen Huang")
    """
    result = await _call("/v1/search", {"q": query, "format": "ui"})
    return _format_result(result)


@mcp.tool()
async def ceo_list(limit: int = 50, offset: int = 0) -> str:
    """List all CEOs with performance scores, paginated.

    Returns companies sorted with CEO performance metrics including
    CEORaterScore, AlphaScore, CompScore, compensation, and TSR.

    Args:
        limit: Number of results per page (default 50, max 2000)
        offset: Starting position for pagination (default 0)
    """
    result = await _call("/v1/ceos", {"limit": limit, "offset": offset, "format": "ui"})
    return _format_result(result)


@mcp.tool()
async def ceo_meta() -> str:
    """Get CEORater dataset metadata — total CEO count, last refresh time, and API version."""
    result = await _call("/v1/meta")
    return _format_result(result)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
