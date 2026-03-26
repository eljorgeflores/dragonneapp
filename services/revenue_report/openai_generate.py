"""Segunda llamada OpenAI: produce RevenueReport JSON bajo schema strict."""
from __future__ import annotations

import json
import os
from typing import Any, Dict

import requests

from config import DEFAULT_MODEL, OPENAI_API_KEY

from .prompt import REVENUE_REPORT_SYSTEM_PROMPT
from .schema_util import load_schema, prepare_schema_for_openai_strict


def _extract_output_text(data: Dict[str, Any]) -> str:
    text = None
    if data.get("output"):
        for item in data["output"]:
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"} and content.get("text"):
                    text = content["text"]
                    break
            if text:
                break
    if not text:
        text = data.get("output_text") or data.get("text", "")
    return text or ""


def generate_revenue_report_via_openai(
    summary: Dict[str, Any],
    legacy_analysis: Dict[str, Any],
    hotel_context: Dict[str, Any],
    business_context: str,
    row_meta: Dict[str, Any],
) -> Dict[str, Any]:
    if not OPENAI_API_KEY or not OPENAI_API_KEY.strip():
        raise RuntimeError("OPENAI_API_KEY no configurada")

    schema = prepare_schema_for_openai_strict(load_schema())
    user_payload = {
        "instrucciones": (
            "Genera el documento RevenueReport en español LATAM. "
            "Usa cover.hotel_name desde contexto_hotel.hotel_nombre si aplica. "
            "cover.report_date en formato YYYY-MM-DD usando metadata.created_at si viene. "
            "cover.period_label debe reflejar el rango temporal del resumen de datos cuando sea posible. "
            "prepared_by: Dragonné."
        ),
        "contexto_hotel": hotel_context,
        "contexto_negocio": business_context or "Sin notas adicionales.",
        "resumen_datos": summary,
        "analisis_panel_previo": legacy_analysis,
        "metadata": row_meta,
    }

    payload = {
        "model": DEFAULT_MODEL,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": REVENUE_REPORT_SYSTEM_PROMPT}]},
            {
                "role": "user",
                "content": [{"type": "input_text", "text": json.dumps(user_payload, ensure_ascii=False)}],
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "dragonne_revenue_report",
                "schema": schema,
                "strict": True,
            }
        },
    }
    r = requests.post(
        "https://api.openai.com/v1/responses",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    r.raise_for_status()
    text = _extract_output_text(r.json())
    if not text.strip():
        raise RuntimeError("Respuesta OpenAI vacía para revenue report")
    return json.loads(text)


def should_skip_openai_for_revenue_report() -> bool:
    return os.environ.get("REVENUE_REPORT_SKIP_AI", "").strip() in ("1", "true", "yes")
