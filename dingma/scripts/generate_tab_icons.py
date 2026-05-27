"""Generate WeChat tabBar icons from Lucide SVG assets (81×81 canvas, 28×28 glyph)."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ICONS_DIR = ROOT / "src" / "static" / "icons"
TAB_DIR = ROOT / "src" / "static" / "tab"

CANVAS = 81
ICON = 28
INACTIVE = (138, 126, 120, 255)
ACTIVE = (217, 75, 54, 255)
SCALE = 8


def load_svg_paths(icon_name: str) -> list[tuple[str, str]]:
    """Parse Lucide SVG into (tag, d-or-attrs) tuples for rasterization."""
    svg_path = ICONS_DIR / f"{icon_name}.svg"
    text = svg_path.read_text(encoding="utf-8")
    root = ET.fromstring(text)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    items: list[tuple[str, str]] = []
    for el in root.findall(".//svg:*", ns):
        tag = el.tag.split("}")[-1]
        if tag == "path":
            d = el.get("d")
            if d:
                items.append(("path", d))
        elif tag == "circle":
            cx, cy, r = el.get("cx"), el.get("cy"), el.get("r")
            if cx and cy and r:
                items.append(("circle", f"{cx},{cy},{r}"))
    return items


def _scale_point(x: float, y: float, pad: int, size: int) -> tuple[float, float]:
    sx = pad + (x / 24.0) * size
    sy = pad + (y / 24.0) * size
    return sx, sy


def _draw_path(draw: ImageDraw.ImageDraw, d: str, pad: int, size: int, color: tuple[int, int, int, int], width: int) -> None:
    tokens = re.findall(r"([MLHVCSQTAZmlhvcsqtaz])|(-?\d*\.?\d+)", d)
    idx = 0
    cur_x, cur_y = 0.0, 0.0
    start_x, start_y = 0.0, 0.0
    points: list[tuple[float, float]] = []

    def read_num() -> float:
        nonlocal idx
        while idx < len(tokens):
            cmd, num = tokens[idx]
            idx += 1
            if num:
                return float(num)
        return 0.0

    while idx < len(tokens):
        cmd, _ = tokens[idx]
        if not cmd:
            idx += 1
            continue
        idx += 1
        upper = cmd.upper()
        rel = cmd.islower()

        if upper == "M":
            x, y = read_num(), read_num()
            if rel:
                cur_x += x
                cur_y += y
            else:
                cur_x, cur_y = x, y
            start_x, start_y = cur_x, cur_y
            points = [_scale_point(cur_x, cur_y, pad, size)]
        elif upper == "L":
            x, y = read_num(), read_num()
            if rel:
                cur_x += x
                cur_y += y
            else:
                cur_x, cur_y = x, y
            points.append(_scale_point(cur_x, cur_y, pad, size))
        elif upper == "H":
            x = read_num()
            cur_x = cur_x + x if rel else x
            points.append(_scale_point(cur_x, cur_y, pad, size))
        elif upper == "V":
            y = read_num()
            cur_y = cur_y + y if rel else y
            points.append(_scale_point(cur_x, cur_y, pad, size))
        elif upper == "C":
            x1, y1 = read_num(), read_num()
            x2, y2 = read_num(), read_num()
            x, y = read_num(), read_num()
            if rel:
                x1 += cur_x
                y1 += cur_y
                x2 += cur_x
                y2 += cur_y
                x += cur_x
                y += cur_y
            p1 = _scale_point(x1, y1, pad, size)
            p2 = _scale_point(x2, y2, pad, size)
            p3 = _scale_point(x, y, pad, size)
            draw.line([points[-1], p1], fill=color, width=width)
            draw.line([p1, p2], fill=color, width=width)
            draw.line([p2, p3], fill=color, width=width)
            cur_x, cur_y = x, y
            points.append(p3)
        elif upper == "A":
            read_num()
            read_num()
            read_num()
            read_num()
            read_num()
            x, y = read_num(), read_num()
            if rel:
                cur_x += x
                cur_y += y
            else:
                cur_x, cur_y = x, y
            points.append(_scale_point(cur_x, cur_y, pad, size))
        elif upper == "Z":
            if len(points) > 1:
                draw.line([points[-1], points[0]], fill=color, width=width)
            cur_x, cur_y = start_x, start_y

    if len(points) > 1:
        for i in range(1, len(points)):
            draw.line([points[i - 1], points[i]], fill=color, width=width)


def render_lucide(icon_name: str, color: tuple[int, int, int, int]) -> Image.Image:
    big = ICON * SCALE
    pad = 0
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    stroke = max(2, SCALE // 2)

    for tag, data in load_svg_paths(icon_name):
        if tag == "path":
            _draw_path(draw, data, pad, big, color, stroke)
        elif tag == "circle":
            cx, cy, r = (float(v) for v in data.split(","))
            sx, sy = _scale_point(cx, cy, pad, big)
            sr = (float(r) / 24.0) * big
            draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], outline=color, width=max(1, stroke // 2))

    return img.resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)


def main() -> None:
    TAB_DIR.mkdir(parents=True, exist_ok=True)
    icons = [
        ("sfire.png", "user-round-cog", INACTIVE),
        ("sfire-active.png", "user-round-cog", ACTIVE),
        ("home.png", "user-round-cog", INACTIVE),
        ("home-active.png", "user-round-cog", ACTIVE),
        ("mine.png", "user", INACTIVE),
        ("mine-active.png", "user", ACTIVE),
    ]
    for name, lucide_key, color in icons:
        path = TAB_DIR / name
        im = render_lucide(lucide_key, color)
        im.save(path, optimize=True)
        print(name, im.getbbox(), path.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
