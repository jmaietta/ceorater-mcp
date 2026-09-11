"""CEORater MCP Server — CEO performance data as MCP tools.

The CEORater API is free and needs no key, so this server carries no
Authorization header and there is nothing for a user to configure. The previous
version required CEORATER_API_KEY and forwarded each caller's bearer token to a
billing gateway that no longer exists; every tool in it now fails.

Runs two ways:
  stdio (default)          local install, e.g. from Claude Desktop
  MCP_TRANSPORT=http       remote server, one instance serving everyone

Every tool returns the same ten fields www.ceorater.com displays. The scores
this server used to expose -- CEORaterScore, AlphaScore, CompScore,
RevenueCAGRScore -- have been retired from the product, as has Avg Annual TSR,
which was computed as total return divided by tenure rather than compounded and
overstated every multi-year record.
"""
import json
import os
from typing import Any

import httpx

from ceorater_mcp import __version__

# mcp 2.0 renamed FastMCP to MCPServer. Both are supported: a user may have
# either pinned, and a fresh pip install now resolves to 2.x -- which is how
# this shipped broken the first time, working in a dev environment that still
# had 1.x installed.
try:
    from mcp.server.mcpserver import MCPServer as _Server
    _MCP2 = True
except ImportError:  # mcp < 2
    from mcp.server.fastmcp import FastMCP as _Server
    _MCP2 = False

API_BASE = "https://api.ceorater.com/api/v1"
TIMEOUT = 30

mcp = _Server(
    "ceorater",
    version=__version__,
    instructions=(
        "CEO performance for 500+ US public companies: how the stock did over "
        "each CEO's tenure, what the S&P 500 did over that same window, how long "
        "they have been in the job, and what they were paid. Sectors and "
        "industries are S&P's own GICS classification. Reported figures only -- "
        "no ratings or scores, and no investment recommendations."
    ),
)


async def _call(path: str, params: dict | None = None) -> Any:
    params = {k: v for k, v in (params or {}).items() if v is not None}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(f"{API_BASE}{path}", params=params)
    except httpx.HTTPError as exc:
        return f"Could not reach the CEORater API: {exc}"

    if resp.status_code == 404:
        return "Not found in CEORater coverage."
    if resp.status_code == 429:
        return "Rate limited: 100 requests per 15 minutes per IP. Wait for the window to roll."
    if resp.status_code == 503:
        return "CEORater data is temporarily unavailable."
    if resp.status_code >= 400:
        return f"API error {resp.status_code}: {resp.text[:200]}"
    return resp.json()


def _format_result(data: Any) -> str:
    if isinstance(data, str):
        return data
    return json.dumps(data, indent=2)


FIELD_NOTE = (
    "Fields: ticker, company, ceo, founder, sector, industry, tenure_years, "
    "total_return_pct, spy_return_pct, compensation_musd. Returns are already "
    "percentages, so total_return_pct 545800 means +545,800%. Compensation is in "
    "millions of USD."
)


@mcp.tool()
async def ceo_lookup(ticker: str) -> str:
    """Look up the CEO of a company by ticker.

    Returns an array: a ticker can hold more than one record, because Oracle,
    KKR, Globe Life, Lululemon and Netflix run co-CEOs and each executive has
    their own start date and their own return.

    {note}

    Args:
        ticker: Stock ticker symbol, e.g. AAPL, MSFT, NVDA
    """
    return _format_result(await _call(f"/ceo/{ticker.strip().upper()}"))


@mcp.tool()
async def ceo_list(
    sector: str | None = None,
    industry: str | None = None,
    founder: bool | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> str:
    """List CEOs, optionally filtered. With no arguments, returns all of them.

    Filters are exact and case-insensitive, and combine. Use ceo_sectors or
    ceo_industries first to see the valid values rather than guessing a spelling.

    {note}

    Args:
        sector: Exact GICS sector, e.g. "Information Technology"
        industry: Exact GICS sub-industry, e.g. "Semiconductors"
        founder: True for founder-led companies only, False to exclude them
        limit: Maximum records to return. Omit for every CEO.
        offset: Starting position, for paging
    """
    return _format_result(await _call("/ceos", {
        "sector": sector,
        "industry": industry,
        "founder": None if founder is None else str(bool(founder)).lower(),
        "limit": limit,
        "offset": offset or None,
    }))


@mcp.tool()
async def ceo_search(query: str) -> str:
    """Search CEOs by company name, ticker, CEO name, sector or industry.

    This is a loose substring match across all five, so "Technology" also
    returns Align Technology and every Biotechnology company. For an exact
    sector or industry, use ceo_list with the sector or industry argument.

    {note}

    Args:
        query: Search term, e.g. "Apple", "Jensen Huang", "Semiconductors"
    """
    return _format_result(await _call("/search", {"q": query}))


@mcp.tool()
async def ceo_sectors() -> str:
    """The 11 GICS sectors CEORater uses, with a company count for each.

    These are S&P's own sector names, matched to each company on SEC CIK rather
    than ticker. Use one of these values verbatim as ceo_list's sector argument.
    """
    return _format_result(await _call("/sectors"))


@mcp.tool()
async def ceo_industries(sector: str | None = None) -> str:
    """The GICS sub-industries in use, with a company count and parent sector.

    Args:
        sector: Optionally narrow to one GICS sector
    """
    return _format_result(await _call("/industries", {"sector": sector}))


@mcp.tool()
async def ceo_meta() -> str:
    """Dataset size, field list, and how recently the data was refreshed."""
    return _format_result(await _call("/meta"))


# Tool docstrings are what the model reads, so the shared field note is spliced
# in rather than repeated by hand and allowed to drift between tools.
for _tool in (ceo_lookup, ceo_list, ceo_search):
    if _tool.__doc__:
        _tool.__doc__ = _tool.__doc__.replace("{note}", FIELD_NOTE)


def main():
    transport = os.environ.get("MCP_TRANSPORT", "stdio").strip().lower()
    if transport in ("http", "streamable-http"):
        import uvicorn

        port = int(os.environ.get("PORT", "8080"))
        # Stateless: no session affinity required, safe behind Cloud Run.
        # 2.x takes it as an argument; 1.x read it off a settings object.
        if _MCP2:
            app = mcp.streamable_http_app(stateless_http=True, host="0.0.0.0")
        else:
            mcp.settings.stateless_http = True
            app = mcp.streamable_http_app()
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
