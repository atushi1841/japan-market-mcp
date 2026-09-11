"""
MAFF 青果物卸売市場調査（旬別結果・市場別）データ取得モジュール。

農林水産省が公開する公的統計CSVを直接取得・整形する。
政府標準利用規約2.0（出典明記で商用可）対象のオープンデータ。
※ スケープではなく、広報統計ファイルへの直接ダウンロード。

URLパターン:
  https://www.maff.go.jp/j/tokei/syohi/shunbetu/{year}/csv/{yy}{mm}{suffix}ss_{code}_{slug}.csv
  例: .../2026/csv/26081ss_51300_sapporo.csv  (令和08年 8月 上旬, 札幌)

CSVはShift-JISエンコーディング。ヘッダ:
  品目名, 品目コード, 産地名, 産地コード, 数量(t), 価格(円),
  対前年同旬比数量(%), 対前年同旬比価格(%), 対前旬比数量(%), 対前旬比価格(%)

価格は円/100kg（青果物卸売市場調査の販売価格＝100kg当たり）。産地名が空の行が
「市場全体合計（総計）」レコード。
"""

from __future__ import annotations

import calendar
import csv
import io
import re
from datetime import date
from typing import Any

import httpx

BASE_URL = "https://www.maff.go.jp/j/tokei/syohi/shunbetu"

# slug → (market code, 日本語市場名)
MARKET_SLUGS: dict[str, tuple[str, str]] = {
    "sapporo": ("51300", "札幌市中央"),
    "sendai": ("04300", "仙台市中央"),
    "toyosu": ("13300", "東京・豊洲"),
    "oota": ("13310", "東京・大田"),
    "tosima": ("13350", "東京・としま"),
    "yodohasi": ("13360", "東京・淀橋"),
    "yokohama": ("14300", "横浜市中央"),
    "kanazawa": ("17300", "金沢市中央"),
    "nagohon": ("23300", "名古屋市北部"),
    "nagohoku": ("23310", "名古屋市南部"),
    "kyoto": ("26300", "京都市中央"),
    "oosakaho": ("27300", "大阪市北部"),
    "oosakato": ("27310", "大阪市南部"),
    "kobe": ("28300", "神戸市中央"),
    "hirosima": ("34300", "広島市中央"),
    "takamatu": ("37300", "高松市中央"),
    "kitakyu": ("40300", "北九州市中央"),
    "hukuoka": ("40320", "福岡市中央"),
    "okinawa": ("47300", "那覇市"),
}

# 旬 suffix: 上旬=1, 中旬=2, 下旬=3
_PERIOD_SUFFIX = {1: "1", 2: "2", 3: "3"}
_PERIOD_NAME = {1: "上旬", 2: "中旬", 3: "下旬"}

_HTTP_TIMEOUT = 30.0
# 成果キャッシュ（同一期間の再取得を回避）
_fetch_cache: dict[tuple[str, str], list[dict[str, Any]]] = {}


def list_markets() -> list[dict[str, str]]:
    """利用可能な市場一覧（スラッグ・市場名）。"""
    return [
        {"market": slug, "name": jp, "code": code}
        for slug, (code, jp) in sorted(MARKET_SLUGS.items(), key=lambda kv: kv[1][1])
    ]


def _rewa_year(year: int) -> int:
    """URLに含まれるYY部分 = 西暦の下2桁（e.g. 2026→26）。MAFFのCSVファイル名はこの形式。"""
    return year % 100


def _latest_period(today: date | None = None) -> dict[str, int]:
    """本日時点の最新旬（year, month, part）を返す。中旬・下旬はその月内で確定済み扱い。"""
    today = today or date.today()
    yy = today.year
    mm = today.month
    day = today.day
    if day <= 10:
        part = 1
    elif day <= 20:
        part = 2
    else:
        part = 3
    return {"year": yy, "month": mm, "part": part}


def _period_key(period: dict[str, int]) -> str:
    return f"{period['year']:04d}-{period['month']:02d}-{period['part']}"


def _prev_period(period: dict[str, int]) -> dict[str, int]:
    """直前の旬へ1歩戻す。"""
    p = dict(period)
    if p["part"] > 1:
        p["part"] -= 1
    else:
        if p["month"] == 1:
            p["month"] = 12
            p["year"] -= 1
        else:
            p["month"] -= 1
        p["part"] = 3
    return p


def latest_available_period(
    slug: str,
    max_back: int = 6,
    today: date | None = None,
) -> dict[str, int]:
    """
    指定市場について、実際に公開済みの最新旬を返す。

    MAFFは旬別結果を公表時点で掲載するため、「本日が中旬でもデータは上旬のまま」
    という場合がある。403（未公開）を検知して、公開済みの直近旬まで遡る。
    """
    period = _latest_period(today)
    for _ in range(max_back + 1):
        key = (_period_key(period), slug)
        if key in _fetch_cache:
            return period
        url = _build_url(period, slug)
        try:
            resp = httpx.get(url, timeout=_HTTP_TIMEOUT, follow_redirects=True)
            if resp.status_code == 200:
                return period
        except Exception:
            pass
        period = _prev_period(period)
    # 全滅時は現在旬のまま（fetch時により詳細なエラーが上がる）
    return _latest_period(today)


def _build_url(period: dict[str, int], slug: str) -> str:
    code, _jp = MARKET_SLUGS[slug]
    yy = _rewa_year(period["year"])
    suffix = _PERIOD_SUFFIX[period["part"]]
    mm = f"{period['month']:02d}"
    return f"{BASE_URL}/{period['year']}/csv/{yy}{mm}{suffix}ss_{code}_{slug}.csv"


def _parse_num(s: str) -> float | None:
    s = (s or "").replace(",", "").strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _parse_csv(text: str) -> list[dict[str, Any]]:
    reader = csv.reader(io.StringIO(text))
    rows = []
    for raw in reader:
        if not raw or len(raw) < 6:
            continue
        row = [c.strip() for c in raw]
        # ヘッダ行・オープンデータ説明行はスキップ（品目コードが数値以外）
        if not re.match(r"^\d+$", row[1] or ""):
            continue
        price = _parse_num(row[5])
        qty = _parse_num(row[4])
        rows.append(
            {
                "item": row[0],
                "itemCode": row[1],
                "origin": row[2].strip() or None,
                "originCode": row[3].strip() or None,
                "quantityTons": qty,
                "pricePer100kg": price,
                "yoyQuantityPct": _parse_num(row[6]) if len(row) > 6 else None,
                "yoyPricePct": _parse_num(row[7]) if len(row) > 7 else None,
                "prevQuantityPct": _parse_num(row[8]) if len(row) > 8 else None,
                "prevPricePct": _parse_num(row[9]) if len(row) > 9 else None,
                "isMarketTotal": (row[2].strip() == ""),
            }
        )
    return rows


def fetch_market(period: dict[str, int], slug: str) -> list[dict[str, Any]]:
    """指定市場・旬の全品目データを取得（market全体合計のみの行も含む）。"""
    key = (_period_key(period), slug)
    if key in _fetch_cache:
        return _fetch_cache[key]
    # 指定市場の確認
    if slug not in MARKET_SLUGS:
        raise ValueError(
            f"未知の市場 '{slug}'。利用可能: {', '.join(sorted(MARKET_SLUGS))}"
        )
    url = _build_url(period, slug)
    resp = httpx.get(url, timeout=_HTTP_TIMEOUT, follow_redirects=True)
    resp.raise_for_status()
    # Shift-JISデコード（BOM/エラー耐性）
    raw = resp.content
    enc = "cp932"
    try:
        text = raw.decode(enc)
    except UnicodeDecodeError:
        text = raw.decode(enc, errors="replace")
    rows = _parse_csv(text)
    _fetch_cache[key] = rows
    return rows


def market_total_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """市場全体合計レコード（産地名が空）のみを抽出。"""
    return [r for r in rows if r["isMarketTotal"]]


def _by_item(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        out.setdefault(r["item"], []).append(r)
    return out


def price_trend(
    item: str,
    slugs: list[str],
    periods: list[dict[str, int]] | None = None,
    today: date | None = None,
) -> list[dict[str, Any]]:
    """
    指定品目の複数旬にわたる市場別価格推移を返す。

    各市場・各旬で該当品目の市場合計レコード（産地名空）を探し、
    価格・数量・前年比を時系列で並べる。
    """
    periods = periods or [_latest_period(today)]
    out: list[dict[str, Any]] = []
    for slug in slugs:
        name = MARKET_SLUGS[slug][1]
        for period in periods:
            try:
                rows = fetch_market(period, slug)
            except Exception:
                continue
            for r in market_total_rows(rows):
                if r["item"] == item:
                    out.append(
                        {
                            "market": slug,
                            "marketName": name,
                            "period": _period_key(period),
                            "periodName": _period_label(period),
                            **r,
                        }
                    )
                    break
    # 時系列順にソート（market単位では period昇順）
    out.sort(key=lambda x: (x["market"], x["period"]))
    return out


def top_movers(
    slug: str,
    period: dict[str, int] | None = None,
    limit: int = 10,
    today: date | None = None,
) -> list[dict[str, Any]]:
    """指定市場・旬で、前年同旬比価格上昇率が大きい品目トップNを返す。"""
    period = period or _latest_period(today)
    rows = fetch_market(period, slug)
    items: list[dict[str, Any]] = []
    for r in market_total_rows(rows):
        if r["yoyPricePct"] is None:
            continue
        items.append(r)
    items.sort(key=lambda x: (x["yoyPricePct"] or 0), reverse=True)
    return items[:limit]


def _period_label(period: dict[str, int]) -> str:
    return f"{period['year']}年{period['month']}月{_PERIOD_NAME[period['part']]}"


def _fmt_int(v: float | None) -> str:
    if v is None:
        return "-"
    return f"{v:,.0f}"


def format_market_report(
    period: dict[str, int],
    slug: str,
    rows: list[dict[str, Any]],
    item_filter: str | None = None,
) -> str:
    """市場旬報のテキスト整形。"""
    name = MARKET_SLUGS[slug][1]
    lines = [
        f"**青果物卸売市場調査（旬別・市場別） — {name}**",
        f"期間: {_period_label(period)}（{period['year']}年 / {slug} / code={MARKET_SLUGS[slug][0]}）",
        "",
        "| 品目 | 数量(t) | 価格(円/100kg) | 対前年比% | 対前旬比% |",
        "|---|---|---|---|---|",
    ]
    totals = market_total_rows(rows)
    if item_filter:
        totals = [r for r in totals if item_filter in r["item"]]
    if not totals:
        return f"**{name} / {_period_label(period)}**: 該当品目のデータがありません。"
    for r in totals:
        yoy = f"{r['yoyPricePct']:.0f}" if r["yoyPricePct"] is not None else "-"
        prev = f"{r['prevPricePct']:.0f}" if r["prevPricePct"] is not None else "-"
        lines.append(
            f"| {r['item']} | {_fmt_int(r['quantityTons'])} | {_fmt_int(r['pricePer100kg'])} | {yoy} | {prev} |"
        )
    lines.append("")
    lines.append("*出典: 農林水産省「青果物卸売市場調査（旬別結果・市場別）」")
    lines.append("*価格は100kg当たりの販売価格。データは政府標準利用規約2.0で公開。")
    return "\n".join(lines)


def format_trend(text_rows: list[dict[str, Any]]) -> str:
    """価格推移のテキスト整形。"""
    if not text_rows:
        return "指定品目の価格推移データが見つかりません。"
    item = text_rows[0]["item"]
    lines = [f"**{item} — 卸売価格推移（市場別・旬別）**", ""]
    per_market: dict[str, list[dict[str, Any]]] = {}
    for r in text_rows:
        per_market.setdefault(r["marketName"], []).append(r)
    for mname, rows in per_market.items():
        lines.append(f"**{mname}**")
        lines.append("| 期間 | 数量(t) | 価格(円/100kg) | 対前年比% |")
        lines.append("|---|---|---|---|")
        for r in sorted(rows, key=lambda x: x["period"]):
            yoy = f"{r['yoyPricePct']:.0f}" if r["yoyPricePct"] is not None else "-"
            lines.append(
                f"| {r['periodName']} | {_fmt_int(r['quantityTons'])} | {_fmt_int(r['pricePer100kg'])} | {yoy} |"
            )
        lines.append("")
    lines.append("*出典: 農林水産省「青果物卸売市場調査（旬別結果・市場別）」")
    return "\n".join(lines)


def format_movers(movers: list[dict[str, Any]], slug: str, period: dict[str, int]) -> str:
    """前年比上昇トップのテキスト整形。"""
    name = MARKET_SLUGS[slug][1]
    lines = [
        f"**前年同旬比 価格上昇トップ — {name}**",
        f"期間: {_period_label(period)}",
        "",
        "| 順位 | 品目 | 価格(円/100kg) | 対前年比%(価格) |",
        "|---|---|---|---|",
    ]
    for i, r in enumerate(movers, 1):
        yoy = f"{r['yoyPricePct']:.0f}" if r["yoyPricePct"] is not None else "-"
        lines.append(f"| {i} | {r['item']} | {_fmt_int(r['pricePer100kg'])} | {yoy} |")
    lines.append("")
    lines.append("*出典: 農林水産省「青果物卸売市場調査（旬別結果・市場別）」")
    return "\n".join(lines)
