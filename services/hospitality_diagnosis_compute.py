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


def compute_hospitality_diagnosis(payload: dict[str, Any]) -> dict[str, float]:
    """
    Retorna savings_mxn, growth_mxn, growth_rate (0–1), rev_year_mxn.
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
    g = _growth_rate(pct_ota, pct_direct)
    growth_amt = rev_year * g

    return {
        "rev_year_mxn": rev_year,
        "savings_mxn": savings,
        "growth_mxn": growth_amt,
        "growth_rate": g,
        "avg_ota_commission": comm,
    }
