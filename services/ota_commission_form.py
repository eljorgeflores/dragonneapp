"""Formulario de comisiones OTA (filas canal + %) → JSON en perfil."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple


def _slug_key(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", (name or "").strip().lower())
    s = s.strip("_")
    return s or ""


def build_ota_commissions_json(channels: List[str], pcts: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Empareja listas del formulario en orden. Devuelve (json o None si vacío, mensaje de error o None).
    """
    out: Dict[str, float] = {}
    chs = list(channels or [])
    pcs = list(pcts or [])
    n = max(len(chs), len(pcs))
    for i in range(n):
        raw_ch = chs[i].strip() if i < len(chs) else ""
        raw_pc = pcs[i].strip() if i < len(pcs) else ""
        if not raw_ch and not raw_pc:
            continue
        key = _slug_key(raw_ch)
        if not key:
            return None, "Escribe un nombre de canal en cada fila que tenga porcentaje."
        if not raw_pc:
            return None, f"Falta el porcentaje para «{raw_ch}»."
        try:
            pct = float(raw_pc.replace(",", "."))
        except ValueError:
            return None, f"Porcentaje inválido para «{raw_ch}» (usa un número, ej. 15 o 15.5)."
        if pct < 0 or pct > 100:
            return None, f"El porcentaje para «{raw_ch}» debe estar entre 0 y 100."
        out[key] = round(pct, 2)
    if not out:
        return None, None
    return json.dumps(out, ensure_ascii=False), None


def _fmt_pct(v: Any) -> str:
    try:
        fv = float(v)
    except (TypeError, ValueError):
        return ""
    if fv == int(fv):
        return str(int(fv))
    return str(round(fv, 2)).rstrip("0").rstrip(".")


def rows_for_ota_commission_template(stored_json: Any, min_rows: int = 4, max_rows: int = 12) -> List[Dict[str, str]]:
    """
    Filas para el HTML: channel, pct, hint_c, hint_p (placeholders tipo diagnóstico Dragonné).
    """
    hints = [
        ("Ej. Booking.com", "15"),
        ("Ej. Expedia", "18"),
        ("Ej. Airbnb", "12"),
        ("% resto OTAs → clave «default»", "16"),
    ]
    rows: List[Dict[str, str]] = []
    if stored_json:
        try:
            data = json.loads(str(stored_json).strip())
        except (json.JSONDecodeError, TypeError):
            data = None
        if isinstance(data, dict):
            for k, v in data.items():
                kk = str(k).strip()
                if not kk:
                    continue
                display = kk.replace("_", " ")
                rows.append(
                    {
                        "channel": display,
                        "pct": _fmt_pct(v),
                        "hint_c": "",
                        "hint_p": "",
                    }
                )
    while len(rows) < min_rows:
        i = len(rows)
        hc, hp = hints[i] if i < len(hints) else ("Canal (ej. Despegar)", "0–100")
        rows.append({"channel": "", "pct": "", "hint_c": hc, "hint_p": hp})
    return rows[:max_rows]


def rows_from_post_lists(channels: List[str], pcts: List[str], min_rows: int = 4, max_rows: int = 12) -> List[Dict[str, str]]:
    """Tras error de validación, rehidrata lo que envió el usuario."""
    chs = list(channels or [])
    pcs = list(pcts or [])
    n = max(len(chs), len(pcs), min_rows)
    rows: List[Dict[str, str]] = []
    for i in range(min(n, max_rows)):
        c = chs[i].strip() if i < len(chs) else ""
        p = pcs[i].strip() if i < len(pcs) else ""
        rows.append({"channel": c, "pct": p, "hint_c": "", "hint_p": ""})
    while len(rows) < min_rows:
        rows.append({"channel": "", "pct": "", "hint_c": "", "hint_p": ""})
    return rows[:max_rows]
