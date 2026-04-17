"""Qué bloques del informe revenue tienen sustancia (HTML y PDF)."""
from __future__ import annotations

from typing import Any, Dict, List

# Debe coincidir con el texto de relleno en display_util (si cambia uno, cambiar ambos).
HIGHLIGHT_PLACEHOLDER = "Profundizar con datos de canal, paridad y pickup por fecha de llegada."


def _strip(s: Any) -> str:
    return (str(s) if s is not None else "").strip()


def _is_placeholder_read(s: str) -> bool:
    t = s.lower()
    if not t:
        return True
    if t in ("—", "-", "n/a", "na", "s/d", "sin dato", "sin datos", "no disponible", "n/d"):
        return True
    if "sin dato" in t and len(t) < 40:
        return True
    return False


def kpi_rows_with_substance(kpi_table: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in kpi_table or []:
        if not isinstance(row, dict):
            continue
        metric = _strip(row.get("metric"))
        value = _strip(row.get("value"))
        read = _strip(row.get("executive_read"))
        if not metric and not value and not read:
            continue
        if not value and _is_placeholder_read(read):
            continue
        if value and _is_placeholder_read(value) and _is_placeholder_read(read):
            continue
        out.append(row)
    return out


def plan_columns_meaningful(plan: Any) -> bool:
    if not isinstance(plan, dict):
        return False
    for key in ("days_30", "days_60", "days_90"):
        items = plan.get(key) or []
        if not isinstance(items, list):
            continue
        for x in items:
            s = _strip(x)
            if s and s not in ("—", "-"):
                return True
    return False


def lectura_operativa_is_meaningful(lo: Any) -> bool:
    if not isinstance(lo, dict):
        return False
    if lo.get("inventario_habitaciones_perfil"):
        return True
    cr = lo.get("comisiones_referencia_pct")
    if isinstance(cr, dict) and len(cr) > 0:
        return True
    est = lo.get("estimaciones") or {}
    if isinstance(est, dict) and len(est) > 0:
        return True
    return False


def filter_executive_highlights(highlights: List[str]) -> List[str]:
    out: List[str] = []
    for h in highlights or []:
        s = _strip(h)
        if not s or len(s) < 8:
            continue
        if s == HIGHLIGHT_PLACEHOLDER or s.rstrip(".") == HIGHLIGHT_PLACEHOLDER.rstrip("."):
            continue
        out.append(s)
    return out[:3]


def compute_revenue_report_sections(
    report: Dict[str, Any],
    lectura_operativa: Any = None,
) -> Dict[str, Any]:
    """
    Flags y listas filtradas para plantillas. `lectura_operativa` viene del summary_json
    (backend), no del JSON del modelo revenue.
    """
    kpi_filtered = kpi_rows_with_substance(report.get("kpi_table"))
    return {
        "show_key_findings": bool(report.get("key_findings")),
        "show_anomalies": bool(report.get("anomalies")),
        "show_kpi_table": bool(kpi_filtered),
        "kpi_table_filtered": kpi_filtered,
        "show_strategic_recommendations": bool(report.get("strategic_recommendations")),
        "show_plan_30_60_90": plan_columns_meaningful(report.get("plan_30_60_90")),
        "show_additional_reports": bool(report.get("additional_reports_needed")),
        "show_next_steps": bool(report.get("next_steps")),
        "show_lectura_operativa": lectura_operativa_is_meaningful(lectura_operativa),
        "lectura_operativa": lectura_operativa if lectura_operativa_is_meaningful(lectura_operativa) else None,
    }
