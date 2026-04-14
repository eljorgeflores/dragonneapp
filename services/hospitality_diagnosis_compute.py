"""Cálculo orientativo del diagnóstico hospitalidad (misma lógica que el antiguo modal JS)."""

from __future__ import annotations

from typing import Any


def _avg_ota_commission(ota_rows: list[dict[str, Any]]) -> float:
    total = 0.0
    n = 0
    for row in ota_rows:
        try:
            c = float(row.get("comm") or 0)
        except (TypeError, ValueError):
            continue
        if c > 0:
            total += c
            n += 1
    return total / n if n else 17.0


def _growth_rate(pct_ota: float, pct_direct_online: float | None) -> float:
    o = max(0.0, min(100.0, pct_ota)) / 100.0
    if pct_direct_online is None or pct_direct_online != pct_direct_online:
        d_raw = max(6.0, min(32.0, 28.0 - (pct_ota * 0.22)))
    else:
        d_raw = float(pct_direct_online)
    d = max(0.0, min(100.0, d_raw)) / 100.0
    if d < 0.10:
        base = 0.40
    elif d > 0.28:
        base = 0.20
    else:
        base = 0.40 - ((d - 0.10) / 0.18) * 0.20
    bonus = min(0.06, max(0.0, (pct_ota - 52) / 180))
    if o > 0.55:
        bonus += min(0.04, (o - 0.55) * 0.12)
    g = base + bonus
    return max(0.18, min(0.42, g))


def _target_direct_pct(pct_direct_online: float | None, pct_ota: float) -> float:
    """Objetivo realista de % venta directa online, según baseline del usuario.

    Reglas (definidas por negocio):
    - <10%  -> 20%
    - 10–20 -> 30%
    - 30–40 -> 40%
    - >=40  -> 40% (tope)
    - Si no hay dato, inferimos uno conservador a partir de pct_ota (misma heurística previa).
    """
    if pct_direct_online is None or pct_direct_online != pct_direct_online:
        inferred = max(6.0, min(32.0, 28.0 - (pct_ota * 0.22)))
        pct_direct_online = inferred
    d = max(0.0, min(100.0, float(pct_direct_online)))
    if d < 10.0:
        return 20.0
    if d <= 30.0:
        return 30.0
    if d >= 40.0:
        return 40.0
    if d >= 30.0:
        return 40.0
    # Entre 30–40 ya cubrimos arriba; el resto cae en 30 por realismo.
    return 30.0


def compute_hospitality_diagnosis(payload: dict[str, Any]) -> dict[str, float]:
    """
    Retorna métricas orientativas:
    - savings_mxn: margen prudente recuperable en comisiones OTAs
    - mix_shift_gain_mxn: ganancia por mover mix a directo (sin vender más noches)
    - total_uplift_mxn: +20% de ingreso total (escenario optimizado)
    - growth_mxn/growth_rate: legado (se mantiene para compatibilidad)
    """
    rooms = float(payload["rooms"])
    adr = float(payload["adr"])
    occ = float(payload["occ"])
    if occ < 1.0:
        occ = 1.0
    elif occ > 100.0:
        occ = 100.0
    pct_ota = max(0.0, min(100.0, float(payload["pct_ota"])))
    raw_direct = payload.get("pct_direct")
    pct_direct: float | None
    try:
        if raw_direct is None or raw_direct == "":
            pct_direct = None
        else:
            pct_direct = float(raw_direct)
    except (TypeError, ValueError):
        pct_direct = None

    ota_rows = payload.get("otas") or []
    if not isinstance(ota_rows, list):
        ota_rows = []

    rev_year = rooms * adr * 365.0 * (occ / 100.0)
    comm = _avg_ota_commission(ota_rows)
    savings = rev_year * (pct_ota / 100.0) * 0.5 * (comm / 100.0)

    # (B) Mover mix a directo: usamos el % directo que declaró el usuario y un objetivo realista.
    direct_target = _target_direct_pct(pct_direct, pct_ota)
    direct_now = (
        max(0.0, min(100.0, float(pct_direct)))
        if pct_direct is not None and pct_direct == pct_direct
        else max(0.0, min(100.0, 28.0 - (pct_ota * 0.22)))
    )
    direct_delta = max(0.0, direct_target - direct_now)
    # No podemos bajar OTAs más de lo que existe.
    direct_delta = min(direct_delta, pct_ota)
    # Prudent factor: no todo el delta se logra, ni todas las ventas “migran” limpias.
    mix_shift_gain = rev_year * (direct_delta / 100.0) * (comm / 100.0) * 0.7

    # (C) Crecimiento total: escenario “optimizado” +20% sobre ingreso base.
    total_uplift_rate = 0.20
    total_uplift = rev_year * total_uplift_rate

    g = _growth_rate(pct_ota, pct_direct)
    growth_amt = rev_year * g

    return {
        "rev_year_mxn": rev_year,
        "savings_mxn": savings,
        "mix_shift_gain_mxn": mix_shift_gain,
        "direct_now_pct": direct_now,
        "direct_target_pct": direct_target,
        "direct_delta_pct": direct_delta,
        "total_uplift_mxn": total_uplift,
        "total_uplift_rate": total_uplift_rate,
        "growth_mxn": growth_amt,
        "growth_rate": g,
        "avg_ota_commission": comm,
    }
