#!/usr/bin/env python3
"""Generate a 400x400 PNG logo for the Japan Market MCP server (Cline marketplace icon)."""
from PIL import Image, ImageDraw, ImageFont
import os

SIZE = 400
OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "logo.png")

img = Image.new("RGB", (SIZE, SIZE), "#101828")
d = ImageDraw.Draw(img)

# Rounded-square accent panel
d.rounded_rectangle([70, 80, 330, 320], radius=24, fill="#1D2939", outline="#7C3AED", width=4)

# Price-bar glyph: three ascending bars (upward trend / cross-shop comparison)
bars = [(150, 210), (190, 190), (230, 230), (270, 160)]
for i, (x, y) in enumerate(bars):
    h = 320 - y
    color = ["#F59E0B", "#22C55E", "#3B82F6", "#7C3AED"][i]
    d.rounded_rectangle([x, y, x + 14, y + h], radius=4, fill=color)

# "JAPAN MARKET" label + MCP tag
try:
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
    font_sm = ImageFont.truetype("DejaVuSans-Bold.ttf", 16)
except Exception:
    font = ImageFont.load_default()
    font_sm = font

d.text((200, 40), "JAPAN", font=font, fill="#F2F4F7", anchor="mm")
d.text((200, 70), "MARKET", font=font, fill="#F2F4F7", anchor="mm")
d.rounded_rectangle([150, 340, 250, 368], radius=14, fill="#7C3AED")
d.text((200, 354), "MCP", font=font_sm, fill="#FFFFFF", anchor="mm")

out_abs = os.path.abspath(OUT)
os.makedirs(os.path.dirname(out_abs), exist_ok=True)
img.save(out_abs, "PNG")
print("wrote", out_abs, os.path.getsize(out_abs), "bytes")
