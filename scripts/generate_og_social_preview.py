#!/usr/bin/env python3
"""Genera la imagen Open Graph 1200x630 con isotipo, tipografía Inter e estilo del titular."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "static" / "branding" / "og-social-preview.png"
ISOTIPO = ROOT / "static" / "branding" / "dragonne-isotipo.png"
FONT_PATH = ROOT / "static" / "fonts" / "Inter-Variable.ttf"

W, H = 1200, 630
BG = (249, 249, 249)  # #F9F9F9
GRID = (234, 232, 229)  # cuadrícula un poco más cálida
# Igual que static/styles.css (--accent-primary / --accent-primary-strong) y que
# templates/consulting.html → .cp-hero h1:
#   linear-gradient(90deg, var(--accent-gold), var(--accent));
#   max-width: 14ch; background-clip: text;
ACCENT_GOLD = (246, 169, 5)  # #F6A905
ACCENT_ORANGE = (240, 126, 7)  # #F07E07
HERO_H1_MAX_CH = 14  # .cp-hero h1 { max-width: 14ch; }

LINES = [
    "We connect your",
    "vision with the talent",
    "that makes it real",
]


def draw_grid(img: Image.Image, step: int = 32) -> None:
    draw = ImageDraw.Draw(img)
    for x in range(0, W + 1, step):
        draw.line([(x, 0), (x, H)], fill=GRID, width=1)
    for y in range(0, H + 1, step):
        draw.line([(0, y), (W, y)], fill=GRID, width=1)


def subtle_center_glow(base: Image.Image) -> Image.Image:
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.ellipse((-120, -80, W + 120, H + 80), fill=(255, 255, 255, 45))
    # Velo cálido muy suave al centro para dar sensación de “más vivo”
    d.ellipse((80, -40, W - 80, H + 60), fill=(255, 210, 170, 14))
    rgb = base.convert("RGBA")
    return Image.alpha_composite(rgb, overlay).convert("RGB")


def punch_up_isotipo(iso: Image.Image) -> Image.Image:
    """Más saturación y contraste en el PNG del isotipo."""
    iso = ImageEnhance.Color(iso).enhance(1.28)
    iso = ImageEnhance.Contrast(iso).enhance(1.06)
    return iso


def _lerp_rgb(t: float, a: tuple[int, int, int], b: tuple[int, int, int]) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def draw_tracking_text_brand_gradient(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    font: ImageFont.FreeTypeFont,
    tracking: float,
    grad_left: float,
    grad_width: float,
    left_rgb: tuple[int, int, int],
    right_rgb: tuple[int, int, int],
) -> None:
    """Mismo criterio que .cp-hero h1: degradado horizontal oro → naranja."""
    x, y = xy
    gw = max(grad_width, 1.0)
    for i, ch in enumerate(text):
        half = font.getlength(ch) / 2
        t = (x + half - grad_left) / gw
        fill = _lerp_rgb(t, left_rgb, right_rgb)
        draw.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch)
        if i < len(text) - 1:
            x += tracking


def line_width(font: ImageFont.FreeTypeFont, line: str, tracking: float) -> float:
    if not line:
        return 0.0
    w = 0.0
    for i, ch in enumerate(line):
        w += font.getlength(ch)
        if i < len(line) - 1:
            w += tracking
    return w


def main() -> None:
    if not FONT_PATH.is_file():
        raise SystemExit(f"Falta la fuente: {FONT_PATH}")
    if not ISOTIPO.is_file():
        raise SystemExit(f"Falta el isotipo: {ISOTIPO}")

    img = Image.new("RGB", (W, H), BG)
    draw_grid(img)
    img = subtle_center_glow(img)

    # Escala mayor = encuadre “más de cerca” como en el screenshot de referencia
    font_size = 76
    font = ImageFont.truetype(str(FONT_PATH), font_size)
    try:
        font.set_variation_by_name("ExtraBold")
    except OSError:
        font.set_variation_by_name("Bold")
    tracking = -1.1

    line_spacing = 6
    line_heights = []
    line_widths = []
    for line in LINES:
        line_widths.append(line_width(font, line, tracking))
        bbox = font.getbbox(line)
        line_heights.append(bbox[3] - bbox[1])

    text_block_h = sum(line_heights) + line_spacing * (len(LINES) - 1)
    # Ancho del degradé = 14ch (como el bloque del h1 en web), centrado en el lienzo
    ch_unit = font.getlength("0")
    grad_w = HERO_H1_MAX_CH * ch_unit
    grad_left = (W - grad_w) / 2

    iso = Image.open(ISOTIPO).convert("RGBA")
    iso = punch_up_isotipo(iso)
    iso_target_h = 142
    ratio = iso_target_h / iso.height
    iso_w = int(iso.width * ratio)
    iso = iso.resize((iso_w, iso_target_h), Image.Resampling.LANCZOS)

    gap_logo_text = 28
    stack_h = iso_target_h + gap_logo_text + text_block_h
    y0 = (H - stack_h) / 2

    iso_x = (W - iso_w) / 2
    img.paste(iso, (int(iso_x), int(y0)), iso)

    text_top = y0 + iso_target_h + gap_logo_text
    y = text_top
    for i, line in enumerate(LINES):
        lw = line_widths[i]
        x = (W - lw) / 2
        draw = ImageDraw.Draw(img)
        draw_tracking_text_brand_gradient(
            draw,
            (x, y),
            line,
            font,
            tracking,
            grad_left,
            grad_w,
            ACCENT_GOLD,
            ACCENT_ORANGE,
        )
        y += line_heights[i] + line_spacing

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True, compress_level=9)
    print(f"Escrito: {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
