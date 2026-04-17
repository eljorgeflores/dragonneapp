"""PDF a partir del JSON del informe revenue.

Por defecto usa ReportLab (sin dependencias nativas). Opcionalmente, si está instalado
``xhtml2pdf`` y ``REVENUE_REPORT_PDF_ENGINE=xhtml``, intenta HTML+CSS → PDF.
"""
from __future__ import annotations

import io
import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)


def _link_callback(uri: str, rel):
    from config import BASE_DIR

    if uri.startswith("file:"):
        return uri
    if uri.startswith("/static/"):
        p = BASE_DIR / "static" / uri[len("/static/") :]
        if p.is_file():
            return p.resolve().as_uri()
    return uri


def revenue_report_html_to_pdf_bytes(report: Dict[str, Any], extra: Dict[str, Any] | None = None) -> bytes:
    extra = extra or {}
    if os.environ.get("REVENUE_REPORT_PDF_ENGINE", "").strip().lower() == "xhtml":
        try:
            return _pdf_via_xhtml2pdf(report, extra)
        except Exception as e:
            logger.warning("xhtml2pdf falló, usando ReportLab: %s", e)
    from services.revenue_report.render_pdf_canvas import build_revenue_pdf_bytes

    return build_revenue_pdf_bytes(report, extra)


def _pdf_via_xhtml2pdf(report: Dict[str, Any], extra: Dict[str, Any]) -> bytes:
    from xhtml2pdf import pisa

    from config import BASE_DIR

    from .render_html import render_revenue_report_html

    html = render_revenue_report_html(report, extra)
    css_path = BASE_DIR / "static" / "css" / "revenue_report.css"
    if css_path.is_file():
        link = f'<link rel="stylesheet" href="{css_path.resolve().as_uri()}" />'
        if "<head>" in html:
            html = html.replace("<head>", f"<head>{link}", 1)
    buffer = io.BytesIO()
    result = pisa.CreatePDF(html, dest=buffer, encoding="utf-8", link_callback=_link_callback)
    if result.err:
        raise RuntimeError("xhtml2pdf devolvió errores")
    buffer.seek(0)
    return buffer.read()
