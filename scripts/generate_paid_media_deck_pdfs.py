"""
Genera PDFs estáticos para el deck de Paid Media Management (ES/EN).

Motivo: el botón "Descargar PDF" debe bajar un PDF del deck, no una propuesta por hotel/caso.
Esto mantiene el patrón de las otras landings que apuntan a `static/exports/*.pdf`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

import sys

# Permite importar módulos del root del repo al ejecutar desde /scripts.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from paid_media_package_deck_i18n import get_paid_media_package_deck_copy  # noqa: E402


# El resto de los decks descargables de hospitality están diseñados “tipo slides”.
# Para que Paid Media se sienta igual de “deck”, usamos A4 horizontal.
PAGE_W, PAGE_H = landscape(A4)
MARGIN_X = 64
MARGIN_Y = 56

INK = HexColor("#121110")
MUTED = HexColor("#5c6169")
PAPER = HexColor("#fbfbfc")
DARK = HexColor("#0c0c0e")
RULE = HexColor("#e6e7ea")
ACCENT = HexColor("#f07e07")


def _wrap(text: str, font: str, size: int, max_w: float) -> list[str]:
    words = (text or "").replace("\u2014", "-").split()
    lines: list[str] = []
    current: list[str] = []
    for w in words:
        trial = " ".join(current + [w]).strip()
        if trial and stringWidth(trial, font, size) > max_w and current:
            lines.append(" ".join(current))
            current = [w]
        else:
            current.append(w)
    if current:
        lines.append(" ".join(current))
    return lines


def _draw_brand(c: canvas.Canvas, *, dark: bool, lang: str, page_title: str) -> None:
    # Top rule + brand
    if dark:
        c.setFillColor(DARK)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        c.setStrokeColor(HexColor("#2a2a2f"))
        c.setFillColor(HexColor("#ffffff"))
    else:
        c.setFillColor(PAPER)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        c.setStrokeColor(RULE)
        c.setFillColor(INK)
    c.setLineWidth(1)
    c.line(MARGIN_X, PAGE_H - 44, PAGE_W - MARGIN_X, PAGE_H - 44)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(MARGIN_X, PAGE_H - 32, "DRAGONNÉ")
    c.setFont("Helvetica", 9.5)
    c.setFillColor(ACCENT)
    c.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 32, page_title)
    c.setFillColor(HexColor("#ffffff") if dark else INK)
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor("#9aa0a6") if dark else MUTED)
    c.drawString(MARGIN_X, 32, "dragonne.co")
    c.drawRightString(PAGE_W - MARGIN_X, 32, "ES" if lang == "es" else "EN")


def _draw_slide(
    c: canvas.Canvas,
    *,
    lang: str,
    slide: dict[str, Any],
    idx: int,
    total: int,
) -> None:
    variant = (slide.get("variant") or "light").strip()
    dark = variant in ("dark", "services", "hero")
    page_title = "Paid Media Management"
    _draw_brand(c, dark=dark, lang=lang, page_title=page_title)

    x = MARGIN_X
    y = PAGE_H - 96
    max_w = PAGE_W - 2 * MARGIN_X

    # Step badge (if present)
    step = slide.get("step")
    if step:
        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 9)
        c.roundRect(x, y, 34, 22, 8, fill=1, stroke=0)
        c.setFillColor(HexColor("#0c0c0e"))
        c.drawCentredString(x + 17, y + 6.5, f"{int(step):02d}")
        y -= 34

    # Kicker
    kicker = slide.get("kicker") or ""
    if kicker:
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(ACCENT)
        c.drawString(x, y, kicker.upper())
        y -= 18

    # Title
    title_lines = slide.get("title_lines")
    title = slide.get("title")
    lines: list[str] = []
    if isinstance(title_lines, list) and title_lines:
        lines = [str(t) for t in title_lines]
    elif title:
        lines = _wrap(str(title), "Helvetica-Bold", 26, max_w)

    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(HexColor("#ffffff") if dark else INK)
    for tl in lines[:4]:
        c.drawString(x, y, tl)
        y -= 32
    y -= 6

    # Lead/body
    lead = slide.get("lead") or ""
    body = slide.get("body") or ""
    if lead:
        c.setFont("Helvetica", 12)
        c.setFillColor(HexColor("#d8dbe2") if dark else MUTED)
        for ln in _wrap(str(lead), "Helvetica", 12, max_w)[:6]:
            c.drawString(x, y, ln)
            y -= 18
        y -= 8
    if body:
        c.setFont("Helvetica", 11)
        c.setFillColor(HexColor("#c8ccd6") if dark else MUTED)
        for ln in _wrap(str(body), "Helvetica", 11, max_w)[:10]:
            c.drawString(x, y, ln)
            y -= 16
        y -= 10

    # Bullets (high-level cards)
    bullets = slide.get("bullets")
    if isinstance(bullets, list) and bullets and isinstance(bullets[0], dict):
        card_w = (max_w - 18) / 2
        card_h = 96
        cx, cy = x, y
        for i, b in enumerate(bullets[:4]):
            if i == 2:
                cx = x
                cy -= card_h + 14
            elif i == 1:
                cx = x + card_w + 18
            elif i == 3:
                cx = x + card_w + 18
            if dark:
                c.setFillColor(HexColor("#14141a"))
                c.setStrokeColor(HexColor("#2a2a2f"))
            else:
                c.setFillColor(HexColor("#ffffff"))
                c.setStrokeColor(RULE)
            c.roundRect(cx, cy - card_h, card_w, card_h, 14, fill=1, stroke=1)
            c.setFillColor(ACCENT)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(cx + 14, cy - 22, str(b.get("title", ""))[:56])
            c.setFillColor(HexColor("#d8dbe2") if dark else MUTED)
            c.setFont("Helvetica", 9.5)
            tx = str(b.get("text", ""))
            ty = cy - 40
            for ln in _wrap(tx, "Helvetica", 9.5, card_w - 28)[:4]:
                c.drawString(cx + 14, ty, ln)
                ty -= 13
        y = cy - card_h - 18

    # Footer page counter
    c.setFillColor(HexColor("#9aa0a6") if dark else MUTED)
    c.setFont("Helvetica", 8)
    c.drawRightString(PAGE_W - MARGIN_X, 32, f"{idx}/{total}")


def generate(lang: str, out_path: Path) -> None:
    deck = get_paid_media_package_deck_copy(lang)
    slides = list(deck.get("slides") or [])
    # omit "lead" (form) slide from PDF export
    slides = [s for s in slides if (s or {}).get("variant") != "lead"]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_path), pagesize=(PAGE_W, PAGE_H))
    for i, s in enumerate(slides, start=1):
        _draw_slide(c, lang=lang, slide=s, idx=i, total=len(slides))
        c.showPage()
    c.save()


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    exports = root / "static" / "exports"
    generate("es", exports / "Dragonne-paid-media-management-ES.pdf")
    generate("en", exports / "Dragonne-paid-media-management-EN.pdf")


if __name__ == "__main__":
    main()

