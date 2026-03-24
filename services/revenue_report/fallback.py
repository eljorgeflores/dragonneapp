"""Construye un RevenueReport válido desde el JSON legacy del panel (sin segunda llamada IA)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


def _level_from_text(s: str) -> str:
    sl = (s or "").lower()
    if any(x in sl for x in ("alto", "alta", "high", "crít", "crit", "urgent")):
        return "high"
    if any(x in sl for x in ("bajo", "baja", "low", "leve")):
        return "low"
    return "medium"


def _period_label(summary: Dict[str, Any]) -> str:
    reports = summary.get("report_summaries") or []
    if not reports:
        return "Según ventana del export cargado"
    dr = (reports[0] or {}).get("date_range") or {}
    a, b = dr.get("start"), dr.get("end")
    if a and b:
        return f"{str(a)[:10]} — {str(b)[:10]}"
    od = summary.get("overall_days_covered")
    if od:
        return f"Aprox. {od} días de datos en el export"
    return "Periodo del export analizado"


def legacy_to_revenue_report(
    user: Dict[str, Any],
    row: Dict[str, Any],
    summary: Dict[str, Any],
    analysis: Dict[str, Any],
) -> Dict[str, Any]:
    hotel = (user.get("hotel_name") or "").strip() or "Hotel"
    created = (row.get("created_at") or "")[:19].replace("T", " ")
    report_date = created[:10] if created else datetime.now().strftime("%Y-%m-%d")

    cover = {
        "hotel_name": hotel,
        "report_title": "Diagnóstico ejecutivo de revenue y distribución",
        "period_label": _period_label(summary),
        "prepared_by": "Dragonné",
        "report_date": report_date,
    }

    executive_summary = (analysis.get("resumen_ejecutivo") or "").strip() or (
        "Lectura generada a partir del export disponible. "
        "Revisa hallazgos, KPIs y próximos pasos en el cuerpo del informe."
    )

    key_findings: List[Dict[str, Any]] = []
    for h in (analysis.get("hallazgos_prioritarios") or [])[:12]:
        if not isinstance(h, dict):
            continue
        key_findings.append(
            {
                "title": h.get("titulo") or "Hallazgo",
                "impact": _level_from_text(str(h.get("impacto", ""))),
                "diagnosis": h.get("detalle") or "",
                "business_implication": f"Prioridad indicada: {h.get('prioridad', '—')}.",
                "recommended_action": "Validar con comercial/revenue y ajustar tarifa, inventario o canales según el caso.",
            }
        )
    if not key_findings:
        key_findings.append(
            {
                "title": "Lectura acotada por datos del export",
                "impact": "medium",
                "diagnosis": "El análisis del panel no devolvió hallazgos estructurados en lista.",
                "business_implication": "Conviene repetir la carga con exports más completos (fechas, canal, ingresos).",
                "recommended_action": "Subir producción por canal o forecast con fechas para afinar el diagnóstico.",
            }
        )

    anomalies: List[Dict[str, Any]] = []
    for r in (analysis.get("riesgos_detectados") or [])[:10]:
        if isinstance(r, str):
            anomalies.append(
                {
                    "title": "Riesgo o punto de atención",
                    "severity": "medium",
                    "what_happened": r,
                    "why_it_matters": "Puede afectar margen, ocupación o dependencia de canales.",
                    "recommended_action": "Revisar con datos de canal y tarifa en el PMS o channel manager.",
                }
            )

    kpi_table: List[Dict[str, Any]] = []
    for m in (analysis.get("metricas_clave") or [])[:20]:
        if not isinstance(m, dict):
            continue
        kpi_table.append(
            {
                "metric": m.get("nombre") or "Métrica",
                "value": m.get("valor") or "—",
                "executive_read": m.get("lectura") or "",
                "attention_level": "medium",
            }
        )
    if not kpi_table:
        kpi_table.append(
            {
                "metric": "Fuentes analizadas",
                "value": str(summary.get("reports_detected", 0)),
                "executive_read": "Número de tablas/hojas leídas en la corrida.",
                "attention_level": "low",
            }
        )

    strategic: List[Dict[str, Any]] = []
    for rec in (analysis.get("recomendaciones_accionables") or [])[:12]:
        if not isinstance(rec, dict):
            continue
        strategic.append(
            {
                "title": (rec.get("accion") or "Acción")[:120],
                "priority": _level_from_text(str(rec.get("urgencia", ""))),
                "action": rec.get("accion") or "",
                "expected_impact": rec.get("por_que") or "Mejora de control comercial o de margen.",
            }
        )
    if not strategic:
        strategic.append(
            {
                "title": "Definir plan comercial a 30 días",
                "priority": "high",
                "action": "Priorizar 1–2 palancas (tarifa, canal directo, estancia mínima) según el hotel.",
                "expected_impact": "Mayor claridad operativa y foco en ingresos.",
            }
        )

    recs = analysis.get("recomendaciones_accionables") or []
    d30 = [str((x or {}).get("accion", "")) for x in recs[:4] if isinstance(x, dict) and x.get("accion")]
    d60 = [str((x or {}).get("accion", "")) for x in recs[4:8] if isinstance(x, dict) and x.get("accion")]
    d90 = [str((x or {}).get("accion", "")) for x in recs[8:12] if isinstance(x, dict) and x.get("accion")]
    if not d30:
        d30 = ["Revisar mix de canales y ADR por día de la semana.", "Confirmar reglas en channel manager."]
    if not d60:
        d60 = ["Medir impacto de cambios y ajustar pacing.", "Alinear tarifa pública con estrategia directa."]
    if not d90:
        d90 = ["Estructurar reporting recurrente (semanal/mensual).", "Evaluar costo de distribución neto por canal."]

    additional: List[Dict[str, Any]] = []
    for d in (analysis.get("datos_faltantes") or [])[:15]:
        if isinstance(d, str) and d.strip():
            additional.append({"report_name": d.strip()[:200], "why_it_is_needed": "Permite afinar el diagnóstico y reducir incertidumbre."})

    next_steps: List[str] = []
    for rec in recs[:6]:
        if isinstance(rec, dict) and rec.get("accion"):
            next_steps.append(str(rec["accion"]))
    if not next_steps:
        next_steps = [
            "Validar los hallazgos con el equipo de operación y comercial.",
            "Programar una segunda corrida con exports que incluyan canales y comisiones si aplica.",
        ]

    return {
        "cover": cover,
        "executive_summary": executive_summary,
        "key_findings": key_findings,
        "anomalies": anomalies,
        "kpi_table": kpi_table,
        "strategic_recommendations": strategic,
        "plan_30_60_90": {"days_30": d30, "days_60": d60, "days_90": d90},
        "additional_reports_needed": additional,
        "next_steps": next_steps,
    }
