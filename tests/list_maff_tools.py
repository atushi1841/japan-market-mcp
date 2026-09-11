"""ツール登録検証 — get_server() で登録される全ツール名を出力。"""
import asyncio
import os
import sys

# ローカルでは shim Actor を使う
os.environ.pop("APIFY_CONTAINER_PORT", None)
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from src.server import get_server  # noqa: E402
from src.maff_market import list_markets  # noqa: E402


async def main():
    server = get_server()
    tools = await server.list_tools()
    names = [t.name for t in tools]
    print(f"{len(names)} tools registered:")
    for n in names:
        print("  -", n)
    required = {
        "get_maff_market_report", "search_maff_price_trend",
        "get_maff_top_movers", "get_maff_markets",
    }
    missing = required - set(names)
    print("missing:", missing if missing else "NONE")
    print("markets:", len(list_markets()))
    if missing:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
