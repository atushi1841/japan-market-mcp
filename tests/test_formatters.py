"""
Tests for Japan Market MCP Server output formatting.

These tests validate that formatter functions produce correct output
for known input data shapes, catching field name mismatches early.
"""

import sys
import json
from pathlib import Path

# Add src to path
_SRC = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, _SRC)
sys.path.insert(0, str(Path(__file__).parent.parent))  # for src.apify_shim

from server import (
    _format_camera_results,
    _format_watch_results,
    _format_luxury_results,
    _format_instrument_results,
    _format_offmall_results,
    _format_kakaku_results,
    _format_car_stats_results,
    _format_prize_results,
    _format_prize_stats_results,
    _format_rakuten_results,
    _format_rakuten_ranking_results,
)


def _sample_market_item(source="kitamura"):
    return {
        "productId": "TEST-001",
        "title": "SONY α7 III ボディ [ILCE-7M3]",
        "price": 159000,
        "brand": "SONY",
        "shop": "キタムラ新宿",
        "category": "ミラーレスカメラ",
        "condition": "中古品A",
        "source": source,
        "imageUrl": "https://example.com/img.jpg",
        "productUrl": "https://example.com/product/1",
        "scrapedAt": "2026-08-10T00:00:00Z",
    }


def test_format_camera_results():
    result = {
        "items": [_sample_market_item("kitamura"), _sample_market_item("fujiya")],
        "runId": "run-camera-1",
        "datasetId": "ds-camera-1",
    }
    out = _format_camera_results(result)
    assert "中古カメラ市場" in out
    assert "SONY α7 III" in out
    assert "¥159,000" in out
    assert "kitamura" in out or "fujiya" in out
    assert "run-camera-1" in out


def test_format_watch_results():
    result = {
        "items": [
            {"title": "ロレックス サブマリーナー", "price": 2480000, "brand": "ROLEX",
             "source": "jackroad", "shop": "Jackroad", "productUrl": "https://example.com/2"},
        ],
        "runId": "run-watch-1",
        "datasetId": "ds-watch-1",
    }
    out = _format_watch_results(result)
    assert "中古時計市場" in out
    assert "ロレックス サブマリーナー" in out
    assert "¥2,480,000" in out
    assert "Jackroad" in out


def test_format_offmall_results():
    result = {
        "items": [
            {"title": "iPhone 11", "price": 27500, "brand": "APPLE", "rank": "S",
             "modelCode": "MWLX2J/A", "productUrl": "https://netmall.hardoff.co.jp/product/1/"},
        ],
        "runId": "run-offmall-1",
        "datasetId": "ds-offmall-1",
    }
    out = _format_offmall_results(result)
    assert "オフモール" in out
    assert "iPhone 11" in out
    assert "¥27,500" in out
    assert "ランクS" in out
    assert "OffMall" in out


def test_format_luxury_results():
    result = {
        "items": [
            {"title": "エルメス バーキン 25cm", "price": 3400000, "brand": "HERMES",
             "source": "komehyo", "shop": "Komehyo", "condition": "未使用品",
             "productUrl": "https://example.com/3"},
        ],
        "runId": "run-lux-1",
        "datasetId": "ds-lux-1",
    }
    out = _format_luxury_results(result)
    assert "中古ブランド品市場" in out
    assert "エルメス バーキン" in out
    assert "¥3,400,000" in out
    assert "Komehyo" in out


def test_format_instrument_results():
    result = {
        "items": [
            {"title": "Fender Stratocaster 中古", "price": 143550, "brand": "Fender",
             "source": "digimart", "shop": "デジマート", "productUrl": "https://example.com/4"},
        ],
        "runId": "run-inst-1",
        "datasetId": "ds-inst-1",
    }
    out = _format_instrument_results(result)
    assert "中古楽器市場" in out
    assert "Fender Stratocaster" in out
    assert "¥143,550" in out
    assert "デジマート" in out


def test_format_empty():
    result = {"items": [], "runId": "run-empty-1"}
    out = _format_camera_results(result)
    assert "検索結果はありませんでした" in out


def test_format_kakaku_results():
    result = {
        "items": [
            {"title": "iPhone 17e", "maker": "Apple", "price": 101799, "priceType": "端末価格",
             "shopCount": 149, "review": "4.25 (44)", "productUrl": "https://kakaku.com/model/M1"},
        ],
        "runId": "run-kakaku-1",
        "datasetId": "ds-kakaku-1",
    }
    out = _format_kakaku_results(result)
    assert "価格.com" in out
    assert "iPhone 17e" in out
    assert "¥101,799" in out
    assert "149店舗" in out
    assert "4.25 (44)" in out


def test_format_car_stats_results():
    result = {
        "items": [
            {"statsType": "goo-net-car-price", "keyword": "N-BOX", "count": 28,
             "priceMin": 198000, "priceMax": 2498000, "priceAvg": 1250000, "priceMedian": 1198000,
             "sampleItems": [
                 {"title": "ホンダ N-BOX カスタム G・Lパッケージ", "price": 1580000,
                  "detailUrl": "https://example.com/car/1", "shop": "○○ショップ"},
             ],
             "collectedAt": "2026-09-08T00:00:00.000Z"},
        ],
        "runId": "run-stats-1",
        "datasetId": "ds-stats-1",
    }
    out = _format_car_stats_results(result)
    assert "goo-net 中古車相場" in out
    assert "N-BOX" in out
    assert "¥198,000" in out
    assert "¥2,498,000" in out
    assert "¥1,250,000" in out
    assert "¥1,198,000" in out
    assert "N-BOX カスタム" in out
    assert "run-stats-1" in out


def test_format_car_stats_results_empty():
    result = {
        "items": [
            {"statsType": "goo-net-car-price", "keyword": "存在しない車種", "count": 0,
             "priceMin": None, "priceMax": None, "priceAvg": None, "priceMedian": None,
             "sampleItems": [], "collectedAt": "2026-09-08T00:00:00.000Z"},
        ],
        "runId": "run-stats-0",
        "datasetId": "ds-stats-0",
    }
    out = _format_car_stats_results(result)
    assert "サンプル0件" in out
    assert "存在しない車種" in out


def test_format_car_stats_results_insufficient():
    """count<20 (insufficientSample) must render a notice, NOT fake statistics."""
    result = {
        "items": [
            {"statsType": "goo-net-car-price", "keyword": "レア車", "count": 5,
             "insufficientSample": True,
             "notice": "サンプル僅少のため統計値は返しません",
             "priceMin": 100, "priceAvg": 200, "priceMedian": 150, "priceMax": 400,
             "sampleItems": [], "collectedAt": "2026-09-08T00:00:00.000Z"},
        ],
        "runId": "run-stats-5",
        "datasetId": "ds-stats-5",
    }
    out = _format_car_stats_results(result)
    assert "サンプル僅少（5台 / 最低20台）" in out
    assert "統計値は返しません" in out
    assert "サンプル僅少のため統計値は返しません" in out
    # must NOT render a numeric statistic block
    assert "¥400" not in out
    assert "¥150" not in out


def test_format_prize_results():
    result = {
        "items": [
            {
                "title": "【プレゼント】最新ネタ iPhone 15 Pro 抽選",
                "prize": "iPhone 15 Pro 256GB",
                "deadline": "2026-09-30",
                "winnerCount": 3,
                "source": "kenshou.club",
                "xUrl": "https://x.com/account/status/111222333",
            },
            {
                "title": "お米プレゼントキャンペーン",
                "prize": "新潟コシヒカリ5kg",
                "deadline": "2026-10-15",
                "winnerCount": 100,
                "source": "cp.meikan.org",
                "xUrl": "https://x.com/account/status/444555666",
            },
        ],
        "runId": "run-prize-1",
        "datasetId": "ds-prize-1",
    }
    out = _format_prize_results(result)
    assert "国内懸賞・プレゼント応募情報" in out
    assert "iPhone 15 Pro 256GB" in out
    assert "当選数: 3名" in out
    assert "締切: 2026-09-30" in out
    assert "kenshou.club" in out
    assert "お米プレゼントキャンペーン" in out
    assert "run-prize-1" in out


def test_format_prize_stats_results():
    result = {
        "items": [
            {
                "statsType": "japan-prize-giveaway",
                "keyword": "お米",
                "count": 12,
                "activeCount": 9,
                "totalWinnerCount": 150,
                "sources": {"kenshou.club": 7, "cp.meikan.org": 5},
                "collectedAt": "2026-09-09T00:00:00.000Z",
            }
        ],
        "runId": "run-prize-stats-1",
        "datasetId": "ds-prize-stats-1",
    }
    out = _format_prize_stats_results(result)
    assert "国内懸賞・プレゼント相場 — お米" in out
    assert "有効件数: 9" in out
    assert "総当選者数: 150" in out
    assert "kenshou.club: 7件" in out
    assert "cp.meikan.org: 5件" in out
    assert "run-prize-stats-1" in out


def test_format_prize_stats_results_empty():
    result = {
        "items": [
            {"statsType": "japan-prize-giveaway", "keyword": "存在しない言葉", "count": 0}
        ],
        "runId": "run-prize-stats-2",
        "datasetId": "ds-prize-stats-2",
    }
    out = _format_prize_stats_results(result)
    assert "サンプル0件" in out
    assert "存在しない言葉" in out


def test_format_rakuten_results():
    result = {
        "items": [
            {
                "itemName": "ルイヴィトン アルマ BB モノグラム",
                "itemPrice": 299200,
                "itemUrl": "https://item.rakuten.co.jp/across/m46990/",
                "shopName": "ブランドショップACROSS",
                "reviewAverage": 4.5,
                "reviewCount": 12,
                "imageUrl": "https://thumbnail.image.rakuten.co.jp/@0_mall/across/x.jpg",
            },
            {
                "itemName": "商品2",
                "itemPrice": "5980",  # 文字列priceも許容
                "itemUrl": "https://item.rakuten.co.jp/shop2/2/",
                "shopName": "ショップ2",
                "reviewAverage": 0.0,
                "reviewCount": 0,
            },
        ],
        "runId": "run-rk-1",
        "datasetId": "ds-rk-1",
    }
    out = _format_rakuten_results(result)
    assert "楽天市場（公式API）検索結果" in out
    assert "ルイヴィトン アルマ BB" in out
    assert "¥299,200" in out
    assert "¥5,980" in out
    assert "ブランドショップACROSS" in out
    assert "評価: 4.5(12件)" in out
    assert "run-rk-1" in out


def test_format_rakuten_results_empty():
    out = _format_rakuten_results({"items": [], "runId": "run-rk-2", "datasetId": "ds-rk-2"})
    assert "0件" in out
    assert "run-rk-2" in out


def test_format_rakuten_ranking_results():
    result = {
        "items": [
            {
                "rank": 1,
                "itemName": "ULRUBヘッドスクラブ",
                "itemPrice": 4173,
                "itemUrl": "https://item.rakuten.co.jp/churacos/r_ulrub/",
                "shopName": "CHURACOS",
            },
            {
                "rank": 2,
                "itemName": "ランキング商品2",
                "itemPrice": "1980",
                "itemUrl": "",
                "shopName": "",
            },
        ],
        "runId": "run-rkr-1",
        "datasetId": "ds-rkr-1",
    }
    out = _format_rakuten_ranking_results(result)
    assert "楽天市場 ランキング（公式API）" in out
    assert "1. **ULRUBヘッドスクラブ** — ¥4,173 [CHURACOS]" in out
    assert "2. **ランキング商品2** — ¥1,980" in out
    assert "run-rkr-1" in out


def test_format_rakuten_ranking_results_empty():
    out = _format_rakuten_ranking_results({"items": [], "runId": "r", "datasetId": "d"})
    assert "0件" in out


if __name__ == "__main__":
    tests = [
        test_format_camera_results,
        test_format_watch_results,
        test_format_luxury_results,
        test_format_instrument_results,
        test_format_offmall_results,
        test_format_kakaku_results,
        test_format_car_stats_results,
        test_format_car_stats_results_empty,
        test_format_empty,
        test_format_prize_results,
        test_format_prize_stats_results,
        test_format_prize_stats_results_empty,
        test_format_rakuten_results,
        test_format_rakuten_results_empty,
        test_format_rakuten_ranking_results,
        test_format_rakuten_ranking_results_empty,
    ]
    for t in tests:
        t()
        print(f"✅ {t.__name__}")
    print("全テスト成功")
