#!/usr/bin/env python3
"""Genera imágenes Open Graph 1200×630 (Facebook, LinkedIn, X, WhatsApp) con branding DRAGONNÉ / Pullso.

Ejecutar desde la raíz del repo:
  python3 scripts/generate_og_social_preview.py
Requiere Pillow (`pip install pillow`).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "static" / "branding"
OUT_DIR = BRAND
ISOTIPO = BRAND / "dragonne-isotipo.png"
PULLSO_LOGO = BRAND / "pullso-logo.png"
FONT_PATH = ROOT / "static" / "fonts" / "Inter-Variable.ttf"

W, H = 1200, 630
BG = (249, 249, 249)
GRID = (234, 232, 229)
ACCENT_GOLD = (246, 169, 5)
ACCENT_ORANGE = (240, 126, 7)
PULLSO_ORANGE = (240, 126, 7)
TEXT_MUTED = (80, 78, 76)
TEXT_DARK = (28, 28, 30)
HERO_H1_MAX_CH = 14


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
    d.ellipse((80, -40, W - 80, H + 60), fill=(255, 210, 170, 14))
    rgb = base.convert("RGBA")
    return Image.alpha_composite(rgb, overlay).convert("RGB")


def punch_up_isotipo(iso: Image.Image) -> Image.Image:
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


def wrap_words_to_width(text: str, font: ImageFont.FreeTypeFont, max_width: float) -> list[str]:
    words = (text or "").split()
    if not words:
        return []
    lines: list[str] = []
    cur: list[str] = []
    for w in words:
        test = (" ".join(cur + [w])).strip()
        if not cur or font.getlength(test) <= max_width:
            cur.append(w)
        else:
            lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines


def _load_font(size: int, variation: str) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(FONT_PATH), size)
    try:
        font.set_variation_by_name(variation)
    except OSError:
        try:
            font.set_variation_by_name("Bold" if variation == "ExtraBold" else variation)
        except OSError:
            pass
    return font


@dataclass(frozen=True)
class OgCardSpec:
    filename: str
    kicker: str
    title_lines: tuple[str, ...]
    variant: str  # "dragonne" | "pullso"


def _fit_title_lines(
    lines: tuple[str, ...],
    max_width: float,
    sizes: tuple[int, ...] = (58, 52, 46, 40),
) -> tuple[int, list[str]]:
    flat = " ".join(lines) if len(lines) == 1 else "\n".join(lines)
    if "\n" in flat:
        parts = [p.strip() for p in flat.split("\n") if p.strip()]
    else:
        parts = list(lines)

    for size in sizes:
        font = _load_font(size, "ExtraBold")
        out: list[str] = []
        for p in parts:
            wrapped = wrap_words_to_width(p, font, max_width) if " " in p else ([p] if p else [])
            out.extend(wrapped)
        if len(out) <= 4:
            return size, out
    font = _load_font(sizes[-1], "ExtraBold")
    out = []
    for p in parts:
        out.extend(wrap_words_to_width(p, font, max_width))
    return sizes[-1], out[:4]


def render_card(spec: OgCardSpec) -> None:
    if not FONT_PATH.is_file():
        raise SystemExit(f"Falta la fuente: {FONT_PATH}")

    img = Image.new("RGB", (W, H), BG)
    draw_grid(img)
    img = subtle_center_glow(img)

    max_text_width = W - 160
    title_size, title_lines = _fit_title_lines(spec.title_lines, max_text_width)
    title_font = _load_font(title_size, "ExtraBold")
    kicker_font = _load_font(22, "SemiBold")
    footer_font = _load_font(17, "Medium")

    tracking = -0.8
    line_spacing = 8
    line_heights: list[int] = []
    line_widths: list[float] = []
    for line in title_lines:
        line_widths.append(line_width(title_font, line, tracking))
        bbox = title_font.getbbox(line)
        line_heights.append(bbox[3] - bbox[1])

    text_block_h = sum(line_heights) + line_spacing * (max(0, len(title_lines) - 1))
    kicker_h = int(kicker_font.getbbox(spec.kicker)[3] - kicker_font.getbbox(spec.kicker)[1]) if spec.kicker else 0
    gap_kicker = 18 if spec.kicker else 0
    gap_logo_text = 26

    if spec.variant == "pullso":
        if not PULLSO_LOGO.is_file():
            raise SystemExit(f"Falta logo Pullso: {PULLSO_LOGO}")
        logo = Image.open(PULLSO_LOGO).convert("RGBA")
        logo_target_h = 72
        ratio = logo_target_h / logo.height
        logo_w = int(logo.width * ratio)
        logo = logo.resize((logo_w, logo_target_h), Image.Resampling.LANCZOS)
        logo_x = (W - logo_w) / 2
    else:
        if not ISOTIPO.is_file():
            raise SystemExit(f"Falta el isotipo: {ISOTIPO}")
        iso = Image.open(ISOTIPO).convert("RGBA")
        iso = punch_up_isotipo(iso)
        iso_target_h = 132
        ratio = iso_target_h / iso.height
        iso_w = int(iso.width * ratio)
        logo = iso.resize((iso_w, iso_target_h), Image.Resampling.LANCZOS)
        logo_x = (W - logo.width) / 2

    logo_h = logo.height
    stack_h = logo_h + gap_logo_text + (kicker_h + gap_kicker if spec.kicker else 0) + text_block_h + 36 + 22
    y0 = max(36, (H - stack_h) / 2)

    if spec.variant == "pullso":
        img.paste(logo, (int(logo_x), int(y0)), logo)
    else:
        img.paste(logo, (int(logo_x), int(y0)), logo)

    draw = ImageDraw.Draw(img)
    y = y0 + logo_h + gap_logo_text
    if spec.kicker:
        kw = kicker_font.getlength(spec.kicker)
        kx = (W - kw) / 2
        k_color = PULLSO_ORANGE if spec.variant == "pullso" else TEXT_MUTED
        draw.text((kx, y), spec.kicker, font=kicker_font, fill=k_color)
        y += kicker_h + gap_kicker

    ch_unit = title_font.getlength("0")
    grad_w = HERO_H1_MAX_CH * ch_unit
    grad_left = (W - grad_w) / 2

    for i, line in enumerate(title_lines):
        lw = line_widths[i]
        x = (W - lw) / 2
        if spec.variant == "pullso":
            draw.text((x, y), line, font=title_font, fill=TEXT_DARK)
        else:
            draw_tracking_text_brand_gradient(
                draw,
                (x, y),
                line,
                title_font,
                tracking,
                grad_left,
                grad_w,
                ACCENT_GOLD,
                ACCENT_ORANGE,
            )
        y += line_heights[i] + line_spacing

    footer = "dragonne.co"
    fw = footer_font.getlength(footer)
    draw.text(((W - fw) / 2, H - 52), footer, font=footer_font, fill=(150, 148, 145))

    out = OUT_DIR / spec.filename
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True, compress_level=9)
    print(f"Escrito: {out} ({out.stat().st_size // 1024} KB)")


def main() -> None:
    cards: list[OgCardSpec] = [
        OgCardSpec(
            "og-social-preview.png",
            "DRAGONNÉ",
            (
                "We connect your",
                "vision with the talent",
                "that makes it real",
            ),
            "dragonne",
        ),
        OgCardSpec(
            "og-hospitality-fractional-rm-es.png",
            "Hospitalidad · DRAGONNÉ",
            ("Revenue Management fraccional", "para hoteles"),
            "dragonne",
        ),
        OgCardSpec(
            "og-hospitality-fractional-rm-en.png",
            "Hospitality · DRAGONNÉ",
            ("Fractional Revenue Management", "for hotels"),
            "dragonne",
        ),
        OgCardSpec(
            "og-hospitality-deck-es.png",
            "Presentación comercial · DRAGONNÉ",
            ("El reto del hotel independiente",),
            "dragonne",
        ),
        OgCardSpec(
            "og-hospitality-deck-en.png",
            "Commercial deck · DRAGONNÉ",
            ("The independent hotel challenge",),
            "dragonne",
        ),
        OgCardSpec(
            "og-hospitality-vertical-es.png",
            "Consultoría · DRAGONNÉ",
            ("Hospitalidad", "independientes y boutique"),
            "dragonne",
        ),
        OgCardSpec(
            "og-hospitality-vertical-en.png",
            "Consulting · DRAGONNÉ",
            ("Hospitality", "independent & boutique hotels"),
            "dragonne",
        ),
        OgCardSpec(
            "og-hospitality-diagnosis-es.png",
            "Hospitalidad · DRAGONNÉ",
            ("Diagnóstico inicial", "de posicionamiento online"),
            "dragonne",
        ),
        OgCardSpec(
            "og-hospitality-diagnosis-en.png",
            "Hospitality · DRAGONNÉ",
            ("Initial online positioning", "diagnosis for your hotel"),
            "dragonne",
        ),
        OgCardSpec(
            "og-social-media-management-es.png",
            "Hospitalidad · DRAGONNÉ",
            ("Social Media Management", "& Content Creation"),
            "dragonne",
        ),
        OgCardSpec(
            "og-social-media-management-en.png",
            "Hospitality · DRAGONNÉ",
            ("Social Media Management", "& Content Creation"),
            "dragonne",
        ),
        OgCardSpec(
            "og-pullso.png",
            "Producto hotelero",
            ("Pullso by DRAGONNÉ", "Inteligencia de revenue para equipos"),
            "pullso",
        ),
        OgCardSpec(
            "og-pullso-demo.png",
            "Pullso · DRAGONNÉ",
            ("Demo del analizador", "KPIs y lectura comercial"),
            "pullso",
        ),
        OgCardSpec(
            "og-corporate-misc.png",
            "DRAGONNÉ",
            ("Consultoría estratégica", "y producto Pullso"),
            "dragonne",
        ),
        OgCardSpec(
            "og-vertical-startups-es.png",
            "Consultoría · DRAGONNÉ",
            ("Startups", "prioridades, producto y crecimiento"),
            "dragonne",
        ),
        OgCardSpec(
            "og-vertical-startups-en.png",
            "Consulting · DRAGONNÉ",
            ("Startups", "priorities, product and growth"),
            "dragonne",
        ),
        OgCardSpec(
            "og-vertical-smbs-es.png",
            "Consultoría · DRAGONNÉ",
            ("SMBs y pymes", "operación, tecnología y margen"),
            "dragonne",
        ),
        OgCardSpec(
            "og-vertical-smbs-en.png",
            "Consulting · DRAGONNÉ",
            ("SMBs", "operations, technology and margin"),
            "dragonne",
        ),
        OgCardSpec(
            "og-vertical-medios-es.png",
            "DRAGONNÉ",
            ("Posicionamiento en medios", "para marcas y ejecutivos"),
            "dragonne",
        ),
        OgCardSpec(
            "og-vertical-medios-en.png",
            "DRAGONNÉ",
            ("Media positioning", "for brands and executives"),
            "dragonne",
        ),
        OgCardSpec(
            "og-pullso-brief.png",
            "Pullso Brief · DRAGONNÉ",
            ("Lectura comercial", "donde el equipo sí responde"),
            "pullso",
        ),
        OgCardSpec(
            "og-pullso-mvp.png",
            "Pullso · DRAGONNÉ",
            ("Analista de revenue", "con IA para hoteles"),
            "pullso",
        ),
        OgCardSpec(
            "og-pullso-mvp-en.png",
            "Pullso · DRAGONNÉ",
            ("AI revenue analyst", "for hotels"),
            "pullso",
        ),
    ]

    for c in cards:
        render_card(c)


if __name__ == "__main__":
    main()
