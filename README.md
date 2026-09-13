# CEORater MCP Server

CEO performance data for AI agents, over the Model Context Protocol.

How the stock did over each CEO's tenure, what the S&P 500 did over that same
window, how long they have been in the job, and what they were paid — for 500+
US public companies.

**Free. No account, no API key, no signup.**

---

## Connect from the web

The server runs at one public URL. Paste it wherever your client asks for a
remote MCP server — no login, nothing to install:

```
https://mcp.ceorater.com/mcp
```

| Client | Where |
|---|---|
| Claude.ai | Settings → Connectors → Add custom connector |
| ChatGPT | Settings → Connectors → Create (developer mode) |
| Claude Code | `claude mcp add --transport http ceorater https://mcp.ceorater.com/mcp` |
| Cursor | `"ceorater": { "url": "https://mcp.ceorater.com/mcp" }` in `mcp.json` |

Streamable HTTP, stateless. `GET /health` answers 200 when it is up.

---

## Install locally instead

Needs Python 3.10 or newer.

### Windows

```
pip install ceorater-mcp
```

### macOS

```
brew install pipx
pipx install ceorater-mcp
```

Homebrew's Python refuses `pip install` into the system environment, so plain
`pip install` fails there with *externally-managed-environment*.

### Linux

```
sudo apt install pipx      # Debian, Ubuntu
sudo dnf install pipx      # Fedora, RHEL
pipx install ceorater-mcp
```

---

## Connect it to a client

MCP is an open standard — Claude, ChatGPT, Cursor, VS Code and other clients all
speak it. Claude Desktop, Cursor and VS Code take a server config file in this
form; other clients add servers their own way.

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ceorater": {
      "command": "ceorater-mcp"
    }
  }
}
```

That file lives at:

| | |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |

Restart Claude Desktop. No `env` block and no key — that is the whole config.

---

## Tools

| Tool | What it does |
|---|---|
| `ceo_lookup` | One company by ticker. Always returns an array. |
| `ceo_list` | Every CEO, or filter by `sector`, `industry`, `founder` |
| `ceo_search` | Loose substring match across company, ticker, CEO, sector, industry |
| `ceo_sectors` | The 11 GICS sectors and their company counts |
| `ceo_industries` | GICS sub-industries, optionally within one sector |
| `ceo_meta` | Row count, field list, data freshness |

Ask things like *"Which founder-led tech CEOs beat the S&P 500 over their
tenure?"* — the agent can call `ceo_list` with `sector="Information Technology"`
and `founder=true` and do the comparison itself.

---

## The fields

Exactly the ten www.ceorater.com displays.

| Field | Meaning |
|---|---|
| `ticker` | Exchange ticker |
| `company` | Registrant name as filed |
| `ceo` | Chief executive |
| `founder` | Whether this CEO founded the company |
| `sector` | GICS sector |
| `industry` | GICS sub-industry |
| `tenure_years` | Years in the role |
| `total_return_pct` | Total stock return across the tenure, as a percentage |
| `spy_return_pct` | The S&P 500 over that same period |
| `compensation_musd` | Reported compensation, in millions of USD |

Returns are already percentages: `545800` means +545,800%. Nothing to convert.

**Sectors and industries are S&P's own GICS values**, matched company by company
on SEC CIK rather than ticker, because tickers get reassigned and CIKs do not.
Eleven sectors, 128 sub-industries.

**Co-CEOs get a record each.** Oracle, KKR, Globe Life, Lululemon and Netflix
each return two people with their own start dates and returns, which is why
`ceo_lookup` always returns a list.

---

## Upgrading from 1.0.x

1.0.1 and 1.0.2 fail at import on every `mcp` 1.x install (`unexpected keyword
argument 'version'`). 1.1.0 runs on 1.27.1 and later, and on 2.x.

## Upgrading from 0.x

Version 0.x required a `CEORATER_API_KEY` and called a paid API that no longer
exists — every tool in it fails. Version 1.0 needs no key and is not
configurable; remove any `CEORATER_API_KEY` from your MCP config.

The scores are gone. CEORaterScore, AlphaScore, CompScore and RevenueCAGRScore
have been retired from the product, along with Avg Annual TSR, which was
computed as total return divided by tenure rather than compounded and
overstated every multi-year record. What remains is reported figures only.

---

## Running your own remote server

```
MCP_TRANSPORT=http PORT=8080 ceorater-mcp
```

Serves streamable HTTP, stateless, so it sits behind Cloud Run or similar
without session affinity. No per-user credentials to manage. The `Dockerfile`
and `.github/workflows/deploy.yml` here are what build and deploy
mcp.ceorater.com.

The API rate-limits by IP, and a shared server makes every user's calls from
one address. mcp.ceorater.com carries a key the API recognises; a server you
run yourself shares the ordinary per-IP limit across everyone using it.

---

## The underlying API

The server is a thin client over a public HTTP API you can call directly:

```
curl -s https://api.ceorater.com/api/v1/ceo/NVDA
```

Documented at https://www.ceorater.com/api-docs.html
Rate limit 100 requests per 15 minutes per IP.

CEORater publishes reported figures and makes no investment recommendations.

---

## Licence

MIT. The server is yours to use, fork and embed.

The CEO data it retrieves is free to use, including commercially; attribution to
CEORater is appreciated. See https://www.ceorater.com/terms.html
