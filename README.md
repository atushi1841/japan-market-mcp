# Japan Market MCP — Cross-Shop Price Comparison for AI Agents

An **MCP server** that lets AI agents (Claude, Cursor, VS Code Copilot, ChatGPT) compare used-good prices across leading Japanese shops in a single tool call. Instead of scraping site by site, an agent queries one server and gets inter-store price gaps for the same product — perfect for **reseller arbitrage**, **price monitoring**, and **market research** on the Japanese second-hand market.

## How it works

The server wraps 7 market-scraping actors behind one MCP endpoint. Each tool returns price, brand, shop, condition and a link per item, with the shop-pair crossed so you see the price spread at a glance.

## Available tools

| Tool | Market | Shop pair |
|---|---|---|
| `search_camera_market` | Used cameras & lenses | Kitamura + Fujiya Camera |
| `search_watch_market` | Luxury watches | Jackroad + Kitamura used watches |
| `search_luxury_market` | Used luxury brands | Komehyo + Jackroad |
| `search_instrument_market` | Used instruments | Digimart + Ishibashi U-BOX |
| `search_offmall_market` | General used goods | OffMall (Hard Off official, 800+ stores) |
| `search_kakaku_prices` | New price comparison | Kakaku.com (aggregated, thousands of shops) |
| `search_car_market` | Used cars | goo-net (nationwide, by body type) |

Each tool takes a keyword (e.g. `SONY α7`, `ROLEX`, `Hermes`, `Fender`) and returns results from the crossed shops. Leaving the keyword empty scans the full category.

## Pricing

Pay per event — **$0.001 per search** + actor start fee. Runs finish in seconds, so a full keyword lookup typically costs well under $0.01.

## Connect as an MCP server

Run it from the Apify Store (Run button), then point your MCP client at the endpoint. It stays in standby mode.

**MCP client config (Claude Desktop / Cursor / VS Code):**

```json
{
  "mcpServers": {
    "japan-market-mcp": {
      "url": "https://fruitful_quintessence--japan-market-mcp.apify.actor/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_APIFY_TOKEN"
      }
    }
  }
}
```

- **URL**: `<your-username>--japan-market-mcp.apify.actor/mcp`
- **Auth**: Apify API token in the `Authorization: Bearer` header (Apify Console → Settings → Integrations)

## Example agent prompts

```
"Compare used prices for Sony a7 III between Kitamura and Fujiya"
→ search_camera_market(keyword="SONY α7 III")

"What's the inter-store price gap for a Rolex Submariner?"
→ search_watch_market(keyword="ROLEX Submariner")

"What's the market price for a Hermes Birkin 25?"
→ search_luxury_market(keyword="Hermes Birkin 25")

"What's a used Fender Stratocaster going for?"
→ search_instrument_market(keyword="Fender Stratocaster")
```

## Use cases

- **Reseller arbitrage** — spot the same product priced differently across shops
- **Market research** — track used prices for cameras, watches, luxury goods, instruments, cars
- **Export sourcing** — goo-net JDM inventory and goo-net price checks for exporters
- **Collector price checks** — condition-ranked physical used items from OffMall

## Data sources

- Each actor collects **factual data only** (product name, price, brand, condition, inventory, URL). No photos or descriptions are harvested.
- All target sites allow crawling via their `robots.txt`.

## Local development

```bash
pip install -r requirements.txt
APIFY_TOKEN=apify_api_xxx python -m src.main
# Streamable HTTP endpoint at http://localhost:3000/mcp
```

## License

MIT
