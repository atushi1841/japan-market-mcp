# Installing Japan Market MCP

> Guidance for AI agents (Cline, Claude Code, Cursor, VS Code Copilot, ChatGPT) setting up this MCP server on the user's behalf. This file is additive to the main `README.md`.

## What this server does

`japan-market-mcp` is a **remote (HTTP / Streamable-HTTP) MCP server** that compares real prices across leading Japanese marketplaces — used cameras & lenses, luxury watches, used brand goods, used instruments, used cars, plus Kakaku.com, the official Rakuten Ichiba API, and MAFF fresh-produce wholesale market data — in single tool calls.

It is **not a local Node/Python package deps install**. It is hosted remotely on the Apify platform and reached over HTTPS. A user only needs to add the MCP client configuration below; there is no cloning or dependency setup.

## Prerequisites

- An **Apify account** with an **API token** — get it from Apify Console → Settings → **Integrations** → "API token". This is the only credential the server needs (sent as `Authorization: Bearer`).
- No local install, no build, no API keys of its own.

## MCP client config

Add this to the MCP settings of the user's client (Cline: `cline_mcp_settings.json`; Claude Desktop: `claude_desktop_config.json`; Cursor: `~/.cursor/mcp.json`; VS Code: `.vscode/mcp.json`):

```json
{
  "mcpServers": {
    "japan-market-mcp": {
      "type": "http",
      "url": "https://fruitful-quintessence--japan-market-mcp.apify.actor/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_APIFY_API_TOKEN"
      }
    }
  }
}
```

> **URL note:** the actor username in the hostname uses a **hyphen** (`fruitful-quintessence`), not an underscore. An underscore in the hostname will not resolve.

Replace `YOUR_APIFY_API_TOKEN` with the user's real Apify token. Do **not** hardcode or commit a real token.

## Verification after install

1. Ask the client to list tools — you should see 16 tools including `search_camera_market`, `search_car_price_stats`, `search_rakuten_items`, `get_maff_market_report`, etc.
2. Try a no-cost call: `get_maff_markets` returns the list of available wholesale markets.
3. A paid call, e.g. `search_camera_market(keyword="SONY α7 III")`, runs in seconds and costs ≈$0.001.

## Pricing

Pay-per-event: **$0.001 per search** + a tiny actor-start fee. A full keyword lookup typically costs well under $0.01.

## Data & license

All data is factual (price / brand / condition / inventory / URL). The MAFF datasets come from official 農林水産省 open-data CSVs under the Government Standard Terms of Use v2.0. Server code is MIT licensed.
