"""Orquesta: IA → validar → o fallback → validar."""
from __future__ import annotations

import logging
from typing import Any, Dict, Tuple

from .fallback import legacy_to_revenue_report
from .openai_generate import generate_revenue_report_via_openai, should_skip_openai_for_revenue_report
from .schema_util import validate_revenue_report, validation_errors

logger = logging.getLogger(__name__)


def build_hotel_context_from_user(user: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "hotel_nombre": user.get("hotel_name") or "",
        "hotel_tamano": user.get("hotel_size") or "",
        "hotel_categoria": user.get("hotel_category") or "",
        "hotel_ubicacion": user.get("hotel_location") or "",
        "hotel_estrellas": user.get("hotel_stars") or 0,
        "hotel_ubicacion_destino": user.get("hotel_location_context") or "",
        "hotel_pms": user.get("hotel_pms") or "",
        "hotel_channel_manager": user.get("hotel_channel_manager") or "",
        "hotel_booking_engine": user.get("hotel_booking_engine") or "",
    }


def build_revenue_report_document(
    user: Dict[str, Any],
    row: Dict[str, Any],
    summary: Dict[str, Any],
    legacy_analysis: Dict[str, Any],
    business_context: str = "",
) -> Tuple[Dict[str, Any], str]:
    """
    Devuelve (documento_validado, fuente) donde fuente es 'openai' | 'fallback'.
    """
    hotel_context = build_hotel_context_from_user(user)
    row_meta = {
        "analysis_id": row.get("id"),
        "created_at": (row.get("created_at") or "")[:19],
    }

    if not should_skip_openai_for_revenue_report():
        try:
            doc = generate_revenue_report_via_openai(
                summary=summary,
                legacy_analysis=legacy_analysis,
                hotel_context=hotel_context,
                business_context=business_context,
                row_meta=row_meta,
            )
            validate_revenue_report(doc)
            return doc, "openai"
        except Exception as e:
            logger.warning("Revenue report OpenAI o validación falló, usando fallback: %s", e)

    doc = legacy_to_revenue_report(user, row, summary, legacy_analysis)
    err = validation_errors(doc)
    if err:
        logger.error("Fallback revenue report no validó: %s", err)
        raise RuntimeError(f"Revenue report inválido tras fallback: {err}")
    validate_revenue_report(doc)
    return doc, "fallback"
