"""Envío SMTP (recuperación contraseña, compartir análisis, lead consultoría)."""
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

import config
from debuglog import fd2ebf_log

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
        r = requests.post(
            _RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {config.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": from_addr,
                "to": [to_addr],
                "subject": subject,
                "text": text,
                "html": html,
            },
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
    subject = "Recuperar contraseña — DRAGONNÉ"
    text = f"""Hola,

Alguien pidió restablecer la contraseña de tu cuenta en DRAGONNÉ.

Haz clic en el siguiente enlace para elegir una nueva contraseña (válido {ttl_es}):

{reset_link}
{alt_plain}
Si no pediste esto, ignora este correo.

—
DRAGONNÉ
"""
    html = f"""<p>Hola,</p>
<p>Alguien pidió restablecer la contraseña de tu cuenta en DRAGONNÉ.</p>
<p><a href="{reset_link}">Haz clic aquí para elegir una nueva contraseña</a> (válido {ttl_es}).</p>
{alt_html}
<p>Si no pediste esto, ignora este correo.</p>
<p>—<br>DRAGONNÉ</p>"""

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
    subject = "Tu enlace para entrar — DRAGONNÉ"
    text = f"""Hola,

Usa este enlace para entrar a tu cuenta en DRAGONNÉ (válido {ttl_label}):

{magic_link}
{alt_plain}
Si no pediste este acceso, ignora este correo.

—
DRAGONNÉ
"""
    html = f"""<p>Hola,</p>
<p>Usa este enlace para entrar a tu cuenta en <strong>DRAGONNÉ</strong> (válido {ttl_label}).</p>
<p><a href="{magic_link}">Entrar ahora</a></p>
{alt_html}
<p>Si no pediste este acceso, ignora este correo.</p>
<p>—<br>DRAGONNÉ</p>"""

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
    subject = f"Informe compartido — {hotel_label} — DRAGONNÉ"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_FROM
    msg["To"] = to_email.strip()
    text = f"""Hola,

Te comparten un informe de análisis hotelero generado con DRAGONNÉ (vista de solo lectura):

{share_url}

Cualquiera con este enlace puede ver el contenido del informe. Si no esperabas este correo, ignóralo.

—
DRAGONNÉ
"""
    html = f"""<p>Hola,</p>
<p>Te comparten un informe de análisis hotelero generado con <strong>DRAGONNÉ</strong> (solo lectura).</p>
<p><a href="{share_url}">Abrir informe compartido</a></p>
<p class="muted">Cualquiera con este enlace puede ver el contenido. Si no esperabas este correo, ignóralo.</p>
<p>—<br>DRAGONNÉ</p>"""
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
