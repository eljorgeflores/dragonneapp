"""
Configuración central de DragonApp (entorno, rutas, límites de producto).

Fase 1: extraído de app.py para claridad. La app sigue arrancando con `uvicorn app:app`.
Deuda (Fase 2): validar variables críticas al arranque; agrupar por dominio (billing, ai, etc.).
"""
from __future__ import annotations

import os
from pathlib import Path

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
SECRET_KEY = os.getenv("APP_SECRET_KEY", "change-me-now")

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
EMAIL_FROM = os.getenv("EMAIL_FROM", "DRAGONNÉ <noreply@ejemplo.com>").strip()

API_RATE_LIMIT_PER_MINUTE = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "60"))
API_RATE_LIMIT_PER_DAY = int(os.getenv("API_RATE_LIMIT_PER_DAY", "1000"))

# --- Fuera del núcleo DragonApp (consultoría / parent); ver docs/dragonapp_phase1.md ---
CONSULTING_CALENDAR_URL = (
    os.getenv("CONSULTING_CALENDAR_URL", "").strip()
    or "https://calendar.app.google/h4SKsVcUvTp3JpNM6"
)
