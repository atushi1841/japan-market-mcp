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


if __name__ == "__main__":
    tests = [
        test_format_camera_results,
        test_format_watch_results,
        test_format_luxury_results,
        test_format_instrument_results,
        test_format_offmall_results,
        test_format_empty,
    ]
    for t in tests:
        t()
        print(f"✅ {t.__name__}")
    print("全テスト成功")
