"""
Configuración central de DragonApp (entorno, rutas, límites de producto).

Fase 1: extraído de app.py para claridad. La app sigue arrancando con `uvicorn app:app`.
Deuda (Fase 2): validar variables críticas al arranque; agrupar por dominio (billing, ai, etc.).
"""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent

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

SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
# Cabecera "From" visible en el cliente de correo (puede incluir nombre <correo>)
EMAIL_FROM = os.getenv("EMAIL_FROM", "DRAGONNÉ <noreply@ejemplo.com>").strip()
# Remitente del sobre SMTP (muchas APIs exigen el mismo correo que SMTP_USER); por defecto SMTP_USER
SMTP_ENVELOPE_FROM = os.getenv("SMTP_ENVELOPE_FROM", "").strip()
# "starttls" (587 típ.) o "ssl" (SMTP_SSL, p. ej. puerto 465)
_smtp_sec = os.getenv("SMTP_SECURITY", "starttls").strip().lower()
SMTP_SECURITY = _smtp_sec if _smtp_sec in ("starttls", "ssl") else "starttls"

# Caducidad del enlace de restablecimiento (debe coincidir con textos de correo y UI)
PASSWORD_RESET_TOKEN_TTL_HOURS = max(1, int(os.getenv("PASSWORD_RESET_TOKEN_TTL_HOURS", "1")))

API_RATE_LIMIT_PER_MINUTE = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "60"))
API_RATE_LIMIT_PER_DAY = int(os.getenv("API_RATE_LIMIT_PER_DAY", "1000"))

# --- Fuera del núcleo DragonApp (consultoría / parent); ver docs/dragonapp_phase1.md ---
CONSULTING_CALENDAR_URL = (
    os.getenv("CONSULTING_CALENDAR_URL", "").strip()
    or "https://calendar.app.google/h4SKsVcUvTp3JpNM6"
)
