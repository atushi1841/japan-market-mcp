"""
MCPサーバーファクトリー — Japan Market MCP (Cross-Shop Comparison).

4つの横断比較アクター（カメラ/時計/ブランド品/楽器）を1つのMCPサーバーにまとめ、
AIエージェントから日本の複数店舗の中古品価格を横断比較できるようにします。

get_server() がコントラクト関数。main.py がこれを呼び出し、
uvicorn 経由で Apify Standby モードでホスティングします。

各ツールは Apify API を呼び出して Actor を実行し、
結果を整形して AI エージェントに返します。
課金は pay_per_event.json に定義された PPE イベント経由で行われます。
"""

from __future__ import annotations

import json
import os
from typing import Any

import asyncio

import httpx

from fastmcp import FastMCP

# Apify ランタイムかローカル実行かを自動判定
# 注意: main.py と判定条件を揃えること（APIFY_CONTAINER_PORT のみで本物を使う）
if os.environ.get("APIFY_CONTAINER_PORT"):
    from apify import Actor
else:
    from src.apify_shim import Actor  # type: ignore[assignment]

# Actor ID 定数（横断比較アクター）
CAMERA_ACTOR_ID = "mQaZFo6up4YZKepC3"          # japan-used-camera-market-scraper
WATCH_ACTOR_ID = "gMqdrS2evpcybSZc2"           # japan-watch-market-scraper
LUXURY_ACTOR_ID = "b0vuqa3ESvy2mOwFB"          # japan-luxury-brand-market-scraper
INSTRUMENT_ACTOR_ID = "yN1R26HrV6C2MBKas"      # japan-used-instrument-market-scraper
OFFMALL_ACTOR_ID = "Zh4kqcS4dYPWpFzBd"          # japan-offmall-market-scraper
KAKAKU_ACTOR_ID = "XOqsB7rCHYrb42kcY"            # japan-kakaku-price-search
GOO_NET_ACTOR_ID = "bgm5Gxn4BeBmoO7xD"           # goo-net-car-scraper

# Apify API エンドポイント
APIFY_API_BASE = "https://api.apify.com/v2"

# ツールアノテーション（MCPクライアントへのヒント）
_OPEN_WORLD_ANNOTATIONS = {
    "readOnlyHint": False,
    "destructiveHint": False,
    "idempotentHint": False,
    "openWorldHint": True,
}


def _get_apify_token() -> str:
    """APIFY_TOKEN を環境変数から取得。なければ raise。"""
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        raise RuntimeError("APIFY_TOKEN 環境変数が設定されていません")
    return token


async def _call_actor(
    actor_id: str,
    actor_input: dict[str, Any],
    actor_full_name: str,
) -> dict[str, Any]:
    """
    Apify API 経由で Actor を呼び出し、結果を取得する共通関数。

    1. Actor を実行 (POST /acts/{actorId}/runs)
    2. 実行完了を待機 (GET /actor-runs/{runId})
    3. データセットから結果を取得 (GET /datasets/{datasetId}/items)
    """
    token = _get_apify_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=120.0) as client:
        # Step 1: Actor を起動
        Actor.log.info(f"{actor_full_name} を起動中... input={json.dumps(actor_input, ensure_ascii=False)[:200]}")
        run_resp = await client.post(
            f"{APIFY_API_BASE}/acts/{actor_id}/runs",
            headers=headers,
            json=actor_input,
        )
        if run_resp.status_code != 201:
            error_detail = run_resp.text[:500]
            raise RuntimeError(
                f"Actor起動失敗 (HTTP {run_resp.status_code}): {error_detail}"
            )

        run_data = run_resp.json()["data"]
        run_id = run_data["id"]
        default_dataset_id = run_data.get("defaultDatasetId")
        Actor.log.info(f"{actor_full_name} 起動完了: runId={run_id}")

        # Step 2: 完了を待機（ポーリング）
        max_retries = 60  # 最大 5 分 (5s × 60)
        for attempt in range(max_retries):
            status_resp = await client.get(
                f"{APIFY_API_BASE}/actor-runs/{run_id}",
                headers=headers,
            )
            if status_resp.status_code != 200:
                raise RuntimeError(f"Run状態確認失敗: {status_resp.text[:300]}")

            status_data = status_resp.json()["data"]
            status = status_data["status"]

            if status == "SUCCEEDED":
                Actor.log.info(f"{actor_full_name} 実行成功 (attempt {attempt + 1})")
                break
            elif status == "FAILED":
                raise RuntimeError(
                    f"{actor_full_name} 実行失敗: {status_data.get('statusMessage', '不明なエラー')}"
                )
            elif status in ("ABORTED", "TIMED-OUT"):
                raise RuntimeError(f"{actor_full_name} 実行が中断/タイムアウトしました")

            await asyncio.sleep(5)
        else:
            raise RuntimeError(f"{actor_full_name} タイムアウト (5分経過)")

        # Step 3: 結果を取得
        if not default_dataset_id:
            return {
                "runId": run_id,
                "status": "SUCCEEDED",
                "note": "defaultDatasetId がありません。データはありません。",
            }

        items_resp = await client.get(
            f"{APIFY_API_BASE}/datasets/{default_dataset_id}/items",
            headers=headers,
            params={"format": "json", "limit": 50},
        )
        if items_resp.status_code != 200:
            raise RuntimeError(f"データセット取得失敗: {items_resp.text[:300]}")

        items = items_resp.json()

        return {
            "runId": run_id,
            "datasetId": default_dataset_id,
            "status": "SUCCEEDED",
            "itemCount": len(items),
            "items": items,
        }


# ──────────────────────────────────────────────
# 共通フォーマッター
# ──────────────────────────────────────────────

def _fmt_price(v) -> str:
    if isinstance(v, (int, float)):
        return f"¥{int(v):,}"
    return ""


def _fmt_market_results(result: dict[str, Any], market_name: str) -> str:
    """横断Market型アクターの共通整形（source/shop/price/title）。"""
    items = result.get("items", [])
    if not items:
        return f"検索結果はありませんでした。\nRun ID: {result.get('runId')}"

    lines = [f"**{market_name} 横断比較結果** ({len(items)}件)", ""]
    for i, item in enumerate(items[:20], 1):
        title = item.get("title") or item.get("name") or "（タイトルなし）"
        price = item.get("price") or item.get("current_price_jpy") or "?"
        source = item.get("source", "")
        shop = item.get("shop") or ""
        brand = item.get("brand") or ""
        condition = item.get("condition") or ""
        url = item.get("productUrl") or item.get("item_url") or item.get("url") or item.get("detailUrl") or ""

        price_str = _fmt_price(price) if isinstance(price, (int, float)) else f"{price}"
        shop_str = f" [{shop}]" if shop else ""
        brand_str = f" ブランド: {brand}" if brand else ""
        cond_str = f" 状態: {condition}" if condition else ""

        lines.append(f"{i}. **{title}**{shop_str}")
        lines.append(f"   価格: {price_str}{brand_str}{cond_str}")
        lines.append(f"   出典: {source}{' / ' + shop if shop else ''}")
        if url:
            lines.append(f"   [リンク]({url})")
        lines.append("")
    if len(items) > 20:
        lines.append(f"...他 {len(items) - 20} 件")

    lines.append(f"\nRun ID: `{result.get('runId')}`")
    lines.append(f"データセット: `{result.get('datasetId')}`")
    return "\n".join(lines)


def _format_camera_results(result: dict[str, Any]) -> str:
    return _fmt_market_results(result, "中古カメラ市場（キタムラ+フジヤ）")


def _format_watch_results(result: dict[str, Any]) -> str:
    return _fmt_market_results(result, "中古時計市場（ジャックロード+キタムラ）")


def _format_luxury_results(result: dict[str, Any]) -> str:
    return _fmt_market_results(result, "中古ブランド品市場（コメ兵+ジャックロード）")


def _format_instrument_results(result: dict[str, Any]) -> str:
    return _fmt_market_results(result, "中古楽器市場（デジマート+イシバシ）")


def _format_offmall_results(result: dict[str, Any]) -> str:
    """オフモール結果用フォーマッター（shopは常にOffMall）"""
    items = result.get("items", [])
    run_id = result.get("runId", "")
    dataset_id = result.get("datasetId", "")
    if not items:
        return f"**オフモール（ハードオフ公式800店舗）検索結果**: 0件\n\nRun ID: `{run_id}`\nデータセット: `{dataset_id}`"

    lines = [
        f"**オフモール（ハードオフ公式800店舗）検索結果** ({len(items)}件)",
        "",
    ]
    for i, it in enumerate(items, 1):
        title = it.get("title", "")
        brand = it.get("brand", "")
        price = it.get("price")
        rank = it.get("rank", "")
        url = it.get("productUrl", "")
        model = it.get("modelCode", "")
        price_str = f"¥{price:,}" if isinstance(price, int) else str(price or "?")
        rank_str = f" [ランク{rank}]" if rank else ""
        model_str = f" [{model}]" if model else ""
        lines.append(f"{i}. **{title}**{model_str}{rank_str} {brand}")
        lines.append(f"   価格: {price_str}")
        lines.append(f"   出典: OffMall | {url}")
        lines.append("")
    lines.append(f"Run ID: `{run_id}`")
    lines.append(f"データセット: `{dataset_id}`")
    return "\n".join(lines)


def _format_kakaku_results(result: dict[str, Any]) -> str:
    """価格.com検索結果用フォーマッター（最安価格・店舗数・レビュー）"""
    items = result.get("items", [])
    run_id = result.get("runId", "")
    dataset_id = result.get("datasetId", "")
    if not items:
        return f"**価格.com 検索結果**: 0件\n\nRun ID: `{run_id}`\nデータセット: `{dataset_id}`"

    lines = [
        f"**価格.com（日本最大級の価格比較サイト）検索結果** ({len(items)}件)",
        "",
    ]
    for i, it in enumerate(items, 1):
        title = it.get("title", "")
        maker = it.get("maker", "")
        price = it.get("price")
        price_type = it.get("priceType", "")
        shop_count = it.get("shopCount", 0)
        review = it.get("review", "")
        url = it.get("productUrl", "")
        price_str = f"¥{price:,}" if isinstance(price, int) else str(price or "?")
        maker_str = f" [{maker}]" if maker else ""
        shops_str = f"（{shop_count}店舗）" if shop_count else ""
        review_str = f" 評価: {review}" if review else ""
        type_str = f" {price_type}" if price_type else ""
        lines.append(f"{i}. **{title}**{maker_str}")
        lines.append(f"   最安価格: {price_str}{type_str}{shops_str}{review_str}")
        lines.append(f"   出典: 価格.com | {url}")
        lines.append("")
    lines.append(f"Run ID: `{run_id}`")
    lines.append(f"データセット: `{dataset_id}`")
    return "\n".join(lines)


# ──────────────────────────────────────────────
# サーバー構築
# ──────────────────────────────────────────────

def get_server() -> FastMCP:
    """
    FastMCP サーバーインスタンスを作成。
    この関数が main.py やテストから呼ばれる唯一のコントラクト。
    """
    server = FastMCP("japan-market-mcp", "0.1.0")

    # ──────────────────────────────────────────────
    # Tool 1: 中古カメラ市場 横断比較
    # ──────────────────────────────────────────────
    @server.tool(annotations=_OPEN_WORLD_ANNOTATIONS)
    async def search_camera_market(
        keyword: str,
        max_results: int = 10,
        sources: str = "kitamura,fujiya",
    ) -> dict:
        """日本の複数店舗（キタムラ+フジヤカメラ）の中古カメラ・レンズ価格を横断比較します。

        同じカメラモデルの店舗間価格差（転売利ざや・相場調査）が分かります。

        Args:
            keyword: 検索キーワード（例: "SONY α7", "NIKON Z9", "Canon RF"）
            max_results: 取得する最大件数（デフォルト 10, 最大 50）
            sources: 取得ソース（カンマ区切り: kitamura, fujiya）
        """
        await Actor.charge("camera-market-search")

        actor_input = {
            "searchKeyword": keyword,
            "maxItems": min(max_results, 50),
            "maxPages": 2,
            "sources": sources,
        }
        result = await _call_actor(CAMERA_ACTOR_ID, actor_input, "Japan Used Camera Market")
        text_output = _format_camera_results(result)
        return {"type": "text", "text": text_output, "structuredContent": result}

    # ──────────────────────────────────────────────
    # Tool 2: 中古時計市場 横断比較
    # ──────────────────────────────────────────────
    @server.tool(annotations=_OPEN_WORLD_ANNOTATIONS)
    async def search_watch_market(
        keyword: str,
        max_results: int = 10,
        sources: str = "jackroad,kitamura",
    ) -> dict:
        """日本の複数店舗（ジャックロード+キタムラ中古時計）の高級時計価格を横断比較します。

        ROLEX、OMEGA、グランドセイコーなどのブランド別・モデル別の店舗間価格差が分かります。

        Args:
            keyword: 検索キーワード（例: "ROLEX", "OMEGA", "グランドセイコー"）
            max_results: 取得する最大件数（デフォルト 10, 最大 50）
            sources: 取得ソース（カンマ区切り: jackroad, kitamura）
        """
        await Actor.charge("watch-market-search")

        actor_input = {
            "searchKeyword": keyword,
            "maxItems": min(max_results, 50),
            "maxPages": 2,
            "sources": sources,
        }
        result = await _call_actor(WATCH_ACTOR_ID, actor_input, "Japan Watch Market")
        text_output = _format_watch_results(result)
        return {"type": "text", "text": text_output, "structuredContent": result}

    # ──────────────────────────────────────────────
    # Tool 3: 中古ブランド品市場 横断比較
    # ──────────────────────────────────────────────
    @server.tool(annotations=_OPEN_WORLD_ANNOTATIONS)
    async def search_luxury_market(
        keyword: str = "",
        max_results: int = 10,
        sources: str = "komehyo,jackroad",
    ) -> dict:
        """日本の複数店舗（コメ兵カテゴリ+ジャックロード）の中古ブランド品価格を横断比較します。

        エルメス、ルイヴィトン、シャネルなどのバッグ・財布・ジュエリー・時計の
        店舗間価格差が分かります。キーワード空欄でカテゴリ全体をスキャンします。

        Args:
            keyword: 検索キーワード（例: "エルメス", "ルイヴィトン"）。空欄=カテゴリ全体スキャン
            max_results: 取得する最大件数（デフォルト 10, 最大 50）
            sources: 取得ソース（カンマ区切り: komehyo, jackroad）
        """
        await Actor.charge("luxury-market-search")

        actor_input = {
            "searchKeyword": keyword,
            "maxItems": min(max_results, 50),
            "maxPages": 2,
            "sources": sources,
        }
        result = await _call_actor(LUXURY_ACTOR_ID, actor_input, "Japan Luxury Brand Market")
        text_output = _format_luxury_results(result)
        return {"type": "text", "text": text_output, "structuredContent": result}

    # ──────────────────────────────────────────────
    # Tool 4: 中古楽器市場 横断比較
    # ──────────────────────────────────────────────
    @server.tool(annotations=_OPEN_WORLD_ANNOTATIONS)
    async def search_instrument_market(
        keyword: str = "",
        max_results: int = 10,
        sources: str = "digimart,ishibashi",
    ) -> dict:
        """日本の複数店舗（デジマート+イシバシ楽器U-BOX）の中古楽器価格を横断比較します。

        Fender、Gibsonなどのギター・ベース・アンプの店舗間価格差が分かります。
        キーワード空欄で主要カテゴリ全体をスキャンします。

        Args:
            keyword: 検索キーワード（例: "Fender", "Gibson", "Rickenbacker"）。空欄=カテゴリスキャン
            max_results: 取得する最大件数（デフォルト 10, 最大 50）
            sources: 取得ソース（カンマ区切り: digimart, ishibashi）
        """
        await Actor.charge("instrument-market-search")

        actor_input = {
            "searchKeyword": keyword,
            "maxItems": min(max_results, 50),
            "maxPages": 2,
            "sources": sources,
        }
        result = await _call_actor(INSTRUMENT_ACTOR_ID, actor_input, "Japan Used Instrument Market")
        text_output = _format_instrument_results(result)
        return {"type": "text", "text": text_output, "structuredContent": result}

    # ──────────────────────────────────────────────
    # Tool 5: オフモール 中古総合マーケット
    # ──────────────────────────────────────────────
    @server.tool(annotations=_OPEN_WORLD_ANNOTATIONS)
    async def search_offmall_market(
        keyword: str = "iPhone",
        max_results: int = 10,
        category: str = "",
    ) -> dict:
        """日本の総合中古EC「オフモール」（ハードオフ公式・全国800店舗以上）を検索します。

        カメラ、時計、楽器、ブランド品、スマホ、ゲーム機など13カテゴリをカバーする
        日本最大級のリユース市場。条件ランク（S/A/B/C）付きの実物中古品が検索できます。

        Args:
            keyword: 検索キーワード（例: "iPhone", "ロレックス", "ニンテンドー"）。空欄+category指定でカテゴリスキャン
            max_results: 取得する最大件数（デフォルト 10, 最大 50）
            category: カテゴリ指定（キーワード空欄時）: カメラ, 時計, 楽器, ブランド品, スマートフォン・携帯電話, ゲーム機 など
        """
        await Actor.charge("offmall-market-search")

        actor_input = {
            "searchKeyword": keyword,
            "maxItems": min(max_results, 50),
            "maxPages": 2,
            "category": category,
        }
        result = await _call_actor(OFFMALL_ACTOR_ID, actor_input, "Japan OffMall Used Goods Market")
        text_output = _format_offmall_results(result)
        return {"type": "text", "text": text_output, "structuredContent": result}

    # ──────────────────────────────────────────────
    # Tool 6: 価格.com キーワード価格検索
    # ──────────────────────────────────────────────
    @server.tool(annotations=_OPEN_WORLD_ANNOTATIONS)
    async def search_kakaku_prices(
        keyword: str = "iPhone",
        max_results: int = 10,
    ) -> dict:
        """日本の最大級価格比較サイト「価格.com」で商品の最安価格・店舗数・評価を検索します。

        数千の日本国内オンライン店舗（Amazon, ヨドバシ, ビックカメラ, 楽天など）の集約価格を
        一括で取得できるため、家電・スマホ・PCパーツなどの日本市場価格調査に最適です。

        Args:
            keyword: 検索キーワード（例: "iPhone", "PS5", "RTX 5080", "一眼レフ"）
            max_results: 取得する最大件数（デフォルト 10, 最大 50）
        """
        await Actor.charge("kakaku-price-search")

        actor_input = {
            "keyword": keyword,
            "maxItems": min(max_results, 50),
            "maxPages": 1,
        }
        result = await _call_actor(KAKAKU_ACTOR_ID, actor_input, "Japan Kakaku Price Search")
        text_output = _format_kakaku_results(result)
        return {"type": "text", "text": text_output, "structuredContent": result}

    @server.tool(annotations=_OPEN_WORLD_ANNOTATIONS)
    async def search_car_market(
        body_type: str = "SUV",
        max_results: int = 10,
    ) -> dict:
        """日本最大級の中古車ポータル「goo-net」で、車体タイプ別に在庫車両を検索します。

        車名・価格（円）・メーカー・販売店・詳細URLが取得できます。中古車輸出業者や
        JDM（日本仕様車）調査、相場確認に最適です。

        Args:
            body_type: 車体タイプ（SUV, SEDAN, MINIVAN, KEI, WAGON, COUPE, COMPACT, OPEN, BUS, KEITRUCK）
            max_results: 取得する最大件数（デフォルト 10, 最大 50）
        """
        await Actor.charge("car-market-search")

        actor_input = {
            "bodyType": body_type,
            "maxItems": min(max_results, 50),
            "maxPages": 2,
        }
        result = await _call_actor(GOO_NET_ACTOR_ID, actor_input, "Goo-net Japan Used Cars")
        text_output = _fmt_market_results(result, "中古車市場（goo-net 全国）")
        return {"type": "text", "text": text_output, "structuredContent": result}

    return server
