"""Generate WeChat tabBar icons (81×81 输出，28×28 图形区域，无四边留白)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

CANVAS = 81
ICON = 28
INACTIVE = (138, 126, 120, 255)
ACTIVE = (217, 75, 54, 255)
SCALE = 8

TAB_DIR = Path(__file__).resolve().parents[1] / "src" / "static" / "tab"


def render(draw_fn, color: tuple[int, int, int, int]) -> Image.Image:
    big = ICON * SCALE
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_fn(draw, 0, big, color)
    return img.resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)


def draw_home(draw: ImageDraw.ImageDraw, pad: int, size: int, color: tuple[int, int, int, int]) -> None:
    left, top = pad, pad
    right, bottom = pad + size, pad + size
    cx = left + size // 2
    roof_y = top + int(size * 0.12)
    body_top = top + int(size * 0.40)
    draw.polygon(
        [(cx, roof_y), (left + int(size * 0.12), body_top), (right - int(size * 0.12), body_top)],
        fill=color,
    )
    draw.rounded_rectangle(
        [left + int(size * 0.20), body_top, right - int(size * 0.20), bottom - int(size * 0.10)],
        radius=int(size * 0.08),
        fill=color,
    )


def draw_user(draw: ImageDraw.ImageDraw, pad: int, size: int, color: tuple[int, int, int, int]) -> None:
    cx = pad + size // 2
    top = pad + int(size * 0.08)
    head_r = int(size * 0.18)
    head_cy = top + head_r
    draw.ellipse(
        [cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r],
        fill=color,
    )
    shoulder_y = head_cy + head_r + int(size * 0.06)
    draw.pieslice(
        [
            cx - int(size * 0.38),
            shoulder_y - int(size * 0.10),
            cx + int(size * 0.38),
            shoulder_y + int(size * 0.52),
        ],
        start=200,
        end=-20,
        fill=color,
    )


def main() -> None:
    TAB_DIR.mkdir(parents=True, exist_ok=True)
    icons = [
        ("sfire.png", draw_home, INACTIVE),
        ("sfire-active.png", draw_home, ACTIVE),
        ("mine.png", draw_user, INACTIVE),
        ("mine-active.png", draw_user, ACTIVE),
        ("home.png", draw_home, INACTIVE),
        ("home-active.png", draw_home, ACTIVE),
    ]
    for name, fn, color in icons:
        path = TAB_DIR / name
        im = render(fn, color)
        im.save(path, optimize=True)
        print(name, im.getbbox(), path.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
