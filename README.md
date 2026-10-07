# Japan Market MCP — Cross-Shop Price Comparison for AI Agents

An **MCP server** that lets AI agents (Claude, Cursor, VS Code Copilot, ChatGPT) compare used-good prices across leading Japanese shops in a single tool call. Instead of scraping site by site, an agent queries one server and gets inter-store price gaps for the same product — perfect for **reseller arbitrage**, **price monitoring**, and **market research** on the Japanese second-hand market.

## How it works

The server wraps market-scraping and official-API actors (Rakuten Ichiba included) behind one MCP endpoint. Each tool returns price, brand, shop, condition and a link per item, with the shop-pair crossed so you see the price spread at a glance.

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
| `search_car_price_stats` | Used car price stats (min/max/avg/median JPY) | goo-net (by model keyword, e.g. N-BOX, Alphard) |
| `search_japan_prize_giveaways` | Current JP prize giveaways with deadlines (懸賞/プレゼント) | kenshou.club + cp.meikan.org |
| `get_japan_prize_giveaway_stats` | Aggregate giveaway stats (counts, active, winners) | kenshou.club + cp.meikan.org |
| `search_rakuten_items` | New retail products (official API) | Rakuten Ichiba 楽天市場 (keyword, price range, sort) |
| `get_rakuten_ranking` | Best-seller ranking (official API) | Rakuten Ichiba 楽天市場 (overall or by genre) |
| `get_maff_market_report` | Fresh produce wholesale market report (official MAFF open data) | Japan central markets (旬別, JPY/100kg, YoY%) |
| `search_maff_price_trend` | Fresh produce wholesale price trend (official MAFF open data) | Multi-market, multi-period comparison |
| `get_maff_top_movers` | Fresh produce YoY price movers (official MAFF open data) | Japan central markets (supply-shock signal) |
| `get_maff_markets` | List available MAFF wholesale markets | no charge |

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
      "url": "https://fruitful-quintessence--japan-market-mcp.apify.actor/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_APIFY_TOKEN"
      }
    }
  }
}
```

- **URL**: `<your-username>--japan-market-mcp.apify.actor/mcp`
- **Auth**: Apify API token in the `Authorization: Bearer` header (Apify Console → Settings → Integrations)

> **URL note:** use a hyphen in the username (`fruitful-quintessence`), not an underscore — an underscore hostname will not resolve.

## Discovery & registry

- **Agent install guide:** see [`llms-install.md`](llms-install.md) — grounded guidance for AI agents (Cline, Claude Code, Cursor) that set up this server for a user.
- **MCP discovery manifest:** `.well-known/mcp.json` advertises the endpoint, auth, tool list, and pricing in the standard MCP Directory discovery format.
- **Cline MCP Marketplace:** submitted for review at [`cline/mcp-marketplace`](https://github.com/cline/mcp-marketplace/issues) — once approved it becomes one-click installable from Cline's marketplace.
- **Apify Store:** deployed as the public actor [`fruitful_quintessence/japan-market-mcp`](https://apify.com/fruitful_quintessence/japan-market-mcp) (pay-per-event).

## Related Apify Actors

This MCP server connects to **86+ Apify Actors** in the Kensho ecosystem for real-time data. Key related actors include:

### Marketplace & Price Comparison
- [fruitful_quintessence/japan-market-mcp](https://apify.com/fruitful_quintessence/japan-market-mcp) — Core MCP server
- [fruitful_quintessence/japan-anime-figure-price-data](https://apify.com/fruitful_quintessence/japan-anime-figure-price-data) — Anime figure prices
- [fruitful_quintessence/japan-figure-plamo-resale-price-stats](https://apify.com/fruitful_quintessence/japan-figure-plamo-resale-price-stats) — Figure/plamo resale stats
- [fruitful_quintessence/japan-minimum-wage-mcp](https://apify.com/fruitful_quintessence/japan-minimum-wage-mcp) — Minimum wage data
- [fruitful_quintessence/japan-food-delivery-mcp](https://apify.com/fruitful_quintessence/japan-food-delivery-mcp) — Food delivery prices

### Retail & E-commerce
- [fruitful_quintessence/rakuten-japan-mcp](https://apify.com/fruitful_quintessence/rakuten-japan-mcp) — Rakuten Ichiba data
- [fruitful_quintessence/japan-kakaku-price-search](https://apify.com/fruitful_quintessence/japan-kakaku-price-search) — Kakaku.com price comparison
- [fruitful_quintessence/amazon-japan-bestsellers](https://apify.com/fruitful_quintessence/amazon-japan-bestsellers) — Amazon JP bestsellers
- [fruitful_quintessence/yahoo-shopping-japan](https://apify.com/fruitful_quintessence/yahoo-shopping-japan) — Yahoo! Shopping
- [fruitful_quintessence/mercari-japan-price](https://apify.com/fruitful_quintessence/mercari-japan-price) — Mercari pricing

### Used Goods & Auctions
- [fruitful_quintessence/yahoo-auctions-japan-scraper](https://apify.com/fruitful_quintessence/yahoo-auctions-japan-scraper) — Yahoo! Auctions
- [fruitful_quintessence/mercari-japan-search-scraper](https://apify.com/fruitful_quintessence/mercari-japan-search-scraper) — Mercari search
- [fruitful_quintessence/surugaya-japan-hobby-prices](https://apify.com/fruitful_quintessence/surugaya-japan-hobby-prices) — Suruga-ya hobby
- [fruitful_quintessence/mandarake-auction-scraper](https://apify.com/fruitful_quintessence/mandarake-auction-scraper) — Mandarake auction
- [fruitful_quintessence/off-mall-japan-scraper](https://apify.com/fruitful_quintessence/off-mall-japan-scraper) — OffMall (Hard Off)

### Local Business & Services
- [fruitful_quintessence/google-maps-japan-reviews](https://apify.com/fruitful_quintessence/google-maps-japan-reviews) — Google Maps reviews
- [fruitful_quintessence/tabelog-japan-restaurants](https://apify.com/fruitful_quintessence/tabelog-japan-restaurants) — Tabelog restaurants
- [fruitful_quintessence/hotpepper-beauty-salons](https://apify.com/fruitful_quintessence/hotpepper-beauty-salons) — Beauty salons
- [fruitful_quintessence/japan-post-office-locations](https://apify.com/fruitful_quintessence/japan-post-office-locations) — Post offices

### Government & Public Data
- [fruitful_quintessence/japan-maff-markets](https://apify.com/fruitful_quintessence/japan-maff-markets) — MAFF wholesale markets
- [fruitful_quintessence/japan-maff-price-trend](https://apify.com/fruitful_quintessence/japan-maff-price-trend) — MAFF price trends
- [fruitful_quintessence/japan-maff-top-movers](https://apify.com/fruitful_quintessence/japan-maff-top-movers) — MAFF top movers
- [fruitful_quintessence/japan-maff-market-report](https://apify.com/fruitful_quintessence/japan-maff-market-report) — MAFF market reports

### Specialized Collections
- [fruitful_quintessence/japan-anime-figure-demand-features](https://apify.com/fruitful_quintessence/japan-anime-figure-demand-features) — Anime figure demand
- [fruitful_quintessence/japan-vintage-clothing-prices](https://apify.com/fruitful_quintessence/japan-vintage-clothing-prices) — Vintage clothing
- [fruitful_quintessence/japan-used-book-prices](https://apify.com/fruitful_quintessence/japan-used-book-prices) — Used books
- [fruitful_quintessence/japan-record-store-prices](https://apify.com/fruitful_quintessence/japan-record-store-prices) — Record stores
- [fruitful_quintessence/japan-toy-collector-prices](https://apify.com/fruitful_quintessence/japan-toy-collector-prices) — Toy collector

## MCP Connection Examples
### 6. External run example (fallback)

```bash
# If GitHub API returns 403, use curl + git clone
curl -s https://raw.githubusercontent.com/atushi1841/japan-market-mcp/main/README.md > README.patch
# edit README.patch as needed
git clone https://github.com/atushi1841/japan-market-mcp.git
cd japan-market-mcp
cp ../README.patch README.md
git add README.md
git commit -m "update README via external run"
git push
```

### 1. Standard I/O (stdio) — Claude Desktop, Cursor, etc.

In your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "japan-market-mcp": {
      "command": "python",
      "args": ["-m", "src.main"]
    }
  }
}
```

### 2. HTTP Server Mode

```bash
# Install dependencies
pip install -r requirements.txt

# Run as HTTP server on port 3000
APIFY_TOKEN=your_token python -m src.main --http --port 3000

# Test the endpoint
curl http://localhost:3000/mcp/tools | jq .
```

### 3. Direct Python Import

```python
from src.main import mcp
# FastMCP instance can be embedded directly
```

### 4. n8n / Apify Workflow (via HTTP)

Use Apify's **Webhook** node to POST JSON-RPC to `POST /mcp` endpoint.

### 5. Docker Deployment

```bash
docker build -t japan-market-mcp .
docker run -p 3000:3000 -e APIFY_TOKEN=your_token japan-market-mcp
```

```
"Compare used prices for Sony a7 III between Kitamura and Fujiya"
→ search_camera_market(keyword="SONY α7 III")

"What's the inter-store price gap for a Rolex Submariner?"
→ search_watch_market(keyword="ROLEX Submariner")

"What's the market price for a Hermes Birkin 25?"
→ search_luxury_market(keyword="Hermes Birkin 25")

"What's a used Fender Stratocaster going for?"
→ search_instrument_market(keyword="Fender Stratocaster")

"Show this 旬's wholesale market report for Tokyo (Toyosu) fresh vegetables"
→ get_maff_market_report(market="toyosu")

"Which fresh produce items have spiked in price vs last year at Osaka?"
→ get_maff_top_movers(market="oosakaho")

"Track the price of daikon (だいこん) across Tokyo and Osaka this month"
→ search_maff_price_trend(item="だいこん", markets=["toyosu","oosakaho"])
```

## Use cases

- **Reseller arbitrage** — spot the same product priced differently across shops
- **Market research** — track used prices for cameras, watches, luxury goods, instruments, cars
- **Export sourcing** — goo-net JDM inventory and goo-net price checks for exporters
- **Collector price checks** — condition-ranked physical used items from OffMall

## Data sources


- Each actor collects **factual data only** (product name, price, brand, condition, inventory, URL). No photos or descriptions are harvested.
- All target sites allow crawling via their `robots.txt`.
- **MAFF 青果物卸売市場調査（旬別・市場別）** is served from the official 農林水産省 open-data CSV — no scraping, direct download. Published under the **Government Standard Terms of Use v2.0** (政府標準利用規約2.0): commercial use allowed with attribution. Price is JPY per 100kg. Data updates are published by MAFF each 旬 (10-day period).

## Local development

```bash
pip install -r requirements.txt
APIFY_TOKEN=apify_api_xxx python -m src.main
# Streamable HTTP endpoint at http://localhost:3000/mcp
```

## License

MIT
