"""
Configuración central de DragonApp (entorno, rutas, límites de producto).

Fase 1: extraído de app.py para claridad. La app sigue arrancando con `uvicorn app:app`.
Deuda (Fase 2): validar variables críticas al arranque; agrupar por dominio (billing, ai, etc.).
"""
from __future__ import annotations

import os
import socket
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent


def _first_nonempty_env(*names: str) -> str:
    """Primer valor definido y no vacío (documentación Django/Render suele usar EMAIL_* o MAIL_*)."""
    for name in names:
        v = (os.getenv(name) or "").strip()
        if v:
            return v
    return ""


def _normalize_api_secret(val: str) -> str:
    """Quita BOM/espacios y saltos de línea (copiar/pegar desde panel o .env mal formado)."""
    s = (val or "").strip().lstrip("\ufeff").strip()
    return s.replace("\r\n", "").replace("\n", "").strip()


_env_file = BASE_DIR / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv

        load_dotenv(_env_file)
    except ImportError:
        pass

APP_NAME = "DRAGONNÉ"
DB_PATH = BASE_DIR / "data" / "profitpilot.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_UPLOAD_EXTENSIONS = {".csv", ".xlsx", ".xls", ".xlsm"}
MAX_UPLOAD_BYTES_PER_FILE = int(os.getenv("MAX_UPLOAD_MB", "50")) * 1024 * 1024

# Límites de producto (planes)
FREE_MAX_DAYS = 30
FREE_MAX_FILES_PER_ANALYSIS = 1
FREE_MAX_ANALYSES = 3
FREE_REPORTS_PER_MONTH = 1
MONTHLY_PRICE = 19
ANNUAL_PRICE = 49
PREMIUM_MONTHLY_PRICE = 49
PRO_90_MAX_DAYS = 90
PRO_90_MAX_FILES = 5
PRO_90_MAX_ANALYSES = 10
PRO_180_MAX_DAYS = 180
PRO_180_MAX_FILES = 5
PRO_180_MAX_ANALYSES = 10
PRO_PLUS_MAX_ANALYSES = 10

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
APP_URL = os.getenv("APP_URL", "http://127.0.0.1:8000")
# Ruta pública donde el navegador ve la app (p. ej. reverse proxy en /dragonne). Vacío si está en la raíz.
_url_prefix_env = os.getenv("URL_PREFIX", "").strip().rstrip("/")
_path_from_app_url = (urlparse((APP_URL or "").strip()).path or "").rstrip("/")
if _path_from_app_url == "/":
    _path_from_app_url = ""
_raw_px = _url_prefix_env or _path_from_app_url
if _raw_px and not _raw_px.startswith("/"):
    _raw_px = "/" + _raw_px
URL_PREFIX = "" if _raw_px in ("/", "") else _raw_px
SECRET_KEY = os.getenv("APP_SECRET_KEY", "change-me-now")


def reset_password_public_path() -> str:
    """Ruta URL pública del formulario de restablecimiento (con prefijo de proxy si aplica)."""
    p = (URL_PREFIX or "").rstrip("/")
    return f"{p}/reset-password" if p else "/reset-password"


def magic_link_consume_public_path() -> str:
    """Ruta base para consumir el enlace mágico (añadir ?token= o /{token})."""
    px = (URL_PREFIX or "").rstrip("/")
    return f"{px}/login/magic-link/consume" if px else "/login/magic-link/consume"


def url_path(relative: str) -> str:
    """Ruta para cabecera Location / href internos cuando hay URL_PREFIX (proxy con subruta)."""
    rel = (relative or "").strip()
    if not rel.startswith("/"):
        rel = "/" + rel
    base = (URL_PREFIX or "").rstrip("/")
    return f"{base}{rel}" if base else rel


def internal_path(path: str) -> str:
    """Normaliza el path de la petición a ruta interna de la app (sin duplicar URL_PREFIX)."""
    p = (path or "").strip() or "/"
    base = (URL_PREFIX or "").rstrip("/")
    if not base:
        return p if p.startswith("/") else "/" + p
    if p == base or p == base + "/":
        return "/"
    if p.startswith(base + "/"):
        p = p[len(base) :]
    return p if p.startswith("/") else "/" + p


STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_MONTHLY_PRICE_ID = os.getenv("STRIPE_MONTHLY_PRICE_ID", "")
STRIPE_ANNUAL_PRICE_ID = os.getenv("STRIPE_ANNUAL_PRICE_ID", "")
STRIPE_PRO_PLUS_PRICE_ID = os.getenv("STRIPE_PRO_PLUS_PRICE_ID", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
TRIAL_DAYS = int(os.getenv("TRIAL_DAYS", "0"))
ADMIN_EMAILS = {e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()}

SMTP_HOST = _first_nonempty_env("SMTP_HOST", "EMAIL_HOST", "MAIL_SERVER")
_port_s = _first_nonempty_env("SMTP_PORT", "EMAIL_PORT")
SMTP_PORT = int(_port_s) if _port_s else 587
SMTP_USER = _first_nonempty_env("SMTP_USER", "EMAIL_HOST_USER", "MAIL_USERNAME")
SMTP_PASSWORD = _first_nonempty_env("SMTP_PASSWORD", "EMAIL_HOST_PASSWORD", "MAIL_PASSWORD")
# Cabecera "From" visible. Si no se define, alinear con SMTP_USER (noreply@ejemplo.com rompe entrega en muchos SMTP).
_email_from_env = _first_nonempty_env("EMAIL_FROM", "DEFAULT_FROM_EMAIL")
EMAIL_FROM = (
    _email_from_env
    if _email_from_env
    else (f"DRAGONNÉ <{SMTP_USER}>" if SMTP_USER else "DRAGONNÉ <noreply@localhost>")
)
# Remitente del sobre SMTP (muchas APIs exigen el mismo correo que SMTP_USER); por defecto SMTP_USER
SMTP_ENVELOPE_FROM = os.getenv("SMTP_ENVELOPE_FROM", "").strip()
# "starttls" (587 típ.) o "ssl" (SMTP_SSL, p. ej. puerto 465)
_smtp_sec = (os.getenv("SMTP_SECURITY", "starttls") or "starttls").strip().lower()
SMTP_SECURITY = _smtp_sec if _smtp_sec in ("starttls", "ssl") else "starttls"
# Django / plantillas: SSL implícito en 465 (MAIL_USE_SSL)
if (
    SMTP_SECURITY == "starttls"
    and _first_nonempty_env("EMAIL_USE_SSL", "MAIL_USE_SSL").lower() in ("1", "true", "yes")
):
    SMTP_SECURITY = "ssl"


def smtp_host_tcp_reachable(timeout_sec: float = 2.0) -> bool | None:
    """Conexión TCP al host:puerto SMTP (sin TLS ni credenciales). None si no hay host."""
    host = (SMTP_HOST or "").strip()
    if not host:
        return None
    try:
        port = int(SMTP_PORT)
    except (TypeError, ValueError):
        return None
    try:
        with socket.create_connection((host, port), timeout=timeout_sec):
            return True
    except OSError:
        return False


# API HTTPS (alternativa a SMTP en hosting que bloquea puerto o credenciales difíciles — p. ej. Resend)
RESEND_API_KEY = _normalize_api_secret(os.getenv("RESEND_API_KEY", ""))
RESEND_FROM = _first_nonempty_env("RESEND_FROM")


def resend_sender_plausible() -> bool:
    """Con RESEND_API_KEY, el From no debe ser placeholder (Resend rechaza localhost/ejemplo)."""
    if not RESEND_API_KEY:
        return True
    raw = (RESEND_FROM or EMAIL_FROM or "").strip()
    if not raw or "@" not in raw:
        return False
    low = raw.lower()
    if "localhost" in low or "ejemplo.com" in low or "example.com" in low:
        return False
    return True


def password_reset_email_delivery_configured() -> bool:
    """True si SMTP está completo o Resend está listo (clave + remitente plausible)."""
    smtp_ok = bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)
    resend_ok = bool(RESEND_API_KEY) and resend_sender_plausible()
    return smtp_ok or resend_ok


# Caducidad del enlace de restablecimiento (debe coincidir con textos de correo y UI)
PASSWORD_RESET_TOKEN_TTL_HOURS = max(1, int(os.getenv("PASSWORD_RESET_TOKEN_TTL_HOURS", "1")))

# Magic link (login sin contraseña): TTL y límites anti-abuso (ventana en segundos).
MAGIC_LINK_TTL_MINUTES = max(5, min(60, int(os.getenv("MAGIC_LINK_TTL_MINUTES", "15"))))
MAGIC_LINK_RATE_LIMIT_EMAIL = max(1, int(os.getenv("MAGIC_LINK_RATE_LIMIT_EMAIL", "5")))
MAGIC_LINK_RATE_LIMIT_IP = max(1, int(os.getenv("MAGIC_LINK_RATE_LIMIT_IP", "20")))
MAGIC_LINK_RATE_LIMIT_WINDOW_SEC = max(60, int(os.getenv("MAGIC_LINK_RATE_LIMIT_WINDOW_SEC", "900")))

API_RATE_LIMIT_PER_MINUTE = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "60"))
API_RATE_LIMIT_PER_DAY = int(os.getenv("API_RATE_LIMIT_PER_DAY", "1000"))

# --- Fuera del núcleo DragonApp (consultoría / parent); ver docs/dragonapp_phase1.md ---
CONSULTING_CALENDAR_URL = (
    os.getenv("CONSULTING_CALENDAR_URL", "").strip()
    or "https://calendar.app.google/h4SKsVcUvTp3JpNM6"
)
