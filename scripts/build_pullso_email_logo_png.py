#!/usr/bin/env python3
"""Genera static/branding/pullso-logo-email.png (RGBA) para correos: wordmark + isotipo, sin dependencias Cairo."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "static" / "branding" / "pullso-logo-email.png"
W, H = 440, 100
TEXT = "#343434"
ORANGE = (240, 126, 7)
ORANGE_HI = (246, 169, 5)
RING_GRAY = (230, 230, 230)


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for p in candidates:
        fp = Path(p)
        if fp.is_file():
            try:
                return ImageFont.truetype(str(fp), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def build() -> None:
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    font = _load_font(44)
    text = "Pullso"
    bbox = dr.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    ty = (H - th) // 2 - bbox[1]
    tx = 28
    dr.text((tx, ty), text, font=font, fill=TEXT)

    cx, cy = int(tx + tw + 36), H // 2
    r_outer = 30
    r_white = 24
    r_orange = 15

    dr.ellipse(
        (cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer),
        fill=(255, 255, 255, 255),
        outline=RING_GRAY,
        width=2,
    )
    dr.ellipse(
        (cx - r_white, cy - r_white, cx + r_white, cy + r_white),
        fill=(255, 255, 255, 255),
    )
    for i in range(r_orange, 0, -1):
        t = i / r_orange
        c = (
            int(ORANGE_HI[0] * t + ORANGE[0] * (1 - t)),
            int(ORANGE_HI[1] * t + ORANGE[1] * (1 - t)),
            int(ORANGE_HI[2] * t + ORANGE[2] * (1 - t)),
            255,
        )
        dr.ellipse(
            (cx - i, cy - i, cx + i, cy + i),
            fill=c,
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    im.save(OUT, format="PNG", optimize=True)
    print("wrote", OUT, im.size)


if __name__ == "__main__":
    build()
