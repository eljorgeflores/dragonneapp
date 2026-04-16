"""Cuerpo WhatsApp Pullso Brief: nombres y personalización."""
from __future__ import annotations

import json

from services.pullso_whatsapp_user_delivery import (
    personalized_whatsapp_brief_body,
    recipients_named_entries_from_blob,
)


def test_recipients_named_entries_keeps_name_and_dedupes_phone():
    blob = json.dumps(
        [
            {"name": "  Revenue  ", "phone": "5299811111111"},
            {"name": "", "phone": "5299811111111"},
            {"name": "Ops", "phone": "5215512345678"},
        ],
        ensure_ascii=False,
    )
    rows = recipients_named_entries_from_blob(blob)
    assert len(rows) == 2
    assert rows[0]["name"] == "Revenue"
    assert rows[0]["phone"] == "5299811111111"
    assert rows[1]["name"] == "Ops"
    assert rows[1]["phone"] == "5215512345678"


def test_personalized_body_uses_name_when_present():
    base = "Resumen aquí.\n\nTablero: https://x.example/s/abc"
    out = personalized_whatsapp_brief_body(base, "María")
    assert "María" in out
    assert "Pullso Brief" in out
    assert "Resumen aquí" in out


def test_personalized_body_generic_when_name_empty():
    base = "Solo resumen."
    out = personalized_whatsapp_brief_body(base, "")
    assert "*Hola,*" in out
    assert "Solo resumen." in out


def test_personalized_body_strips_markdown_chars_from_name():
    out = personalized_whatsapp_brief_body("Cuerpo.", "Juan_*`x")
    assert "*Hola Juanx,*" in out
