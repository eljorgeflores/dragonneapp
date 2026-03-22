"""Envío SMTP (recuperación contraseña, compartir análisis, lead consultoría)."""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import EMAIL_FROM, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USER


def send_password_reset_email(to_email: str, reset_link: str) -> bool:
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Recuperar contraseña — DRAGONNÉ"
    msg["From"] = EMAIL_FROM
    msg["To"] = to_email
    text = f"""Hola,

Alguien pidió restablecer la contraseña de tu cuenta en DRAGONNÉ.

Haz clic en el siguiente enlace para elegir una nueva contraseña (válido 1 hora):

{reset_link}

Si no pediste esto, ignora este correo.

—
DRAGONNÉ
"""
    html = f"""<p>Hola,</p>
<p>Alguien pidió restablecer la contraseña de tu cuenta en DRAGONNÉ.</p>
<p><a href="{reset_link}">Haz clic aquí para elegir una nueva contraseña</a> (válido 1 hora).</p>
<p>Si no pediste esto, ignora este correo.</p>
<p>—<br>DRAGONNÉ</p>"""
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, [to_email], msg.as_string())
        return True
    except Exception:
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
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, [to_email.strip()], msg.as_string())
        return True
    except Exception:
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
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            msg["To"] = to_email
            server.sendmail(EMAIL_FROM, [to_email], msg.as_string())
        return True
    except Exception:
        return False
