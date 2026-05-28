# CEORater MCP Server

Model Context Protocol server for CEORater.com — CEO performance analytics for AI agents.

Requires a CEORater API subscription ($99/month). Get your key at [ceorater.com](https://www.ceorater.com).

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
| `ceo_search` | Search by company, CEO name, sector, or industry |
| `ceo_list` | Paginated list of all CEOs with scores |
| `ceo_meta` | Dataset metadata (count, freshness, version) |

## License

MIT
