"""Validación del contrato RevenueReport y PDF mock (sin OpenAI)."""
import json

import pytest

from services.revenue_report.fallback import legacy_to_revenue_report
from services.revenue_report.mock_sample import MOCK_REVENUE_REPORT
from services.revenue_report.render_pdf_canvas import build_revenue_pdf_bytes
from services.revenue_report.schema_util import load_schema, prepare_schema_for_openai_strict, validate_revenue_report


def test_mock_validates():
    validate_revenue_report(MOCK_REVENUE_REPORT)


def test_openai_strict_schema_is_object():
    s = prepare_schema_for_openai_strict(load_schema())
    assert s["type"] == "object"
    assert s.get("additionalProperties") is False
    assert "cover" in s["required"]


def test_fallback_produces_valid_doc():
    user = {"hotel_name": "Hotel X", "plan": "free"}
    row = {"id": 1, "created_at": "2025-01-15T10:00:00"}
    summary = {"reports_detected": 1, "overall_days_covered": 14, "report_summaries": []}
    analysis = {
        "resumen_ejecutivo": "Texto",
        "metricas_clave": [{"nombre": "ADR", "valor": "100", "lectura": "Ok"}],
        "hallazgos_prioritarios": [],
        "riesgos_detectados": [],
        "recomendaciones_accionables": [],
        "datos_faltantes": [],
    }
    doc = legacy_to_revenue_report(user, row, summary, analysis)
    validate_revenue_report(doc)


def test_pdf_bytes_non_empty():
    b = build_revenue_pdf_bytes(MOCK_REVENUE_REPORT)
    assert len(b) > 2000
    assert b[:4] == b"%PDF"
