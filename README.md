# Japan Market MCP — 日本の複数店舗横断比較 MCPサーバー

**AIエージェントから日本の4市場（中古カメラ・時計・ブランド品・楽器）の店舗間価格比較ができるMCPサーバー。**

4つの横断比較アクター（Japan Used Camera / Watch / Luxury Brand / Instrument Market）を1つのMCPサーバーに統合。同一モデルの店舗間価格差（転売利ざや・相場調査）をAIエージェントから直接検索できます。

## 提供ツール

| ツール | 市場 | 対象店舗 |
|---|---|---|
| `search_camera_market` | 中古カメラ | キタムラ + フジヤカメラ |
| `search_watch_market` | 中古時計 | ジャックロード + キタムラ中古時計 |
| `search_luxury_market` | 中古ブランド品 | コメ兵（バッグ/財布/ジュエリー/時計）+ ジャックロード |
| `search_instrument_market` | 中古楽器 | デジマート + イシバシ楽器U-BOX |
| `search_offmall_market` | 中古総合 | オフモール（ハードオフ公式800店舗） |
| `search_kakaku_prices` | 価格.com | 日本全国オンライン店舗の最安価格 |
| `search_car_market` | 中古車 | goo-net（全国・車体タイプ別） |

各ツールはキーワード（例: "SONY α7", "ROLEX", "エルメス", "Fender"）を入力すると、対象店舗から横断的に商品を収集し、価格・ブランド・状態・出典店舗を返します。

## 価格

Pay per event — 各検索 **$0.001/search** + Actor実行費。

## 接続方法

### Apify上のMCPサーバーとして

Store の Run ボタンから起動し、MCPエンドポイント（Streamable HTTP）を MCPクライアント（Claude Desktop, Cursor, VS Code等）に接続します。

**MCPクライアント設定（Claude Desktop / Cursor等）:**

```json
{
  "mcpServers": {
    "japan-market-mcp": {
      "url": "https://YOUR-USERNAME--japan-market-mcp.apify.actor/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_APIFY_TOKEN"
      }
    }
  }
}
```

- **URL形式**: `<your-username>--<actor-name>.apify.actor/mcp`（例: `https://fruitful_quintessence--japan-market-mcp.apify.actor/mcp`）
- **認証**: Apify APIトークンを `Authorization: Bearer` ヘッダーで付与（Apify Console → Settings → Integrations から取得）
- **起動**: StoreのRunボタンで起動後、Standbyモードで常駐し `/mcp` エンドポイントが公開されます

### ローカル開発

```bash
pip install -r requirements.txt
APIFY_TOKEN=apify_api_xxx python -m src.main
# http://localhost:3000/mcp でStreamable HTTPエンドポイントが起動
```

## ツールの使用例

```
"SONY α7 IIIの中古価格をキタムラとフジヤで比較して"
→ search_camera_market(keyword="SONY α7 III")

"ROLEXサブマリーナーの店舗間価格差を教えて"
→ search_watch_market(keyword="ROLEX サブマリーナー")

"エルメスのバーキン25の相場は？"
→ search_luxury_market(keyword="エルメス バーキン 25")

"Fenderストラトキャスターの中古相場"
→ search_instrument_market(keyword="Fender Stratocaster")
```

## データソース

- 各アクターは **事実データのみ**（商品名・価格・ブランド・状態・在庫・登録日）を収集。写真・説明文は取得しません
- 対象サイトのrobots.txtは全てクロール許可
- 詳細は各MarketアクターのREADME参照:
  - [japan-used-camera-market-scraper](https://apify.com/fruitful_quintessence/japan-used-camera-market-scraper)
  - [japan-watch-market-scraper](https://apify.com/fruitful_quintessence/japan-watch-market-scraper)
  - [japan-luxury-brand-market-scraper](https://apify.com/fruitful_quintessence/japan-luxury-brand-market-scraper)
  - [japan-used-instrument-market-scraper](https://apify.com/fruitful_quintessence/japan-used-instrument-market-scraper)

## License

MIT
