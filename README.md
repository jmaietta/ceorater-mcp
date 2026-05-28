# CEORater MCP Server

Model Context Protocol server for CEORater.com — CEO performance analytics for AI agents.

Requires a CEORater API subscription ($99/month). [Subscribe and get your API key](https://www.ceorater.com/api-docs.html).

## Install

```bash
pip install ceorater-mcp
```

## Configure

Set your API key:
```bash
export CEORATER_API_KEY=zpka_your_key_here
```

## Use with Claude Desktop

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ceorater": {
      "command": "ceorater-mcp",
      "env": {
        "CEORATER_API_KEY": "zpka_your_key_here"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `ceo_lookup` | Get CEO performance data for a specific ticker |
| `ceo_search` | Search by company name, ticker, CEO name, sector, or industry |
| `ceo_list` | Paginated list of all CEOs with scores |
| `ceo_meta` | Dataset metadata (count, freshness, version) |

---

## API Reference

### Base URL

```
https://api.ceorater.com
```

### Authentication

All requests require your API key in the `Authorization` header:

```
Authorization: Bearer zpka_your_api_key_here
```

Your API key starts with `zpka_` and is available in the [Developer Portal](https://ceorater-api-main-7ef1acf.zuplo.site) after subscribing.

---

### GET `/v1/meta`

Returns information about the current dataset.

**Response:**
```json
{
  "count": 517,
  "last_loaded": "2026-01-17T08:00:00.000Z",
  "base_url": "https://api.ceorater.com",
  "docs_url": "https://www.ceorater.com/api-docs.html",
  "api_version": "1.1.0",
  "request_id": "2f9c2870f486d294"
}
```

---

### GET `/v1/ceos`

Retrieve a paginated list of CEOs with performance ratings.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Number of results (max: 2000) |
| `offset` | integer | 0 | Starting position for pagination |
| `format` | string | ui | Response format: `ui` or `raw` |

**Example Request:**
```bash
curl -H "Authorization: Bearer zpka_your_api_key_here" "https://api.ceorater.com/v1/ceos?limit=20&offset=0&format=ui"
```

**Response (UI format):**
```json
{
  "items": [
    {
      "Company Name": "Apple Inc.",
      "Ticker": "AAPL",
      "Sector": "Technology",
      "Industry": "Computer Manufacturing",
      "CEO Name": "Tim Cook",
      "Founder (Y/N)": "N",
      "CEORaterScore": 87,
      "AlphaScore": 94,
      "RevenueCAGRScore": 72,
      "Revenue CAGR (Adj.)": "4.2%",
      "CompScore": "C",
      "TSR During Tenure": "2,223%",
      "Avg. Annual TSR": "155%",
      "TSR vs. SPY": "1,564%",
      "Avg Annual TSR vs. SPY": "109%",
      "Compensation ($ millions)": "$74.6M",
      "CEO Compensation Cost / 1% Avg TSR": "$0.482M",
      "Tenure (years)": "14.4 years"
    }
  ],
  "total": 517,
  "offset": 0,
  "limit": 20
}
```

---

### GET `/v1/ceo/:ticker`

Retrieve detailed CEO performance data for a specific company ticker symbol.

**Path Parameters:**
- `ticker` (string) — Stock ticker symbol (case-insensitive)

**Query Parameters:**
- `format` (string) — Response format: `ui` or `raw` (default: ui)

**Example Request:**
```bash
curl -H "Authorization: Bearer zpka_your_api_key_here" "https://api.ceorater.com/v1/ceo/AAPL?format=raw"
```

**Response (raw format):**
```json
{
  "companyName": "Apple Inc.",
  "ticker": "AAPL",
  "sector": "Technology",
  "industry": "Computer Manufacturing",
  "ceo": "Tim Cook",
  "founderCEO": false,
  "ceoraterScore": 87,
  "alphaScore": 93.5,
  "revenueCagrScore": 72,
  "revenueCagr": 0.042,
  "compScore": "C",
  "compensationMM": 74.6,
  "tsrMultiple": 22.23,
  "tenureYears": 14.4,
  "avgAnnualTsrRatio": 1.55,
  "compPer1PctTsrMM": 0.482,
  "tsrVsSpyRatio": 15.64,
  "avgAnnualVsSpyRatio": 1.09
}
```

---

### GET `/v1/search`

Search CEOs by company name, ticker, sector, industry, or CEO name.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Search query (required) |
| `format` | string | Response format: `ui` or `raw` (default: ui) |

**Example Request:**
```bash
curl -H "Authorization: Bearer zpka_your_api_key_here" "https://api.ceorater.com/v1/search?q=technology&format=raw"
```

**Response:**
```json
{
  "q": "technology",
  "count": 45,
  "items": [
    { "companyName": "Apple Inc.", "ticker": "AAPL", "...": "..." },
    { "companyName": "Microsoft Corp.", "ticker": "MSFT", "...": "..." }
  ]
}
```

---

## Coverage

CEORater covers **517 CEOs** across the S&P 500 constituent companies.

## Data Formats

| Format | Description |
|--------|-------------|
| `format=ui` (default) | Human-readable labels and formatted values: "155%", "$74.6M", "14.4 years" |
| `format=raw` | Machine-readable camelCase keys and numeric values: 1.55, 74.6, 14.4 |

## Field Reference

| UI Label | Raw Key | Description | Example (UI / Raw) |
|----------|---------|-------------|---------------------|
| CEO Name | `ceo` | Current CEO full name | "Tim Cook" |
| Founder (Y/N) | `founderCEO` | Whether the CEO is a company founder | "Y" or "N" / true or false |
| Company Name | `companyName` | Full company name | "Apple Inc." |
| Ticker | `ticker` | Stock symbol | "AAPL" |
| CEORaterScore | `ceoraterScore` | Proprietary overall CEO rating (0-100) | 87 |
| AlphaScore | `alphaScore` | Performance vs. market (0-100) | 94 |
| RevenueCAGRScore | `revenueCagrScore` | Revenue growth rating (0-100) | 72 |
| Revenue CAGR (Adj.) | `revenueCagr` | Tenure-adjusted Revenue CAGR | "4.2%" / 0.042 |
| CompScore | `compScore` | Compensation efficiency grade (A-F) | "C" |
| TSR During Tenure | `tsrMultiple` | Total Shareholder Return | "2,223%" / 22.23 |
| Avg. Annual TSR | `avgAnnualTsrRatio` | Average Annual TSR | "155%" / 1.55 |
| TSR vs. SPY | `tsrVsSpyRatio` | TSR vs. S&P 500 | "1,564%" / 15.64 |
| Avg Annual TSR vs. SPY | `avgAnnualVsSpyRatio` | Avg Annual TSR vs. S&P 500 | "109%" / 1.09 |
| Compensation ($ millions) | `compensationMM` | Total CEO Compensation | "$74.6M" / 74.6 |
| CEO Compensation / 1% Avg TSR | `compPer1PctTsrMM` | Compensation cost per percentage point TSR | "$0.482M" / 0.482 |
| Tenure (years) | `tenureYears` | CEO Tenure | "14.4 years" / 14.4 |

## Code Examples

### Python
```python
import requests

API_KEY = 'zpka_your_api_key_here'
BASE_URL = 'https://api.ceorater.com'

def list_ceos(limit=50, offset=0):
    response = requests.get(
        f'{BASE_URL}/v1/ceos',
        headers={'Authorization': f'Bearer {API_KEY}'},
        params={'limit': limit, 'offset': offset, 'format': 'raw'}
    )
    return response.json()

# Usage
data = list_ceos(limit=20)
print(f"Total CEOs: {data['total']}")
```

### JavaScript
```javascript
const API_KEY = 'zpka_your_api_key_here';
const BASE_URL = 'https://api.ceorater.com';

async function searchCompanies(query) {
  const response = await fetch(
    `${BASE_URL}/v1/search?q=${encodeURIComponent(query)}`,
    {
      headers: {
        'Authorization': `Bearer ${API_KEY}`
      }
    }
  );
  return response.json();
}

// Usage
const results = await searchCompanies('apple');
console.log(results.items);
```

### cURL
```bash
# Search for CEOs
curl -H "Authorization: Bearer zpka_your_api_key_here" "https://api.ceorater.com/v1/search?q=technology"

# Get a specific CEO
curl -H "Authorization: Bearer zpka_your_api_key_here" "https://api.ceorater.com/v1/ceo/AAPL?format=raw"

# List CEOs (paginated)
curl -H "Authorization: Bearer zpka_your_api_key_here" "https://api.ceorater.com/v1/ceos?limit=50&offset=0&format=raw"

# Get metadata
curl -H "Authorization: Bearer zpka_your_api_key_here" "https://api.ceorater.com/v1/meta"
```

## CLI

Query CEORater data directly from your terminal:

```bash
pip install ceorater
ceorater configure                # paste your API key
ceorater lookup AAPL              # CEO card with scores and metrics
ceorater search "technology"      # Search by company, CEO, sector, or industry
ceorater list --limit 50          # Paginated list of all CEOs
ceorater meta                     # Dataset stats and freshness
ceorater lookup NVDA --json       # Raw JSON for scripts and agents
```

Source: [github.com/jmaietta/ceorater-cli](https://github.com/jmaietta/ceorater-cli)

## Error Responses

| Status | Code | Description |
|--------|------|-------------|
| 401 | Unauthorized | Missing or invalid API key |
| 404 | Not Found | Ticker not in CEORater coverage |
| 400 | Bad Request | Missing required parameter (e.g., `q` for search) |
| 429 | Too Many Requests | Rate limit exceeded |

## Additional Information

- **Data Refresh:** Dataset updates daily (weekdays, after market close)
- **Versioning:** Breaking changes are introduced on new major versions with advance notice
- **Observability:** Every response includes an `X-Request-Id` header for support troubleshooting
- **CORS:** Enabled for all origins

## Trust & Governance

- [Methodology](https://www.ceorater.com/methodology.html)
- [Privacy Policy](https://www.ceorater.com/privacy.html)
- [Terms of Service](https://www.ceorater.com/terms.html)
- [Support](https://www.ceorater.com/support.html)

## Support

- **Email:** support@ceorater.com
- **Web:** [ceorater.com/support.html](https://www.ceorater.com/support.html)
- **Developer Portal:** [ceorater-api-main-7ef1acf.zuplo.site](https://ceorater-api-main-7ef1acf.zuplo.site)

## License

MIT
