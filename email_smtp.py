"""Envío SMTP (recuperación contraseña, compartir análisis, lead consultoría)."""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import (
    EMAIL_FROM,
    PASSWORD_RESET_TOKEN_TTL_HOURS,
    SMTP_ENVELOPE_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_SECURITY,
    SMTP_USER,
)

_log = logging.getLogger(__name__)

_SMTP_TIMEOUT_SEC = 30


def _envelope_from() -> str:
    return (SMTP_ENVELOPE_FROM or SMTP_USER or "").strip()


def _sendmail(recipients: list[str], raw_message: str) -> None:
    env_from = _envelope_from()
    if not env_from:
        raise ValueError("smtp_envelope_from_missing")
    if SMTP_SECURITY == "ssl":
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=_SMTP_TIMEOUT_SEC) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(env_from, recipients, raw_message)
        return
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=_SMTP_TIMEOUT_SEC) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(env_from, recipients, raw_message)


def _reset_ttl_label_es(hours: int) -> str:
    return "1 hora" if hours == 1 else f"{hours} horas"


def send_password_reset_email(
    to_email: str,
    reset_link: str,
    *,
    reset_link_fallback: str | None = None,
    ttl_hours: int | None = None,
) -> bool:
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        return False
    h = PASSWORD_RESET_TOKEN_TTL_HOURS if ttl_hours is None else ttl_hours
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
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Recuperar contraseña — DRAGONNÉ"
    msg["From"] = EMAIL_FROM
    msg["To"] = to_email
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
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    try:
        _sendmail([to_email], msg.as_string())
        return True
    except Exception as exc:
        _log.warning(
            "Falló envío correo recuperación contraseña (revisar SMTP_SECURITY=%s puerto=%s): %s",
            SMTP_SECURITY,
            SMTP_PORT,
            exc,
            exc_info=True,
        )
        return False


def send_analysis_share_link_email(to_email: str, share_url: str, hotel_label: str) -> bool:
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        return False
    subject = f"Informe compartido — {hotel_label} — DRAGONNÉ"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
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
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        return False
    subject = "Nuevo lead consultoría — DRAGONNÉ"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
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
