#!/usr/bin/env python3
"""
stdio entry point for japan-market-mcp (MCPB bundle / local mode).

Usage:
  uv run --directory <repo_root> src/stdio_main.py
"""

from __future__ import annotations

import logging
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.server import get_server  # noqa: E402


def main() -> None:
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
    server = get_server()
    server.run()


if __name__ == "__main__":
    main()
