"""Plan efectivo: facturación (`users.plan`) + override manual (noStripe)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Union

UserLike = Union[Mapping[str, Any], Any]

PLAN_RANK = {"free": 0, "pro": 1, "pro_plus": 2, "free_trial": 3}

VALID_MANUAL_PLANS = frozenset({"pro", "pro_plus", "free_trial"})


def _get(user: UserLike, key: str, default=None):
    if isinstance(user, dict):
        return user.get(key, default)
    try:
        return user[key]
    except (KeyError, TypeError, IndexError):
        return default


def normalize_product_plan(plan: Optional[str]) -> str:
    p = (plan or "free").strip()
    if p in PLAN_RANK:
        return p
    return "free"


def max_plan(a: str, b: str) -> str:
    a, b = normalize_product_plan(a), normalize_product_plan(b)
    return a if PLAN_RANK[a] >= PLAN_RANK[b] else b


def get_paid_plan(user: UserLike) -> str:
    """
    Únicamente `users.plan`: facturación / Stripe / plan base de producto.
    No incluye overrides manuales (usar `get_effective_plan`).
    """
    return normalize_product_plan(_get(user, "plan"))


def _parse_expires_at(raw: Optional[str]) -> Optional[datetime]:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def stored_manual_override_plan(user: UserLike) -> Optional[str]:
    """Valor guardado en BD (aunque esté caducado)."""
    o = _get(user, "manual_plan_override")
    if o is None:
        return None
    s = str(o).strip()
    return s if s in VALID_MANUAL_PLANS else None


def get_active_manual_plan(user: UserLike) -> Optional[str]:
    """
    Nivel otorgado por override manual si está configurado y no caducó.
    'pro', 'pro_plus' o 'free_trial' (solo admin). None si no aplica.
    """
    override = _get(user, "manual_plan_override")
    if override is None:
        return None
    o = str(override).strip()
    if o not in VALID_MANUAL_PLANS:
        return None
    exp_raw = _get(user, "manual_plan_expires_at")
    exp = _parse_expires_at(exp_raw if exp_raw is not None else None)
    if exp is not None and datetime.now(timezone.utc) >= exp:
        return None
    return o


def get_effective_plan(user: UserLike) -> str:
    """
    Fuente única de verdad para límites, permisos de análisis y UI de producto.

    Regla explícita (sin downgrade accidental): `max(plan_base, override_manual_activo)`.
    Un override Pro con usuario pagando Pro+ no reduce el acceso; el manual solo suma
    si mejora respecto al billing. Si el override caducó, no entra en el max (equivale
    a no haber manual activo); los datos en BD se conservan.

    Override `free_trial` (solo admin): plan efectivo dedicado con mismos topes que Pro+
    en archivos/cupo/guardados, pero sin tope de días por lectura.
    """
    paid = get_paid_plan(user)
    manual = get_active_manual_plan(user)
    if manual == "free_trial":
        return "free_trial"
    if manual is None:
        return paid
    return max_plan(paid, manual)


def plan_for_openai_model(effective_plan: str) -> str:
    p = normalize_product_plan(effective_plan)
    if p == "free":
        return "free_30"
    if p == "pro":
        return "pro_90"
    return "pro_180"


def manual_override_expiry_summary(user: UserLike) -> str:
    """Texto para admin: permanente, fecha vigente o caducada (sin borrar filas)."""
    if not manual_override_is_configured(user):
        return "—"
    raw = _get(user, "manual_plan_expires_at")
    if raw is None or not str(raw).strip():
        return "Permanente"
    p = _parse_expires_at(str(raw))
    if p is None:
        return "Permanente"
    ts = p.strftime("%Y-%m-%d %H:%M UTC")
    if get_active_manual_plan(user) is not None:
        return f"{ts} (vigente)"
    return f"{ts} (caducada; sin efecto en acceso)"


def manual_override_is_configured(user: UserLike) -> bool:
    """True si hay filas de override definidas (aunque estén caducadas)."""
    o = _get(user, "manual_plan_override")
    if o is None:
        return False
    return str(o).strip() in VALID_MANUAL_PLANS


def manual_expiry_input_value(user: UserLike) -> str:
    """Valor para input datetime-local (UTC naive string YYYY-MM-DDTHH:MM)."""
    raw = _get(user, "manual_plan_expires_at")
    p = _parse_expires_at(raw if raw else None)
    if p is None:
        return ""
    return p.strftime("%Y-%m-%dT%H:%M")


def normalize_manual_expiry_form(raw: Optional[str]) -> Optional[str]:
    """
    Formulario admin (datetime-local): guarda ISO UTC en users.manual_plan_expires_at.
    Cadena vacía => permanente (None).
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def manual_access_notice_for_account(user: UserLike) -> Optional[dict]:
    """Texto discreto para /app/account si hay override vigente."""
    eff = get_effective_plan(user)
    if eff == "free_trial":
        from plans import plan_label  # import local para evitar ciclo

        label = plan_label(eff)
        exp_raw = _get(user, "manual_plan_expires_at")
        exp = _parse_expires_at(exp_raw if exp_raw is not None else None)
        if exp is not None:
            exp_str = exp.strftime("%Y-%m-%d %H:%M UTC")
            return {
                "body": f"Tu cuenta tiene {label} concedida por el equipo.",
                "detail": f"Activa hasta el {exp_str}. Sin tope de días por lectura; el resto de límites sigue las reglas de la prueba (archivos por corrida, lecturas al mes y análisis guardados).",
            }
        return {
            "body": f"Tu cuenta tiene {label} concedida por el equipo.",
            "detail": "Sin fecha de caducidad. Sin tope de días por lectura; el resto de límites sigue las reglas de la prueba.",
        }
    if get_active_manual_plan(user) is None:
        return None
    from plans import plan_label  # import local para evitar ciclo

    label = plan_label(eff)
    exp_raw = _get(user, "manual_plan_expires_at")
    exp = _parse_expires_at(exp_raw if exp_raw is not None else None)
    if exp is not None:
        exp_str = exp.strftime("%Y-%m-%d %H:%M UTC")
        return {
            "body": f"Tu cuenta tiene acceso {label} concedido por el equipo (acceso manual).",
            "detail": f"Activo hasta el {exp_str}.",
        }
    return {
        "body": f"Tu cuenta tiene acceso {label} concedido por el equipo (acceso manual).",
        "detail": "Sin fecha de caducidad.",
    }


def pullso_brief_whatsapp_entitled(user: UserLike) -> bool:
    """
    Pullso Brief (WhatsApp desde el panel, equipo por hotel): no está en el plan gratuito base.

    Queda habilitado con el plan efectivo Pro, Pro+ o **prueba extendida** (`free_trial`): esa prueba
    debe comportarse como acceso completo al producto (mismos módulos que pago), no como plan free.
    """
    p = normalize_product_plan(get_effective_plan(user))
    return p in ("pro", "pro_plus", "free_trial")
