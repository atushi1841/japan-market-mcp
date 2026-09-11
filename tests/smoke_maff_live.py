"""
MAFF 旬別市況 ライブ取得スモーク。

MAFF公式CSVから実際にデータを取得し、パース・整形が正しく動くことを検証する。
pytestのテストではない（ネットワーク依存のため別スクリプトに分離）。

  /home/atushi/japan-market-mcp-venv/bin/python tests/smoke_maff_live.py
"""
import sys
from pathlib import Path

_SRC = str(Path(__file__).parent.parent / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import maff_market as m

PASS = 0
FAIL = 0


def green(msg):
    global PASS
    PASS += 1
    print(f"  \033[32mPASS\033[0m  {msg}")


def red(msg):
    global FAIL
    FAIL += 1
    print(f"  \033[31mFAIL\033[0m  {msg}")


def main():
    period = m.latest_available_period("sapporo")
    print(f"公開済み最新旬: {m._period_label(period)}")

    # 1. 市場レポート（札幌・公開済み最新旬）
    try:
        rows = m.fetch_market(period, "sapporo")
        totals = m.market_total_rows(rows)
        if len(rows) > 100 and len(totals) > 20:
            green(f"fetch sapporo {period}: {len(rows)}行 / 市場合計 {len(totals)}品目")
        else:
            red(f"fetch sapporo 分類数が想定外: rows={len(rows)} totals={len(totals)}")
        out = m.format_market_report(period, "sapporo", rows)
        if "北海道" in out or "野菜総計" in out or "だいこん" in out or "品目" in out:
            green("市場レポート整形OK")
        else:
            red("市場レポート整形に市況データが含まれない")
    except Exception as e:
        red(f"sapporo fetch失敗: {e}")

    # 2. 前年比トップマーケットムーバー
    try:
        mv = m.top_movers("sapporo", period, limit=5)
        if mv and all(r.get("yoyPricePct") is not None for r in mv):
            green(f"top_movers: {len(mv)}件, 首位={mv[0]['item']} yoy={mv[0]['yoyPricePct']}")
        else:
            red(f"top_movers 結果が空 or 前年比欠落: {len(mv)}")
    except Exception as e:
        red(f"top_movers失敗: {e}")

    # 3. 価格推移（だいこん・3市場・直近2旬）
    try:
        latest = m.latest_available_period("sapporo")
        prev = m._prev_period(latest)
        tr = m.price_trend("だいこん", ["sapporo", "toyosu", "oosakaho"], [prev, latest])
        if len(tr) >= 3:
            green(f"price_trend だいこん: {len(tr)}行")
        else:
            red(f"price_trend 件数少 {len(tr)}")
    except Exception as e:
        red(f"price_trend失敗: {e}")

    print(f"Results: {PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
