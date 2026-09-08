import asyncio
from src.server import get_server

s = get_server()
tools = asyncio.run(s.list_tools())
print([t.name for t in tools])
