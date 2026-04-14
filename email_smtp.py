"""Envío SMTP (recuperación contraseña, compartir análisis, lead consultoría)."""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape

import requests

import config
from debuglog import fd2ebf_log
from seo_helpers import absolute_url

_log = logging.getLogger(__name__)

_SMTP_TIMEOUT_SEC = 30


def _yn(b: bool) -> str:
    return "Y" if b else "N"


def _envelope_from() -> str:
    return (config.SMTP_ENVELOPE_FROM or config.SMTP_USER or "").strip()


def _sendmail(recipients: list[str], raw_message: str) -> None:
    env_from = _envelope_from()
    if not env_from:
        raise ValueError("smtp_envelope_from_missing")
    tls_ctx = ssl.create_default_context()
    if config.SMTP_SECURITY == "ssl":
        with smtplib.SMTP_SSL(
            config.SMTP_HOST,
            config.SMTP_PORT,
            timeout=_SMTP_TIMEOUT_SEC,
            context=tls_ctx,
        ) as server:
            server.ehlo()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.sendmail(env_from, recipients, raw_message)
        return
    with smtplib.SMTP(
        config.SMTP_HOST, config.SMTP_PORT, timeout=_SMTP_TIMEOUT_SEC
    ) as server:
        server.ehlo()
        server.starttls(context=tls_ctx)
        server.ehlo()
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.sendmail(env_from, recipients, raw_message)


def _reset_ttl_label_es(hours: int) -> str:
    return "1 hora" if hours == 1 else f"{hours} horas"


_RESEND_API_URL = "https://api.resend.com/emails"


def _resend_response_detail(resp: requests.Response, max_len: int = 1200) -> str:
    """Texto seguro para logs (evidencia en hosting); evita volcar el cuerpo entero."""
    raw = (resp.text or "")[:max_len]
    try:
        data = resp.json()
        if isinstance(data, dict):
            bits = []
            for key in ("message", "name", "statusCode"):
                val = data.get(key)
                if val is not None and val != "":
                    bits.append(f"{key}={val}")
            if bits:
                return "; ".join(bits)
    except Exception:
        pass
    return raw


def _send_via_resend(
    to_addr: str,
    subject: str,
    text: str,
    html: str,
    *,
    purpose: str = "email",
    sender_plausible: bool,
    cc: list[str] | None = None,
) -> bool:
    """Envío vía Resend (HTTPS). `from` debe ser un remitente verificado en el panel de Resend."""
    if not config.RESEND_API_KEY:
        return False
    from_addr = (config.RESEND_FROM or config.EMAIL_FROM or "").strip()
    if not from_addr:
        _log.warning(
            "resend.rejected purpose=%s reason=sender_address_missing tried_resend=%s sender_plausible=%s",
            purpose,
            "Y",
            _yn(sender_plausible),
        )
        return False
    try:
        _payload: dict = {
            "from": from_addr,
            "to": [to_addr],
            "subject": subject,
            "text": text,
            "html": html,
        }
        if cc:
            _payload["cc"] = [c.strip() for c in cc if (c or "").strip()]
        r = requests.post(
            _RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {config.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json=_payload,
            timeout=30,
        )
    except requests.RequestException as exc:
        _log.warning(
            "resend.rejected purpose=%s reason=network_error tried_resend=%s sender_plausible=%s detail=%s",
            purpose,
            "Y",
            _yn(sender_plausible),
            type(exc).__name__,
            exc_info=True,
        )
        return False
    if r.status_code in (200, 201):
        try:
            jid = r.json().get("id") if r.content else None
        except Exception:
            jid = None
        _log.info(
            "resend.accepted purpose=%s http=%s resend_id=%s tried_resend=%s sender_plausible=%s",
            purpose,
            r.status_code,
            jid or "?",
            "Y",
            _yn(sender_plausible),
        )
        # #region agent log
        fd2ebf_log(
            "email_smtp.py:_send_via_resend",
            "response",
            {"ok": True, "http": r.status_code, "has_id": bool(jid)},
            "H4",
        )
        # #endregion
        return True
    _log.warning(
        "resend.rejected purpose=%s http=%s tried_resend=%s sender_plausible=%s detail=%s",
        purpose,
        r.status_code,
        "Y",
        _yn(sender_plausible),
        _resend_response_detail(r),
    )
    # #region agent log
    fd2ebf_log(
        "email_smtp.py:_send_via_resend",
        "response",
        {"ok": False, "http": r.status_code},
        "H4",
    )
    # #endregion
    return False


def send_password_reset_email(
    to_email: str,
    reset_link: str,
    *,
    reset_link_fallback: str | None = None,
    ttl_hours: int | None = None,
) -> bool:
    to_addr = (to_email or "").strip()
    if not to_addr:
        _log.warning(
            "password_reset.email_failed purpose=password_reset reason=empty_recipient "
            "tried_resend=N smtp_attempted=N"
        )
        return False
    h = (
        config.PASSWORD_RESET_TOKEN_TTL_HOURS
        if ttl_hours is None
        else ttl_hours
    )
    ttl_es = _reset_ttl_label_es(h)
    alt_plain = ""
    alt_html = ""
    if reset_link_fallback:
        alt_plain = f"""

Si el enlace anterior no abre en tu correo (algunos programas cortan la dirección), copia y pega este en la barra del navegador:

{reset_link_fallback}
"""
        alt_html = f"""<p>Si el enlace anterior no funciona (algunos correos cortan la dirección), copia y pega esto en el navegador:</p>
<p><a href="{reset_link_fallback}">Abrir restablecimiento (enlace alternativo)</a></p>
<p class="muted" style="font-size:0.85em;word-break:break-all;">{reset_link_fallback}</p>"""
    subject = "Recuperar contraseña — Pullso"
    text = f"""Hola,

Alguien pidió restablecer la contraseña de tu cuenta en Pullso.

Haz clic en el siguiente enlace para elegir una nueva contraseña (válido {ttl_es}):

{reset_link}
{alt_plain}
Si no pediste esto, ignora este correo.

—
Pullso
"""
    html = f"""<p>Hola,</p>
<p>Alguien pidió restablecer la contraseña de tu cuenta en Pullso.</p>
<p><a href="{reset_link}">Haz clic aquí para elegir una nueva contraseña</a> (válido {ttl_es}).</p>
{alt_html}
<p>Si no pediste esto, ignora este correo.</p>
<p>—<br>Pullso</p>"""

    _rp = config.resend_sender_plausible()
    resend_key = bool(config.RESEND_API_KEY)
    smtp_complete = bool(
        config.SMTP_HOST and config.SMTP_USER and config.SMTP_PASSWORD
    )
    resend_will_try = bool(resend_key and _rp)
    # #region agent log
    fd2ebf_log(
        "email_smtp.py:send_password_reset_email",
        "pre_channels",
        {
            "resend_key_set": resend_key,
            "resend_sender_plausible": _rp if resend_key else None,
            "smtp_complete": smtp_complete,
        },
        "H3,H5",
    )
    # #endregion

    _log.info(
        "password_reset.email_attempt purpose=password_reset resend_key_set=%s "
        "sender_plausible=%s resend_will_try=%s smtp_complete=%s",
        _yn(resend_key),
        _yn(_rp),
        _yn(resend_will_try),
        _yn(smtp_complete),
    )

    resend_http_attempted = False
    if resend_key:
        if not _rp:
            _log.warning(
                "password_reset.skipped_resend purpose=password_reset reason=sender_not_plausible "
                "resend_key_set=Y sender_plausible=N will_try_smtp=%s",
                _yn(smtp_complete),
            )
        else:
            resend_http_attempted = True
            if _send_via_resend(
                to_addr,
                subject,
                text,
                html,
                purpose="password_reset",
                sender_plausible=_rp,
            ):
                _log.info(
                    "password_reset.email_sent purpose=password_reset channel=resend "
                    "fallback_to_smtp=N sender_plausible=%s",
                    _yn(_rp),
                )
                return True
            _log.warning(
                "password_reset.resend_failed_fallback purpose=password_reset "
                "will_try_smtp=%s",
                _yn(smtp_complete),
            )

    if not smtp_complete:
        _log.info(
            "password_reset.email_failed purpose=password_reset reason=no_delivery_channel "
            "resend_http_attempted=%s smtp_complete=N sender_plausible=%s",
            _yn(resend_http_attempted),
            _yn(_rp),
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_FROM
    msg["To"] = to_addr
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    try:
        _sendmail([to_addr], msg.as_string())
        _log.info(
            "smtp.accepted purpose=password_reset security=%s port=%s "
            "fallback_after_resend=%s sender_plausible=%s",
            config.SMTP_SECURITY,
            config.SMTP_PORT,
            _yn(resend_http_attempted),
            _yn(_rp),
        )
        _log.info(
            "password_reset.email_sent purpose=password_reset channel=smtp "
            "fallback_after_resend=%s sender_plausible=%s",
            _yn(resend_http_attempted),
            _yn(_rp),
        )
        return True
    except Exception as exc:
        _log.warning(
            "smtp.failed purpose=password_reset security=%s port=%s "
            "fallback_after_resend=%s detail=%s",
            config.SMTP_SECURITY,
            config.SMTP_PORT,
            _yn(resend_http_attempted),
            type(exc).__name__,
            exc_info=True,
        )
        _log.warning(
            "password_reset.email_failed purpose=password_reset reason=smtp_error "
            "resend_http_attempted=%s",
            _yn(resend_http_attempted),
        )
        return False


def send_magic_link_email(
    to_email: str,
    magic_link: str,
    *,
    magic_link_fallback: str | None = None,
    ttl_minutes: int | None = None,
) -> bool:
    """Enlace de acceso sin contraseña (misma canalización que recuperación: Resend o SMTP)."""
    to_addr = (to_email or "").strip()
    if not to_addr:
        _log.warning(
            "magic_link.email_failed purpose=magic_link reason=empty_recipient "
            "tried_resend=N smtp_attempted=N"
        )
        return False
    m = int(config.MAGIC_LINK_TTL_MINUTES) if ttl_minutes is None else max(1, int(ttl_minutes))
    ttl_label = f"{m} minutos" if m != 1 else "1 minuto"
    alt_plain = ""
    alt_html = ""
    if magic_link_fallback:
        alt_plain = f"""

Si el enlace anterior no abre en tu correo, copia y pega esta dirección en el navegador:

{magic_link_fallback}
"""
        alt_html = f"""<p>Si el enlace anterior no funciona, copia y pega esto en el navegador:</p>
<p><a href="{magic_link_fallback}">Abrir acceso (enlace alternativo)</a></p>
<p class="muted" style="font-size:0.85em;word-break:break-all;">{magic_link_fallback}</p>"""
    subject = "Tu enlace para entrar — Pullso"
    text = f"""Hola,

Usa este enlace para entrar a tu cuenta en Pullso (válido {ttl_label}):

{magic_link}
{alt_plain}
Si no pediste este acceso, ignora este correo.

—
Pullso
"""
    html = f"""<p>Hola,</p>
<p>Usa este enlace para entrar a tu cuenta en <strong>Pullso</strong> (válido {ttl_label}).</p>
<p><a href="{magic_link}">Entrar ahora</a></p>
{alt_html}
<p>Si no pediste este acceso, ignora este correo.</p>
<p>—<br>Pullso</p>"""

    _rp = config.resend_sender_plausible()
    resend_key = bool(config.RESEND_API_KEY)
    smtp_complete = bool(
        config.SMTP_HOST and config.SMTP_USER and config.SMTP_PASSWORD
    )
    resend_will_try = bool(resend_key and _rp)

    _log.info(
        "magic_link.email_attempt purpose=magic_link resend_key_set=%s "
        "sender_plausible=%s resend_will_try=%s smtp_complete=%s",
        _yn(resend_key),
        _yn(_rp),
        _yn(resend_will_try),
        _yn(smtp_complete),
    )

    resend_http_attempted = False
    if resend_key:
        if not _rp:
            _log.warning(
                "magic_link.skipped_resend purpose=magic_link reason=sender_not_plausible "
                "resend_key_set=Y sender_plausible=N will_try_smtp=%s",
                _yn(smtp_complete),
            )
        else:
            resend_http_attempted = True
            if _send_via_resend(
                to_addr,
                subject,
                text,
                html,
                purpose="magic_link",
                sender_plausible=_rp,
            ):
                _log.info(
                    "magic_link.email_sent purpose=magic_link channel=resend "
                    "fallback_to_smtp=N sender_plausible=%s",
                    _yn(_rp),
                )
                return True
            _log.warning(
                "magic_link.resend_failed_fallback purpose=magic_link will_try_smtp=%s",
                _yn(smtp_complete),
            )

    if not smtp_complete:
        _log.warning(
            "magic_link.email_failed purpose=magic_link reason=no_delivery_channel "
            "resend_http_attempted=%s smtp_complete=N sender_plausible=%s",
            _yn(resend_http_attempted),
            _yn(_rp),
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_FROM
    msg["To"] = to_addr
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    try:
        _sendmail([to_addr], msg.as_string())
        _log.info(
            "smtp.accepted purpose=magic_link security=%s port=%s "
            "fallback_after_resend=%s sender_plausible=%s",
            config.SMTP_SECURITY,
            config.SMTP_PORT,
            _yn(resend_http_attempted),
            _yn(_rp),
        )
        _log.info(
            "magic_link.email_sent purpose=magic_link channel=smtp "
            "fallback_after_resend=%s sender_plausible=%s",
            _yn(resend_http_attempted),
            _yn(_rp),
        )
        return True
    except Exception as exc:
        _log.warning(
            "smtp.failed purpose=magic_link security=%s port=%s "
            "fallback_after_resend=%s detail=%s",
            config.SMTP_SECURITY,
            config.SMTP_PORT,
            _yn(resend_http_attempted),
            type(exc).__name__,
            exc_info=True,
        )
        _log.warning(
            "magic_link.email_failed purpose=magic_link reason=smtp_error "
            "resend_http_attempted=%s",
            _yn(resend_http_attempted),
        )
        return False


def send_analysis_share_link_email(to_email: str, share_url: str, hotel_label: str) -> bool:
    if (
        not config.SMTP_HOST
        or not config.SMTP_USER
        or not config.SMTP_PASSWORD
    ):
        return False
    subject = f"Informe compartido — {hotel_label} — Pullso"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_FROM
    msg["To"] = to_email.strip()
    text = f"""Hola,

Te comparten un informe de análisis hotelero generado con Pullso (vista de solo lectura):

{share_url}

Cualquiera con este enlace puede ver el contenido del informe. Si no esperabas este correo, ignóralo.

—
Pullso
"""
    html = f"""<p>Hola,</p>
<p>Te comparten un informe de análisis hotelero generado con <strong>Pullso</strong> (solo lectura).</p>
<p><a href="{share_url}">Abrir informe compartido</a></p>
<p class="muted">Cualquiera con este enlace puede ver el contenido. Si no esperabas este correo, ignóralo.</p>
<p>—<br>Pullso</p>"""
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    try:
        _sendmail([to_email.strip()], msg.as_string())
        return True
    except Exception as exc:
        _log.warning(
            "Falló envío correo compartir informe: %s",
            exc,
            exc_info=True,
        )
        return False


def send_consulting_lead_email(
    to_email: str,
    name: str,
    from_email: str,
    company: str,
    type_: str,
    message: str,
    phone: str,
    lang: str,
) -> bool:
    if (
        not config.SMTP_HOST
        or not config.SMTP_USER
        or not config.SMTP_PASSWORD
    ):
        return False
    subject = "Nuevo lead consultoría — DRAGONNÉ"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_FROM
    msg["To"] = to_email
    if from_email:
        msg["Reply-To"] = from_email
    lines = [
        f"Nombre: {name}",
        f"Email: {from_email}",
        f"Empresa / Proyecto: {company}",
        f"Tipo: {type_}",
        f"Teléfono: {phone}",
        "",
        "Mensaje:",
        message,
        "",
        f"Idioma del formulario: {lang}",
    ]
    text = "\n".join(lines)
    html = "<br>".join(
        [
            f"<strong>Nombre:</strong> {name}",
            f"<br><strong>Email:</strong> {from_email}",
            f"<br><strong>Empresa / Proyecto:</strong> {company}",
            f"<br><strong>Tipo:</strong> {type_}",
            f"<br><strong>Teléfono:</strong> {phone}",
            "<br><br><strong>Mensaje:</strong><br>",
            message.replace("\n", "<br>"),
            f"<br><br><em>Idioma del formulario: {lang}</em>",
        ]
    )
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    try:
        msg["To"] = to_email
        _sendmail([to_email], msg.as_string())
        return True
    except Exception as exc:
        _log.warning("Falló envío correo lead consultoría: %s", exc, exc_info=True)
        return False


def send_pullso_whatsapp_waitlist_email(
    *,
    to_email: str,
    full_name: str,
    from_email: str,
    company: str,
    whatsapp: str,
    note: str,
) -> bool:
    """Aviso interno por nueva entrada en waitlist Pullso Brief (página /pullsobrief)."""
    if (
        not config.SMTP_HOST
        or not config.SMTP_USER
        or not config.SMTP_PASSWORD
    ):
        return False
    subject = "Pullso Brief — nueva entrada en waitlist"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_FROM
    msg["To"] = to_email.strip()
    if from_email:
        msg["Reply-To"] = from_email.strip()
    note_block = (note or "").strip() or "—"
    lines = [
        "Origen: Pullso Brief — waitlist /pullsobrief/waitlist",
        f"Nombre: {full_name}",
        f"Email trabajo: {from_email}",
        f"Hotel / empresa: {company or '—'}",
        f"WhatsApp: {whatsapp}",
        "",
        "Nota opcional:",
        note_block,
    ]
    text = "\n".join(lines)
    html = "<br>".join(
        [
            "<strong>Origen:</strong> Pullso Brief — waitlist /pullsobrief/waitlist",
            f"<br><strong>Nombre:</strong> {full_name}",
            f"<br><strong>Email trabajo:</strong> {from_email}",
            f"<br><strong>Hotel / empresa:</strong> {company or '—'}",
            f"<br><strong>WhatsApp:</strong> {whatsapp}",
            "<br><br><strong>Nota opcional:</strong><br>",
            note_block.replace("\n", "<br>"),
        ]
    )
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    try:
        _sendmail([to_email.strip()], msg.as_string())
        return True
    except Exception as exc:
        _log.warning("Falló envío correo waitlist Pullso Brief: %s", exc, exc_info=True)
        return False


def send_pullso_mvp_lead_email(
    *,
    to_email: str,
    full_name: str,
    phone: str,
    lead_email: str,
    hotel_name: str,
    hotel_url: str,
    pms: str,
    channel_manager: str,
    booking_engine: str,
    lang: str,
) -> bool:
    """Aviso interno por lead desde landing Pullso MVP (/pullsomvp)."""
    if (
        not config.SMTP_HOST
        or not config.SMTP_USER
        or not config.SMTP_PASSWORD
    ):
        return False
    subject = "Pullso MVP landing: nuevo lead"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_FROM
    msg["To"] = to_email.strip()
    le = (lead_email or "").strip()
    if le:
        msg["Reply-To"] = le

    def _dash(s: str) -> str:
        t = (s or "").strip()
        return t if t else "—"

    lines = [
        "Origen: Pullso MVP /pullsomvp/lead",
        f"Idioma formulario: {lang}",
        f"Nombre: {full_name}",
        f"Teléfono: {phone}",
        f"Correo: {_dash(le)}",
        f"Hotel: {hotel_name}",
        f"Enlace hotel / OTA: {_dash(hotel_url)}",
        f"PMS: {_dash(pms)}",
        f"Channel manager: {_dash(channel_manager)}",
        f"Motor de reservas: {_dash(booking_engine)}",
    ]
    text = "\n".join(lines)
    html = "<br>".join(
        [
            "<strong>Origen:</strong> Pullso MVP /pullsomvp/lead",
            f"<br><strong>Idioma formulario:</strong> {lang}",
            f"<br><strong>Nombre:</strong> {full_name}",
            f"<br><strong>Teléfono:</strong> {phone}",
            f"<br><strong>Correo:</strong> {_dash(le)}",
            f"<br><strong>Hotel:</strong> {hotel_name}",
            f"<br><strong>Enlace hotel / OTA:</strong> {_dash(hotel_url)}",
            f"<br><strong>PMS:</strong> {_dash(pms)}",
            f"<br><strong>Channel manager:</strong> {_dash(channel_manager)}",
            f"<br><strong>Motor de reservas:</strong> {_dash(booking_engine)}",
        ]
    )
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    try:
        _sendmail([to_email.strip()], msg.as_string())
        return True
    except Exception as exc:
        _log.warning("Falló envío correo lead Pullso YC: %s", exc, exc_info=True)
        return False


DRAGONNE_DIAG_CC = "jorge@dragonne.co"


def _hospitality_diagnosis_email_bodies(
    *,
    lang: str,
    contact_name: str,
    hotel_name: str,
    savings_line: str,
    growth_line: str,
    savings_formula: str = "",
    growth_formula: str = "",
    savings_cap: str = "",
    savings_badge: str = "",
    savings_hook: str = "",
    savings_formula_label: str = "",
    growth_cap: str = "",
    growth_badge: str = "",
    growth_hook: str = "",
    growth_formula_label: str = "",
    trust_line: str = "",
    disclaimer_short: str = "",
    cta_note: str = "",
    facts_rows: list[tuple[str, str]],
    disclaimer: str,
    result_narrative: str = "",
    context_line: str = "",
    meeting_url: str = "",
) -> tuple[str, str, str]:
    """(subject, text_plain, html)"""
    sub_hotel = (hotel_name or "").replace("\n", " ").strip()[:80] or ("Hotel" if lang == "es" else "Hotel")
    cn = (contact_name or "").replace("\n", " ").strip() or ("Cliente" if lang == "es" else "Guest")
    ctx_plain = (context_line or "").replace("\n", " ").strip()
    meet = (meeting_url or "").strip()
    sav_formula_txt = (savings_formula or "").strip()
    gro_formula_txt = (growth_formula or "").strip()
    sav_cap = (savings_cap or "").strip()
    sav_badge = (savings_badge or "").strip()
    sav_hook = (savings_hook or "").strip()
    sav_formula_label = (savings_formula_label or "").strip()
    gro_cap = (growth_cap or "").strip()
    gro_badge = (growth_badge or "").strip()
    gro_hook = (growth_hook or "").strip()
    gro_formula_label = (growth_formula_label or "").strip()
    disc_short = (disclaimer_short or "").strip()
    hospitality_url_txt = absolute_url("/hoteles" if lang == "es" else "/hotels")
    if lang == "es":
        subject = f"Tu diagnóstico de posicionamiento online — {sub_hotel}"
        intro = (
            f"Hola {cn},\n\n"
            f"Gracias por el diagnóstico inicial de posicionamiento online para {sub_hotel}. "
            "Con habitaciones, ADR, ocupación y mix OTAs te dejamos dos lecturas accionables: cuánto margen suele "
            "quedar en intermediarios y un techo ilustrativo si fortaleces venta directa y ordenas canales.\n\n"
        )
        if ctx_plain:
            intro += ctx_plain + "\n\n"
        narrative_block = (f"{result_narrative.strip()}\n\n" if (result_narrative or "").strip() else "")
        if sav_cap:
            mid = (
                f"{narrative_block}"
                f"{sav_cap}\n{savings_line}\n"
                f"{(sav_badge + ' — ' if sav_badge else '')}{sav_hook}\n\n"
            )
        else:
            mid = f"{narrative_block}Ahorro anual estimado (orientativo): {savings_line}\n\n"
        if sav_formula_txt:
            mid += f"{sav_formula_label or 'Tu ruta numérica'}\n{sav_formula_txt}\n\n"
        if gro_cap:
            mid += (
                f"{gro_cap}\n{growth_line}\n"
                f"{(gro_badge + ' — ' if gro_badge else '')}{gro_hook}\n\n"
            )
        else:
            mid += f"{growth_line}\n\n"
        if gro_formula_txt:
            mid += f"{gro_formula_label or 'Tu proyección'}\n{gro_formula_txt}\n\n"
        cta_txt = f"Ver vertical de hospitality: {hospitality_url_txt}\n"
        if meet:
            cta_txt += f"Agendar reunión: {meet}\n"
        cta_txt += "\n"
        outro = (
            ("\n\n" + (disc_short or disclaimer) + "\n\n" if (disc_short or disclaimer) else "\n\n")
            + cta_txt
            + "—\nJorge Flores · Head of Hospitality\n+52 998 186 4670 · jorge@dragonne.co\n"
        )
    else:
        subject = f"Your online positioning diagnosis — {sub_hotel}"
        intro = (
            f"Hi {cn},\n\n"
            f"Thanks for completing the initial online positioning diagnosis for {sub_hotel}. "
            "From rooms, ADR, occupancy, and OTA mix we distilled two actionable reads: typical margin left "
            "in intermediaries and an illustrative upside if you strengthen direct and tidy channels.\n\n"
        )
        if ctx_plain:
            intro += ctx_plain + "\n\n"
        narrative_block = (f"{result_narrative.strip()}\n\n" if (result_narrative or "").strip() else "")
        if sav_cap:
            mid = (
                f"{narrative_block}"
                f"{sav_cap}\n{savings_line}\n"
                f"{(sav_badge + ' — ' if sav_badge else '')}{sav_hook}\n\n"
            )
        else:
            mid = f"{narrative_block}Estimated annual commission savings (indicative): {savings_line}\n\n"
        if sav_formula_txt:
            mid += f"{sav_formula_label or 'Your numeric path'}\n{sav_formula_txt}\n\n"
        if gro_cap:
            mid += (
                f"{gro_cap}\n{growth_line}\n"
                f"{(gro_badge + ' — ' if gro_badge else '')}{gro_hook}\n\n"
            )
        else:
            mid += f"{growth_line}\n\n"
        if gro_formula_txt:
            mid += f"{gro_formula_label or 'Your projection'}\n{gro_formula_txt}\n\n"
        cta_txt = f"View hospitality vertical: {hospitality_url_txt}\n"
        if meet:
            cta_txt += f"Book a meeting: {meet}\n"
        cta_txt += "\n"
        outro = (
            ("\n\n" + (disc_short or disclaimer) + "\n\n" if (disc_short or disclaimer) else "\n\n")
            + cta_txt
            + "—\nJorge Flores · Head of Hospitality\n+52 998 186 4670 · jorge@dragonne.co\n"
        )
    fact_lines_txt = "\n".join(f"{k}: {v}" for k, v in facts_rows)
    text = intro + mid + fact_lines_txt + outro

    rows_html = "".join(
        f"<tr><td style='padding:10px 14px;border-bottom:1px solid #eee;color:#555;font-size:14px'>{escape(k)}</td>"
        f"<td style='padding:10px 14px;border-bottom:1px solid #eee;font-size:14px;font-weight:600;color:#111'>{escape(v)}</td></tr>"
        for k, v in facts_rows
    )
    ctx_html = ""
    if ctx_plain:
        ctx_html = (
            "<p style=\"margin:12px 0 0;font-size:13px;line-height:1.5;color:#4b5563;"
            "border-left:3px solid #f6a905;padding-left:12px;\">"
            f"{escape(ctx_plain)}</p>"
        )
    story_p_es = (
        "Estas dos cifras resumen tu diagnóstico: margen en comisiones OTAs y potencial de crecimiento en venta directa."
    )
    story_p_en = (
        "These two figures summarize your diagnosis: OTA commission margin and direct-sales growth potential."
    )
    core_story = (result_narrative or "").strip() or (story_p_es if lang == "es" else story_p_en)
    sig_img = absolute_url("/static/team/jorge-flores.jpg")
    brand_logo = absolute_url("/static/branding/dragonne-wordmark.png")
    hospitality_url = absolute_url("/hoteles" if lang == "es" else "/hotels")
    cta_label = "Agendar reunión" if lang == "es" else "Book a meeting"
    cta_hospitality_label = "Ver vertical de hospitality" if lang == "es" else "View hospitality vertical"
    cta_html = ""
    if meet:
        cta_html = (
            "<table role=\"presentation\" width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"margin:12px 0 0;\">"
            "<tr><td align=\"center\" style=\"padding-bottom:10px;\">"
            f"<a href=\"{escape(hospitality_url)}\" target=\"_blank\" rel=\"noopener noreferrer\" "
            "style=\"display:inline-block;padding:10px 16px;border-radius:10px;"
            "background:#fff;color:#111827;text-decoration:none;"
            "font-weight:700;font-size:13px;border:1px solid #e5e7eb;\">"
            f"{escape(cta_hospitality_label)}</a>"
            "</td></tr>"
            "<tr><td align=\"center\">"
            f"<a href=\"{escape(meet)}\" target=\"_blank\" rel=\"noopener noreferrer\" "
            "style=\"display:inline-block;padding:12px 18px;border-radius:12px;"
            "background:linear-gradient(120deg,#f6a905,#f07e07);color:#fff;text-decoration:none;"
            "font-weight:800;font-size:14px;letter-spacing:.01em;\">"
            f"{escape(cta_label)}</a>"
            "</td></tr></table>"
        )
    else:
        cta_html = (
            "<table role=\"presentation\" width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"margin:12px 0 0;\">"
            "<tr><td align=\"center\">"
            f"<a href=\"{escape(hospitality_url)}\" target=\"_blank\" rel=\"noopener noreferrer\" "
            "style=\"display:inline-block;padding:10px 16px;border-radius:10px;"
            "background:#fff;color:#111827;text-decoration:none;"
            "font-weight:700;font-size:13px;border:1px solid #e5e7eb;\">"
            f"{escape(cta_hospitality_label)}</a>"
            "</td></tr></table>"
        )
    formula_css = (
        "margin:10px 0 0;padding:12px 12px 12px 14px;border-radius:14px;"
        "background:linear-gradient(165deg,rgba(246,169,5,.08),rgba(11,13,18,.04));"
        "border:1px solid rgba(11,13,18,.08);"
        "font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,'Liberation Mono','Courier New',monospace;"
        "font-size:12px;line-height:1.5;color:#111;white-space:pre-wrap;word-break:break-word;overflow-wrap:anywhere;"
    )
    def _card_html(*, cap: str, badge: str, hook: str, main: str, label: str, formula: str) -> str:
        bits = []
        if cap:
            bits.append(
                f"<p style=\"margin:0 0 6px;font-size:11px;font-weight:900;letter-spacing:.12em;text-transform:uppercase;color:#6b7280;line-height:1.35;\">{escape(cap)}</p>"
            )
        if badge:
            bits.append(
                f"<p style=\"margin:0 0 8px;font-size:11px;font-weight:800;color:#b45309;letter-spacing:.02em;\">{escape(badge)}</p>"
            )
        if main:
            bits.append(
                f"<p style=\"margin:0 0 6px;font-size:22px;font-weight:900;color:#111;letter-spacing:-.03em;line-height:1.18;\">{escape(main)}</p>"
            )
        if hook:
            bits.append(
                f"<p style=\"margin:0;font-size:13px;line-height:1.55;color:#4b5563;font-weight:600;\">{escape(hook)}</p>"
            )
        if formula:
            if label:
                bits.append(
                    f"<p style=\"margin:14px 0 0;font-size:10px;font-weight:900;letter-spacing:.12em;text-transform:uppercase;color:#b45309;\">{escape(label)}</p>"
                )
            bits.append(f"<pre style=\"{formula_css}\">{escape(formula)}</pre>")
        return "".join(bits)

    card_1 = _card_html(
        cap=sav_cap,
        badge=sav_badge,
        hook=sav_hook,
        main=savings_line,
        label=sav_formula_label,
        formula=sav_formula_txt,
    )
    card_2 = _card_html(
        cap=gro_cap,
        badge=gro_badge,
        hook=gro_hook,
        main=growth_line,
        label=gro_formula_label,
        formula=gro_formula_txt,
    )
    trust_html = ""
    disc_short_html = ""
    cta_note_html = ""
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f6;font-family:Inter,Segoe UI,system-ui,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4f4f6;padding:24px 12px;">
    <tr><td align="center">
      <table role="presentation" width="100%" style="max-width:560px;background:#fff;border-radius:16px;overflow:hidden;
        box-shadow:0 12px 40px rgba(0,0,0,.08);border:1px solid #ececf0;">
        <tr><td style="padding:0;background:linear-gradient(90deg,#f6a905,#f07e07);height:4px;font-size:0;line-height:0;">&nbsp;</td></tr>
        <tr><td style="padding:28px 28px 8px 28px;">
          <p style="margin:0 0 12px;">
            <a href="{hospitality_url}" target="_blank" rel="noopener noreferrer">
              <img src="{brand_logo}" alt="DRAGONNÉ" width="160" style="display:block;width:160px;max-width:100%;height:auto;border:0;" />
            </a>
          </p>
          <p style="margin:0 0 6px;font-size:11px;font-weight:800;letter-spacing:.14em;color:#9a9ca3;">
            {"Diagnóstico online" if lang == "es" else "Online diagnosis"}
          </p>
          <h1 style="margin:0;font-size:22px;line-height:1.2;color:#111;font-weight:800;letter-spacing:-.02em;">
            {"Diagnóstico inicial de posicionamiento online" if lang == "es" else "Initial online positioning diagnosis"}
          </h1>
          <p style="margin:14px 0 0;font-size:15px;line-height:1.55;color:#4b5563;">
            {"Hola" if lang == "es" else "Hi"} <strong>{escape(contact_name)}</strong> — {"este es tu resumen para" if lang == "es" else "here is your summary for"} <strong>{escape(hotel_name)}</strong>.
          </p>
          <p style="margin:10px 0 0;font-size:14px;line-height:1.55;color:#6b7280;">{escape(core_story)}</p>
          {ctx_html}
          {trust_html}
          {disc_short_html}
          {cta_html}
          {cta_note_html}
        </td></tr>
        <tr><td style="padding:8px 28px 20px 28px;">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-radius:14px;overflow:hidden;border:1px solid #f0e8dc;background:linear-gradient(165deg,#fffdf9,#fff7ee);">
            <tr><td style="padding:18px 20px;">{card_1}</td></tr>
          </table>
        </td></tr>
        <tr><td style="padding:0 28px 20px 28px;">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-radius:14px;overflow:hidden;border:1px solid #e5e7eb;background:#f8fafc;">
            <tr><td style="padding:18px 20px;">{card_2}</td></tr>
          </table>
        </td></tr>
        <tr><td style="padding:0 28px 8px 28px;">
          <p style="margin:0 0 8px;font-size:12px;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:.08em;">
            {"Datos declarados" if lang == "es" else "Submitted inputs"}
          </p>
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border:1px solid #eee;border-radius:10px;overflow:hidden;">
            {rows_html}
          </table>
        </td></tr>
        <tr><td style="padding:16px 28px 28px 28px;">
          <p style="margin:0;font-size:12px;line-height:1.5;color:#6b7280;">{escape(disclaimer)}</p>
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin:18px 0 0;border-top:1px solid #eee;padding-top:16px;">
            <tr>
              <td style="width:56px;vertical-align:top;">
                <img src="{sig_img}" alt="Jorge Flores" width="44" height="44"
                  style="display:block;border-radius:999px;border:1px solid #eee;object-fit:cover;" />
              </td>
              <td style="vertical-align:top;">
                <p style="margin:0;font-size:13px;font-weight:800;color:#111;line-height:1.25;">Jorge Flores</p>
                <p style="margin:2px 0 0;font-size:12px;color:#6b7280;line-height:1.35;">Head of Hospitality</p>
                <p style="margin:8px 0 0;font-size:12px;line-height:1.5;">
                  <a href="tel:+529981864670" style="color:#111;text-decoration:none;font-weight:700;">+52 998 186 4670</a><br />
                  <a href="mailto:jorge@dragonne.co" style="color:#111;text-decoration:none;font-weight:700;">jorge@dragonne.co</a>
                </p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""
    return subject, text, html


def send_hospitality_diagnosis_report(
    *,
    to_email: str,
    contact_name: str,
    lang: str,
    hotel_name: str,
    savings_line: str,
    growth_line: str,
    savings_formula: str = "",
    growth_formula: str = "",
    savings_cap: str = "",
    savings_badge: str = "",
    savings_hook: str = "",
    savings_formula_label: str = "",
    growth_cap: str = "",
    growth_badge: str = "",
    growth_hook: str = "",
    growth_formula_label: str = "",
    trust_line: str = "",
    disclaimer_short: str = "",
    cta_note: str = "",
    facts_rows: list[tuple[str, str]],
    disclaimer: str,
    result_narrative: str = "",
    context_line: str = "",
    meeting_url: str = "",
) -> bool:
    """
    Envía el reporte al lead y copia a jorge@dragonne.co (SMTP o Resend con CC).
    """
    to_addr = (to_email or "").strip()
    if not to_addr or "@" not in to_addr:
        return False
    subject, text, html = _hospitality_diagnosis_email_bodies(
        lang=lang,
        contact_name=contact_name.strip() or ("Cliente" if lang == "es" else "Guest"),
        hotel_name=hotel_name.strip() or ("Hotel" if lang == "es" else "Hotel"),
        savings_line=savings_line,
        growth_line=growth_line,
        savings_formula=savings_formula,
        growth_formula=growth_formula,
        savings_cap=savings_cap,
        savings_badge=savings_badge,
        savings_hook=savings_hook,
        savings_formula_label=savings_formula_label,
        growth_cap=growth_cap,
        growth_badge=growth_badge,
        growth_hook=growth_hook,
        growth_formula_label=growth_formula_label,
        trust_line=trust_line,
        disclaimer_short=disclaimer_short,
        cta_note=cta_note,
        facts_rows=facts_rows,
        disclaimer=disclaimer,
        result_narrative=result_narrative,
        context_line=context_line,
        meeting_url=meeting_url,
    )
    _rp = config.resend_sender_plausible()
    cc_list = [DRAGONNE_DIAG_CC]

    if config.SMTP_HOST and config.SMTP_USER and config.SMTP_PASSWORD:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = config.EMAIL_FROM
        msg["To"] = to_addr
        msg["Cc"] = ", ".join(cc_list)
        msg["Reply-To"] = DRAGONNE_DIAG_CC
        msg.attach(MIMEText(text, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))
        try:
            _sendmail([to_addr, cc_list[0]], msg.as_string())
            _log.info("hospitality_diag.email_sent channel=smtp to=%s cc=%s", to_addr, cc_list[0])
            return True
        except Exception as exc:
            _log.warning("hospitality_diag.email_failed channel=smtp detail=%s", exc, exc_info=True)

    if config.RESEND_API_KEY and _rp:
        if _send_via_resend(
            to_addr,
            subject,
            text,
            html,
            purpose="hospitality_diagnosis",
            sender_plausible=_rp,
            cc=cc_list,
        ):
            _log.info("hospitality_diag.email_sent channel=resend to=%s", to_addr)
            return True

    _log.warning("hospitality_diag.email_failed reason=no_delivery_channel to=%s", to_addr)
    return False
