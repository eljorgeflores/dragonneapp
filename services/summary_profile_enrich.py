"""Perfil hotelero + métricas derivadas para el resumen que consume el modelo."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


def _safe_int_rooms(val: Any) -> Optional[int]:
    if val is None or val == "":
        return None
    try:
        n = int(str(val).strip())
        return n if n > 0 else None
    except (TypeError, ValueError):
        return None


def _parse_commission_map(raw: Any) -> Dict[str, float]:
    if raw is None or not str(raw).strip():
        return {}
    try:
        data = json.loads(str(raw).strip())
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    out: Dict[str, float] = {}
    for k, v in data.items():
        key = str(k).strip().lower()
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        if fv < 0 or fv > 100:
            continue
        out[key] = fv
    return out


def _match_commission_pct(canal: str, cmap: Dict[str, float]) -> Optional[float]:
    if not cmap or not canal:
        return None
    c = str(canal).lower().strip()
    for k in sorted(cmap.keys(), key=len, reverse=True):
        if len(k) < 2:
            continue
        if k in c or c in k:
            return cmap[k]
    for k in ("default", "ota", "otas", "otros"):
        if k in cmap:
            return cmap[k]
    return None


def build_hotel_context_for_analysis(user: Dict[str, Any]) -> Dict[str, Any]:
    """Contexto hotelero unificado para call_openai y revenue report."""
    cmap = _parse_commission_map(user.get("hotel_ota_commissions_json"))
    rooms = _safe_int_rooms(user.get("hotel_room_count"))
    return {
        "hotel_nombre": (user.get("hotel_name") or "").strip(),
        "hotel_tamano": (user.get("hotel_size") or "").strip(),
        "hotel_categoria": (user.get("hotel_category") or "").strip(),
        "hotel_ubicacion": (user.get("hotel_location") or "").strip(),
        "hotel_estrellas": int(user.get("hotel_stars") or 0),
        "hotel_ubicacion_destino": (user.get("hotel_location_context") or "").strip(),
        "hotel_pms": (user.get("hotel_pms") or "").strip(),
        "hotel_channel_manager": (user.get("hotel_channel_manager") or "").strip(),
        "hotel_booking_engine": (user.get("hotel_booking_engine") or "").strip(),
        "hotel_tech_other": (user.get("hotel_tech_other") or "").strip(),
        "hotel_google_business_url": (user.get("hotel_google_business_url") or "").strip(),
        "hotel_expedia_url": (user.get("hotel_expedia_url") or "").strip(),
        "hotel_booking_url": (user.get("hotel_booking_url") or "").strip(),
        "hotel_habitaciones_fisicas": rooms,
        "hotel_comisiones_ota_pct_referencia": cmap,
    }


def enrich_summary_with_hotel_profile(summary: Dict[str, Any], hotel_context: Dict[str, Any]) -> None:
    """
    Añade `lectura_operativa` al resumen (in-place): inventario del perfil, comisiones de referencia
    y estimaciones conservadoras (ocupación proxy, margen neto por canal). El modelo debe usarlas
    como referencia configurada, no como datos contables del PMS.
    """
    rooms: Optional[int] = hotel_context.get("hotel_habitaciones_fisicas")
    cmap: Dict[str, float] = dict(hotel_context.get("hotel_comisiones_ota_pct_referencia") or {})

    block: Dict[str, Any] = {
        "inventario_habitaciones_perfil": rooms,
        "comisiones_referencia_pct": cmap or None,
        "estimaciones": {},
        "metodologia": [
            "Inventario y % de comisión provienen del perfil del hotel; validar contra contratos OTA y configuración real.",
            "Ocupación proxy = room nights del export / (habitaciones físicas × días del rango agregado); es aproximada si el export no cubre calendario completo o hay cortes.",
        ],
    }

    overall_days = int(summary.get("overall_days_covered") or 0)
    total_rn = 0.0
    total_rev = 0.0
    for rs in summary.get("report_summaries") or []:
        m = rs.get("metrics") or {}
        trn = m.get("room_nights")
        if trn is not None:
            try:
                total_rn += float(trn)
            except (TypeError, ValueError):
                pass
        tr = m.get("revenue_total")
        if tr is not None:
            try:
                total_rev += float(tr)
            except (TypeError, ValueError):
                pass

    estim: Dict[str, Any] = {}

    if total_rn > 0:
        estim["room_nights_agregadas_export"] = round(total_rn, 2)
    if total_rev > 0:
        estim["ingreso_bruto_agregado_export"] = round(total_rev, 2)

    if rooms and overall_days > 0 and total_rn > 0:
        cap = float(rooms) * float(overall_days)
        if cap > 0:
            estim["ocupacion_proxy_pct"] = round(min(100.0, (total_rn / cap) * 100.0), 2)
            estim["capacidad_room_nights_teorica_rango"] = round(cap, 2)

    if cmap:
        ing_by_canal: Dict[str, float] = {}
        for rs in summary.get("report_summaries") or []:
            tops = (rs.get("metrics") or {}).get("top_canales_por_ingreso") or []
            for row in tops:
                canal = str(row.get("canal") or "").strip()
                if not canal:
                    continue
                ing = row.get("ingreso")
                if ing is None:
                    continue
                try:
                    ingf = float(ing)
                except (TypeError, ValueError):
                    continue
                ing_by_canal[canal] = ing_by_canal.get(canal, 0.0) + ingf
        margins: List[Dict[str, Any]] = []
        for canal, ingf in sorted(ing_by_canal.items(), key=lambda x: x[1], reverse=True):
            pct = _match_commission_pct(canal, cmap)
            if pct is None:
                continue
            com_est = round(ingf * pct / 100.0, 2)
            margins.append(
                {
                    "canal": canal,
                    "ingreso_bruto_export": round(ingf, 2),
                    "pct_comision_perfil": pct,
                    "comision_estimada": com_est,
                    "ingreso_neto_estimado": round(ingf - com_est, 2),
                }
            )
        if margins:
            estim["margen_por_canal_comision_perfil"] = margins

    block["estimaciones"] = estim
    summary["lectura_operativa"] = block
