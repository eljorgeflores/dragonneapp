"""
Reportes programados vía correo desde el PMS: inbox único, webhook y orquestación de lectura.

MVP: recepción JSON estilo Postmark Inbound + adjuntos en multipart (pruebas locales).
"""
from __future__ import annotations

import base64
import json
import logging
import secrets
import sqlite3
from email.utils import parseaddr
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, UploadFile

from config import ALLOWED_UPLOAD_EXTENSIONS, MAX_UPLOAD_BYTES_PER_FILE, PMS_INBOUND_EMAIL_DOMAIN
from db import db
from plan_entitlements import get_effective_plan, plan_for_openai_model, pms_scheduled_reports_entitled
from services.analysis_core import (
    call_openai,
    enforce_plan,
    release_reserved_generation_row,
    require_business_context,
    reserve_monthly_generation_or_raise,
    save_analysis,
    summarize_reports,
    user_row_as_dict,
)
from services.hotel_pullso import user_is_hotel_admin
from time_utils import now_iso

_log = logging.getLogger(__name__)

PMS_VENDOR_CHOICES: Tuple[Tuple[str, str], ...] = (
    ("mews", "Mews"),
    ("cloudbeds", "Cloudbeds"),
    ("siteminder", "SiteMinder"),
    ("littlehotelier", "Little Hotelier"),
    ("yanolja", "Yanolja"),
    ("shiji", "Shiji"),
    ("opera", "Oracle Opera / OHIP"),
    ("protel", "Protel"),
    ("other", "Otro / varios"),
)

PMS_LOCAL_PREFIX = "pms."


def inbound_address_for_token(token: str) -> str:
    t = (token or "").strip().lower()
    return f"{PMS_LOCAL_PREFIX}{t}@{PMS_INBOUND_EMAIL_DOMAIN}"


def _parse_recipient_to_token(to_raw: str) -> Optional[str]:
    """Extrae token desde To / OriginalRecipient (formato pms.<token>@dominio)."""
    if not to_raw or not PMS_INBOUND_EMAIL_DOMAIN:
        return None
    dom = PMS_INBOUND_EMAIL_DOMAIN.lower()
    parts = [p.strip() for p in str(to_raw).replace(",", " ").split() if "@" in p]
    for chunk in parts:
        _, addr = parseaddr(chunk)
        a = (addr or chunk).strip().lower()
        if "@" not in a:
            continue
        local, _, host = a.partition("@")
        if host != dom:
            continue
        if not local.startswith(PMS_LOCAL_PREFIX):
            continue
        tok = local[len(PMS_LOCAL_PREFIX) :].strip()
        if len(tok) >= 8:
            return tok
    _, addr = parseaddr(str(to_raw))
    a = (addr or "").strip().lower()
    if "@" in a:
        local, _, host = a.partition("@")
        if host == dom and local.startswith(PMS_LOCAL_PREFIX):
            tok = local[len(PMS_LOCAL_PREFIX) :].strip()
            if len(tok) >= 8:
                return tok
    return None


def plan_usage_hints(effective_plan: str) -> Dict[str, Any]:
    """Textos para UI: cupos mensuales y guardados según plan."""
    from config import (
        PRO_180_MAX_ANALYSES,
        PRO_180_MAX_DAYS,
        PRO_180_MAX_FILES,
        PRO_90_MAX_ANALYSES,
        PRO_90_MAX_DAYS,
        PRO_90_MAX_FILES,
        PRO_90_REPORTS_PER_MONTH,
        PRO_PLUS_MAX_ANALYSES,
        PRO_PLUS_REPORTS_PER_MONTH,
    )

    if effective_plan == "pro":
        return {
            "max_saved": PRO_90_MAX_ANALYSES,
            "reads_per_month": PRO_90_REPORTS_PER_MONTH,
            "max_days": PRO_90_MAX_DAYS,
            "max_files": PRO_90_MAX_FILES,
            "schedule_hint": (
                f"Plan Pro: hasta {PRO_90_REPORTS_PER_MONTH} lecturas nuevas por mes (UTC) y "
                f"{PRO_90_MAX_ANALYSES} análisis guardados a la vez. Programa el PMS para no superar "
                f"{PRO_90_REPORTS_PER_MONTH} envíos al mes (cada envío cuenta aunque borres la lectura después). "
                f"Cada archivo no debe superar {PRO_90_MAX_DAYS} días de rango."
            ),
        }
    # pro_plus y free_trial (mismos topes que Pro+ salvo días ilimitados en free_trial)
    days_note = (
        "Sin tope de días por lectura (prueba extendida)."
        if effective_plan == "free_trial"
        else f"Hasta {PRO_180_MAX_DAYS} días por lectura."
    )
    return {
        "max_saved": PRO_PLUS_MAX_ANALYSES,
        "reads_per_month": PRO_PLUS_REPORTS_PER_MONTH,
        "max_days": PRO_180_MAX_DAYS,
        "max_files": PRO_180_MAX_FILES,
        "schedule_hint": (
            f"Plan Pro+ / prueba extendida: hasta {PRO_PLUS_REPORTS_PER_MONTH} lecturas nuevas por mes (UTC) y "
            f"{PRO_PLUS_MAX_ANALYSES} análisis guardados a la vez. Ajusta la frecuencia del reporte programado "
            f"para no pasarte de {PRO_PLUS_REPORTS_PER_MONTH} correos con adjuntos al mes. {days_note}"
        ),
    }


def ideal_report_types_block() -> str:
    return (
        "Tipos de export que suelen dar más valor con Pullso (prioriza los que ya uses en el panel):\n"
        "• **Detalle por reserva** (una fila por reserva): mix y share por canal, ADR por fuente, pick-up si traes "
        "fecha de reserva + llegada, cancelaciones/no-show si traes estado.\n"
        "• **Producción diaria** (una fila por día): tendencia de ingresos/noches, patrón entre semana vs fin de semana, "
        "picos o caídas claras en el periodo.\n"
        "• **Mismo corte y columnas** en cada envío automático: así la comparación contra la lectura previa es limpia "
        "(tendencias, picos de reservas, ADR medio, participación por segmento/canal).\n"
        "Evita mezclar en un solo correo muchos reportes distintos si tu plan limita archivos por corrida."
    )


def _prior_analysis_excerpt(conn: sqlite3.Connection, user_id: int, prior_id: Optional[int]) -> str:
    if not prior_id:
        return (
            "(Primera corrida automática para este inbox: no hay lectura previa en el sistema. "
            "Enfócate en tendencias dentro del rango del export — inicio vs fin del periodo — y deja "
            "recomendaciones para mantener el mismo tipo de reporte en la próxima entrega.)"
        )
    row = conn.execute(
        "SELECT analysis_json, title FROM analyses WHERE id = ? AND user_id = ?",
        (prior_id, user_id),
    ).fetchone()
    if not row:
        return "(No se encontró lectura previa enlazada; trata este envío como primera corrida.)"
    try:
        aj = json.loads(row["analysis_json"] or "{}")
    except json.JSONDecodeError:
        aj = {}
    resumen = (aj.get("resumen_ejecutivo") or "")[:2400]
    metricas = aj.get("metricas_clave") or []
    m_lines: List[str] = []
    if isinstance(metricas, list):
        for m in metricas[:12]:
            if not isinstance(m, dict):
                continue
            nombre = (m.get("nombre") or m.get("metrica") or "").strip()
            valor = (m.get("valor") or "").strip()
            lectura = (m.get("lectura") or m.get("interpretacion") or "").strip()
            if nombre or valor:
                m_lines.append(f"- {nombre}: {valor}" + (f" — {lectura}" if lectura else ""))
    title = (row["title"] or "").strip()
    block = f"Título anterior: {title}\nResumen ejecutivo previo (recortado):\n{resumen}\n"
    if m_lines:
        block += "Métricas clave previas:\n" + "\n".join(m_lines)
    return block


def build_pms_automation_business_context(
    conn: sqlite3.Connection,
    user_id: int,
    pms_vendor: str,
    last_analysis_id: Optional[int],
) -> str:
    vendor_label = dict(PMS_VENDOR_CHOICES).get(pms_vendor, pms_vendor or "PMS")
    prior = _prior_analysis_excerpt(conn, user_id, last_analysis_id)
    body = (
        f"Este análisis se generó automáticamente desde un reporte programado enviado por correo desde {vendor_label}. "
        "Instrucción prioritaria: compara de forma explícita con la lectura previa de este mismo flujo automático "
        "(ver bloque de contexto abajo). Identifica tendencias (↑/↓/estable), picos o valles de reservas o ingresos, "
        "cambios en ADR o tarifa promedio, y cambios en participación por segmento o canal. "
        "Si la lectura previa no aplica o está vacía, analiza tendencias dentro del rango del export actual "
        "(primer tercio vs último tercio del periodo) y deja en datos_faltantes cómo enriquecer el próximo envío.\n\n"
        "Contexto de lectura previa (referencia; la fuente de verdad son los archivos actuales):\n"
        f"{prior}\n\n"
        f"{ideal_report_types_block()}"
    )
    return require_business_context(body)


def ensure_route_for_hotel(user_id: int, hotel_id: Optional[int]) -> sqlite3.Row:
    """
    Garantiza una fila `pms_inbound_routes` por (usuario, hotel): correo único por propiedad.
    `hotel_id` debe ser el hotel activo en sesión (o el primero del usuario si se pasa None y existe membresía).
    """
    with db() as conn:
        hid = hotel_id
        if hid is None or int(hid) <= 0:
            row0 = conn.execute(
                "SELECT hotel_id FROM hotel_members WHERE user_id = ? ORDER BY hotel_id LIMIT 1",
                (user_id,),
            ).fetchone()
            if not row0:
                raise ValueError("No hay hotel en la cuenta; completa el perfil o la invitación al equipo.")
            hid = int(row0["hotel_id"])
        else:
            hid = int(hid)
        if not conn.execute(
            "SELECT 1 FROM hotel_members WHERE user_id = ? AND hotel_id = ?",
            (user_id, hid),
        ).fetchone():
            raise ValueError("No tienes acceso a este hotel.")
        row = conn.execute(
            "SELECT * FROM pms_inbound_routes WHERE user_id = ? AND hotel_id = ?",
            (user_id, hid),
        ).fetchone()
        if row:
            return row
        token = secrets.token_hex(12)
        ts = now_iso()
        conn.execute(
            """
            INSERT INTO pms_inbound_routes (user_id, hotel_id, token, pms_vendor, notify_whatsapp, created_at, updated_at)
            VALUES (?, ?, ?, '', 1, ?, ?)
            """,
            (user_id, hid, token, ts, ts),
        )
        return conn.execute(
            "SELECT * FROM pms_inbound_routes WHERE user_id = ? AND hotel_id = ?",
            (user_id, hid),
        ).fetchone()


def ensure_route_for_user(user_id: int, hotel_id: Optional[int]) -> sqlite3.Row:
    """Alias retrocompatible: usa el hotel indicado o el primero del usuario."""
    return ensure_route_for_hotel(user_id, hotel_id)


def get_route_by_token(token: str) -> Optional[sqlite3.Row]:
    t = (token or "").strip().lower()
    if not t:
        return None
    with db() as conn:
        return conn.execute("SELECT * FROM pms_inbound_routes WHERE token = ?", (t,)).fetchone()


def update_route_settings(
    user_id: int,
    *,
    pms_vendor: str,
    notify_whatsapp: bool,
    hotel_id: Optional[int],
) -> Optional[sqlite3.Row]:
    allowed = {k for k, _ in PMS_VENDOR_CHOICES}
    pv = (pms_vendor or "").strip().lower()
    if pv not in allowed:
        pv = "other"
    with db() as conn:
        if hotel_id is None or int(hotel_id) <= 0:
            raise HTTPException(status_code=400, detail="Selecciona un hotel en el panel (sesión actual).")
        hid = int(hotel_id)
        if not conn.execute(
            "SELECT 1 FROM hotel_members WHERE hotel_id = ? AND user_id = ?",
            (hid, user_id),
        ).fetchone():
            raise HTTPException(status_code=403, detail="No tienes acceso a ese hotel.")
        if not user_is_hotel_admin(user_id, hid):
            raise HTTPException(status_code=403, detail="Solo el administrador del hotel puede cambiar esta configuración.")
        row = conn.execute(
            "SELECT * FROM pms_inbound_routes WHERE user_id = ? AND hotel_id = ?",
            (user_id, hid),
        ).fetchone()
        if not row:
            return None
        ts = now_iso()
        conn.execute(
            """
            UPDATE pms_inbound_routes
            SET pms_vendor = ?, notify_whatsapp = ?, updated_at = ?
            WHERE id = ?
            """,
            (pv, 1 if notify_whatsapp else 0, ts, int(row["id"])),
        )
        return conn.execute("SELECT * FROM pms_inbound_routes WHERE id = ?", (int(row["id"]),)).fetchone()


def _uploads_from_postmark_attachments(raw: Any) -> List[UploadFile]:
    out: List[UploadFile] = []
    if not isinstance(raw, list):
        return out
    for att in raw:
        if not isinstance(att, dict):
            continue
        name = (att.get("Name") or att.get("filename") or "adjunto").strip()
        ext = name.lower().rsplit(".", 1)[-1] if "." in name else ""
        if f".{ext}" not in ALLOWED_UPLOAD_EXTENSIONS:
            continue
        b64 = att.get("Content") or att.get("content")
        if not b64 or not isinstance(b64, str):
            continue
        try:
            data = base64.b64decode(b64, validate=False)
        except Exception:
            continue
        if len(data) > MAX_UPLOAD_BYTES_PER_FILE:
            continue
        out.append(UploadFile(filename=name, file=BytesIO(data)))
    return out


def load_user_row(user_id: int) -> Optional[sqlite3.Row]:
    with db() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def process_inbound_email_payload(
    *,
    to_field: str,
    attachments_json: Any,
    multipart_files: Optional[List[UploadFile]] = None,
) -> Dict[str, Any]:
    """
    Procesa un correo entrante: valida token, adjuntos, plan, genera lectura, actualiza cadena y opcionalmente WhatsApp.
    Devuelve dict serializable (status, mensajes).
    """
    from auth_session import onboarding_pending
    from plan_entitlements import pullso_brief_whatsapp_entitled

    from services.pullso_whatsapp_user_delivery import send_diagnosis_whatsapp_for_analysis

    token = _parse_recipient_to_token(to_field)
    if not token:
        return {"ok": False, "error": "No reconocimos un destinatario válido (formato pms.<token>@dominio)."}

    route = get_route_by_token(token)
    if not route:
        return {"ok": False, "error": "Token de inbox no válido o revocado."}

    rid_hotel = route["hotel_id"]
    if rid_hotel is None:
        return {"ok": False, "error": "Ruta de correo sin hotel asignado; reconfigura desde el panel."}
    uid = int(route["user_id"])
    with db() as conn:
        if not conn.execute(
            "SELECT 1 FROM hotel_members WHERE user_id = ? AND hotel_id = ?",
            (uid, int(rid_hotel)),
        ).fetchone():
            return {"ok": False, "error": "Token no asociado a un hotel válido."}
    user_row = load_user_row(uid)
    if not user_row:
        return {"ok": False, "error": "Usuario no encontrado."}

    user = user_row_as_dict(user_row)
    if onboarding_pending(user):
        return {"ok": False, "error": "Cuenta con onboarding pendiente; no se procesó el correo."}

    if not pms_scheduled_reports_entitled(user):
        return {"ok": False, "error": "Plan sin acceso a automatización por correo."}

    files = _uploads_from_postmark_attachments(attachments_json)
    if multipart_files:
        for f in multipart_files:
            if f and f.filename:
                ext = (f.filename.lower().rsplit(".", 1)[-1] if "." in f.filename else "")
                if f".{ext}" in ALLOWED_UPLOAD_EXTENSIONS:
                    files.append(f)

    if not files:
        return {"ok": False, "error": "No hay adjuntos CSV/Excel reconocidos."}

    with db() as conn:
        combined_business_context = build_pms_automation_business_context(
            conn,
            uid,
            str(route["pms_vendor"] or "other"),
            int(route["last_analysis_id"]) if route["last_analysis_id"] else None,
        )

    return _process_inbound_core(
        user=user,
        route=route,
        files=files,
        combined_business_context=combined_business_context,
        send_wa_fn=send_diagnosis_whatsapp_for_analysis,
        pullso_brief_whatsapp_entitled_fn=pullso_brief_whatsapp_entitled,
    )


def _process_inbound_core(
    *,
    user: Dict[str, Any],
    route: sqlite3.Row,
    files: List[UploadFile],
    combined_business_context: str,
    send_wa_fn: Any,
    pullso_brief_whatsapp_entitled_fn: Any,
) -> Dict[str, Any]:
    from datetime import datetime

    uid = int(user["id"])
    reserved_run_log_id: Optional[int] = None
    try:
        summary = summarize_reports(files)
        enforce_plan(user, summary)
        effective = get_effective_plan(user)
        reserved_run_log_id = reserve_monthly_generation_or_raise(uid, effective)

        hotel_context = {
            "hotel_nombre": user["hotel_name"],
            "hotel_tamano": user["hotel_size"] or "",
            "hotel_categoria": user["hotel_category"] or "",
            "hotel_ubicacion": user["hotel_location"] or "",
            "hotel_estrellas": user.get("hotel_stars") or 0,
            "hotel_ubicacion_destino": user.get("hotel_location_context") or "",
            "hotel_pms": user.get("hotel_pms") or "",
            "hotel_channel_manager": user.get("hotel_channel_manager") or "",
            "hotel_booking_engine": user.get("hotel_booking_engine") or "",
            "hotel_tech_other": user.get("hotel_tech_other") or "",
            "hotel_google_business_url": user.get("hotel_google_business_url") or "",
            "hotel_expedia_url": user.get("hotel_expedia_url") or "",
            "hotel_booking_url": user.get("hotel_booking_url") or "",
        }
        plan_for_model = plan_for_openai_model(effective)
        analysis = call_openai(summary, combined_business_context, hotel_context, plan_for_model)
        vendor = str(route["pms_vendor"] or "").strip() or "pms"
        n = summary["reports_detected"]
        hotel_label = ""
        try:
            from services.hotel_pullso import load_hotel_row

            hr = load_hotel_row(int(route["hotel_id"]))
            if hr and (hr["display_name"] or "").strip():
                hotel_label = (hr["display_name"] or "").strip() + " · "
        except Exception:
            pass
        title = (
            f"{hotel_label}Lectura automática ({vendor}) · {n} fuente{'s' if n != 1 else ''} · "
            f"{datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )

        hid = route["hotel_id"]
        if hid is not None:
            try:
                hid = int(hid)
            except (TypeError, ValueError):
                hid = None
        if hid is not None and hid > 0:
            if not user_is_hotel_admin(uid, hid):
                hid = None
        if hid is not None and hid <= 0:
            hid = None

        analysis_id, share_token = save_analysis(
            uid,
            title,
            effective,
            summary,
            analysis,
            files,
            reserved_run_log_id=reserved_run_log_id,
            hotel_id=hid,
        )
        reserved_run_log_id = None

        with db() as conn:
            conn.execute(
                "UPDATE pms_inbound_routes SET last_analysis_id = ?, updated_at = ? WHERE id = ?",
                (analysis_id, now_iso(), int(route["id"])),
            )

        wa_sent = False
        wa_note = ""
        if int(route["notify_whatsapp"] or 0) and pullso_brief_whatsapp_entitled_fn(user):
            try:
                send_wa_fn(uid, analysis_id)
                wa_sent = True
            except Exception as exc:
                wa_note = str(exc)[:200]
                _log.warning("WhatsApp automático no enviado: %s", exc)
        else:
            wa_note = "WhatsApp desactivado para esta ruta o plan sin Pullso Brief."

        return {
            "ok": True,
            "analysis_id": analysis_id,
            "title": title,
            "share_token": share_token,
            "whatsapp_sent": wa_sent,
            "whatsapp_note": wa_note,
        }
    except HTTPException as e:
        if reserved_run_log_id is not None:
            release_reserved_generation_row(reserved_run_log_id, uid)
        return {"ok": False, "error": e.detail, "status_code": e.status_code}
    except ValueError as e:
        if reserved_run_log_id is not None:
            release_reserved_generation_row(reserved_run_log_id, uid)
        return {"ok": False, "error": str(e)}
    except Exception as e:
        if reserved_run_log_id is not None:
            release_reserved_generation_row(reserved_run_log_id, uid)
        _log.exception("Fallo procesando inbound PMS")
        return {"ok": False, "error": str(e)[:500]}
