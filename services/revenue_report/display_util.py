"""Derivaciones de presentación (highlights, cierre) sin ampliar el contrato JSON obligatorio."""
from __future__ import annotations

import re
from typing import Any, Dict, List


def derive_executive_highlights(report: Dict[str, Any]) -> List[str]:
    """Tres bullets de apertura: frases del resumen o implicaciones de hallazgos."""
    summary = (report.get("executive_summary") or "").strip()
    parts = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", summary)
        if s.strip() and len(s.strip()) > 12
    ]
    if len(parts) >= 3:
        return parts[:3]
    kf = report.get("key_findings") or []
    out: List[str] = []
    for f in kf[:3]:
        if not isinstance(f, dict):
            continue
        line = (f.get("business_implication") or f.get("title") or "").strip()
        if line:
            out.append(line)
    while len(out) < 3:
        out.append("Profundizar con datos de canal, paridad y pickup por fecha de llegada.")
    return out[:3]


def derive_closing_strategic_implication(report: Dict[str, Any]) -> str:
    c = report.get("closing_strategic_implication") or report.get("strategic_closure")
    if isinstance(c, str) and c.strip():
        return c.strip()
    summary = (report.get("executive_summary") or "").strip()
    if summary:
        segs = [s.strip() for s in re.split(r"(?<=[.!?])\s+", summary) if s.strip()]
        if segs:
            return segs[-1]
    return (
        "El eje estratégico es proteger margen en noches fuertes mientras se construye "
        "producción directa en ventanas débiles, con reglas de inventario y tarifa alineadas al channel manager."
    )
