"""Generación de PDF de informes de análisis (misma salida web y API v1)."""
from __future__ import annotations

import io
import json
import logging
import os
import re
import sqlite3

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

from config import BASE_DIR
from db import db
from plan_entitlements import get_effective_plan
from plans import plan_label

logger = logging.getLogger(__name__)

# Colores brandbook para PDF
_PDF_BRAND_TEXT = HexColor("#343434")
_PDF_BRAND_ACCENT = HexColor("#f07e07")
_PDF_MARGIN = 50
_PDF_FOOTER_H = 36


def _pdf_draw_footer(c: canvas.Canvas, width: float, height: float, hotel_name: str, report_date: str) -> None:
    """Pie de página: nombre del hotel y fecha en todas las páginas."""
    c.setFillColor(_PDF_BRAND_TEXT)
    c.setFont("Helvetica", 9)
    c.drawString(_PDF_MARGIN, 22, f"{hotel_name}  ·  {report_date}")
    c.setFillColor(_PDF_BRAND_ACCENT)
    c.setStrokeColor(_PDF_BRAND_ACCENT)
    c.setLineWidth(0.5)
    c.line(_PDF_MARGIN, 30, width - _PDF_MARGIN, 30)
    c.setFillColor(_PDF_BRAND_TEXT)


def _pdf_draw_wrapped(
    c: canvas.Canvas, text: str, x: float, y: float, max_width: int, font: str = "Helvetica", size: int = 10, leading: int = 14
) -> float:
    """Dibuja texto con salto de línea; devuelve la y final."""
    c.setFont(font, size)
    lines: list[str] = []
    for raw_line in (text or "").split("\n"):
        current = ""
        for word in raw_line.split():
            test = (current + " " + word).strip()
            if stringWidth(test, font, size) > max_width:
                if current:
                    lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def _pdf_build_analysis_pdf(
    c: canvas.Canvas, width: float, height: float, user: dict, row: dict, summary: dict, analysis: dict
) -> None:
    hotel_name = user.get("hotel_name") or "Hotel"
    plan = plan_label(get_effective_plan(user))
    report_date = (row.get("created_at") or "")[:19].replace("T", " ")
    analysis_id = row.get("id", 0)

    # Pie de página en la primera hoja
    _pdf_draw_footer(c, width, height, hotel_name, report_date)

    def new_page(y: float, min_need: int = 120) -> float:
        if y < _PDF_FOOTER_H + min_need:
            c.showPage()
            _pdf_draw_footer(c, width, height, hotel_name, report_date)
            return height - _PDF_MARGIN - 20
        return y

    # ---------- Encabezado con branding ----------
    logo_path = BASE_DIR / "static" / "branding" / "pullso-logo.png"
    if logo_path.exists():
        try:
            c.drawImage(str(logo_path), _PDF_MARGIN, height - 52, width=120, height=30)
        except Exception:
            c.setFillColor(_PDF_BRAND_ACCENT)
            c.setFont("Helvetica-Bold", 20)
            c.drawString(_PDF_MARGIN, height - 48, "Pullso")
            c.setFillColor(_PDF_BRAND_TEXT)
    else:
        c.setFillColor(_PDF_BRAND_ACCENT)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(_PDF_MARGIN, height - 48, "Pullso")
        c.setFillColor(_PDF_BRAND_TEXT)
    c.setFont("Helvetica", 11)
    c.drawString(_PDF_MARGIN, height - 68, "Análisis de revenue hotelero")
    c.setStrokeColor(_PDF_BRAND_ACCENT)
    c.setLineWidth(1.5)
    c.line(_PDF_MARGIN, height - 76, min(_PDF_MARGIN + 180, width - _PDF_MARGIN), height - 76)
    c.setFillColor(_PDF_BRAND_TEXT)

    # ---------- Bloque personalizado: Hotel y fecha ----------
    y = height - 100
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(_PDF_BRAND_ACCENT)
    c.drawString(_PDF_MARGIN, y, "Hotel")
    c.setFillColor(_PDF_BRAND_TEXT)
    c.setFont("Helvetica", 10)
    c.drawString(_PDF_MARGIN + 32, y, hotel_name)
    y -= 14
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(_PDF_BRAND_ACCENT)
    c.drawString(_PDF_MARGIN, y, "Fecha del reporte")
    c.setFillColor(_PDF_BRAND_TEXT)
    c.setFont("Helvetica", 10)
    c.drawString(_PDF_MARGIN + 70, y, report_date)
    y -= 14
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(_PDF_BRAND_ACCENT)
    c.drawString(_PDF_MARGIN, y, "Plan")
    c.setFillColor(_PDF_BRAND_TEXT)
    c.setFont("Helvetica", 10)
    c.drawString(_PDF_MARGIN + 28, y, plan)
    y -= 28

    # ---------- Tabla resumen (KPIs como en el dashboard) ----------
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(_PDF_BRAND_ACCENT)
    c.drawString(_PDF_MARGIN, y, "Vista numérica del export")
    y -= 6
    c.setStrokeColor(HexColor("#e0e0e0"))
    c.setLineWidth(0.5)
    tw = (width - 2 * _PDF_MARGIN) / 4
    th = 22
    kpis = [
        ("Archivos (carga)", str(summary.get("total_files", 0))),
        ("Fuentes leídas", str(summary.get("reports_detected", 0))),
        ("Días (ventana total)", str(summary.get("overall_days_covered", 0))),
        ("Máx. días (una fuente)", str(summary.get("max_days_covered", 0))),
    ]
    for i, (label, value) in enumerate(kpis):
        cx = _PDF_MARGIN + i * tw
        c.rect(cx, y - th, tw, th, stroke=1, fill=0)
        c.setFont("Helvetica", 8)
        c.setFillColor(HexColor("#808081"))
        c.drawString(cx + 6, y - th + 12, label)
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(_PDF_BRAND_TEXT)
        c.drawString(cx + 6, y - th + 2, value)
    c.setFillColor(_PDF_BRAND_TEXT)
    y -= th + 18

    # ---------- Resumen ejecutivo ----------
    y = new_page(y, 80)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(_PDF_BRAND_ACCENT)
    c.drawString(_PDF_MARGIN, y, "Resumen ejecutivo")
    y -= 6
    c.setStrokeColor(_PDF_BRAND_ACCENT)
    c.setLineWidth(1)
    c.line(_PDF_MARGIN, y - 2, _PDF_MARGIN + 120, y - 2)
    c.setFillColor(_PDF_BRAND_TEXT)
    y -= 16
    resumen = analysis.get("resumen_ejecutivo", "")
    y = _pdf_draw_wrapped(c, resumen, _PDF_MARGIN, y, int(width - 2 * _PDF_MARGIN))
    y -= 14

    # ---------- Métricas clave ----------
    y = new_page(y, 100)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(_PDF_BRAND_ACCENT)
    c.drawString(_PDF_MARGIN, y, "Métricas y lectura")
    y -= 6
    c.setStrokeColor(_PDF_BRAND_ACCENT)
    c.line(_PDF_MARGIN, y - 2, _PDF_MARGIN + 100, y - 2)
    c.setFillColor(_PDF_BRAND_TEXT)
    y -= 14
    c.setFont("Helvetica", 10)
    for item in analysis.get("metricas_clave", [])[:8]:
        nombre = item.get("nombre", "")
        valor = item.get("valor", "")
        lectura = item.get("lectura", "")
        y = _pdf_draw_wrapped(c, f"{nombre}: {valor}", _PDF_MARGIN, y, int(width - 2 * _PDF_MARGIN))
        if lectura:
            y = _pdf_draw_wrapped(c, lectura, _PDF_MARGIN + 10, y, int(width - 2 * _PDF_MARGIN - 10), size=9)
        y -= 6
        if y < _PDF_FOOTER_H + 60:
            y = new_page(y, 60)
            c.setFont("Helvetica", 10)
    y -= 8

    # ---------- Hallazgos prioritarios ----------
    y = new_page(y, 100)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(_PDF_BRAND_ACCENT)
    c.drawString(_PDF_MARGIN, y, "Hallazgos prioritarios")
    y -= 6
    c.setStrokeColor(_PDF_BRAND_ACCENT)
    c.line(_PDF_MARGIN, y - 2, _PDF_MARGIN + 130, y - 2)
    c.setFillColor(_PDF_BRAND_TEXT)
    y -= 14
    for item in analysis.get("hallazgos_prioritarios", [])[:6]:
        titulo = item.get("titulo", "")
        detalle = item.get("detalle", "")
        impacto = item.get("impacto", "")
        prioridad = item.get("prioridad", "")
        y = _pdf_draw_wrapped(c, f"• {titulo} (Impacto: {impacto}, Prioridad: {prioridad})", _PDF_MARGIN, y, int(width - 2 * _PDF_MARGIN))
        if detalle:
            y = _pdf_draw_wrapped(c, detalle, _PDF_MARGIN + 12, y, int(width - 2 * _PDF_MARGIN - 12), size=9)
        y -= 8
        if y < _PDF_FOOTER_H + 50:
            y = new_page(y, 50)
    y -= 8

    # ---------- Oportunidades directo vs OTA ----------
    opps = analysis.get("oportunidades_directo_vs_ota", [])
    if opps:
        y = new_page(y, 80)
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(_PDF_BRAND_ACCENT)
        c.drawString(_PDF_MARGIN, y, "Oportunidades directo vs OTA")
        y -= 6
        c.setStrokeColor(_PDF_BRAND_ACCENT)
        c.line(_PDF_MARGIN, y - 2, _PDF_MARGIN + 180, y - 2)
        c.setFillColor(_PDF_BRAND_TEXT)
        y -= 14
        c.setFont("Helvetica", 10)
        for s in opps[:6]:
            y = _pdf_draw_wrapped(c, f"• {s}", _PDF_MARGIN, y, int(width - 2 * _PDF_MARGIN))
            y -= 4
        y -= 8

    # ---------- Riesgos detectados ----------
    riesgos = analysis.get("riesgos_detectados", [])
    if riesgos:
        y = new_page(y, 80)
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(_PDF_BRAND_ACCENT)
        c.drawString(_PDF_MARGIN, y, "Riesgos y puntos de atención")
        y -= 6
        c.setStrokeColor(_PDF_BRAND_ACCENT)
        c.line(_PDF_MARGIN, y - 2, _PDF_MARGIN + 120, y - 2)
        c.setFillColor(_PDF_BRAND_TEXT)
        y -= 14
        c.setFont("Helvetica", 10)
        for s in riesgos[:6]:
            y = _pdf_draw_wrapped(c, f"• {s}", _PDF_MARGIN, y, int(width - 2 * _PDF_MARGIN))
            y -= 4
        y -= 8

    # ---------- Recomendaciones accionables ----------
    y = new_page(y, 120)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(_PDF_BRAND_ACCENT)
    c.drawString(_PDF_MARGIN, y, "Próximos pasos sugeridos")
    y -= 6
    c.setStrokeColor(_PDF_BRAND_ACCENT)
    c.line(_PDF_MARGIN, y - 2, _PDF_MARGIN + 200, y - 2)
    c.setFillColor(_PDF_BRAND_TEXT)
    y -= 14
    c.setFont("Helvetica", 10)
    for item in analysis.get("recomendaciones_accionables", [])[:10]:
        accion = item.get("accion", "")
        por_que = item.get("por_que", "")
        urgencia = item.get("urgencia", "")
        y = _pdf_draw_wrapped(c, f"• {accion} (Urgencia: {urgencia})", _PDF_MARGIN, y, int(width - 2 * _PDF_MARGIN))
        if por_que:
            y = _pdf_draw_wrapped(c, por_que, _PDF_MARGIN + 12, y, int(width - 2 * _PDF_MARGIN - 12), size=9)
        y -= 6
        if y < _PDF_FOOTER_H + 50:
            y = new_page(y, 50)
            c.setFont("Helvetica", 10)
    y -= 8

    # ---------- Datos faltantes ----------
    faltantes = analysis.get("datos_faltantes", [])
    if faltantes:
        y = new_page(y, 60)
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(_PDF_BRAND_ACCENT)
        c.drawString(_PDF_MARGIN, y, "Información que faltó en el export")
        y -= 6
        c.setStrokeColor(_PDF_BRAND_ACCENT)
        c.line(_PDF_MARGIN, y - 2, _PDF_MARGIN + 100, y - 2)
        c.setFillColor(_PDF_BRAND_TEXT)
        y -= 14
        c.setFont("Helvetica", 10)
        for s in faltantes[:5]:
            y = _pdf_draw_wrapped(c, f"• {s}", _PDF_MARGIN, y, int(width - 2 * _PDF_MARGIN))
            y -= 4

    c.showPage()


def streaming_pdf_response_for_owned_analysis(user: sqlite3.Row, analysis_id: int) -> StreamingResponse:
    """PDF descargable para un análisis del usuario autenticado (sesión o misma lógica desde API)."""
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM analyses WHERE id = ? AND user_id = ?",
            (analysis_id, user["id"]),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    summary = json.loads(row["summary_json"])
    analysis = json.loads(row["analysis_json"])
    user_dict = dict(user)
    use_legacy = os.environ.get("REVENUE_REPORT_USE_LEGACY_PDF", "").strip().lower() in ("1", "true", "yes")

    if not use_legacy:
        try:
            from services.revenue_report.pipeline import build_revenue_report_document
            from services.revenue_report.render_pdf import revenue_report_html_to_pdf_bytes

            doc, source = build_revenue_report_document(user_dict, dict(row), summary, analysis, "")
            pdf_bytes = revenue_report_html_to_pdf_bytes(
                doc,
                {
                    "pdf_source": source,
                    "analysis_id": analysis_id,
                    "lectura_operativa": summary.get("lectura_operativa"),
                },
            )
            buffer = io.BytesIO(pdf_bytes)
            buffer.seek(0)
        except Exception as e:
            logger.warning("PDF revenue template falló, usando ReportLab legacy: %s", e)
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            _pdf_build_analysis_pdf(c, width, height, user_dict, dict(row), summary, analysis)
            c.save()
            buffer.seek(0)
    else:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        _pdf_build_analysis_pdf(c, width, height, user_dict, dict(row), summary, analysis)
        c.save()
        buffer.seek(0)
    safe_hotel = re.sub(r"[^\w\s-]", "", (user_dict.get("hotel_name") or "informe"))
    safe_hotel = re.sub(r"[-\s]+", "-", safe_hotel).strip()[:40] or "informe"
    report_date = (row["created_at"] or "")[:10]
    filename = f"pullso-lectura-{safe_hotel}-{report_date}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
