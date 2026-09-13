"""CEORater MCP Server — CEO performance data as MCP tools.

The CEORater API is free and needs no key, so this server carries no
Authorization header and there is nothing for a user to configure. The previous
version required CEORATER_API_KEY and forwarded each caller's bearer token to a
billing gateway that no longer exists; every tool in it now fails.

Runs two ways:
  stdio (default)          local install, e.g. from Claude Desktop
  MCP_TRANSPORT=http       remote server, one instance serving everyone.
                           This is what https://mcp.ceorater.com/mcp runs.

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
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

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
DOCS_URL = "https://www.ceorater.com/api-docs.html"
TIMEOUT = 30

# The API rate-limits by IP. The hosted server makes every user's calls from
# the same few Cloud Run addresses, so without this every MCP user in the world
# would share one 100-per-15-minute bucket. When the key is set, the backend
# gives this server its own ceiling. Local stdio installs leave it unset and
# are limited per user, like any other caller.
INTERNAL_KEY = os.environ.get("CEORATER_INTERNAL_KEY", "").strip()

_SERVER_KWARGS: dict[str, Any] = dict(
    name="ceorater",
    instructions=(
        "CEO performance for 500+ US public companies: how the stock did over "
        "each CEO's tenure, what the S&P 500 did over that same window, how long "
        "they have been in the job, and what they were paid. Sectors and "
        "industries are S&P's own GICS classification. Reported figures only -- "
        "no ratings or scores, and no investment recommendations."
    ),
)
if _MCP2:
    _SERVER_KWARGS["version"] = __version__
else:
    # 1.x decides at construction, from `host`, whether to reject requests whose
    # Host header is not localhost. The default host is 127.0.0.1, which would
    # answer every request to mcp.ceorater.com with 421. 2.x takes the same
    # settings as arguments to streamable_http_app() instead; see main().
    _SERVER_KWARGS.update(host="0.0.0.0", stateless_http=True, json_response=True)

mcp = _Server(**_SERVER_KWARGS)

if not _MCP2:
    # No `version` argument on 1.x -- 1.0.1 and 1.0.2 passed one and so failed
    # at import on every 1.x install. The low-level server reports this attribute
    # at initialize, and the mcp package's own version while it is None.
    mcp._mcp_server.version = __version__


def _retry_hint(resp: httpx.Response) -> str:
    # The API sends Retry-After on 429 (and RateLimit-Reset on every response).
    # Passing the number on lets the agent wait once instead of retrying blind.
    secs = resp.headers.get("retry-after") or resp.headers.get("ratelimit-reset")
    return f" Retry in {secs} seconds." if secs and secs.isdigit() else ""


async def _call(path: str, params: dict | None = None) -> Any:
    params = {k: v for k, v in (params or {}).items() if v is not None}
    headers = {"X-CEORater-Internal": INTERNAL_KEY} if INTERNAL_KEY else {}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(f"{API_BASE}{path}", params=params, headers=headers)
    except httpx.HTTPError as exc:
        return f"Could not reach the CEORater API: {exc}"

    if resp.status_code == 404:
        return "Not found in CEORater coverage."
    if resp.status_code == 429:
        return "Rate limited by the CEORater API." + _retry_hint(resp)
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


# Only reachable in HTTP mode. /mcp answers a bare GET with an error by design
# (it wants a JSON-RPC POST), so Cloud Run's startup probe and any uptime check
# get a route of their own, and a person who pastes the hostname into a browser
# gets a sentence instead of a 4xx.
@mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
async def _health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "version": __version__})


@mcp.custom_route("/", methods=["GET"], include_in_schema=False)
async def _root(_: Request) -> PlainTextResponse:
    return PlainTextResponse(
        f"CEORater MCP server {__version__}.\n"
        "MCP endpoint: POST /mcp (streamable HTTP). "
        f"Docs: {DOCS_URL}\n"
    )


def main():
    transport = os.environ.get("MCP_TRANSPORT", "stdio").strip().lower()
    if transport in ("http", "streamable-http"):
        import uvicorn

        port = int(os.environ.get("PORT", "8080"))
        # Stateless, so any instance answers any request and Cloud Run needs no
        # session affinity. Plain JSON replies rather than event streams: every
        # tool here answers in one shot, and JSON survives any proxy in between.
        if _MCP2:
            app = mcp.streamable_http_app(stateless_http=True, json_response=True, host="0.0.0.0")
        else:
            app = mcp.streamable_http_app()  # settings were fixed at construction
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
