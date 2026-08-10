"""
MCPサーバーのHTTPスモークテスト — mcp SDK の StreamableHTTPClient を使用。

サーバー起動後に実行:
  /home/atushi/japan-market-mcp-venv/bin/python tests/test_http_smoke.py [BASE_URL]

検証項目:
  1. initialize が成功し serverInfo が返る
  2. tools/list で4ツールが返る
  3. tools/call で search_camera_market が実行できる（APIFY_TOKEN必須）
     ※ ローカルでAPIFY_TOKEN未設定の場合は 3 をスキップ
"""

import asyncio
import os
import sys

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000/mcp"

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


async def main() -> int:
    print(f"MCP HTTP smoke test — {BASE_URL}")
    print("──────────────────────────────────────────")

    from mcp import ClientSession  # noqa
    from mcp.client.streamable_http import streamablehttp_client

    try:
        async with streamablehttp_client(url=BASE_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                # 1. initialize
                try:
                    init = await asyncio.wait_for(session.initialize(), timeout=20)
                    name = init.serverInfo.name if hasattr(init, "serverInfo") else "?"
                    if name:
                        green(f"initialize OK (serverInfo.name={name}, version={init.serverInfo.version})")
                    else:
                        red("initialize returned no serverInfo")
                except Exception as e:
                    red(f"initialize failed: {e}")
                    return 1

                # 2. tools/list
                try:
                    tools = await asyncio.wait_for(session.list_tools(), timeout=20)
                    tool_names = [t.name for t in tools.tools]
                    print(f"    Tools: {tool_names}")
                    expected = {"search_camera_market", "search_watch_market",
                                "search_luxury_market", "search_instrument_market",
                                "search_offmall_market"}
                    if expected.issubset(set(tool_names)):
                        green(f"tools/list returns {len(tool_names)} tools (all 4 expected)")
                    else:
                        missing = expected - set(tool_names)
                        red(f"tools/list missing: {missing} (got {tool_names})")
                except Exception as e:
                    red(f"tools/list failed: {e}")
                    return 1

                # 3. tools/call (APIFY_TOKEN必須)
                if os.environ.get("APIFY_TOKEN"):
                    try:
                        result = await asyncio.wait_for(
                            session.call_tool("search_camera_market", {"keyword": "SONY"}),
                            timeout=180,
                        )
                        texts = [c.text for c in result.content if hasattr(c, "text")]
                        joined = " ".join(texts)
                        if "中古カメラ" in joined or "検索結果" in joined:
                            green(f"tools/call search_camera_market returns content ({len(joined)} chars)")
                        else:
                            red(f"tools/call returned unexpected content: {joined[:150]}")
                    except Exception as e:
                        red(f"tools/call failed: {e}")
                else:
                    print("  SKIP  tools/call (APIFY_TOKEN未設定)")
    except Exception as e:
        red(f"connection failed: {e}")
        return 1

    print("──────────────────────────────────────────")
    print(f"Results: {PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
