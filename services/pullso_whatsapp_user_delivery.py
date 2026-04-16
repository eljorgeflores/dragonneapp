"""WhatsApp (Kapso) desde sesión web: destinatarios por usuario y envío de diagnóstico."""
from __future__ import annotations

import json
import re
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import HTTPException

from config import (
    KAPSO_API_KEY,
    KAPSO_PHONE_NUMBER_ID,
    KAPSO_WHATSAPP_BASE_URL,
    KAPSO_WHATSAPP_UTILITY_TEMPLATE_LANGUAGE,
    KAPSO_WHATSAPP_UTILITY_TEMPLATE_NAME,
    PULLSO_WHATSAPP_COOLDOWN_SECONDS,
    PULLSO_WHATSAPP_MAX_RECIPIENTS,
)
from db import db
from services.share_service import public_share_base_url
from time_utils import now_iso

_E164_BODY = re.compile(r"^[1-9]\d{9,14}$")

# Prefijos para UI (valor = dígitos sin +). Orden importa en split (más largos primero).
_KNOWN_DIAL_PREFIXES = (
    "521",
    "52",
    "593",
    "598",
    "591",
    "595",
    "597",
    "54",
    "56",
    "57",
    "58",
    "51",
    "34",
    "502",
    "503",
    "504",
    "505",
    "506",
    "507",
    "1",
)

# Opciones de <select> (valor, etiqueta) — LATAM + US + ES frecuentes.
WA_PREFIX_SELECT_OPTIONS: List[Tuple[str, str]] = [
    ("52", "México (+52)"),
    ("521", "México móvil (+521)"),
    ("1", "Estados Unidos / Canadá (+1)"),
    ("34", "España (+34)"),
    ("54", "Argentina (+54)"),
    ("56", "Chile (+56)"),
    ("57", "Colombia (+57)"),
    ("51", "Perú (+51)"),
    ("593", "Ecuador (+593)"),
    ("598", "Uruguay (+598)"),
    ("58", "Venezuela (+58)"),
    ("591", "Bolivia (+591)"),
    ("595", "Paraguay (+595)"),
    ("597", "Surinam (+597)"),
    ("502", "Guatemala (+502)"),
    ("503", "El Salvador (+503)"),
    ("504", "Honduras (+504)"),
    ("505", "Nicaragua (+505)"),
    ("506", "Costa Rica (+506)"),
    ("507", "Panamá (+507)"),
    ("", "Otro (escribe el número completo con país)"),
]

PULLSO_WA_UI_SLOTS = 3


def normalize_e164_digits(raw: str) -> Optional[str]:
    """Devuelve dígitos sin '+' (formato Cloud API) o None si inválido."""
    s = (raw or "").strip().replace(" ", "").replace("-", "")
    if not s:
        return None
    if s.startswith("+"):
        s = s[1:]
    if not _E164_BODY.match(s):
        return None
    return s


def normalize_e164_display(digits: str) -> str:
    return f"+{digits}" if digits else ""


def parse_recipients_input(text: str) -> List[str]:
    """Parte por saltos de línea, comas o punto y coma; orden estable y sin vacíos."""
    raw = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    parts: List[str] = []
    for chunk in re.split(r"[\n,;]+", raw):
        t = chunk.strip()
        if t:
            parts.append(t)
    return parts


def _raw_recipient_entries_from_json_list(data: list) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for x in data:
        if isinstance(x, dict):
            name = str(x.get("name") or "").strip()[:80]
            raw_phone = x.get("phone") if "phone" in x else x.get("e164")
            d = normalize_e164_digits(str(raw_phone or ""))
            if d:
                out.append({"name": name, "phone": d})
        else:
            d = normalize_e164_digits(str(x))
            if d:
                out.append({"name": "", "phone": d})
    return out


def recipients_list_from_user_column(blob: Optional[str]) -> List[str]:
    """Lee users/hotels pullso_whatsapp_to: JSON array de strings, objetos {name, phone} o un solo número legacy."""
    if blob is None:
        return []
    s = str(blob).strip()
    if not s:
        return []
    if s.startswith("["):
        try:
            data = json.loads(s)
            if isinstance(data, list):
                return [e["phone"] for e in _raw_recipient_entries_from_json_list(data)]
        except (json.JSONDecodeError, TypeError):
            return []
    d = normalize_e164_digits(s)
    return [d] if d else []


def recipients_named_entries_from_blob(blob: Optional[str]) -> List[Dict[str, str]]:
    """
    Destinatarios con nombre (si existe) y teléfono en dígitos E.164, sin duplicar por número.
    """
    if blob is None:
        return []
    s = str(blob).strip()
    if not s:
        return []
    if s.startswith("["):
        try:
            data = json.loads(s)
            if not isinstance(data, list):
                return []
            raw = _raw_recipient_entries_from_json_list(data)
            seen: set = set()
            out: List[Dict[str, str]] = []
            for e in raw:
                ph = e.get("phone") or ""
                if not ph or ph in seen:
                    continue
                seen.add(ph)
                nm = (e.get("name") or "").strip()[:80]
                out.append({"name": nm, "phone": ph})
            return out
        except (json.JSONDecodeError, TypeError):
            return []
    d = normalize_e164_digits(s)
    return [{"name": "", "phone": d}] if d else []


def _sanitize_recipient_display_name(name: str) -> str:
    """Texto seguro para saludo en WhatsApp (sin saltos ni marcadores que rompan el cuerpo)."""
    s = (name or "").replace("\n", " ").replace("\r", "").strip()
    s = re.sub(r"\s+", " ", s)
    s = s.replace("*", "").replace("_", "").replace("`", "")
    return s[:48] if s else ""


def personalized_whatsapp_brief_body(base_body: str, recipient_name: str) -> str:
    """
    Antepone saludo comercial usando el nombre guardado en Mi cuenta; luego el cuerpo común (resumen + enlace).
    """
    label = _sanitize_recipient_display_name(recipient_name)
    if label:
        intro = (
            f"*Hola {label},*\n\n"
            "Aquí va tu *Pullso Brief*: resumen de la lectura, señales clave y enlace al tablero en solo lectura.\n\n"
        )
    else:
        intro = (
            "*Hola,*\n\n"
            "Te enviamos tu *Pullso Brief* con el resumen de la lectura y el enlace al tablero (solo lectura).\n\n"
        )
    full = f"{intro}{base_body}".strip()
    if len(full) > 3900:
        full = full[:3897].rstrip() + "…"
    return full


def split_e164_prefix_and_national(digits: str) -> Tuple[str, str]:
    """Separa prefijo internacional conocido del resto (para inputs de cuenta)."""
    d = re.sub(r"\D", "", digits or "")
    if not d:
        return "", ""
    for p in sorted(_KNOWN_DIAL_PREFIXES, key=len, reverse=True):
        if d.startswith(p):
            return p, d[len(p) :]
    return "", d


def recipients_ui_slots_from_blob(blob: Optional[str], max_slots: int = PULLSO_WA_UI_SLOTS) -> List[Dict[str, str]]:
    """
    Hasta max_slots filas para formulario: name, prefix, national (solo dígitos nacionales sin prefijo repetido).
    """
    entries: List[Dict[str, str]] = []
    if blob:
        s = str(blob).strip()
        if s.startswith("["):
            try:
                data = json.loads(s)
                if isinstance(data, list):
                    entries = _raw_recipient_entries_from_json_list(data)
            except (json.JSONDecodeError, TypeError):
                entries = []
        else:
            d = normalize_e164_digits(s)
            if d:
                entries = [{"name": "", "phone": d}]
    rows: List[Dict[str, str]] = []
    for e in entries[:max_slots]:
        pr, nat = split_e164_prefix_and_national(e.get("phone") or "")
        rows.append(
            {
                "name": (e.get("name") or "")[:80],
                "prefix": pr,
                "national": nat,
            }
        )
    while len(rows) < max_slots:
        rows.append({"name": "", "prefix": "52", "national": ""})
    return rows[:max_slots]


def combine_prefix_and_national_to_digits(prefix: str, national: str) -> Optional[str]:
    """Concatena prefijo (dígitos) + número local (dígitos) y valida E.164."""
    nat = re.sub(r"\D", "", national or "")
    if not nat:
        return None
    pd = re.sub(r"\D", "", prefix or "")
    combined = pd + nat if pd else nat
    return normalize_e164_digits(combined)


def validate_wa_slots_and_build_blob(
    slots: List[Dict[str, str]],
    max_recipients: int,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Valida filas {name, prefix, national} y genera JSON [{name, phone}, ...] con phone en dígitos E.164.
    Retorna (blob_json, error_code) con error_code None si OK.
    """
    intent_rows = 0
    for s in slots:
        nat_digits = re.sub(r"\D", "", str(s.get("national") or ""))
        pref_digits = re.sub(r"\D", "", str(s.get("prefix") or ""))
        if nat_digits or pref_digits:
            intent_rows += 1
    if intent_rows > max_recipients:
        return None, "too_many"

    cleaned: List[Dict[str, str]] = []
    seen_phones: set = set()
    for s in slots[:max_recipients]:
        name = (s.get("name") or "").strip()[:80]
        prefix_raw = str(s.get("prefix") or "").strip()
        national_raw = str(s.get("national") or "").strip()
        nat_digits = re.sub(r"\D", "", national_raw)
        pref_digits = re.sub(r"\D", "", prefix_raw)
        if not nat_digits and not pref_digits:
            continue
        digits = combine_prefix_and_national_to_digits(prefix_raw, national_raw)
        if not digits:
            return None, "invalid_phone"
        if digits in seen_phones:
            continue
        seen_phones.add(digits)
        cleaned.append({"name": name, "phone": digits})
    if not cleaned:
        return None, "empty_recipients"
    return json.dumps(cleaned, ensure_ascii=False), None


def recipients_blob_for_storage(phones_digits: List[str]) -> Optional[str]:
    uniq: List[str] = []
    seen = set()
    for p in phones_digits:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    if not uniq:
        return None
    return json.dumps(uniq, ensure_ascii=False)


def validate_recipients_input(text: str) -> Tuple[Optional[List[str]], Optional[str]]:
    """
    Valida lista de destinatarios.
    Retorna (lista de dígitos E.164 sin '+', código de error) — uno solo no-null.
    """
    parts = parse_recipients_input(text)
    if len(parts) > PULLSO_WHATSAPP_MAX_RECIPIENTS:
        return None, "too_many"
    digits_list: List[str] = []
    for p in parts:
        d = normalize_e164_digits(p)
        if not d:
            return None, "invalid_phone"
        digits_list.append(d)
    # dedupe preservando orden
    out: List[str] = []
    seen = set()
    for d in digits_list:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out, None


def save_user_whatsapp_settings(user_id: int, slots: List[Dict[str, str]], opt_in: bool) -> Optional[str]:
    """
    Persiste opt-in y JSON [{name, phone}, ...] en users.pullso_whatsapp_to.
    slots: filas con keys name, prefix, national (como en el formulario de cuenta).
    """
    if not opt_in:
        with db() as conn:
            conn.execute(
                """
                UPDATE users SET pullso_whatsapp_to = NULL, pullso_whatsapp_opt_in = 0,
                pullso_whatsapp_opt_in_at = NULL, updated_at = ?
                WHERE id = ?
                """,
                (now_iso(), user_id),
            )
        return None
    cap = min(PULLSO_WHATSAPP_MAX_RECIPIENTS, PULLSO_WA_UI_SLOTS)
    blob, err = validate_wa_slots_and_build_blob(slots, cap)
    if err == "too_many":
        return "too_many"
    if err == "invalid_phone":
        return "invalid_phone"
    if err == "empty_recipients" or not blob:
        return "empty_recipients"
    with db() as conn:
        conn.execute(
            """
            UPDATE users SET pullso_whatsapp_to = ?, pullso_whatsapp_opt_in = 1,
            pullso_whatsapp_opt_in_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (blob, now_iso(), now_iso(), user_id),
        )
    return None


def _is_outside_24h_error(status_code: int, text: str) -> bool:
    if status_code != 422:
        return False
    low = (text or "").lower()
    return "24-hour" in low or "non-template" in low


def _kapso_post_message(body: Dict[str, Any]) -> httpx.Response:
    base = (KAPSO_WHATSAPP_BASE_URL or "").strip().rstrip("/")
    url = f"{base}/{KAPSO_PHONE_NUMBER_ID}/messages"
    with httpx.Client(timeout=25.0) as client:
        return client.post(url, headers={"X-API-Key": KAPSO_API_KEY}, json=body)


def _ensure_share_token(conn, analysis_id: int, user_id: int) -> Optional[str]:
    row = conn.execute(
        "SELECT share_token FROM analyses WHERE id = ? AND user_id = ?",
        (analysis_id, user_id),
    ).fetchone()
    if not row:
        return None
    token = row["share_token"]
    if token:
        return str(token)
    token = secrets.token_urlsafe(24)
    conn.execute("UPDATE analyses SET share_token = ? WHERE id = ?", (token, analysis_id))
    return token


def _build_diagnosis_text(title: str, analysis: Dict[str, Any], share_token: Optional[str]) -> str:
    res = (analysis.get("resumen_ejecutivo") or "").strip()
    lines: List[str] = []
    t = (title or "").strip() or "Lectura Pullso"
    lines.append(f"*{t}*")
    if res:
        lines.append("")
        lines.append(res)
    metrics = analysis.get("metricas_clave") or []
    if isinstance(metrics, list) and metrics:
        lines.append("")
        lines.append("*Métricas clave*")
        for m in metrics[:6]:
            if not isinstance(m, dict):
                continue
            label = (m.get("metrica") or m.get("nombre") or "").strip()
            val = (m.get("valor") or m.get("interpretacion") or "").strip()
            if label or val:
                lines.append(f"• {label}: {val}".strip())
    if share_token:
        lines.append("")
        lines.append(f"Tablero (solo lectura): {public_share_base_url()}/s/{share_token}")
    body = "\n".join(lines).strip()
    if len(body) > 3900:
        body = body[:3897].rstrip() + "…"
    return body or "Pullso: lectura lista."


def _cooldown_active(conn, user_id: int, analysis_id: int, phone_digits: str) -> bool:
    row = conn.execute(
        """
        SELECT created_at FROM analysis_whatsapp_sends
        WHERE user_id = ? AND analysis_id = ? AND phone_e164 = ?
        ORDER BY id DESC LIMIT 1
        """,
        (user_id, analysis_id, normalize_e164_display(phone_digits)),
    ).fetchone()
    if not row or not row["created_at"]:
        return False
    try:
        raw = str(row["created_at"]).replace("Z", "+00:00")
        last = datetime.fromisoformat(raw)
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return False
    delta = datetime.now(timezone.utc) - last
    return delta.total_seconds() < float(PULLSO_WHATSAPP_COOLDOWN_SECONDS)


def _record_send(conn, user_id: int, analysis_id: int, phone_digits: str, channel: str) -> None:
    conn.execute(
        """
        INSERT INTO analysis_whatsapp_sends (user_id, analysis_id, phone_e164, channel, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, analysis_id, normalize_e164_display(phone_digits), channel, now_iso()),
    )


def send_diagnosis_whatsapp_for_analysis(user_id: int, analysis_id: int) -> List[Dict[str, Any]]:
    """
    Envía el diagnóstico por WhatsApp a todos los destinatarios configurados.
    Intenta texto; si Meta bloquea por ventana de 24h, intenta template aprobado y reintenta texto una vez.
    """
    if not KAPSO_API_KEY or not KAPSO_PHONE_NUMBER_ID:
        raise HTTPException(status_code=503, detail="WhatsApp (Kapso) no está configurado en el servidor.")
    with db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")
        row = conn.execute(
            "SELECT * FROM analyses WHERE id = ? AND user_id = ?",
            (analysis_id, user_id),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Lectura no encontrada.")
        hid_raw = row["hotel_id"] if "hotel_id" in row.keys() else None
        hid: Optional[int] = None
        if hid_raw is not None:
            try:
                hid = int(hid_raw)
            except (TypeError, ValueError):
                hid = None
        wa_blob: Optional[str] = None
        if hid is not None and hid > 0:
            if not conn.execute(
                "SELECT 1 FROM hotel_members WHERE hotel_id = ? AND user_id = ?",
                (hid, user_id),
            ).fetchone():
                raise HTTPException(status_code=403, detail="No tienes acceso a WhatsApp de este hotel para esta lectura.")
            hrow = conn.execute("SELECT * FROM hotels WHERE id = ?", (hid,)).fetchone()
            if not hrow:
                raise HTTPException(status_code=404, detail="Hotel no encontrado.")
            if not int(hrow["pullso_whatsapp_opt_in"] or 0):
                raise HTTPException(
                    status_code=400,
                    detail="Activa el consentimiento y guarda al menos un número en Mi cuenta → WhatsApp (hotel actual).",
                )
            wa_blob = hrow["pullso_whatsapp_to"]
        else:
            if not int(user["pullso_whatsapp_opt_in"] or 0):
                raise HTTPException(
                    status_code=400,
                    detail="Activa el consentimiento y guarda al menos un número en Mi cuenta → WhatsApp.",
                )
            wa_blob = user["pullso_whatsapp_to"]
        recipient_entries = recipients_named_entries_from_blob(wa_blob)
        if not recipient_entries:
            raise HTTPException(
                status_code=400,
                detail="Configura al menos un número de WhatsApp en Mi cuenta para el hotel de esta lectura."
                if hid is not None and hid > 0
                else "Configura al menos un número de WhatsApp en Mi cuenta.",
            )
        analysis = json.loads(row["analysis_json"])
        title = row["title"] or ""
        share_tok = _ensure_share_token(conn, analysis_id, user_id)
        base_body = _build_diagnosis_text(title, analysis, share_tok)

    results: List[Dict[str, Any]] = []
    for entry in recipient_entries:
        phone_digits = entry["phone"]
        display_name = entry.get("name") or ""
        body_text = personalized_whatsapp_brief_body(base_body, display_name)
        with db() as conn:
            if _cooldown_active(conn, user_id, analysis_id, phone_digits):
                results.append(
                    {
                        "phone": normalize_e164_display(phone_digits),
                        "status": "skipped_cooldown",
                        "detail": f"Reenvío bloqueado {int(PULLSO_WHATSAPP_COOLDOWN_SECONDS // 60)} min para esta lectura y número.",
                    }
                )
                continue

        send_body = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_digits,
            "type": "text",
            "text": {"body": body_text},
        }
        r = _kapso_post_message(send_body)
        if r.status_code < 400:
            with db() as conn:
                _record_send(conn, user_id, analysis_id, phone_digits, "text")
            results.append({"phone": normalize_e164_display(phone_digits), "status": "sent", "channel": "text"})
            continue

        err_txt = r.text
        if not _is_outside_24h_error(r.status_code, err_txt):
            results.append(
                {
                    "phone": normalize_e164_display(phone_digits),
                    "status": "failed",
                    "detail": f"Kapso error {r.status_code}: {err_txt[:400]}",
                }
            )
            continue

        tpl_name = (KAPSO_WHATSAPP_UTILITY_TEMPLATE_NAME or "").strip()
        if not tpl_name:
            results.append(
                {
                    "phone": normalize_e164_display(phone_digits),
                    "status": "failed",
                    "detail": "Fuera de ventana de 24h: define KAPSO_WHATSAPP_UTILITY_TEMPLATE_NAME (template aprobado) en el servidor.",
                }
            )
            continue

        tpl_lang = (KAPSO_WHATSAPP_UTILITY_TEMPLATE_LANGUAGE or "es_MX").strip()
        tpl_body = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_digits,
            "type": "template",
            "template": {"name": tpl_name, "language": {"code": tpl_lang}},
        }
        r2 = _kapso_post_message(tpl_body)
        if r2.status_code >= 400:
            results.append(
                {
                    "phone": normalize_e164_display(phone_digits),
                    "status": "failed",
                    "detail": f"Template Kapso error {r2.status_code}: {r2.text[:400]}",
                }
            )
            continue
        with db() as conn:
            _record_send(conn, user_id, analysis_id, phone_digits, "template")

        r3 = _kapso_post_message(send_body)
        if r3.status_code < 400:
            with db() as conn:
                _record_send(conn, user_id, analysis_id, phone_digits, "text")
            results.append(
                {
                    "phone": normalize_e164_display(phone_digits),
                    "status": "sent",
                    "channel": "text_after_template",
                }
            )
        else:
            results.append(
                {
                    "phone": normalize_e164_display(phone_digits),
                    "status": "partial",
                    "detail": "Se envió el template; el texto largo puede requerir que el destinatario responda o unos minutos para abrir sesión.",
                }
            )
    return results
