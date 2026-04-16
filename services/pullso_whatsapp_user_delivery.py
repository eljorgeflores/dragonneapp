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


def recipients_list_from_user_column(blob: Optional[str]) -> List[str]:
    """Lee users.pullso_whatsapp_to: JSON array o un solo número legacy."""
    if blob is None:
        return []
    s = str(blob).strip()
    if not s:
        return []
    if s.startswith("["):
        try:
            data = json.loads(s)
            if isinstance(data, list):
                out: List[str] = []
                for x in data:
                    d = normalize_e164_digits(str(x))
                    if d:
                        out.append(d)
                return out
        except (json.JSONDecodeError, TypeError):
            return []
    d = normalize_e164_digits(s)
    return [d] if d else []


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


def save_user_whatsapp_settings(user_id: int, recipients_text: str, opt_in: bool) -> Optional[str]:
    """
    Persiste opt-in y lista JSON en users.pullso_whatsapp_to.
    Retorna código de error o None si OK.
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
    digits, err = validate_recipients_input(recipients_text)
    if err == "too_many":
        return "too_many"
    if err == "invalid_phone":
        return "invalid_phone"
    if not digits:
        return "empty_recipients"
    blob = recipients_blob_for_storage(digits)
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
            phones = recipients_list_from_user_column(hrow["pullso_whatsapp_to"])
            if not phones:
                raise HTTPException(
                    status_code=400,
                    detail="Configura al menos un número de WhatsApp en Mi cuenta para el hotel de esta lectura.",
                )
        else:
            if not int(user["pullso_whatsapp_opt_in"] or 0):
                raise HTTPException(
                    status_code=400,
                    detail="Activa el consentimiento y guarda al menos un número en Mi cuenta → WhatsApp.",
                )
            phones = recipients_list_from_user_column(user["pullso_whatsapp_to"])
            if not phones:
                raise HTTPException(
                    status_code=400,
                    detail="Configura al menos un número de WhatsApp en Mi cuenta.",
                )
        analysis = json.loads(row["analysis_json"])
        title = row["title"] or ""
        share_tok = _ensure_share_token(conn, analysis_id, user_id)
        body_text = _build_diagnosis_text(title, analysis, share_tok)

    results: List[Dict[str, Any]] = []
    for phone_digits in phones:
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
