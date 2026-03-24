"""PDF del informe revenue desde JSON (ReportLab). Portada con franja oscura + marca."""
from __future__ import annotations

import io
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config import BASE_DIR

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
COVER_BG = colors.HexColor("#0a0a0a")
ACCENT = colors.HexColor("#f07e07")
TEXT = colors.HexColor("#171717")
MUTED = colors.HexColor("#5f5a53")


def _p(text: str, style) -> Paragraph:
    t = (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(t.replace("\n", "<br/>"), style)


def _badge(level: str) -> str:
    if level == "high":
        return "Alto"
    if level == "low":
        return "Bajo"
    return "Medio"


def _logo_path_dark_bg() -> str | None:
    p = BASE_DIR / "static" / "branding" / "revenue-report" / "logo-for-dark-bg.png"
    if p.is_file():
        return str(p)
    p2 = BASE_DIR / "static" / "branding" / "dragonne-wordmark.png"
    return str(p2) if p2.is_file() else None


def build_revenue_pdf_bytes(report: Dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "T", parent=styles["Heading1"], fontSize=14, textColor=TEXT, spaceAfter=6, fontName="Helvetica-Bold"
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=ACCENT,
        spaceBefore=12,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    body = ParagraphStyle("B", parent=styles["Normal"], fontSize=9, textColor=TEXT, leading=12)
    small = ParagraphStyle("S", parent=styles["Normal"], fontSize=8, textColor=MUTED, leading=11)

    cov = report.get("cover") or {}
    band_h = 78 * mm

    def on_first(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(COVER_BG)
        canvas.rect(0, PAGE_H - band_h, PAGE_W, band_h, fill=1, stroke=0)
        lp = _logo_path_dark_bg()
        if lp:
            try:
                canvas.drawImage(lp, MARGIN, PAGE_H - band_h + 42 * mm, width=48 * mm, height=11 * mm, mask="auto")
            except Exception:
                canvas.setFillColor(ACCENT)
                canvas.setFont("Helvetica-Bold", 14)
                canvas.drawString(MARGIN, PAGE_H - 28 * mm, "DRAGONNÉ")
        else:
            canvas.setFillColor(ACCENT)
            canvas.setFont("Helvetica-Bold", 14)
            canvas.drawString(MARGIN, PAGE_H - 28 * mm, "DRAGONNÉ")
        canvas.setFillColor(ACCENT)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(MARGIN, PAGE_H - band_h + 38 * mm, "DIAGNÓSTICO EJECUTIVO")
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 15)
        y = PAGE_H - band_h + 22 * mm
        canvas.drawString(MARGIN, y, (cov.get("report_title") or "Informe")[:72])
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#a8a29e"))
        y -= 14
        canvas.drawString(MARGIN, y, f"Periodo: {cov.get('period_label', '—')}")
        y -= 12
        canvas.drawString(MARGIN, y, f"Fecha: {cov.get('report_date', '—')}  ·  {cov.get('prepared_by', 'Dragonné')}")
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawString(MARGIN, PAGE_H - band_h + 6 * mm, cov.get("hotel_name") or "Hotel")
        canvas.restoreState()

    def on_later(canvas, doc):
        canvas.saveState()
        lp = BASE_DIR / "static" / "branding" / "revenue-report" / "logo-for-light-bg.png"
        if not lp.is_file():
            lp = BASE_DIR / "static" / "branding" / "dragonne-wordmark.png"
        if lp.is_file():
            try:
                canvas.drawImage(str(lp), MARGIN, PAGE_H - MARGIN - 2, width=34 * mm, height=7 * mm, mask="auto")
            except Exception:
                canvas.setFillColor(TEXT)
                canvas.setFont("Helvetica-Bold", 10)
                canvas.drawString(MARGIN, PAGE_H - MARGIN, "DRAGONNÉ")
        canvas.setStrokeColor(ACCENT)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, PAGE_H - MARGIN - 4, PAGE_W - MARGIN, PAGE_H - MARGIN - 4)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN, MARGIN - 8, f"{cov.get('hotel_name', '')} · {cov.get('report_date', '')}")
        canvas.drawRightString(PAGE_W - MARGIN, MARGIN - 8, "DRAGONNÉ")
        canvas.restoreState()

    # Margen superior deja libre la franja de portada (solo pág. 1); siguientes páginas comparten el mismo frame.
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=MARGIN,
        leftMargin=MARGIN,
        topMargin=band_h + 10 * mm,
        bottomMargin=MARGIN + 6 * mm,
    )

    story: List[Any] = []

    story.append(Paragraph("Resumen ejecutivo", h2_style))
    story.append(_p(report.get("executive_summary") or "—", body))
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("Hallazgos clave", h2_style))
    for f in report.get("key_findings") or []:
        story.append(
            Paragraph(
                f'<b>{f.get("title", "")}</b> &nbsp; <font color="#b45309">[Impacto {_badge(f.get("impact", ""))}]</font>',
                body,
            )
        )
        story.append(_p(f"Diagnóstico: {f.get('diagnosis', '')}", small))
        story.append(_p(f"Implicación: {f.get('business_implication', '')}", small))
        story.append(_p(f"Acción: {f.get('recommended_action', '')}", small))
        story.append(Spacer(1, 3 * mm))

    story.append(Paragraph("Anomalías", h2_style))
    an = report.get("anomalies") or []
    if not an:
        story.append(_p("Sin anomalías destacadas.", small))
    else:
        for a in an:
            story.append(
                Paragraph(
                    f'<b>{a.get("title", "")}</b> &nbsp; <font color="#b45309">[Severidad {_badge(a.get("severity", ""))}]</font>',
                    body,
                )
            )
            story.append(_p(a.get("what_happened", ""), small))
            story.append(_p(a.get("why_it_matters", ""), small))
            story.append(_p(a.get("recommended_action", ""), small))
            story.append(Spacer(1, 3 * mm))

    story.append(Paragraph("Métricas", h2_style))
    rows: List[List[Any]] = [["Métrica", "Valor", "Lectura", "Atención"]]
    for k in report.get("kpi_table") or []:
        rows.append(
            [
                k.get("metric", ""),
                k.get("value", ""),
                k.get("executive_read", ""),
                _badge(k.get("attention_level", "")),
            ]
        )
    t = Table(rows, colWidths=[38 * mm, 22 * mm, 85 * mm, 22 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#211f1d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d8cfc2")),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf8f5")]),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("Recomendaciones estratégicas", h2_style))
    for r in report.get("strategic_recommendations") or []:
        story.append(
            Paragraph(
                f'<b>{r.get("title", "")}</b> &nbsp; <font color="#b45309">[Prioridad {_badge(r.get("priority", ""))}]</font>',
                body,
            )
        )
        story.append(_p(r.get("action", ""), small))
        story.append(_p(f"Impacto esperado: {r.get('expected_impact', '')}", small))
        story.append(Spacer(1, 3 * mm))

    story.append(Paragraph("Plan 30 · 60 · 90 días", h2_style))
    plan = report.get("plan_30_60_90") or {}
    prows = [
        [
            "\n".join(f"• {x}" for x in (plan.get("days_30") or [])[:10]) or "—",
            "\n".join(f"• {x}" for x in (plan.get("days_60") or [])[:10]) or "—",
            "\n".join(f"• {x}" for x in (plan.get("days_90") or [])[:10]) or "—",
        ]
    ]
    pt = Table([["30 días", "60 días", "90 días"], *prows], colWidths=[52 * mm, 52 * mm, 52 * mm])
    pt.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d8cfc2")),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(pt)
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("Reportes adicionales recomendados", h2_style))
    for ar in report.get("additional_reports_needed") or []:
        story.append(Paragraph(f"<b>{ar.get('report_name', '')}</b>", body))
        story.append(_p(ar.get("why_it_is_needed", ""), small))
        story.append(Spacer(1, 2 * mm))

    story.append(Paragraph("Siguientes pasos", h2_style))
    for s in report.get("next_steps") or []:
        story.append(_p(f"• {s}", body))

    story.append(Spacer(1, 8 * mm))
    story.append(
        _p(
            "Contenido generado con apoyo de IA a partir de los exports cargados. Validar decisiones con equipo comercial y revenue.",
            small,
        )
    )

    doc.build(story, onFirstPage=on_first, onLaterPages=on_later)
    buffer.seek(0)
    return buffer.read()
