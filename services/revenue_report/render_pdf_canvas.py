"""PDF del informe revenue (ReportLab) — dirección editorial / memo boutique."""
from __future__ import annotations

import io
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config import BASE_DIR

from .display_util import derive_closing_strategic_implication, derive_executive_highlights
from .section_visibility import compute_revenue_report_sections, filter_executive_highlights

PAGE_W, PAGE_H = A4
MARGIN = 17 * mm
BOTTOM_EXTRA = 8 * mm

VOID = colors.HexColor("#0a0908")
VOID_MID = colors.HexColor("#121110")
ACCENT = colors.HexColor("#e07820")
INK = colors.HexColor("#121110")
INK_SOFT = colors.HexColor("#3d3a36")
MUTED = colors.HexColor("#6b6560")
PAPER = colors.HexColor("#faf7f2")
RULE = colors.HexColor("#d4cdc3")
RULE_HAIR = colors.HexColor("#ebe8e4")
SIDEBAR = colors.HexColor("#e8e2d8")
CLOSURE_BG = colors.HexColor("#161513")


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
    p2 = BASE_DIR / "static" / "branding" / "pullso-logo.png"
    return str(p2) if p2.is_file() else None


def _logo_path_light() -> str | None:
    lp = BASE_DIR / "static" / "branding" / "revenue-report" / "logo-for-light-bg.png"
    if lp.is_file():
        return str(lp)
    p2 = BASE_DIR / "static" / "branding" / "pullso-logo.png"
    return str(p2) if p2.is_file() else None


def build_revenue_pdf_bytes(report: Dict[str, Any], extra: Dict[str, Any] | None = None) -> bytes:
    buffer = io.BytesIO()
    styles = getSampleStyleSheet()

    eyebrow = ParagraphStyle(
        "Eyebrow",
        parent=styles["Normal"],
        fontSize=7,
        textColor=ACCENT,
        spaceAfter=3,
        fontName="Helvetica-Bold",
        leading=9,
    )
    h2_serif = ParagraphStyle(
        "H2Serif",
        parent=styles["Heading2"],
        fontSize=17,
        textColor=INK,
        spaceBefore=0,
        spaceAfter=10,
        fontName="Helvetica-Bold",
        leading=20,
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=9.5,
        textColor=INK_SOFT,
        leading=13.5,
        spaceAfter=6,
    )
    body_tight = ParagraphStyle(
        "BodyTight",
        parent=body,
        spaceAfter=4,
    )
    lede = ParagraphStyle(
        "Lede",
        parent=styles["Normal"],
        fontSize=11,
        textColor=INK_SOFT,
        leading=16,
        spaceAfter=8,
    )
    small = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=8.5,
        textColor=MUTED,
        leading=12,
    )
    label = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=6.5,
        textColor=MUTED,
        leading=8,
        fontName="Helvetica-Bold",
        spaceAfter=3,
    )
    closure = ParagraphStyle(
        "Closure",
        parent=styles["Normal"],
        fontSize=13,
        textColor=colors.HexColor("#f0ebe3"),
        leading=17,
        fontName="Helvetica",
    )

    extra = extra or {}
    cov = report.get("cover") or {}
    lectura = extra.get("lectura_operativa")
    sections = compute_revenue_report_sections(report, lectura)
    highlights = filter_executive_highlights(derive_executive_highlights(report))
    closing = derive_closing_strategic_implication(report)

    def on_cover(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(VOID)
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        canvas.setFillColor(VOID_MID)
        canvas.rect(0, PAGE_H * 0.35, PAGE_W, PAGE_H * 0.65, fill=1, stroke=0)

        ax, ay = 18 * mm, PAGE_H - 32 * mm
        canvas.setFillColor(ACCENT)
        canvas.rect(ax, ay, 3, -(PAGE_H - 48 * mm), fill=1, stroke=0)

        lx = 18 * mm + 14 * mm
        lp = _logo_path_dark_bg()
        if lp:
            try:
                canvas.drawImage(lp, lx, PAGE_H - 38 * mm, width=68 * mm, height=16 * mm, mask="auto", preserveAspectRatio=True)
            except Exception:
                canvas.setFillColor(ACCENT)
                canvas.setFont("Helvetica-Bold", 22)
                canvas.drawString(lx, PAGE_H - 32 * mm, "Pullso")
        else:
            canvas.setFillColor(ACCENT)
            canvas.setFont("Helvetica-Bold", 22)
            canvas.drawString(lx, PAGE_H - 32 * mm, "Pullso")

        canvas.setFillColor(colors.HexColor("#8a8580"))
        canvas.setFont("Helvetica-Bold", 7)
        canvas.drawString(lx, PAGE_H - 44 * mm, "CONSULTORÍA ESTRATÉGICA · REVENUE Y DISTRIBUCIÓN")

        hotel = (cov.get("hotel_name") or "Hotel")[:80]
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 26)
        y = PAGE_H - 95 * mm
        for line in _wrap_text(canvas, hotel, "Helvetica-Bold", 26, PAGE_W - lx - 20 * mm):
            canvas.drawString(lx, y, line)
            y -= 30

        canvas.setFont("Helvetica", 11)
        canvas.setFillColor(colors.HexColor("#e8e4dc"))
        title = (cov.get("report_title") or "")[:100]
        y -= 6 * mm
        canvas.drawString(lx, y, title)
        y -= 16
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#8a8580"))
        canvas.drawString(lx, y, "MEMORANDO EJECUTIVO · LECTURA PARA DIRECCIÓN Y REVENUE")

        rail_x = PAGE_W - MARGIN - 52 * mm
        y_rail = 38 * mm
        canvas.setFont("Helvetica-Bold", 6.5)
        canvas.setFillColor(colors.HexColor("#6b6560"))
        canvas.drawRightString(PAGE_W - MARGIN, y_rail + 36, "PERIODO")
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#d6d2cc"))
        canvas.drawRightString(PAGE_W - MARGIN, y_rail + 24, (cov.get("period_label") or "—")[:42])
        canvas.setFont("Helvetica-Bold", 6.5)
        canvas.setFillColor(colors.HexColor("#6b6560"))
        canvas.drawRightString(PAGE_W - MARGIN, y_rail + 8, "FECHA DEL INFORME")
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#d6d2cc"))
        canvas.drawRightString(PAGE_W - MARGIN, y_rail - 4, str(cov.get("report_date") or "—")[:20])
        canvas.setFont("Helvetica-Bold", 6.5)
        canvas.setFillColor(colors.HexColor("#6b6560"))
        canvas.drawRightString(PAGE_W - MARGIN, y_rail - 22, "ELABORACIÓN")
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#d6d2cc"))
        canvas.drawRightString(PAGE_W - MARGIN, y_rail - 34, (cov.get("prepared_by") or "Pullso")[:28])

        canvas.restoreState()

    def on_interior(canvas, doc):
        canvas.saveState()
        lp = _logo_path_light()
        y_top = PAGE_H - MARGIN + 2
        if lp:
            try:
                canvas.drawImage(lp, MARGIN, y_top - 14, width=32 * mm, height=7 * mm, mask="auto", preserveAspectRatio=True)
            except Exception:
                canvas.setFillColor(ACCENT)
                canvas.setFont("Helvetica-Bold", 10)
                canvas.drawString(MARGIN, y_top - 10, "Pullso")
        else:
            canvas.setFillColor(ACCENT)
            canvas.setFont("Helvetica-Bold", 10)
            canvas.drawString(MARGIN, y_top - 10, "Pullso")
        canvas.setStrokeColor(RULE_HAIR)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, y_top - 18, PAGE_W - MARGIN, y_top - 18)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED)
        mid = (cov.get("hotel_name") or "")[:48]
        canvas.drawCentredString(PAGE_W / 2, y_top - 12, mid)
        canvas.drawRightString(PAGE_W - MARGIN, y_top - 12, str(cov.get("report_date") or ""))
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN, MARGIN - 6, f"Pullso · {cov.get('hotel_name', '')}")
        canvas.drawRightString(PAGE_W - MARGIN, MARGIN - 6, f"Pág. {canvas.getPageNumber()}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=MARGIN,
        leftMargin=MARGIN,
        topMargin=24 * mm,
        bottomMargin=MARGIN + BOTTOM_EXTRA,
    )

    story: List[Any] = []

    story.append(PageBreak())

    story.append(Paragraph("APERTURA", eyebrow))
    story.append(Paragraph("Resumen ejecutivo", h2_serif))
    summary = report.get("executive_summary") or "—"
    lede_tbl = Table(
        [[_p(summary.replace("\n", "<br/>"), lede)]],
        colWidths=[PAGE_W - 2 * MARGIN],
    )
    lede_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PAPER),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("LINEBEFORE", (0, 0), (0, -1), 3, ACCENT),
                ("BOX", (0, 0), (-1, -1), 0.25, RULE),
            ]
        )
    )
    story.append(lede_tbl)
    story.append(Spacer(1, 5 * mm))

    if highlights:
        story.append(Paragraph("LECTURAS INMEDIATAS", eyebrow))
        hl_w = (PAGE_W - 2 * MARGIN - 16) / 3
        hl_cells = []
        for i, h in enumerate(highlights[:3]):
            num = Paragraph(
                f'<font size="18" color="#e07820"><b>0{i + 1}</b></font>',
                ParagraphStyle("HN", parent=styles["Normal"], fontName="Helvetica-Bold"),
            )
            txt = _p(h, body_tight)
            hl_cells.append(Table([[num], [txt]], colWidths=[hl_w - 8]))
        for t in hl_cells:
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), PAPER),
                        ("BOX", (0, 0), (-1, -1), 0.25, RULE),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ]
                )
            )
        hl_row = Table([hl_cells], colWidths=[hl_w, hl_w, hl_w])
        hl_row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
        story.append(hl_row)
        story.append(Spacer(1, 8 * mm))

    if sections.get("show_lectura_operativa") and sections.get("lectura_operativa"):
        lo = sections["lectura_operativa"]
        story.append(Paragraph("DATOS DERIVADOS", eyebrow))
        story.append(Paragraph("Perfil + export (cálculos automáticos)", h2_serif))
        story.append(
            _p(
                "Estimaciones desde inventario y comisiones de referencia en el perfil, cruzadas con el parseo del archivo. "
                "No sustituyen contabilidad ni PMS.",
                small,
            )
        )
        story.append(Spacer(1, 2 * mm))
        if lo.get("inventario_habitaciones_perfil"):
            story.append(
                _p(f"<b>Habitaciones físicas (perfil):</b> {lo['inventario_habitaciones_perfil']}", body_tight)
            )
        cr = lo.get("comisiones_referencia_pct")
        if isinstance(cr, dict) and cr:
            story.append(_p(f"<b>Comisiones de referencia (%):</b> {cr}", body_tight))
        est = lo.get("estimaciones") or {}
        if est.get("room_nights_agregadas_export"):
            story.append(_p(f"<b>Room nights (export):</b> {est['room_nights_agregadas_export']}", body_tight))
        if est.get("ingreso_bruto_agregado_export"):
            story.append(_p(f"<b>Ingreso bruto agregado:</b> {est['ingreso_bruto_agregado_export']}", body_tight))
        if "ocupacion_proxy_pct" in est:
            cap = est.get("capacidad_room_nights_teorica_rango", "—")
            story.append(
                _p(
                    f"<b>Ocupación proxy (%):</b> {est['ocupacion_proxy_pct']} "
                    f"<font size='8' color='#6b6560'>(capacidad teórica: {cap} RN)</font>",
                    body_tight,
                )
            )
        mrows = est.get("margen_por_canal_comision_perfil") or []
        if mrows:
            mdata: List[List[Any]] = [
                [
                    Paragraph("<b>Canal</b>", label),
                    Paragraph("<b>Ingreso</b>", label),
                    Paragraph("<b>% com.</b>", label),
                    Paragraph("<b>Comisión</b>", label),
                    Paragraph("<b>Neto est.</b>", label),
                ]
            ]
            for row in mrows:
                if not isinstance(row, dict):
                    continue
                mdata.append(
                    [
                        Paragraph(str(row.get("canal", "")), body_tight),
                        Paragraph(str(row.get("ingreso_bruto_export", "")), body_tight),
                        Paragraph(str(row.get("pct_comision_perfil", "")), body_tight),
                        Paragraph(str(row.get("comision_estimada", "")), body_tight),
                        Paragraph(str(row.get("ingreso_neto_estimado", "")), body_tight),
                    ]
                )
            tw = PAGE_W - 2 * MARGIN
            mt = Table(mdata, colWidths=[tw * 0.28, tw * 0.2, tw * 0.14, tw * 0.18, tw * 0.2])
            mt.setStyle(
                TableStyle(
                    [
                        ("LINEBELOW", (0, 0), (-1, 0), 1, INK),
                        ("LINEBELOW", (0, 1), (-1, -1), 0.25, RULE_HAIR),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(mt)
        for line in lo.get("metodologia") or []:
            if line:
                story.append(_p(f"• {line}", small))
        story.append(Spacer(1, 6 * mm))

    if sections.get("show_key_findings"):
        story.append(Paragraph("DIAGNÓSTICO", eyebrow))
        story.append(Paragraph("Hallazgos clave", h2_serif))
        for f in report.get("key_findings") or []:
            imp = f.get("impact", "")
            pill = f"Impacto · {_badge(imp)}"
            title = (f.get("title") or "").replace("&", "&amp;").replace("<", "&lt;")
            diag = (f.get("diagnosis") or "").replace("&", "&amp;").replace("<", "&lt;")
            impl = (f.get("business_implication") or "").replace("&", "&amp;").replace("<", "&lt;")
            act = (f.get("recommended_action") or "").replace("&", "&amp;").replace("<", "&lt;")
            left_html = (
                f'<font size="7" color="#e07820"><b>{pill}</b></font><br/><br/>'
                f"<b><font size='12'>{title}</font></b><br/><br/>"
                f"<font size='6.5' color='#6b6560'><b>DIAGNÓSTICO</b></font><br/>"
                f"{diag.replace(chr(10), '<br/>')}"
            )
            right_html = (
                f"<font size='6.5' color='#e07820'><b>POR QUÉ IMPORTA</b></font><br/>"
                f"{impl.replace(chr(10), '<br/>')}<br/><br/>"
                f"<font size='6.5' color='#6b6560'><b>ACCIÓN RECOMENDADA</b></font><br/>"
                f"{act.replace(chr(10), '<br/>')}"
            )
            rw = PAGE_W - 2 * MARGIN
            lw = rw * 0.52
            row = Table(
                [[_p(left_html, body_tight), _p(right_html, body_tight)]],
                colWidths=[lw, rw - lw - 1],
            )
            row.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), PAPER),
                        ("BACKGROUND", (1, 0), (1, -1), SIDEBAR),
                        ("BOX", (0, 0), (-1, -1), 0.25, RULE),
                        ("LINEBEFORE", (1, 0), (1, -1), 0.25, RULE),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                        ("TOPPADDING", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ]
                )
            )
            story.append(row)
            story.append(Spacer(1, 4 * mm))

    if sections.get("show_anomalies"):
        story.append(Paragraph("SEÑALES", eyebrow))
        story.append(Paragraph("Anomalías y alertas analíticas", h2_serif))
        an = report.get("anomalies") or []
        for a in an:
            sev = a.get("severity", "")
            color = colors.HexColor("#9a3412") if sev == "high" else colors.HexColor("#a16207") if sev == "medium" else MUTED
            inner = Table(
                [
                    [
                        Paragraph(
                            f'<font size="7" color="#e07820"><b>Severidad · {_badge(sev)}</b></font>',
                            body_tight,
                        )
                    ],
                    [Paragraph(f"<b>{a.get('title', '')}</b>", ParagraphStyle("AT", parent=body, fontSize=11, fontName="Helvetica-Bold"))],
                    [Paragraph("<b>Qué ocurrió</b>", label)],
                    [_p(a.get("what_happened", ""), body_tight)],
                    [Paragraph("<b>Por qué importa</b>", ParagraphStyle("L3", parent=label, textColor=ACCENT))],
                    [_p(a.get("why_it_matters", ""), body_tight)],
                    [Paragraph("<b>Qué hacer</b>", label)],
                    [_p(a.get("recommended_action", ""), body_tight)],
                ],
                colWidths=[PAGE_W - 2 * MARGIN - 8],
            )
            inner.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), PAPER),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ("BOX", (0, 0), (-1, -1), 0.25, RULE),
                    ]
                )
            )
            stripe = Table([[""]], colWidths=[4])
            stripe.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), color)]))
            wrap = Table([[stripe, inner]], colWidths=[4, PAGE_W - 2 * MARGIN - 4])
            wrap.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
            story.append(wrap)
            story.append(Spacer(1, 3 * mm))

    if sections.get("show_kpi_table"):
        story.append(Paragraph("MÉTRICAS", eyebrow))
        story.append(Paragraph("Lectura ejecutiva por KPI", h2_serif))
        rows = [
            [
                Paragraph("<b>Indicador</b>", label),
                Paragraph("<b>Valor</b>", label),
                Paragraph("<b>Lectura</b>", label),
                Paragraph("<b>Atención</b>", label),
            ]
        ]
        for k in sections.get("kpi_table_filtered") or []:
            rows.append(
                [
                    Paragraph(f"<b>{k.get('metric', '')}</b>", body_tight),
                    Paragraph(f"<b>{k.get('value', '')}</b>", body_tight),
                    _p(k.get("executive_read", ""), body_tight),
                    Paragraph(_badge(k.get("attention_level", "")), small),
                ]
            )
        tw = PAGE_W - 2 * MARGIN
        kt = Table(rows, colWidths=[tw * 0.28, tw * 0.14, tw * 0.44, tw * 0.14])
        kt.setStyle(
            TableStyle(
                [
                    ("LINEBELOW", (0, 0), (-1, 0), 1.5, INK),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.25, RULE_HAIR),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(kt)
        story.append(Spacer(1, 6 * mm))

    if sections.get("show_strategic_recommendations"):
        story.append(Paragraph("PALANCAS", eyebrow))
        story.append(Paragraph("Recomendaciones estratégicas", h2_serif))
        for r in report.get("strategic_recommendations") or []:
            pr = r.get("priority", "")
            story.append(
                Paragraph(
                    f'<font size="7" color="#e07820"><b>Prioridad · {_badge(pr)}</b></font>',
                    body_tight,
                )
            )
            story.append(Paragraph(f"<b>{r.get('title', '')}</b>", ParagraphStyle("RT", parent=body, fontSize=11, fontName="Helvetica-Bold")))
            story.append(_p(r.get("action", ""), body_tight))
            impact_box = Table(
                [[Paragraph("<b>Impacto esperado</b>", label), _p(r.get("expected_impact", ""), body_tight)]],
                colWidths=[PAGE_W - 2 * MARGIN],
            )
            impact_box.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), PAPER),
                        ("BOX", (0, 0), (-1, -1), 0.25, RULE),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ]
                )
            )
            story.append(impact_box)
            story.append(Spacer(1, 4 * mm))

    if sections.get("show_plan_30_60_90"):
        story.append(Paragraph("HORIZONTE", eyebrow))
        story.append(Paragraph("Plan 30 · 60 · 90 días", h2_serif))
        plan = report.get("plan_30_60_90") or {}
        cw = (PAGE_W - 2 * MARGIN - 16) / 3

        def _plan_col(days: List[str], num: str, subtitle: str) -> Table:
            head = Paragraph(
                f'<font size="26" color="white"><b>{num}</b></font>',
                ParagraphStyle("PH", parent=styles["Normal"], fontName="Helvetica-Bold"),
            )
            sub = Paragraph(
                f'<font size="7" color="#e07820"><b>{subtitle}</b></font>',
                ParagraphStyle("PS", parent=styles["Normal"], fontName="Helvetica-Bold"),
            )
            bullets = "<br/>".join(f"• {x}" for x in (days or [])[:12]) or "—"
            bod = _p(bullets, body_tight)
            inner = Table([[head], [sub], [bod]], colWidths=[cw - 10])
            inner.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, 0), INK),
                        ("TOPPADDING", (0, 0), (0, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (0, 0), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("LINEBELOW", (0, 1), (0, 1), 0.25, RULE_HAIR),
                        ("TOPPADDING", (0, 2), (0, 2), 8),
                    ]
                )
            )
            outer = Table([[inner]], colWidths=[cw])
            outer.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.25, RULE), ("BACKGROUND", (0, 0), (-1, -1), PAPER)]))
            return outer

        p30 = _plan_col(plan.get("days_30") or [], "30", "DÍAS — FUNDAMENTOS")
        p60 = _plan_col(plan.get("days_60") or [], "60", "DÍAS — MEDICIÓN")
        p90 = _plan_col(plan.get("days_90") or [], "90", "DÍAS — ESCALA")
        pdeck = Table([[p30, p60, p90]], colWidths=[cw, cw, cw])
        pdeck.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(pdeck)
        story.append(Spacer(1, 6 * mm))

    if sections.get("show_additional_reports"):
        story.append(Paragraph("DATOS", eyebrow))
        story.append(Paragraph("Reportes adicionales recomendados", h2_serif))
        for ar in report.get("additional_reports_needed") or []:
            story.append(Paragraph(f"<b>{ar.get('report_name', '')}</b>", ParagraphStyle("AR", parent=body, fontName="Helvetica-Bold")))
            story.append(_p(ar.get("why_it_is_needed", ""), small))
            story.append(Spacer(1, 2 * mm))

    if sections.get("show_next_steps"):
        story.append(Paragraph("OPERACIÓN", eyebrow))
        story.append(Paragraph("Siguientes pasos", h2_serif))
        for i, s in enumerate(report.get("next_steps") or [], start=1):
            story.append(_p(f"{i}. {s}", body))

    story.append(Spacer(1, 8 * mm))
    closure_tbl = Table(
        [
            [Paragraph("<b>LECTURA FINAL</b>", ParagraphStyle("CE", parent=label, textColor=ACCENT, fontSize=7))],
            [_p(closing, closure)],
        ],
        colWidths=[PAGE_W - 2 * MARGIN],
    )
    closure_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CLOSURE_BG),
                ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#f0ebe3")),
                ("LINEBEFORE", (0, 0), (0, -1), 3, ACCENT),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ]
        )
    )
    story.append(closure_tbl)
    story.append(Spacer(1, 6 * mm))
    story.append(
        _p(
            "Contenido generado con apoyo de IA a partir de los exports cargados. "
            "Validar decisiones con equipo comercial y revenue.",
            small,
        )
    )

    doc.build(story, onFirstPage=on_cover, onLaterPages=on_interior)
    buffer.seek(0)
    return buffer.read()


def _wrap_text(canvas, text: str, font_name: str, font_size: float, max_width: float) -> List[str]:
    words = (text or "").split()
    if not words:
        return [""]
    lines: List[str] = []
    current: List[str] = []
    for w in words:
        trial = " ".join(current + [w])
        if canvas.stringWidth(trial, font_name, font_size) <= max_width or not current:
            current.append(w)
        else:
            lines.append(" ".join(current))
            current = [w]
    if current:
        lines.append(" ".join(current))
    return lines[:3]
