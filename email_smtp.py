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


def _send_via_resend(to_addr: str, subject: str, text: str, html: str) -> bool:
    """Envío vía Resend (HTTPS). `from` debe ser un remitente verificado en el panel de Resend."""
    if not config.RESEND_API_KEY:
        return False
    from_addr = (config.RESEND_FROM or config.EMAIL_FROM or "").strip()
    if not from_addr:
        _log.warning("Resend: define RESEND_FROM o EMAIL_FROM con un remitente verificado")
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
        _log.warning("Resend: error de red: %s", exc, exc_info=True)
        return False
    if r.status_code in (200, 201):
        try:
            jid = r.json().get("id") if r.content else None
        except Exception:
            jid = None
        _log.info(
            "Correo recuperación: Resend API aceptó el envío (HTTP %s id=%s)",
            r.status_code,
            jid or "?",
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
        "Resend API rechazó el envío (HTTP %s): %s",
        r.status_code,
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
        _log.warning("Recuperación contraseña: destinatario vacío, no se envía")
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
    # #region agent log
    fd2ebf_log(
        "email_smtp.py:send_password_reset_email",
        "pre_channels",
        {
            "resend_key_set": bool(config.RESEND_API_KEY),
            "resend_sender_plausible": _rp if config.RESEND_API_KEY else None,
            "smtp_complete": bool(
                config.SMTP_HOST and config.SMTP_USER and config.SMTP_PASSWORD
            ),
        },
        "H3,H5",
    )
    # #endregion

    if config.RESEND_API_KEY:
        if not _rp:
            _log.warning(
                "RESEND_API_KEY definida pero remitente no usable (define RESEND_FROM o EMAIL_FROM verificable; "
                "evita localhost/ejemplo/example en el dominio). Se ignora Resend y se sigue con SMTP si hay."
            )
        elif _send_via_resend(to_addr, subject, text, html):
            return True
        else:
            _log.warning("Resend no pudo enviar; se intentará SMTP si está configurado")

    if (
        not config.SMTP_HOST
        or not config.SMTP_USER
        or not config.SMTP_PASSWORD
    ):
        _log.info(
            "Recuperación contraseña: sin Resend exitoso y SMTP incompleto; no se envía correo"
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
            "Correo recuperación contraseña: SMTP aceptó el mensaje (SECURITY=%s puerto=%s)",
            config.SMTP_SECURITY,
            config.SMTP_PORT,
        )
        return True
    except Exception as exc:
        _log.warning(
            "Falló envío correo recuperación contraseña (revisar SMTP_SECURITY=%s puerto=%s): %s",
            config.SMTP_SECURITY,
            config.SMTP_PORT,
            exc,
            exc_info=True,
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
