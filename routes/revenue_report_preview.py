"""Vista mock del informe revenue (HTML/PDF) para validar branding sin sesión."""
from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, Response

from services.revenue_report.mock_sample import MOCK_REVENUE_REPORT
from services.revenue_report.render_html import render_revenue_report_html
from services.revenue_report.render_pdf import revenue_report_html_to_pdf_bytes
from services.revenue_report.schema_util import validate_revenue_report

logger = logging.getLogger(__name__)

router = APIRouter(tags=["revenue_report_preview"])


@router.get("/revenue-report/mock", response_class=HTMLResponse)
def revenue_report_mock_html():
    validate_revenue_report(MOCK_REVENUE_REPORT)
    html = render_revenue_report_html(MOCK_REVENUE_REPORT, {"is_mock": True})
    return HTMLResponse(html)


@router.get("/revenue-report/mock.pdf")
def revenue_report_mock_pdf():
    validate_revenue_report(MOCK_REVENUE_REPORT)
    try:
        pdf = revenue_report_html_to_pdf_bytes(MOCK_REVENUE_REPORT, {"is_mock": True})
    except Exception as e:
        logger.exception("mock pdf")
        return Response(
            content=f"Error generando PDF: {e}. Revisa: pip install -r requirements.txt (jsonschema, reportlab).",
            media_type="text/plain",
            status_code=500,
        )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="pullso-revenue-mock.pdf"'},
    )
