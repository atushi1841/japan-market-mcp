"""
MAFF 青果物卸売市場調査 テスト。

フォーマッター出力の検証（オフライン）と、ネットワークを伴うライブ取得の
スモーク（MAFF CSVの実データでフィールド名・パースを検証）。

オフラインのフォーマッターテストは pytest で実行:
  /home/atushi/japan-market-mcp-venv/bin/python -m pytest tests/test_maff_market.py -q

ライブ取得スモークは:
  /home/atushi/japan-market-mcp-venv/bin/python tests/smoke_maff_live.py
"""
import sys
from datetime import date
from pathlib import Path

_SRC = str(Path(__file__).parent.parent / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import maff_market as m


# ── オフライン: フォーマッター ─────────────────────────────
def _sample_rows():
    return [
        {
            "item": "だいこん", "itemCode": "30100", "origin": None, "originCode": None,
            "quantityTons": 416.2, "pricePer100kg": 113.0,
            "yoyQuantityPct": 150.1, "yoyPricePct": 110.8,
            "prevQuantityPct": 104.0, "prevPricePct": 124.2,
            "isMarketTotal": True,
        },
        {
            "item": "だいこん", "itemCode": "30100", "origin": "北海道", "originCode": "001",
            "quantityTons": 415.6, "pricePer100kg": 112.0,
            "yoyQuantityPct": None, "yoyPricePct": None,
            "prevQuantityPct": None, "prevPricePct": None,
            "isMarketTotal": False,
        },
        {
            "item": "にんじん", "itemCode": "30300", "origin": None, "originCode": None,
            "quantityTons": 314.9, "pricePer100kg": 85.0,
            "yoyQuantityPct": 86.2, "yoyPricePct": 52.5,
            "prevQuantityPct": 98.3, "prevPricePct": 69.1,
            "isMarketTotal": True,
        },
    ]


def test_market_total_filter():
    rows = _sample_rows()
    totals = m.market_total_rows(rows)
    assert len(totals) == 2
    assert all(r["isMarketTotal"] for r in totals)


def test_format_market_report_contains_columns():
    period = {"year": 2026, "month": 8, "part": 1}
    out = m.format_market_report(period, "sapporo", _sample_rows())
    assert "札幌市中央" in out
    assert "だいこん" in out
    assert "113" in out  # 価格
    assert "対前年比" in out


def test_format_market_report_item_filter():
    period = {"year": 2026, "month": 8, "part": 1}
    out = m.format_market_report(period, "sapporo", _sample_rows(), item_filter="にんじん")
    assert "にんじん" in out
    assert "だいこん" not in out


def test_format_trend():
    tr = [
        {"market": "sapporo", "marketName": "札幌市中央", "period": "2026-08-1",
         "periodName": "2026年8月上旬", "item": "だいこん", "yoyPricePct": 110.8,
         "quantityTons": 416.2, "pricePer100kg": 113.0},
    ]
    out = m.format_trend(tr)
    assert "だいこん" in out
    assert "札幌市中央" in out


def test_format_movers():
    mv = [
        {"item": "にんじん", "pricePer100kg": 85.0, "yoyPricePct": 52.5},
        {"item": "だいこん", "pricePer100kg": 113.0, "yoyPricePct": 110.8},
    ]
    out = m.format_movers(mv, "sapporo", {"year": 2026, "month": 8, "part": 1})
    assert "前年同旬比" in out
    assert "にんじん" in out


def test_period_key_and_label():
    assert m._period_key({"year": 2026, "month": 8, "part": 1}) == "2026-08-1"
    assert m._period_label({"year": 2026, "month": 8, "part": 1}) == "2026年8月上旬"


def test_rewa_year():
    assert m._rewa_year(2026) == 26
    assert m._rewa_year(2025) == 25


def test_list_markets():
    mkts = m.list_markets()
    assert len(mkts) >= 15
    by_slug = {x["market"]: x for x in mkts}
    assert by_slug["sapporo"]["name"] == "札幌市中央"
    assert by_slug["toyosu"]["name"].startswith("東京")


# ── オフライン: 期間ロジック ─────────────────────────────
def test_prev_period_mid():
    assert m._prev_period({"year": 2026, "month": 9, "part": 2}) == {
        "year": 2026, "month": 9, "part": 1}


def test_prev_period_first_of_month():
    assert m._prev_period({"year": 2026, "month": 9, "part": 1}) == {
        "year": 2026, "month": 8, "part": 3}


def test_prev_period_jan_first():
    assert m._prev_period({"year": 2026, "month": 1, "part": 1}) == {
        "year": 2025, "month": 12, "part": 3}


def test_latest_period_bounds():
    assert m._latest_period(date(2026, 9, 5)) == {"year": 2026, "month": 9, "part": 1}
    assert m._latest_period(date(2026, 9, 15)) == {"year": 2026, "month": 9, "part": 2}
    assert m._latest_period(date(2026, 9, 25)) == {"year": 2026, "month": 9, "part": 3}
