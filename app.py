import hashlib
import hmac
import io
import json
import math
import os
import re
import secrets
import smtplib
import sqlite3
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple
import time

# #region agent log
def _debug_log(location: str, message: str, data: Optional[Dict] = None, hypothesis_id: Optional[str] = None, run_id: Optional[str] = None):
    try:
        _log_path = _path / ".cursor" / "debug-95cdbc.log"
        payload = {"sessionId": "95cdbc", "timestamp": int(time.time() * 1000), "location": location, "message": message, "data": data or {}, "hypothesisId": hypothesis_id or "", "runId": run_id or ""}
        with open(_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass

def _dbg(location: str, message: str, data: Optional[Dict] = None, hypothesis_id: Optional[str] = None):
    try:
        log_path = Path(__file__).resolve().parent / ".cursor" / "debug-b78cbe.log"
        payload = {"sessionId": "b78cbe", "timestamp": int(time.time() * 1000), "location": location, "message": message, "data": data or {}, "hypothesisId": hypothesis_id or ""}
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
# #endregion

# Cargar .env desde la carpeta del proyecto (así no dependes de "export" en la terminal)
_path = Path(__file__).resolve().parent
_env_file = _path / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        pass  # si no tienes python-dotenv, usa export como antes

import pandas as pd
import requests
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, Request, Response, UploadFile
from fastapi.routing import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, StreamingResponse
from fastapi.openapi.docs import get_redoc_html
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

APP_NAME = "DRAGONNÉ"
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "profitpilot.db"
# Asegurar que la carpeta de base de datos exista también en entornos como Render
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_UPLOAD_EXTENSIONS = {".csv", ".xlsx", ".xls", ".xlsm"}
MAX_UPLOAD_BYTES_PER_FILE = int(os.getenv("MAX_UPLOAD_MB", "50")) * 1024 * 1024

FREE_MAX_DAYS = 30
FREE_MAX_FILES_PER_ANALYSIS = 1
FREE_MAX_ANALYSES = 3
FREE_REPORTS_PER_MONTH = 1  # reportes gratuitos por mes (luego se bloquea hasta upgrade)
MONTHLY_PRICE = 19
ANNUAL_PRICE = 49
PREMIUM_MONTHLY_PRICE = 49
PRO_90_MAX_DAYS = 90
PRO_90_MAX_FILES = 5
PRO_90_MAX_ANALYSES = 10
PRO_180_MAX_DAYS = 180
PRO_180_MAX_FILES = 5
PRO_180_MAX_ANALYSES = 10
PRO_PLUS_MAX_ANALYSES = 10  # al llegar al límite, invitar a contactar (plan máximo)
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


def max_upload_files_for_plan(plan: str) -> int:
    """Máximo de archivos por análisis según plan de producto."""
    if plan == "free":
        return FREE_MAX_FILES_PER_ANALYSIS
    if plan == "pro":
        return PRO_90_MAX_FILES
    if plan == "pro_plus":
        return PRO_180_MAX_FILES
    return FREE_MAX_FILES_PER_ANALYSIS


def public_share_base_url() -> str:
    return (APP_URL or "http://127.0.0.1:8000").rstrip("/")
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
# Email (recuperar contraseña). Si no configuras SMTP, el enlace se muestra en pantalla (solo pruebas).
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
EMAIL_FROM = os.getenv("EMAIL_FROM", "DRAGONNÉ <noreply@ejemplo.com>").strip()
# API pública: acceso por clave asignada en Admin. Límites estándar (por clave).
API_RATE_LIMIT_PER_MINUTE = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "60"))
API_RATE_LIMIT_PER_DAY = int(os.getenv("API_RATE_LIMIT_PER_DAY", "1000"))
# Consultoría: enlace a calendario (30 min con Jorge). Puedes sobreescribirlo con CONSULTING_CALENDAR_URL en .env.
CONSULTING_CALENDAR_URL = (
    os.getenv("CONSULTING_CALENDAR_URL", "").strip()
    or "https://calendar.app.google/h4SKsVcUvTp3JpNM6"
)

app = FastAPI(
    title=APP_NAME,
    description="API para ejecutar análisis de reportes hoteleros, listar análisis y descargar PDFs. Autenticación por API key (header X-API-Key o Authorization: Bearer <key>).",
    version="1.0",
    docs_url="/docs",
    redoc_url=None,  # servimos ReDoc a mano con URL absoluta del schema para que cargue bien
    openapi_url="/openapi.json",
)
# Cookie de sesión: Secure en producción (HTTPS)
_https_only = (APP_URL or "").strip().lower().startswith("https")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, same_site="lax", https_only=_https_only)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Headers de seguridad para reducir riesgos XSS, clickjacking y fuga de referrer."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    """Para 401 (no autenticado): redirigir a login en peticiones HTML; devolver JSON con redirect en API/fetch."""
    if exc.status_code == 401:
        accept = (request.headers.get("accept") or "").lower()
        wants_html = "text/html" in accept and "application/json" not in accept
        path = (request.url.path or "").strip()
        if wants_html or path.startswith("/app") or path.startswith("/admin") or path == "/":
            next_url = path if path and path != "/" else "/app"
            return RedirectResponse(url=f"/login?next={next_url}", status_code=303)
        return JSONResponse(
            {"ok": False, "error": exc.detail or "Debes iniciar sesión", "redirect": "/login"},
            status_code=401,
        )
    raise exc


api_v1 = APIRouter(prefix="/api/v1", tags=["API v1"])
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
# SEO: app_url disponible en todas las plantillas (canonical, JSON-LD, OG)
templates.env.globals["app_url"] = (APP_URL or "").rstrip("/") or None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_SHARE_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def looks_like_email(addr: str) -> bool:
    s = (addr or "").strip()
    return bool(s) and len(s) <= 254 and bool(_SHARE_EMAIL_RE.match(s))


def send_password_reset_email(to_email: str, reset_link: str) -> bool:
    """Envía el enlace de recuperación por correo. Devuelve True si se envió, False si no hay SMTP o falló."""
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
    """Envía por SMTP el enlace público de solo lectura del análisis."""
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
    """Envía por correo el lead de la landing de consultoría."""
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


@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hotel_name TEXT NOT NULL,
                hotel_size TEXT,
                hotel_category TEXT,
                hotel_location TEXT,
                contact_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                plan TEXT NOT NULL DEFAULT 'free',
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                last_login_at TEXT,
                login_count INTEGER NOT NULL DEFAULT 0,
                is_admin INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT,
                plan_at_analysis TEXT NOT NULL,
                file_count INTEGER NOT NULL,
                days_covered INTEGER NOT NULL,
                summary_json TEXT NOT NULL,
                analysis_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                share_token TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS uploaded_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                original_name TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(analysis_id) REFERENCES analyses(id)
            );

            CREATE TABLE IF NOT EXISTS billing_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stripe_event_id TEXT UNIQUE,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                ended_at TEXT,
                request_count INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )
        # Migraciones suaves para instalaciones existentes
        for col in ["hotel_size", "hotel_category", "hotel_location", "last_login_at", "login_count", "is_admin", "api_key", "hotel_stars", "hotel_location_context",
                    "hotel_pms", "hotel_channel_manager", "hotel_booking_engine", "hotel_tech_other",
                    "hotel_google_business_url", "hotel_expedia_url", "hotel_booking_url"]:
            try:
                if col in ["login_count", "is_admin", "hotel_stars"]:
                    conn.execute(f"ALTER TABLE users ADD COLUMN {col} INTEGER DEFAULT 0")
                else:
                    conn.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
            except sqlite3.OperationalError:
                pass

        try:
            conn.execute("ALTER TABLE analyses ADD COLUMN share_token TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_analyses_share_token ON analyses(share_token) WHERE share_token IS NOT NULL"
            )
        except sqlite3.OperationalError:
            pass

        # Tabla simple para recuperación de contraseña
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT NOT NULL UNIQUE,
                expires_at TEXT NOT NULL,
                used INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )
        # Leads del formulario de consultoría (landing /consultoria)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS consulting_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                company TEXT,
                type TEXT,
                message TEXT,
                phone TEXT,
                lang TEXT,
                created_at TEXT NOT NULL
            );
            """
        )


init_db()


DATE_ALIASES = [
    "stay_date", "date", "business_date", "checkin", "check_in", "arrival", "arrival_date",
    "checkout", "check_out", "departure", "departure_date", "booking_date", "created_at",
    "reservation_date", "travel_date", "occupancy_date", "fecha", "fecha_noche", "dia",
]
REVENUE_ALIASES = [
    "net_room_revenue", "room_revenue", "revenue", "revenue_net", "net_revenue", "total_revenue",
    "room_rev", "amount", "booking_value", "room_amount", "total_amount",
    "ingresos", "ingreso", "ingreso_total", "revenue_total",
]
GROSS_ALIASES = ["gross_revenue", "gross_amount", "gross_booking_value", "sell_amount"]
COMM_ALIASES = ["commission", "commission_amount", "ota_commission", "channel_commission"]
PAYMENT_ALIASES = ["payment_cost", "card_fee", "payment_fee", "processing_fee"]
ROOM_NIGHTS_ALIASES = ["room_nights", "nights", "night_count", "roomnights"]
RESERVATION_ID_ALIASES = ["reservation_id", "booking_id", "confirmation", "conf_no", "res_id"]
CHANNEL_ALIASES = ["channel", "source", "booking_channel", "channel_name", "ota", "segmento_canal", "canal"]
STATUS_ALIASES = ["status", "reservation_status", "booking_status", "estatus"]
ROOMS_ALIASES = ["rooms", "room_count", "habitaciones"]
ADR_ALIASES = ["adr", "average_daily_rate", "tarifa_promedio"]
TAX_ALIASES = ["tax", "taxes", "vat", "impuestos"]


ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "resumen_ejecutivo": {"type": "string"},
        "metricas_clave": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string"},
                    "valor": {"type": "string"},
                    "lectura": {"type": "string"},
                },
                "required": ["nombre", "valor", "lectura"],
                "additionalProperties": False,
            },
        },
        "hallazgos_prioritarios": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "titulo": {"type": "string"},
                    "detalle": {"type": "string"},
                    "impacto": {"type": "string"},
                    "prioridad": {"type": "string"},
                },
                "required": ["titulo", "detalle", "impacto", "prioridad"],
                "additionalProperties": False,
            },
        },
        "oportunidades_directo_vs_ota": {
            "type": "array",
            "items": {"type": "string"},
        },
        "riesgos_detectados": {
            "type": "array",
            "items": {"type": "string"},
        },
        "recomendaciones_accionables": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "accion": {"type": "string"},
                    "por_que": {"type": "string"},
                    "urgencia": {"type": "string"},
                },
                "required": ["accion", "por_que", "urgencia"],
                "additionalProperties": False,
            },
        },
        "datos_faltantes": {
            "type": "array",
            "items": {"type": "string"},
        },
        "senal_de_upgrade": {
            "type": "object",
            "properties": {
                "deberia_hacer_upgrade": {"type": "boolean"},
                "motivo": {"type": "string"},
            },
            "required": ["deberia_hacer_upgrade", "motivo"],
            "additionalProperties": False,
        },
    },
    "required": [
        "resumen_ejecutivo",
        "metricas_clave",
        "hallazgos_prioritarios",
        "oportunidades_directo_vs_ota",
        "riesgos_detectados",
        "recomendaciones_accionables",
        "datos_faltantes",
        "senal_de_upgrade",
    ],
    "additionalProperties": False,
}


def normalize_col(col: Any) -> str:
    col = str(col).strip().lower()
    col = re.sub(r"[^a-z0-9]+", "_", col)
    return col.strip("_")


def maybe_to_datetime(series: pd.Series) -> Optional[pd.Series]:
    try:
        converted = pd.to_datetime(series, errors="coerce")
        success_ratio = converted.notna().mean() if len(converted) else 0
        if success_ratio >= 0.45:
            return converted
    except Exception:
        return None
    return None


def find_col(columns: List[str], aliases: List[str]) -> Optional[str]:
    for alias in aliases:
        if alias in columns:
            return alias
    for col in columns:
        for alias in aliases:
            if alias in col:
                return col
    return None


def _has_date_header(columns: Any) -> bool:
    """True si las columnas parecen encabezado de datos (tienen Fecha/Día/Date)."""
    lower = [str(c).lower() for c in columns]
    return any("fecha" in c or "date" in c or "día" in c or "dia" in c for c in lower)


def _excel_to_dataframes_openpyxl(raw: bytes, filename: str, read_only: bool = True) -> List[Tuple[str, pd.DataFrame]]:
    """Fallback: leer Excel con openpyxl directo (soporta formatos que pandas ExcelFile a veces rechaza)."""
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(raw), read_only=read_only, data_only=True)
    result = []
    try:
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows = list(ws.iter_rows(values_only=True))
            if rows:
                header = [str(c) if c is not None else "" for c in rows[0]]
                data = rows[1:]
                df = pd.DataFrame(data, columns=header)
                df = df.dropna(how="all").reset_index(drop=True)
            else:
                df = pd.DataFrame()
            result.append((f"{filename}::{sheet_name}", df))
    finally:
        if read_only:
            wb.close()
    return result


def parse_file(upload: UploadFile) -> List[Tuple[str, pd.DataFrame]]:
    ext = os.path.splitext(upload.filename or "")[1].lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ValueError(f"Formato no permitido. Solo: {', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}")
    raw = upload.file.read()
    if len(raw) > MAX_UPLOAD_BYTES_PER_FILE:
        raise ValueError(f"Archivo demasiado grande. Máximo {MAX_UPLOAD_BYTES_PER_FILE // (1024*1024)} MB por archivo.")
    if ext == ".csv":
        # Detectar separador: coma o punto y coma (común en Excel en español)
        buf = io.BytesIO(raw)
        first_line = buf.readline().decode("utf-8", errors="replace").strip()
        buf.seek(0)
        sep = ","
        if ";" in first_line and "," not in first_line:
            sep = ";"
        elif ";" in first_line and first_line.count(";") >= first_line.count(","):
            sep = ";"
        try:
            df = pd.read_csv(buf, sep=sep, encoding="utf-8")
        except Exception:
            df = pd.read_csv(io.BytesIO(raw), encoding="utf-8")
        # Si la primera fila parece encabezado de PMS (título, moneda, etc.), buscar fila con Fecha/Día
        if not _has_date_header(df.columns) and len(df) > 0:
            for skip in range(1, min(8, len(raw) // 80 + 1)):
                try:
                    buf2 = io.BytesIO(raw)
                    df2 = pd.read_csv(buf2, sep=sep, encoding="utf-8", skiprows=skip)
                    if len(df2.columns) >= 2 and _has_date_header(df2.columns):
                        df = df2
                        break
                except Exception:
                    continue
        return [(upload.filename or "reporte.csv", df)]
    if ext == ".xls":
        # Excel 97-2003: xlrd a veces marca como "corruptos" archivos válidos de PMS; ignorar esa comprobación
        try:
            excel = pd.ExcelFile(
                io.BytesIO(raw),
                engine="xlrd",
                engine_kwargs={"ignore_workbook_corruption": True},
            )
            result = []
            for sheet in excel.sheet_names:
                df = excel.parse(sheet)
                if not _has_date_header(df.columns) and len(df) >= 4:
                    for header_row in range(1, 6):
                        try:
                            df2 = excel.parse(sheet, header=header_row)
                            if len(df2.columns) >= 2 and _has_date_header(df2.columns):
                                df = df2
                                break
                        except Exception:
                            continue
                result.append((f"{upload.filename}::{sheet}", df))
            return result
        except Exception as e:
            raise ValueError(
                "No pudimos leer este archivo Excel 97-2003 (.xls). "
                "Prueba exportando el reporte en CSV o en formato .xlsx."
            ) from e
    if ext in [".xlsx", ".xlsm"]:
        # Intentar primero con pandas (rápido y estándar)
        try:
            excel = pd.ExcelFile(io.BytesIO(raw))
            result = []
            for sheet in excel.sheet_names:
                df = excel.parse(sheet)
                if not _has_date_header(df.columns) and len(df) >= 4:
                    for header_row in range(1, 6):
                        try:
                            df2 = excel.parse(sheet, header=header_row)
                            if len(df2.columns) >= 2 and _has_date_header(df2.columns):
                                df = df2
                                break
                        except Exception:
                            continue
                result.append((f"{upload.filename}::{sheet}", df))
            return result
        except Exception as e:
            err = str(e).strip().lower()
            # Si falla por “corruption” o formato raro, intentar con openpyxl en modo read_only (otra ruta de lectura)
            if "corruption" in err or "workbook" in err or "seen[" in err or "bad zip" in err or "invalid" in err:
                for use_read_only in (True, False):
                    try:
                        return _excel_to_dataframes_openpyxl(raw, upload.filename or "reporte.xlsx", read_only=use_read_only)
                    except Exception:
                        continue
                raise ValueError(
                    "No pudimos leer este Excel (formato propio de tu PMS/channel). "
                    "Estamos mejorando el soporte. Mientras tanto: exporta el mismo reporte en CSV y súbelo aquí."
                ) from e
            raise
    raise ValueError(f"Formato no soportado: {ext}")


def infer_sheet(sheet_name: str, df: pd.DataFrame) -> Dict[str, Any]:
    original_cols = [str(c) for c in df.columns]
    norm_cols = [normalize_col(c) for c in original_cols]
    work = df.copy()
    work.columns = norm_cols
    work = work.dropna(how="all")
    if len(work) > 5000:
        work = work.head(5000)

    mappings = {
        "reservation_id": find_col(norm_cols, RESERVATION_ID_ALIASES),
        "channel": find_col(norm_cols, CHANNEL_ALIASES),
        "status": find_col(norm_cols, STATUS_ALIASES),
        "revenue": find_col(norm_cols, REVENUE_ALIASES),
        "gross_revenue": find_col(norm_cols, GROSS_ALIASES),
        "commission": find_col(norm_cols, COMM_ALIASES),
        "payment_cost": find_col(norm_cols, PAYMENT_ALIASES),
        "room_nights": find_col(norm_cols, ROOM_NIGHTS_ALIASES),
        "rooms": find_col(norm_cols, ROOMS_ALIASES),
        "adr": find_col(norm_cols, ADR_ALIASES),
        "taxes": find_col(norm_cols, TAX_ALIASES),
    }

    date_candidates = []
    for col in norm_cols:
        if any(alias in col for alias in DATE_ALIASES):
            converted = maybe_to_datetime(work[col])
            if converted is not None:
                work[col] = converted
                date_candidates.append(col)

    for col in norm_cols:
        if col not in date_candidates and work[col].dtype == object:
            converted = maybe_to_datetime(work[col])
            if converted is not None and len(date_candidates) < 4:
                work[col] = converted
                date_candidates.append(col)

    checkin_col = next((c for c in date_candidates if any(x in c for x in ["checkin", "check_in", "arrival"])), None)
    checkout_col = next((c for c in date_candidates if any(x in c for x in ["checkout", "check_out", "departure"])), None)
    stay_col = next((c for c in date_candidates if any(x in c for x in ["stay", "business_date", "occupancy"])), None) or checkin_col
    booking_col = next((c for c in date_candidates if any(x in c for x in ["booking", "created", "reservation_date"])), None)

    for col in norm_cols:
        try:
            converted = pd.to_numeric(work[col], errors="coerce")
            if converted.notna().mean() >= 0.5:
                work[col] = converted
        except Exception:
            pass

    row_count = int(len(work))
    rev_col = mappings["revenue"] or mappings["gross_revenue"]
    comm_col = mappings["commission"]
    pay_col = mappings["payment_cost"]
    rn_col = mappings["room_nights"]
    channel_col = mappings["channel"]
    status_col = mappings["status"]
    adr_col = mappings["adr"]

    # Convertir columnas de dinero con formato "$1,234.56" a numérico
    def _to_numeric_currency(series: pd.Series) -> pd.Series:
        if series.dtype != object and pd.api.types.is_numeric_dtype(series):
            return series
        cleaned = series.astype(str).str.replace(r"[$,\s]", "", regex=True)
        return pd.to_numeric(cleaned, errors="coerce")

    for col in [rev_col, comm_col, pay_col, adr_col]:
        if col and col in work.columns:
            work[col] = _to_numeric_currency(work[col])

    metrics: Dict[str, Any] = {}
    if rev_col:
        metrics["revenue_total"] = round(float(work[rev_col].fillna(0).sum()), 2)
    if comm_col:
        metrics["comision_total"] = round(float(work[comm_col].fillna(0).sum()), 2)
    if pay_col:
        metrics["costo_pago_total"] = round(float(work[pay_col].fillna(0).sum()), 2)
    if rn_col:
        metrics["room_nights"] = round(float(work[rn_col].fillna(0).sum()), 2)
    elif checkin_col and checkout_col:
        metrics["room_nights"] = round(float((work[checkout_col] - work[checkin_col]).dt.days.clip(lower=0).fillna(0).sum()), 2)
    if adr_col:
        metrics["adr_promedio"] = round(float(pd.to_numeric(work[adr_col], errors="coerce").mean()), 2)
    elif metrics.get("revenue_total") and metrics.get("room_nights"):
        if metrics["room_nights"] > 0:
            metrics["adr_estimado"] = round(metrics["revenue_total"] / metrics["room_nights"], 2)

    if status_col:
        s = work[status_col].astype(str).str.lower()
        cancelled = int(s.str.contains("cancel|void|no show|noshow").sum())
        metrics["cancelaciones"] = cancelled
        metrics["cancelacion_pct"] = round((cancelled / max(row_count, 1)) * 100, 2)

    if channel_col:
        channel_series = work[channel_col].astype(str).str.strip().replace("", "Sin canal")
        top_channels = channel_series.value_counts().head(8)
        metrics["top_canales_por_reservas"] = [{"canal": str(k), "reservas": int(v)} for k, v in top_channels.items()]
        if rev_col:
            rev_by_channel = work.groupby(channel_series)[rev_col].sum().sort_values(ascending=False).head(8)
            metrics["top_canales_por_ingreso"] = [{"canal": str(k), "ingreso": round(float(v), 2)} for k, v in rev_by_channel.items()]
        if comm_col and rev_col:
            grouped = work.groupby(channel_series)[[rev_col, comm_col]].sum()
            channel_margin = []
            for chan, row in grouped.iterrows():
                margin = float(row[rev_col]) - float(row[comm_col])
                channel_margin.append({"canal": str(chan), "ingreso": round(float(row[rev_col]), 2), "comision": round(float(row[comm_col]), 2), "margen_estimado": round(margin, 2)})
            metrics["margen_estimado_por_canal"] = sorted(channel_margin, key=lambda x: x["margen_estimado"], reverse=True)[:8]

    min_date = None
    max_date = None
    for col in [stay_col, checkin_col, booking_col, checkout_col]:
        if col and col in work.columns:
            col_min = work[col].dropna().min()
            col_max = work[col].dropna().max()
            if col_min is not pd.NaT and col_max is not pd.NaT:
                if min_date is None or col_min < min_date:
                    min_date = col_min
                if max_date is None or col_max > max_date:
                    max_date = col_max
    # Reportes tipo forecast/revenue con una columna "Fecha" (una fila por día): usar primera columna de fecha
    if (min_date is None or max_date is None) and date_candidates:
        for col in date_candidates:
            if col not in work.columns:
                continue
            col_min = work[col].dropna().min()
            col_max = work[col].dropna().max()
            if col_min is not pd.NaT and col_max is not pd.NaT:
                if min_date is None or col_min < min_date:
                    min_date = col_min
                if max_date is None or col_max > max_date:
                    max_date = col_max
                break

    # Normalizar a tipo fecha (evitar numpy.int64 p. ej. fechas Excel como número)
    try:
        min_date_norm = pd.Timestamp(min_date) if min_date is not None else None
    except (TypeError, ValueError):
        min_date_norm = None
    try:
        max_date_norm = pd.Timestamp(max_date) if max_date is not None else None
    except (TypeError, ValueError):
        max_date_norm = None

    days_covered = 0
    if min_date_norm is not None and max_date_norm is not None:
        try:
            delta = max_date_norm - min_date_norm
            days_covered = int(getattr(delta, "days", delta)) + 1
        except (TypeError, ValueError):
            days_covered = 0

    fields_detected = [k for k, v in mappings.items() if v]
    return {
        "sheet_name": sheet_name,
        "rows": row_count,
        "mappings": mappings,
        "date_columns": {
            "stay": stay_col,
            "booking": booking_col,
            "checkin": checkin_col,
            "checkout": checkout_col,
        },
        "fields_detected": fields_detected,
        "metrics": metrics,
        "days_covered": days_covered,
        "date_range": {
            "start": min_date_norm.isoformat() if min_date_norm is not None else None,
            "end": max_date_norm.isoformat() if max_date_norm is not None else None,
        },
        "sample_columns": norm_cols[:30],
    }


def summarize_reports(files: List[UploadFile]) -> Dict[str, Any]:
    report_summaries = []
    max_days = 0
    all_starts = []
    all_ends = []
    for upload in files:
        sheets = parse_file(upload)
        for sheet_name, df in sheets:
            summary = infer_sheet(sheet_name, df)
            report_summaries.append(summary)
            max_days = max(max_days, summary.get("days_covered", 0))
            dr = summary.get("date_range", {})
            if dr.get("start"):
                t = pd.to_datetime(dr["start"])
                if pd.notna(t):
                    all_starts.append(t)
            if dr.get("end"):
                t = pd.to_datetime(dr["end"])
                if pd.notna(t):
                    all_ends.append(t)
    overall_days = 0
    if all_starts and all_ends:
        try:
            delta = max(all_ends) - min(all_starts)
            d = getattr(delta, "days", None)
            if d is not None and not (isinstance(d, float) and math.isnan(d)):
                overall_days = int(d) + 1
        except (TypeError, ValueError):
            pass
    return {
        "total_files": len(files),
        "reports_detected": len(report_summaries),
        "max_days_covered": max_days,
        "overall_days_covered": overall_days,
        "report_summaries": report_summaries,
    }


HOTEL_PROMPT = """
Eres DRAGONNÉ, director de revenue, distribución y e‑commerce hotelero con experiencia en cadenas internacionales. Siempre respondes en español LATAM, con lenguaje hotelero real y tono de consultor senior (claro, directo, accionable, cero “data por decir datos”).

Recibirás un JSON con:
- plan: "free_30", "pro_90" o "pro_180".
- contexto_hotel: objeto con hotel_nombre, hotel_tamano, hotel_categoria, hotel_ubicacion, hotel_estrellas, hotel_ubicacion_destino; además (opcionales): hotel_pms, hotel_channel_manager, hotel_booking_engine, hotel_tech_other (stack tecnológico), hotel_google_business_url, hotel_expedia_url, hotel_booking_url (enlaces de presencia online). Úsalo SIEMPRE para personalizar.
- contexto_negocio: qué le preocupa al usuario.
- resumen: lectura estructurada de reportes exportados desde PMS / channel / motor (CSV/Excel), incluyendo métricas por canal, días cubiertos y fechas.

Objetivo: entregar una lectura que un dueño / GM entienda en 5 minutos y que un revenue manager pueda usar para decidir hoy qué mover en precio, canales y estrategia.

Reglas de estilo general:
1) No repitas el reporte: tu trabajo NO es decir “hay X reservas” sino explicar QUÉ SIGNIFICA para el negocio. Cada vez que menciones un número, acompáñalo de una lectura (“esto indica…”, “esto implica riesgo de…”).
2) Escribe como colega senior: directo, honesto y empático. Si ves un problema serio (dependencia extrema de una OTA, precios muy bajos en fines de semana fuertes, ocupación de lunes–jueves muy floja), dilo con claridad y con sentido de urgencia.
3) Estructura siempre la respuesta en bloques claros del JSON: resumen_ejecutivo, hallazgos_prioritarios, recomendaciones_accionables, datos_faltantes. Dentro de cada bloque, prioriza 3–7 puntos potentes, no listas largas de detalles sin priorizar.

Reglas analíticas (cómo leer los datos):
4) Palancas que deben aparecer SIEMPRE que haya datos suficientes:
   - Mezcla de canales: canal directo vs OTAs, dependencia de 1–2 agencias, canales con mucho volumen pero ADR o margen neto claramente más bajo.
   - Pricing y ADR: diferencias de tarifa entre canales para las mismas fechas, entre semana vs fin de semana, y entre tipos de día (p.ej. noches con eventos/local demand drivers si las detectas).
   - Ritmo y distribución en el tiempo: qué días de la semana cargan la ocupación (¿solo viernes-sábado?, ¿se cae domingo-jueves?), tendencias dentro del rango (primer tercio vs último tercio).
   - Coste de distribución: cuando haya comisiones o % estimados, habla de margen neto y no solo de revenue bruto; si no hay comisiones, dilo y explica por qué sería clave tenerlas.
   - Riesgos y oportunidades de inventario: noches con poca demanda donde tiene sentido empujar volumen, y noches fuertes donde conviene proteger tarifa y mix directo.
5) Cuando veas patrones interesantes, dilo explícitamente. Ejemplos de redacción:
   - “Tu ocupación se concentra casi solo en viernes y sábado; de domingo a jueves el hotel funciona a media máquina.”
   - “Booking.com te aporta la mayor producción, pero a un ADR un 12–15% más bajo que el resto de tus canales en las mismas fechas; eso está erosionando margen.”
   - “El canal directo casi no participa en fines de semana fuertes; estás dejando toda la fecha en manos de OTAs con comisión.”

Uso del contexto del hotel:
6) CONTEXTO DEL HOTEL (obligatorio): El resumen_ejecutivo y las recomendaciones_accionables deben estar explícitamente adaptados al tipo de propiedad (hotel_tamano), categoría (hotel_categoria), estrellas (hotel_estrellas si > 0), ubicación geográfica (hotel_ubicacion) y posición en el destino (hotel_ubicacion_destino: centro, zona turística o periferia). No des el mismo consejo a un boutique que a un resort, ni a un hotel de ciudad que a un all-inclusive; adapta tono y expectativas a estrellas y ubicación (centro vs periferia).
7) Usa el stack tecnológico (PMS, channel manager, booking engine, otras tecnologías) para proponer acciones realistas: por ejemplo, hablar de reglas en el channel manager, ajustes de inventario hacia canal directo, paquetes en el motor de reservas, etc., siempre que tenga sentido.
8) IMPORTANTE sobre enlaces (Google My Business, Expedia, Booking): los URLs en contexto_hotel son SOLO para contexto (saber dónde está el hotel online). NUNCA inventes datos, reseñas ni métricas a partir de esas URLs; usa solo lo que viene en el resumen de reportes subidos.

Recomendaciones y enfoque accionable:
9) Recomendaciones: nada genérico tipo "revisar pricing". Sé específico en qué moverías (tarifa, canal, estancia mínima, política de cancelación, bundles, visibilidad por canal), en qué fechas / rangos de días / tipos de día y con qué objetivo (subir margen, ganar directo, reducir dependencia de OTA, etc.); y que sean coherentes con la categoría y tipo de propiedad del hotel.
10) Siempre que sea posible, traduce el hallazgo en un “plan de juego” para las próximas 2–4 semanas, agrupando acciones por prioridad: qué moverías primero, qué dejarías en observación y qué revisarías cuando haya más datos.

Datos faltantes y uso responsable:
11) No inventes datos; si asumes algo, dilo. Marca métricas estimadas como tales y mantenlas conservadoras.
12) Datos faltantes: di con claridad qué falta (ej. canales, comisiones, room nights, fechas de estancia, segmentos) y qué tipo de reporte adicional debería subir el usuario. No uses la falta de datos como excusa para no extraer valor de lo que sí existe.
13) REPORTES SIN CANALES (forecast, revenue por día): Si el resumen no incluye canales de distribución pero SÍ tiene ingresos, ADR y/o fechas (p. ej. reporte Forecast and Revenue con una fila por día), OBLIGATORIO extraer valor de lo que sí hay. Analiza: ingresos y ADR por día de la semana, diferencia entre semana vs fin de semana, tendencia en el mes, oportunidades de precio entre semana. Da recomendaciones concretas usando esos números. En resumen_ejecutivo incluye una línea tipo: "Esto es lo que podemos rescatar de tu reporte; con reportes que incluyan canales de distribución podemos aportar aún más valor (mix directo vs OTA, comisiones)." En datos_faltantes menciona canales/comisiones como mejora futura, no como excusa para no analizar lo que sí está.

Planes y señal de upgrade:
14) Planes:
   - "free_30": trata el caso como diagnóstico rápido sobre un máximo de 30 días; prioriza quick wins y, si faltan periodos para tener contexto, explícalo en la señal de upgrade.
   - "pro_90" y "pro_180": además de la foto actual, compara dentro del rango primeros días vs últimos (por ejemplo, primer tercio vs último tercio) y marca en hallazgos_prioritarios cualquier cambio de tendencia relevante (mix de canal, ADR, margen, cancelaciones). Usa también recomendaciones_accionables para proponer cómo reaccionar a esos cambios.
15) Señal de upgrade: si con más días o más reportes la lectura sería mucho más fuerte, dilo con tacto y con un ejemplo concreto (ej. "comparar este trimestre con el mismo periodo del año pasado").
16) Las integraciones directas con PMS (Mews, Cloudbeds, Little Hotelier) están pensadas como "Próximamente"; no prometas nada distinto a eso.

Devuelve SIEMPRE exclusivamente el JSON con el esquema especificado por el backend, sin texto adicional.
""".strip()


def call_openai(summary: Dict[str, Any], business_context: str, hotel_context: Dict[str, Any], plan: str) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        raise RuntimeError("No encontré OPENAI_API_KEY en el backend.")

    payload = {
        "model": DEFAULT_MODEL,
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": HOTEL_PROMPT}],
            },
            {
                "role": "user",
                "content": [{
                    "type": "input_text",
                    "text": json.dumps({
                        "plan": plan,
                        "contexto_hotel": hotel_context,
                        "uso_contexto_hotel": "Usa siempre contexto_hotel (nombre, tipo de propiedad/tamaño, categoría, ubicación) para redactar resumen_ejecutivo y recomendaciones_accionables de forma específica a este hotel.",
                        "contexto_negocio": business_context or "No se proporcionó contexto adicional.",
                        "resumen": summary,
                    }, ensure_ascii=False),
                }],
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "profitpilot_hotel_analysis",
                "schema": ANALYSIS_SCHEMA,
                "strict": True,
            }
        },
    }
    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    text = None
    if data.get("output"):
        for item in data["output"]:
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"} and content.get("text"):
                    text = content["text"]
                    break
            if text:
                break
    if not text:
        text = data.get("output_text") or data.get("text", "")
    if not text:
        raise RuntimeError("No pude leer la respuesta estructurada de OpenAI.")
    return json.loads(text)


def password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, password_hash_value: str) -> bool:
    try:
        salt, stored = password_hash_value.split("$", 1)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000).hex()
        return hmac.compare_digest(digest, stored)
    except Exception:
        return False


def create_reset_token(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    with db() as conn:
        conn.execute(
            """
            INSERT INTO password_resets (user_id, token, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, token, expires_at, now_iso()),
        )
    return token


def consume_reset_token(token: str) -> Optional[int]:
    now_ts = datetime.now(timezone.utc).isoformat()
    with db() as conn:
        row = conn.execute(
            """
            SELECT * FROM password_resets
            WHERE token = ? AND used = 0 AND expires_at > ?
            """,
            (token, now_ts),
        ).fetchone()
        if not row:
            return None
        conn.execute(
            "UPDATE password_resets SET used = 1 WHERE id = ?",
            (row["id"],),
        )
        return int(row["user_id"])


def get_current_user(request: Request) -> Optional[sqlite3.Row]:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    with db() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def require_user(request: Request) -> sqlite3.Row:
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Debes iniciar sesión")
    return user


def onboarding_pending(user: sqlite3.Row) -> bool:
    """True si el usuario aún no completó el onboarding (nombre hotel / contacto)."""
    name = (user["hotel_name"] or "").strip() if user["hotel_name"] is not None else ""
    contact = (user["contact_name"] or "").strip() if user["contact_name"] is not None else ""
    return not name or not contact


class APIRateLimiter:
    """Límites por API key: N peticiones/minuto y M/día (estándar industria)."""
    def __init__(self, per_minute: int = 60, per_day: int = 1000):
        self.per_minute = per_minute
        self.per_day = per_day
        self._data: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()

    def _day_start(self) -> str:
        return datetime.now(timezone.utc).date().isoformat()

    def check_and_consume(self, api_key: str) -> None:
        """Lanza HTTPException 429 si se excede el límite."""
        now = time.time()
        today = self._day_start()
        with self._lock:
            rec = self._data.get(api_key)
            if not rec:
                rec = {"minute_count": 0, "minute_ts": now, "day_count": 0, "day_date": today}
                self._data[api_key] = rec
            if now - rec["minute_ts"] >= 60:
                rec["minute_count"] = 0
                rec["minute_ts"] = now
            if rec["day_date"] != today:
                rec["day_count"] = 0
                rec["day_date"] = today
            rec["minute_count"] += 1
            rec["day_count"] += 1
            if rec["minute_count"] > self.per_minute:
                raise HTTPException(
                    status_code=429,
                    detail=f"Límite por minuto excedido ({self.per_minute} req/min). Intenta más tarde.",
                    headers={"Retry-After": "60"},
                )
            if rec["day_count"] > self.per_day:
                raise HTTPException(
                    status_code=429,
                    detail=f"Límite diario excedido ({self.per_day} req/día). Mañana se reinicia.",
                    headers={"Retry-After": "86400"},
                )


api_rate_limiter = APIRateLimiter(per_minute=API_RATE_LIMIT_PER_MINUTE, per_day=API_RATE_LIMIT_PER_DAY)

LOGIN_RATE_LIMIT_ATTEMPTS = 6
LOGIN_RATE_LIMIT_WINDOW_SEC = 300  # 5 minutos


class LoginRateLimiter:
    """Límite de intentos de login fallidos por IP para mitigar fuerza bruta."""
    def __init__(self, max_attempts: int = 6, window_sec: int = 300):
        self.max_attempts = max_attempts
        self.window_sec = window_sec
        self._attempts: Dict[str, List[float]] = {}
        self._lock = Lock()

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return (request.scope.get("client") or ("", 0))[0] or "unknown"

    def is_blocked(self, request: Request) -> bool:
        ip = self._client_ip(request)
        now = time.time()
        with self._lock:
            if ip not in self._attempts:
                return False
            self._attempts[ip] = [t for t in self._attempts[ip] if now - t < self.window_sec]
            return len(self._attempts[ip]) >= self.max_attempts

    def record_failed(self, request: Request) -> None:
        ip = self._client_ip(request)
        now = time.time()
        with self._lock:
            if ip not in self._attempts:
                self._attempts[ip] = []
            self._attempts[ip] = [t for t in self._attempts[ip] if now - t < self.window_sec]
            self._attempts[ip].append(now)


login_rate_limiter = LoginRateLimiter(max_attempts=LOGIN_RATE_LIMIT_ATTEMPTS, window_sec=LOGIN_RATE_LIMIT_WINDOW_SEC)


def get_api_user(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
) -> sqlite3.Row:
    """Autenticación: API key asignada en Admin. Rate limit por clave."""
    key = x_api_key
    if not key and authorization and authorization.startswith("Bearer "):
        key = authorization[7:].strip()
    if not key:
        raise HTTPException(status_code=401, detail="Falta API key. Usa el header X-API-Key o Authorization: Bearer <tu_key>.")
    with db() as conn:
        user = conn.execute("SELECT * FROM users WHERE api_key = ?", (key,)).fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="API key inválida o no autorizada. Solicita acceso en la web.")
    api_rate_limiter.check_and_consume(key)
    if onboarding_pending(user):
        raise HTTPException(status_code=403, detail="Completa el onboarding antes de usar la API.")
    return user


def plan_label(plan: str) -> str:
    if plan == "pro_plus":
        return "Pro+"
    if plan == "pro":
        return "Pro"
    return "Gratis"


def is_admin_user(user: sqlite3.Row) -> bool:
    if user["is_admin"]:
        return True
    if ADMIN_EMAILS and user["email"].strip().lower() in ADMIN_EMAILS:
        return True
    return False


def require_admin(request: Request) -> sqlite3.Row:
    user = require_user(request)
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador.")
    return user


ADMIN_PLAN_VALUES = frozenset({"free", "pro", "pro_plus"})


def _delete_uploaded_files_for_analysis(conn, analysis_id: int) -> None:
    rows = conn.execute("SELECT stored_path FROM uploaded_files WHERE analysis_id = ?", (analysis_id,)).fetchall()
    for r in rows:
        try:
            p = Path(r["stored_path"])
            if p.is_file():
                p.unlink()
        except OSError:
            pass
    conn.execute("DELETE FROM uploaded_files WHERE analysis_id = ?", (analysis_id,))


def delete_analysis_by_id(conn, analysis_id: int) -> bool:
    """Borra análisis, filas de uploaded_files y archivos en disco."""
    row = conn.execute("SELECT id FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
    if not row:
        return False
    _delete_uploaded_files_for_analysis(conn, analysis_id)
    conn.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
    return True


def delete_user_and_related(conn, user_id: int) -> bool:
    """Borra todos los análisis (y archivos) del usuario, sesiones y el usuario."""
    rows = conn.execute("SELECT id FROM analyses WHERE user_id = ?", (user_id,)).fetchall()
    for r in rows:
        _delete_uploaded_files_for_analysis(conn, r["id"])
    conn.execute("DELETE FROM analyses WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
    cur = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    return cur.rowcount > 0


def analyses_count(user_id: int) -> int:
    with db() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM analyses WHERE user_id = ?", (user_id,)).fetchone()
        return int(row["c"])


def analyses_this_month(user_id: int) -> int:
    """Análisis creados en el mes actual (UTC) para el usuario."""
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()[:19]
    with db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM analyses WHERE user_id = ? AND created_at >= ?",
            (user_id, start_of_month),
        ).fetchone()
        return int(row["c"])


def upload_eligibility(user: sqlite3.Row) -> Dict[str, Any]:
    """
    Indica si el usuario puede subir un nuevo análisis y qué mostrar si no.
    Devuelve: can_upload, limit_reason, invite_upgrade, invite_contact, contact_email.
    """
    uid = user["id"]
    plan = user["plan"]
    contact_email = next(iter(ADMIN_EMAILS), None) if ADMIN_EMAILS else None

    if plan == "free":
        month_count = analyses_this_month(uid)
        total_count = analyses_count(uid)
        if month_count >= FREE_REPORTS_PER_MONTH:
            return {
                "can_upload": False,
                "limit_reason": "Ya usaste tu reporte gratuito de este mes.",
                "invite_upgrade": True,
                "invite_contact": False,
                "contact_email": contact_email,
            }
        if total_count >= FREE_MAX_ANALYSES:
            return {
                "can_upload": False,
                "limit_reason": f"Ya tienes {FREE_MAX_ANALYSES} análisis guardados (límite del plan gratis).",
                "invite_upgrade": True,
                "invite_contact": False,
                "contact_email": contact_email,
            }
        return {"can_upload": True, "limit_reason": None, "invite_upgrade": False, "invite_contact": False, "contact_email": contact_email}

    if plan == "pro":
        total_count = analyses_count(uid)
        if total_count >= PRO_90_MAX_ANALYSES:
            return {
                "can_upload": False,
                "limit_reason": "Has llegado al límite de análisis guardados de Pro.",
                "invite_upgrade": True,
                "invite_contact": True,
                "contact_email": contact_email,
            }
        return {"can_upload": True, "limit_reason": None, "invite_upgrade": False, "invite_contact": False, "contact_email": contact_email}

    if plan == "pro_plus":
        total_count = analyses_count(uid)
        if total_count >= PRO_PLUS_MAX_ANALYSES:
            return {
                "can_upload": False,
                "limit_reason": "Has llegado al límite de análisis de tu plan.",
                "invite_upgrade": False,
                "invite_contact": True,
                "contact_email": contact_email,
            }
        return {"can_upload": True, "limit_reason": None, "invite_upgrade": False, "invite_contact": False, "contact_email": contact_email}

    return {"can_upload": True, "limit_reason": None, "invite_upgrade": False, "invite_contact": False, "contact_email": contact_email}


def enforce_plan(user: sqlite3.Row, summary: Dict[str, Any]):
    uid = user["id"]
    plan = user["plan"]

    if plan == "free":
        if summary["total_files"] > FREE_MAX_FILES_PER_ANALYSIS:
            raise HTTPException(status_code=402, detail=f"El plan gratis permite hasta {FREE_MAX_FILES_PER_ANALYSIS} archivos por análisis.")
        if summary["overall_days_covered"] > FREE_MAX_DAYS or summary["max_days_covered"] > FREE_MAX_DAYS:
            raise HTTPException(status_code=402, detail=f"El plan gratis permite interpretar hasta {FREE_MAX_DAYS} días de histórico o futuro por análisis.")
        if analyses_this_month(uid) >= FREE_REPORTS_PER_MONTH:
            raise HTTPException(status_code=402, detail="Ya usaste tu reporte gratuito de este mes. Pásate a Pro para seguir subiendo.")
        if analyses_count(uid) >= FREE_MAX_ANALYSES:
            raise HTTPException(status_code=402, detail=f"Ya tienes {FREE_MAX_ANALYSES} análisis guardados (límite del plan gratis). Pásate a Pro para guardar más.")
        return

    if plan == "pro":
        if summary["total_files"] > PRO_90_MAX_FILES:
            raise HTTPException(status_code=402, detail=f"El plan Pro permite hasta {PRO_90_MAX_FILES} archivos por análisis.")
        if summary["overall_days_covered"] > PRO_90_MAX_DAYS or summary["max_days_covered"] > PRO_90_MAX_DAYS:
            raise HTTPException(status_code=402, detail=f"El plan Pro permite hasta {PRO_90_MAX_DAYS} días por análisis. Sube a Pro+ para 180 días.")
        if analyses_count(uid) >= PRO_90_MAX_ANALYSES:
            raise HTTPException(status_code=402, detail="Has llegado al límite de análisis guardados de Pro. Sube a Pro+ o contáctanos.")
        return

    if plan == "pro_plus":
        if summary["total_files"] > PRO_180_MAX_FILES:
            raise HTTPException(status_code=402, detail=f"El plan Pro+ permite hasta {PRO_180_MAX_FILES} archivos por análisis.")
        if summary["overall_days_covered"] > PRO_180_MAX_DAYS or summary["max_days_covered"] > PRO_180_MAX_DAYS:
            raise HTTPException(status_code=402, detail=f"El plan Pro+ permite hasta {PRO_180_MAX_DAYS} días por análisis.")
        if analyses_count(uid) >= PRO_PLUS_MAX_ANALYSES:
            raise HTTPException(status_code=402, detail="Has llegado al límite de análisis de tu plan. Contáctanos para ampliar tu capacidad.")
        return


def save_analysis(user_id: int, title: str, plan: str, summary: Dict[str, Any], analysis: Dict[str, Any], files: List[UploadFile]) -> Tuple[int, str]:
    created_at = now_iso()
    share_token = secrets.token_urlsafe(24)
    with db() as conn:
        cur = conn.execute(
            """
            INSERT INTO analyses (user_id, title, plan_at_analysis, file_count, days_covered, summary_json, analysis_json, created_at, share_token)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                title,
                plan,
                len(files),
                int(summary.get("overall_days_covered", 0)),
                json.dumps(summary, ensure_ascii=False),
                json.dumps(analysis, ensure_ascii=False),
                created_at,
                share_token,
            ),
        )
        analysis_id = cur.lastrowid
        for upload in files:
            upload.file.seek(0)
            content = upload.file.read()
            if len(content) > MAX_UPLOAD_BYTES_PER_FILE:
                raise ValueError("Archivo excede el tamaño máximo permitido.")
            ext = (Path(upload.filename or "archivo").suffix or "").lower()
            if ext not in ALLOWED_UPLOAD_EXTENSIONS:
                ext = ".bin"
            safe_name = f"u{user_id}_a{analysis_id}_{secrets.token_hex(8)}{ext}"
            file_path = UPLOAD_DIR / safe_name
            file_path.write_bytes(content)
            conn.execute(
                "INSERT INTO uploaded_files (analysis_id, original_name, stored_path, created_at) VALUES (?, ?, ?, ?)",
                (analysis_id, upload.filename or safe_name, str(file_path), created_at),
            )
        return analysis_id, share_token


def format_money(value: float) -> str:
    return f"${value:,.2f}"


def stripe_request(method: str, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
    if not STRIPE_SECRET_KEY:
        raise RuntimeError("Falta STRIPE_SECRET_KEY")
    response = requests.request(
        method,
        f"https://api.stripe.com{path}",
        auth=(STRIPE_SECRET_KEY, ""),
        data=data,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def ensure_stripe_customer(user: sqlite3.Row) -> str:
    if user["stripe_customer_id"]:
        return user["stripe_customer_id"]
    customer = stripe_request("POST", "/v1/customers", {
        "email": user["email"],
        "name": user["contact_name"],
        "metadata[user_id]": str(user["id"]),
        "metadata[hotel_name]": user["hotel_name"],
    })
    customer_id = customer["id"]
    with db() as conn:
        conn.execute("UPDATE users SET stripe_customer_id = ?, updated_at = ? WHERE id = ?", (customer_id, now_iso(), user["id"]))
    return customer_id


def sync_user_from_stripe_customer(customer_id: str, subscription_id: Optional[str], status: str):
    plan = "free"
    if status in {"active", "trialing", "past_due"} and subscription_id:
        try:
            sub = stripe_request("GET", f"/v1/subscriptions/{subscription_id}")
            items = sub.get("items", {}).get("data", [])
            if items:
                price_obj = items[0].get("price")
                price_id = price_obj.get("id", "") if isinstance(price_obj, dict) else (price_obj or "")
                if price_id == STRIPE_PRO_PLUS_PRICE_ID:
                    plan = "pro_plus"
                elif price_id in (STRIPE_MONTHLY_PRICE_ID, STRIPE_ANNUAL_PRICE_ID):
                    plan = "pro"
                else:
                    plan = "pro"
        except Exception:
            plan = "pro"
    elif status in {"active", "trialing", "past_due"}:
        plan = "pro"
    with db() as conn:
        conn.execute(
            "UPDATE users SET plan = ?, stripe_subscription_id = ?, updated_at = ? WHERE stripe_customer_id = ?",
            (plan, subscription_id, now_iso(), customer_id),
        )


def _marketing_context():
    return {
        "monthly_price": MONTHLY_PRICE,
        "annual_price": ANNUAL_PRICE,
        "free_max_days": FREE_MAX_DAYS,
        "free_max_files": FREE_MAX_FILES_PER_ANALYSIS,
        "free_max_analyses": FREE_MAX_ANALYSES,
        "premium_monthly_price": PREMIUM_MONTHLY_PRICE,
        "pro_90_max_days": PRO_90_MAX_DAYS,
        "pro_90_max_files": PRO_90_MAX_FILES,
        "pro_90_max_analyses": PRO_90_MAX_ANALYSES,
        "pro_180_max_days": PRO_180_MAX_DAYS,
        "pro_180_max_files": PRO_180_MAX_FILES,
        "pro_180_max_analyses": PRO_180_MAX_ANALYSES,
        "current_year": datetime.now(timezone.utc).year,
    }


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    # #region agent log
    _debug_log("app.py:home", "GET / entry", {"has_user": bool(get_current_user(request))}, "H2")
    # #endregion
    user = get_current_user(request)
    if user:
        return RedirectResponse("/app", status_code=303)
    ctx = _marketing_context()
    # #region agent log
    _debug_log("app.py:home", "marketing context keys", {"keys": list(ctx.keys())}, "H2")
    # #endregion
    return templates.TemplateResponse("marketing.html", {"request": request, **ctx})


@app.get("/marketing", response_class=HTMLResponse)
def marketing_alias(request: Request):
    """Alias legible para la landing principal del producto."""
    return home(request)


@app.get("/precios", response_class=HTMLResponse)
def precios_page(request: Request):
    """Página de precios fuera de la landing para reducir fricción."""
    return templates.TemplateResponse("precios.html", {"request": request, **_marketing_context()})


def _consulting_translations():
    """Carga traducciones desde consulting_i18n (ruta relativa a app.py para evitar import errors)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "consulting_i18n",
        BASE_DIR / "consulting_i18n.py",
    )
    if spec is None or spec.loader is None:
        return {"es": {}, "en": {}}
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "CONSULTING_TRANSLATIONS", {"es": {}, "en": {}})


class _DefaultT(dict):
    """Dict que devuelve '' para cualquier clave faltante (evita UndefinedError en plantilla)."""
    def __missing__(self, key):
        return ""


@app.get("/consultoria", response_class=HTMLResponse)
def consulting_landing(request: Request, lang: str = Query("es", alias="lang")):
    """Landing de consultoría: startups, SMBs, hospitalidad. Soporta ?lang=es|en."""
    if lang not in ("es", "en"):
        lang = "es"
    trans = _consulting_translations()
    t = trans.get(lang) or trans.get("es")
    if not t:
        t = _DefaultT()
    else:
        t = _DefaultT(t)
    try:
        lead_path = request.url_for("consulting_lead_submit").path
    except Exception:
        lead_path = "/consultoria/lead"
    return templates.TemplateResponse(
        "consulting.html",
        {
            "request": request,
            "current_year": datetime.now(timezone.utc).year,
            "lang": lang,
            "t": t,
            "calendar_url": CONSULTING_CALENDAR_URL,
            "lead_form_action": lead_path,
        },
    )


@app.get("/consulting", response_class=HTMLResponse)
def consulting_landing_en(request: Request, lang: str = Query("en", alias="lang")):
    """
    Alias en inglés para la landing de consultoría: dragonne.co/consulting.
    Por defecto sirve la versión en inglés (?lang=en), pero respeta ?lang=es|en.
    """
    return consulting_landing(request=request, lang=lang)


@app.post("/consultoria/lead", name="consulting_lead_submit")
def consulting_lead_submit(
    request: Request,
    name: str = Form(..., min_length=1, max_length=200),
    email: str = Form(..., min_length=1, max_length=254),
    company: str = Form(""),
    type: str = Form(""),
    message: str = Form(""),
    phone: str = Form(""),
    lang: str = Form("es"),
):
    """Captura lead del formulario de la landing de consultoría. Guarda en DB y envía correo."""
    email = email.strip().lower()
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return JSONResponse({"ok": False, "error": "invalid_email"}, status_code=400)
    now = datetime.now(timezone.utc).isoformat()
    with db() as conn:
        conn.execute(
            """INSERT INTO consulting_leads (name, email, company, type, message, phone, lang, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (name.strip()[:200], email, (company or "").strip()[:300], (type or "").strip()[:80], (message or "").strip()[:5000], (phone or "").strip()[:50], (lang or "es")[:5], now),
        )
    # Email a jorge@dragonne.co
    try:
        send_consulting_lead_email(
            to_email="jorge@dragonne.co",
            name=name.strip()[:200],
            from_email=email,
            company=(company or "").strip()[:300],
            type_=(type or "").strip()[:80],
            message=(message or "").strip()[:5000],
            phone=(phone or "").strip()[:50],
            lang=(lang or "es")[:5],
        )
    except Exception:
        # No rompemos el flujo si el correo falla; queda en DB
        pass
    return JSONResponse({"ok": True})


@app.get("/pricing", include_in_schema=False)
def pricing_redirect():
    """Redirige a la página de precios en español."""
    return RedirectResponse("/precios", status_code=302)


@app.get("/api", response_class=HTMLResponse)
def api_docs_page(request: Request):
    """Página de documentación de la API; enlaza a /docs y /redoc."""
    return templates.TemplateResponse("api_docs.html", {"request": request})


@app.get("/redoc", include_in_schema=False)
def redoc_docs(request: Request):
    """ReDoc: schema en ruta relativa (mismo origen) y ReDoc 2.x estable."""
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{APP_NAME} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
    )


@app.get("/sitemap.xml", response_class=Response)
def sitemap_xml():
    """Sitemap XML para SEO y crawlers."""
    base = (APP_URL or "http://127.0.0.1:8000").rstrip("/")
    urls = [
        base + "/",
        base + "/login",
        base + "/signup",
        base + "/precios",
        base + "/api",
        base + "/#producto",
        base + "/#como-funciona",
        base + "/#prueba",
        base + "/#integraciones",
    ]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        xml += f"  <url><loc>{u}</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>\n"
    xml += "</urlset>"
    return Response(content=xml, media_type="application/xml")


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    """Indica a crawlers la ubicación del sitemap."""
    base = (APP_URL or "http://127.0.0.1:8000").rstrip("/")
    return PlainTextResponse(
        "User-agent: *\nAllow: /\nDisallow: /app\nDisallow: /admin\nDisallow: /s/\nSitemap: " + base + "/sitemap.xml\n"
    )


@app.get("/mockup-analisis", response_class=HTMLResponse)
def mockup_analisis(request: Request):
    """Vista estática de cómo se ve un análisis en la plataforma (para demo/marketing)."""
    return templates.TemplateResponse("mockup_analisis.html", {"request": request})


@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    if get_current_user(request):
        return RedirectResponse("/app", status_code=303)
    return templates.TemplateResponse("signup.html", {"request": request, "error": None})


@app.post("/signup")
def signup(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(""),
):
    email = email.strip().lower()
    if len(password) < 8:
        return templates.TemplateResponse("signup.html", {"request": request, "error": "La contraseña debe tener al menos 8 caracteres."}, status_code=400)
    if password != password_confirm:
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Las contraseñas no coinciden."}, status_code=400)
    with db() as conn:
        exists = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if exists:
            return templates.TemplateResponse("signup.html", {"request": request, "error": "Ese correo ya está registrado."}, status_code=400)
        cur = conn.execute(
            """
            INSERT INTO users (
                hotel_name,
                hotel_size,
                hotel_category,
                hotel_location,
                contact_name,
                email,
                password_hash,
                plan,
                created_at,
                updated_at
            ) VALUES ('', NULL, NULL, NULL, '', ?, ?, 'free', ?, ?)
            """,
            (email, password_hash(password), now_iso(), now_iso()),
        )
        request.session["user_id"] = cur.lastrowid
    return RedirectResponse("/onboarding", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next_url: str = Query("", alias="next")):
    user = get_current_user(request)
    if user:
        return RedirectResponse("/admin" if is_admin_user(user) else "/app", status_code=303)
    next_safe = next_url.strip() if next_url and next_url.strip().startswith("/") and not next_url.strip().startswith("//") else ""
    return templates.TemplateResponse("login.html", {"request": request, "error": None, "next": next_safe})


@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), next_url: str = Form("", alias="next")):
    if login_rate_limiter.is_blocked(request):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Demasiados intentos. Espera unos minutos e intenta de nuevo."}, status_code=429)
    with db() as conn:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    if not user or not verify_password(password, user["password_hash"]):
        login_rate_limiter.record_failed(request)
        return templates.TemplateResponse("login.html", {"request": request, "error": "Correo o contraseña incorrectos."}, status_code=400)
    # Actualizamos métricas de login
    with db() as conn:
        conn.execute(
            "UPDATE users SET last_login_at = ?, login_count = COALESCE(login_count, 0) + 1, updated_at = ? WHERE id = ?",
            (now_iso(), now_iso(), user["id"]),
        )
        cur = conn.execute(
            "INSERT INTO user_sessions (user_id, started_at, last_seen_at, request_count) VALUES (?, ?, ?, ?)",
            (user["id"], now_iso(), now_iso(), 1),
        )
        session_id = cur.lastrowid
    request.session["user_id"] = user["id"]
    request.session["session_id"] = session_id
    next_safe = next_url.strip() if next_url and next_url.strip().startswith("/") and not next_url.strip().startswith("//") else ""
    redirect_to = next_safe or "/app"
    # Si es admin y no pidió una URL concreta, llevarlo al panel admin (gestión de usuarios, accesos)
    if not next_safe and is_admin_user(user):
        redirect_to = "/admin"
    # #region agent log
    _debug_log("app.py:login", "POST login success", {"redirect_to": redirect_to}, "H3")
    # #endregion
    return RedirectResponse(redirect_to, status_code=303)


@app.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    if get_current_user(request):
        return RedirectResponse("/app", status_code=303)
    return templates.TemplateResponse("forgot_password.html", {"request": request, "sent": False, "error": None, "reset_link": None, "smtp_configured": bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)})


@app.post("/forgot-password", response_class=HTMLResponse)
def forgot_password(request: Request, email: str = Form(...)):
    email = email.strip().lower()
    reset_link = None
    email_sent = False
    smtp_configured = bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)
    try:
        with db() as conn:
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not user:
            return templates.TemplateResponse("forgot_password.html", {"request": request, "sent": True, "error": None, "reset_link": None, "email_sent": False, "smtp_configured": smtp_configured})
        token = create_reset_token(user["id"])
        reset_link = f"{APP_URL}/reset-password/{token}"
        if send_password_reset_email(email, reset_link):
            email_sent = True
            reset_link = None  # No mostrar en pantalla cuando el correo se envió bien
        return templates.TemplateResponse("forgot_password.html", {"request": request, "sent": True, "error": None, "reset_link": reset_link, "email_sent": email_sent, "smtp_configured": smtp_configured})
    except Exception:
        return templates.TemplateResponse("forgot_password.html", {
            "request": request, "sent": False, "error": "Algo falló al generar el enlace. Vuelve a intentar; si el servidor no tiene correo configurado, se mostrará un enlace en pantalla.", "reset_link": reset_link, "email_sent": False, "smtp_configured": smtp_configured
        })


@app.get("/reset-password/{token}", response_class=HTMLResponse)
def reset_password_page(request: Request, token: str):
    """Página pública: el usuario abre el enlace desde el correo. No debe estar protegida por WAF ni bloqueada por Referer."""
    # No consumimos todavía el token, solo validamos forma general
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token, "error": None})


@app.post("/reset-password/{token}", response_class=HTMLResponse)
def reset_password(request: Request, token: str, password: str = Form(...), password_confirm: str = Form(...)):
    if password != password_confirm:
        return templates.TemplateResponse("reset_password.html", {"request": request, "token": token, "error": "Las contraseñas no coinciden."})
    if len(password) < 8:
        return templates.TemplateResponse("reset_password.html", {"request": request, "token": token, "error": "La contraseña debe tener al menos 8 caracteres."})
    user_id = consume_reset_token(token)
    if not user_id:
        return templates.TemplateResponse("reset_password.html", {"request": request, "token": None, "error": "El enlace ya no es válido. Solicita uno nuevo."})
    with db() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
            (password_hash(password), now_iso(), user_id),
        )
    return RedirectResponse("/login", status_code=303)


@app.post("/logout")
def logout(request: Request):
    session_id = request.session.get("session_id")
    if session_id:
        with db() as conn:
            conn.execute(
                "UPDATE user_sessions SET ended_at = ?, last_seen_at = ?, request_count = request_count + 1 WHERE id = ?",
                (now_iso(), now_iso(), session_id),
            )
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.get("/onboarding", response_class=HTMLResponse)
def onboarding_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if not onboarding_pending(user):
        # Permitir editar: mostrar formulario con datos actuales
        return templates.TemplateResponse("onboarding.html", {"request": request, "error": None, "user": user, "editing": True})
    return templates.TemplateResponse("onboarding.html", {"request": request, "error": None, "user": user, "editing": False})


@app.post("/onboarding")
def onboarding(
    request: Request,
    hotel_name: str = Form(...),
    contact_name: str = Form(...),
    hotel_size: str = Form(...),
    hotel_category: str = Form(...),
    hotel_location: str = Form(...),
    hotel_stars: str = Form("0"),
    hotel_location_context: str = Form(""),
    hotel_pms: str = Form(""),
    hotel_channel_manager: str = Form(""),
    hotel_booking_engine: str = Form(""),
    hotel_tech_other: str = Form(""),
    hotel_google_business_url: str = Form(""),
    hotel_expedia_url: str = Form(""),
    hotel_booking_url: str = Form(""),
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    hotel_name = hotel_name.strip()
    contact_name = contact_name.strip()
    hotel_size = hotel_size.strip() or None
    hotel_category = hotel_category.strip() or None
    hotel_location = hotel_location.strip() or None
    try:
        stars_int = int(hotel_stars.strip() or "0")
        if stars_int < 0 or stars_int > 5:
            stars_int = 0
    except ValueError:
        stars_int = 0
    location_ctx = hotel_location_context.strip() or None
    pms = hotel_pms.strip() or None
    channel_mgr = hotel_channel_manager.strip() or None
    booking_eng = hotel_booking_engine.strip() or None
    tech_other = hotel_tech_other.strip() or None
    gmb_url = hotel_google_business_url.strip() or None
    expedia_url = hotel_expedia_url.strip() or None
    booking_url = hotel_booking_url.strip() or None
    if not hotel_name or not contact_name:
        return templates.TemplateResponse("onboarding.html", {"request": request, "error": "Nombre del hotel y contacto son obligatorios."}, status_code=400)
    if not hotel_size or not hotel_category:
        return templates.TemplateResponse("onboarding.html", {"request": request, "error": "Indica el tamaño y la categoría de tu hotel para personalizar las recomendaciones."}, status_code=400)
    with db() as conn:
        conn.execute(
            """
            UPDATE users SET hotel_name = ?, contact_name = ?, hotel_size = ?, hotel_category = ?, hotel_location = ?,
            hotel_stars = ?, hotel_location_context = ?,
            hotel_pms = ?, hotel_channel_manager = ?, hotel_booking_engine = ?, hotel_tech_other = ?,
            hotel_google_business_url = ?, hotel_expedia_url = ?, hotel_booking_url = ?,
            updated_at = ?
            WHERE id = ?
            """,
            (hotel_name, contact_name, hotel_size, hotel_category, hotel_location, stars_int, location_ctx,
             pms, channel_mgr, booking_eng, tech_other, gmb_url, expedia_url, booking_url, now_iso(), user["id"]),
        )
    return RedirectResponse("/app", status_code=303)


@app.get("/app/account", response_class=HTMLResponse)
def account_page(request: Request):
    """Mi cuenta: perfil, editar datos, y opciones de plan (Pro y Pro+)."""
    user = require_user(request)
    if onboarding_pending(user):
        return RedirectResponse("/onboarding", status_code=303)
    return templates.TemplateResponse("account.html", {
        "request": request,
        "user": user,
        "plan_label": plan_label(user["plan"]),
        "monthly_price": MONTHLY_PRICE,
        "premium_monthly_price": PREMIUM_MONTHLY_PRICE,
        "stripe_publishable_key": STRIPE_PUBLISHABLE_KEY,
    })


@app.get("/app", response_class=HTMLResponse)
def dashboard(request: Request):
    user = require_user(request)
    if onboarding_pending(user):
        return RedirectResponse("/onboarding", status_code=303)
    # Tracking de sesión básica: último uso del panel
    session_id = request.session.get("session_id")
    if session_id:
        with db() as conn:
            conn.execute(
                "UPDATE user_sessions SET last_seen_at = ?, request_count = request_count + 1 WHERE id = ?",
                (now_iso(), session_id),
            )
    with db() as conn:
        analyses = conn.execute("SELECT * FROM analyses WHERE user_id = ? ORDER BY created_at DESC LIMIT 20", (user["id"],)).fetchall()
    formatted = []
    for row in analyses:
        # #region agent log
        _created = row["created_at"]
        _days = row["days_covered"]
        _debug_log("app.py:dashboard", "analysis row", {"id": row["id"], "created_at_is_none": _created is None, "days_covered_is_none": _days is None}, "H1")
        # #endregion
        analysis = json.loads(row["analysis_json"])
        summary = json.loads(row["summary_json"])
        created_at_str = (_created[:19].replace("T", " ") if _created else "")
        formatted.append({
            "id": row["id"],
            "title": row["title"] or f"Análisis {row['id']}",
            "created_at": created_at_str,
            "file_count": row["file_count"],
            "days_covered": _days if _days is not None else 0,
            "resumen_ejecutivo": analysis.get("resumen_ejecutivo", ""),
            "metricas": analysis.get("metricas_clave", [])[:4],
            "senal_upgrade": analysis.get("senal_de_upgrade", {}),
            "reports_detected": summary.get("reports_detected", 0),
        })
    eligibility = upload_eligibility(user)
    return templates.TemplateResponse("app.html", {
        "request": request,
        "user": user,
        "is_admin": is_admin_user(user),
        "analyses": formatted,
        "plan_label": plan_label(user["plan"]),
        "max_files_per_analysis": max_upload_files_for_plan(user["plan"]),
        "pro_max_files": PRO_90_MAX_FILES,
        "pro_plus_max_files": PRO_180_MAX_FILES,
        "free_max_days": FREE_MAX_DAYS,
        "free_max_files": FREE_MAX_FILES_PER_ANALYSIS,
        "free_max_analyses": FREE_MAX_ANALYSES,
        "monthly_price": MONTHLY_PRICE,
        "annual_price": ANNUAL_PRICE,
        "premium_monthly_price": PREMIUM_MONTHLY_PRICE,
        "stripe_publishable_key": STRIPE_PUBLISHABLE_KEY,
        "can_upload": eligibility["can_upload"],
        "limit_reason": eligibility["limit_reason"],
        "invite_upgrade": eligibility["invite_upgrade"],
        "invite_contact": eligibility["invite_contact"],
        "contact_email": eligibility["contact_email"],
        "smtp_configured": bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD),
    })


def _user_row_as_dict(row: sqlite3.Row) -> dict:
    """Convierte sqlite3.Row a dict para usar .get() y evitar AttributeError."""
    return dict(row) if row is not None else {}


@app.post("/analyze")
async def analyze(request: Request, business_context: str = Form(""), files: List[UploadFile] = File(...)):
    # #region agent log
    _debug_log("app.py:analyze", "POST /analyze entry", {"files_count": len(files) if files else 0}, "H4")
    _dbg("app.py:analyze", "entry", {"files_count": len(files) if files else 0, "filenames": [getattr(f, "filename", None) for f in (files or [])]}, "H_A")
    # #endregion
    user = _user_row_as_dict(require_user(request))
    if onboarding_pending(user):
        _dbg("app.py:analyze", "early_return", {"reason": "onboarding_pending"}, "H_C")
        return JSONResponse({"ok": False, "error": "Completa los datos de tu hotel primero.", "redirect": "/onboarding"}, status_code=400)
    if not files:
        _dbg("app.py:analyze", "early_return", {"reason": "no_files"}, "H_A")
        return JSONResponse({"ok": False, "error": "Sube al menos un reporte."}, status_code=400)
    try:
        summary = summarize_reports(files)
        _dbg("app.py:analyze", "after_summarize", {"reports_detected": summary.get("reports_detected"), "total_files": summary.get("total_files")}, "H_B")
        enforce_plan(user, summary)
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
        combined_business_context = business_context or ""
        if user["plan"] == "free":
            plan_for_model = "free_30"
        elif user["plan"] == "pro":
            plan_for_model = "pro_90"
        else:
            plan_for_model = "pro_180"
        _dbg("app.py:analyze", "before_call_openai", {}, "H_D")
        analysis = call_openai(summary, combined_business_context, hotel_context, plan_for_model)
        title = f"{summary['reports_detected']} reporte(s) · {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        analysis_id, share_token = save_analysis(user["id"], title, user["plan"], summary, analysis, files)
        created_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")[:19].replace("T", " ")
        share_url = f"{public_share_base_url()}/s/{share_token}"
        # #region agent log
        _debug_log("app.py:analyze", "POST /analyze success", {"analysis_id": analysis_id}, "H4")
        _dbg("app.py:analyze", "success", {"analysis_id": analysis_id}, "H_D")
        # #endregion
        return JSONResponse({
            "ok": True,
            "analysis_id": analysis_id,
            "title": title,
            "created_at": created_at,
            "summary": summary,
            "analysis": analysis,
            "plan": user["plan"],
            "share_url": share_url,
        })
    except HTTPException as e:
        _dbg("app.py:analyze", "http_exception", {"detail": e.detail, "status_code": e.status_code}, "H_C")
        return JSONResponse({"ok": False, "error": e.detail}, status_code=e.status_code)
    except ValueError as e:
        _dbg("app.py:analyze", "value_error", {"message": str(e)}, "H_B")
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        # #region agent log
        _debug_log("app.py:analyze", "POST /analyze exception", {"error": str(e)}, "H4")
        _dbg("app.py:analyze", "exception", {"exc_type": type(e).__name__, "exc_msg": str(e)}, "H_B")
        # #endregion
        err_msg = str(e).strip() if str(e) else "Error desconocido"
        return JSONResponse({"ok": False, "error": f"No se pudo completar el análisis. Intenta de nuevo más tarde. ({err_msg})"}, status_code=500)


@app.get("/analysis/{analysis_id}")
def analysis_detail(request: Request, analysis_id: int):
    user = require_user(request)
    with db() as conn:
        row = conn.execute("SELECT * FROM analyses WHERE id = ? AND user_id = ?", (analysis_id, user["id"])).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    stoken = row["share_token"] if row["share_token"] else None
    share_url = f"{public_share_base_url()}/s/{stoken}" if stoken else None
    return JSONResponse({
        "ok": True,
        "summary": json.loads(row["summary_json"]),
        "analysis": json.loads(row["analysis_json"]),
        "id": row["id"],
        "title": row["title"],
        "created_at": row["created_at"],
        "plan": row["plan_at_analysis"] or "free",
        "share_url": share_url,
    })


@app.post("/analysis/{analysis_id}/share")
def ensure_analysis_share_link(request: Request, analysis_id: int):
    """Crea o devuelve el enlace público de solo lectura para un análisis (p. ej. análisis guardados antes de la migración)."""
    user = require_user(request)
    with db() as conn:
        row = conn.execute(
            "SELECT share_token FROM analyses WHERE id = ? AND user_id = ?",
            (analysis_id, user["id"]),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Análisis no encontrado")
        token = row["share_token"]
        if not token:
            token = secrets.token_urlsafe(24)
            conn.execute("UPDATE analyses SET share_token = ? WHERE id = ?", (token, analysis_id))
    return JSONResponse({"ok": True, "share_url": f"{public_share_base_url()}/s/{token}"})


@app.post("/analysis/{analysis_id}/share-email")
async def email_share_link(request: Request, analysis_id: int, to_email: str = Form(...)):
    """Envía por SMTP el enlace público del análisis a un correo (requiere SMTP configurado en el servidor)."""
    user = require_user(request)
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        raise HTTPException(
            status_code=503,
            detail="El envío por correo no está configurado en el servidor. Usa “Abrir en mi correo” o configura SMTP (.env).",
        )
    to_clean = (to_email or "").strip()
    if not looks_like_email(to_clean):
        raise HTTPException(status_code=400, detail="Correo no válido.")
    uid = int(user["id"])
    hotel_label = (user["hotel_name"] or "").strip() or "Hotel"
    with db() as conn:
        row = conn.execute(
            "SELECT share_token FROM analyses WHERE id = ? AND user_id = ?",
            (analysis_id, uid),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Análisis no encontrado")
        token = row["share_token"]
        if not token:
            token = secrets.token_urlsafe(24)
            conn.execute("UPDATE analyses SET share_token = ? WHERE id = ?", (token, analysis_id))
    share_url = f"{public_share_base_url()}/s/{token}"
    if not send_analysis_share_link_email(to_clean, share_url, hotel_label):
        raise HTTPException(status_code=500, detail="No se pudo enviar el correo. Intenta más tarde.")
    return JSONResponse({"ok": True, "message": "Correo enviado."})


@app.get("/s/{share_token}", response_class=HTMLResponse)
def shared_analysis_view(request: Request, share_token: str):
    """Vista pública de solo lectura del análisis (quien tenga el enlace)."""
    with db() as conn:
        row = conn.execute(
            "SELECT title, summary_json, analysis_json, created_at FROM analyses WHERE share_token = ?",
            (share_token,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Enlace no válido o expirado.")
    summary = json.loads(row["summary_json"])
    analysis = json.loads(row["analysis_json"])
    created = (row["created_at"] or "")[:19].replace("T", " ")
    return templates.TemplateResponse(
        "share_public.html",
        {
            "request": request,
            "page_title": row["title"] or "Informe compartido",
            "created_at": created,
            "summary": summary,
            "analysis": analysis,
        },
    )


# Colores brandbook para PDF
_PDF_BRAND_TEXT = HexColor("#343434")
_PDF_BRAND_ACCENT = HexColor("#f07e07")
_PDF_MARGIN = 50
_PDF_FOOTER_H = 36


def _pdf_draw_footer(c: canvas.Canvas, width: float, height: float, hotel_name: str, report_date: str) -> None:
    """Pie de página: nombre del hotel y fecha en todas las páginas."""
    c.setFillColor(_PDF_BRAND_TEXT)
    c.setFont("Helvetica", 9)
    c.drawString(_PDF_MARGIN, 22, f"{hotel_name}  ·  {report_date}")
    c.setFillColor(_PDF_BRAND_ACCENT)
    c.setStrokeColor(_PDF_BRAND_ACCENT)
    c.setLineWidth(0.5)
    c.line(_PDF_MARGIN, 30, width - _PDF_MARGIN, 30)
    c.setFillColor(_PDF_BRAND_TEXT)


def _pdf_draw_wrapped(
    c: canvas.Canvas, text: str, x: float, y: float, max_width: int, font: str = "Helvetica", size: int = 10, leading: int = 14
) -> float:
    """Dibuja texto con salto de línea; devuelve la y final."""
    c.setFont(font, size)
    lines: list[str] = []
    for raw_line in (text or "").split("\n"):
        current = ""
        for word in raw_line.split():
            test = (current + " " + word).strip()
            if stringWidth(test, font, size) > max_width:
                if current:
                    lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def _pdf_build_analysis_pdf(
    c: canvas.Canvas, width: float, height: float, user: dict, row: dict, summary: dict, analysis: dict
) -> None:
    hotel_name = user.get("hotel_name") or "Hotel"
    plan = plan_label(user.get("plan") or "free")
    report_date = (row.get("created_at") or "")[:19].replace("T", " ")
    analysis_id = row.get("id", 0)

    # Pie de página en la primera hoja
    _pdf_draw_footer(c, width, height, hotel_name, report_date)

    def new_page(y: float, min_need: int = 120) -> float:
        if y < _PDF_FOOTER_H + min_need:
            c.showPage()
            _pdf_draw_footer(c, width, height, hotel_name, report_date)
            return height - _PDF_MARGIN - 20
        return y

    # ---------- Encabezado con branding ----------
    logo_path = BASE_DIR / "static" / "branding" / "dragonne-wordmark.png"
    if logo_path.exists():
        try:
            c.drawImage(str(logo_path), _PDF_MARGIN, height - 52, width=120, height=28)
        except Exception:
            c.setFillColor(_PDF_BRAND_ACCENT)
            c.setFont("Helvetica-Bold", 20)
            c.drawString(_PDF_MARGIN, height - 48, "DRAGONNÉ")
            c.setFillColor(_PDF_BRAND_TEXT)
    else:
        c.setFillColor(_PDF_BRAND_ACCENT)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(_PDF_MARGIN, height - 48, "DRAGONNÉ")
        c.setFillColor(_PDF_BRAND_TEXT)
    c.setFont("Helvetica", 11)
    c.drawString(_PDF_MARGIN, height - 68, "Análisis de revenue hotelero")
    c.setStrokeColor(_PDF_BRAND_ACCENT)
    c.setLineWidth(1.5)
    c.line(_PDF_MARGIN, height - 76, min(_PDF_MARGIN + 180, width - _PDF_MARGIN), height - 76)
    c.setFillColor(_PDF_BRAND_TEXT)

    # ---------- Bloque personalizado: Hotel y fecha ----------
    y = height - 100
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(_PDF_BRAND_ACCENT)
    c.drawString(_PDF_MARGIN, y, "Hotel")
    c.setFillColor(_PDF_BRAND_TEXT)
    c.setFont("Helvetica", 10)
    c.drawString(_PDF_MARGIN + 32, y, hotel_name)
    y -= 14
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(_PDF_BRAND_ACCENT)
    c.drawString(_PDF_MARGIN, y, "Fecha del reporte")
    c.setFillColor(_PDF_BRAND_TEXT)
    c.setFont("Helvetica", 10)
    c.drawString(_PDF_MARGIN + 70, y, report_date)
    y -= 14
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(_PDF_BRAND_ACCENT)
    c.drawString(_PDF_MARGIN, y, "Plan")
    c.setFillColor(_PDF_BRAND_TEXT)
    c.setFont("Helvetica", 10)
    c.drawString(_PDF_MARGIN + 28, y, plan)
    y -= 28

    # ---------- Tabla resumen (KPIs como en el dashboard) ----------
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(_PDF_BRAND_ACCENT)
    c.drawString(_PDF_MARGIN, y, "Resumen del análisis")
    y -= 6
    c.setStrokeColor(HexColor("#e0e0e0"))
    c.setLineWidth(0.5)
    tw = (width - 2 * _PDF_MARGIN) / 4
    th = 22
    kpis = [
        ("Archivos", str(summary.get("total_files", 0))),
        ("Reportes", str(summary.get("reports_detected", 0))),
        ("Días cubiertos", str(summary.get("overall_days_covered", 0))),
        ("Máx. rango", str(summary.get("max_days_covered", 0))),
    ]
    for i, (label, value) in enumerate(kpis):
        cx = _PDF_MARGIN + i * tw
        c.rect(cx, y - th, tw, th, stroke=1, fill=0)
        c.setFont("Helvetica", 8)
        c.setFillColor(HexColor("#808081"))
        c.drawString(cx + 6, y - th + 12, label)
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(_PDF_BRAND_TEXT)
        c.drawString(cx + 6, y - th + 2, value)
    c.setFillColor(_PDF_BRAND_TEXT)
    y -= th + 18

    # ---------- Resumen ejecutivo ----------
    y = new_page(y, 80)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(_PDF_BRAND_ACCENT)
    c.drawString(_PDF_MARGIN, y, "Resumen ejecutivo")
    y -= 6
    c.setStrokeColor(_PDF_BRAND_ACCENT)
    c.setLineWidth(1)
    c.line(_PDF_MARGIN, y - 2, _PDF_MARGIN + 120, y - 2)
    c.setFillColor(_PDF_BRAND_TEXT)
    y -= 16
    resumen = analysis.get("resumen_ejecutivo", "")
    y = _pdf_draw_wrapped(c, resumen, _PDF_MARGIN, y, int(width - 2 * _PDF_MARGIN))
    y -= 14

    # ---------- Métricas clave ----------
    y = new_page(y, 100)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(_PDF_BRAND_ACCENT)
    c.drawString(_PDF_MARGIN, y, "Métricas clave")
    y -= 6
    c.setStrokeColor(_PDF_BRAND_ACCENT)
    c.line(_PDF_MARGIN, y - 2, _PDF_MARGIN + 100, y - 2)
    c.setFillColor(_PDF_BRAND_TEXT)
    y -= 14
    c.setFont("Helvetica", 10)
    for item in analysis.get("metricas_clave", [])[:8]:
        nombre = item.get("nombre", "")
        valor = item.get("valor", "")
        lectura = item.get("lectura", "")
        y = _pdf_draw_wrapped(c, f"{nombre}: {valor}", _PDF_MARGIN, y, int(width - 2 * _PDF_MARGIN))
        if lectura:
            y = _pdf_draw_wrapped(c, lectura, _PDF_MARGIN + 10, y, int(width - 2 * _PDF_MARGIN - 10), size=9)
        y -= 6
        if y < _PDF_FOOTER_H + 60:
            y = new_page(y, 60)
            c.setFont("Helvetica", 10)
    y -= 8

    # ---------- Hallazgos prioritarios ----------
    y = new_page(y, 100)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(_PDF_BRAND_ACCENT)
    c.drawString(_PDF_MARGIN, y, "Hallazgos prioritarios")
    y -= 6
    c.setStrokeColor(_PDF_BRAND_ACCENT)
    c.line(_PDF_MARGIN, y - 2, _PDF_MARGIN + 130, y - 2)
    c.setFillColor(_PDF_BRAND_TEXT)
    y -= 14
    for item in analysis.get("hallazgos_prioritarios", [])[:6]:
        titulo = item.get("titulo", "")
        detalle = item.get("detalle", "")
        impacto = item.get("impacto", "")
        prioridad = item.get("prioridad", "")
        y = _pdf_draw_wrapped(c, f"• {titulo} (Impacto: {impacto}, Prioridad: {prioridad})", _PDF_MARGIN, y, int(width - 2 * _PDF_MARGIN))
        if detalle:
            y = _pdf_draw_wrapped(c, detalle, _PDF_MARGIN + 12, y, int(width - 2 * _PDF_MARGIN - 12), size=9)
        y -= 8
        if y < _PDF_FOOTER_H + 50:
            y = new_page(y, 50)
    y -= 8

    # ---------- Oportunidades directo vs OTA ----------
    opps = analysis.get("oportunidades_directo_vs_ota", [])
    if opps:
        y = new_page(y, 80)
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(_PDF_BRAND_ACCENT)
        c.drawString(_PDF_MARGIN, y, "Oportunidades directo vs OTA")
        y -= 6
        c.setStrokeColor(_PDF_BRAND_ACCENT)
        c.line(_PDF_MARGIN, y - 2, _PDF_MARGIN + 180, y - 2)
        c.setFillColor(_PDF_BRAND_TEXT)
        y -= 14
        c.setFont("Helvetica", 10)
        for s in opps[:6]:
            y = _pdf_draw_wrapped(c, f"• {s}", _PDF_MARGIN, y, int(width - 2 * _PDF_MARGIN))
            y -= 4
        y -= 8

    # ---------- Riesgos detectados ----------
    riesgos = analysis.get("riesgos_detectados", [])
    if riesgos:
        y = new_page(y, 80)
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(_PDF_BRAND_ACCENT)
        c.drawString(_PDF_MARGIN, y, "Riesgos detectados")
        y -= 6
        c.setStrokeColor(_PDF_BRAND_ACCENT)
        c.line(_PDF_MARGIN, y - 2, _PDF_MARGIN + 120, y - 2)
        c.setFillColor(_PDF_BRAND_TEXT)
        y -= 14
        c.setFont("Helvetica", 10)
        for s in riesgos[:6]:
            y = _pdf_draw_wrapped(c, f"• {s}", _PDF_MARGIN, y, int(width - 2 * _PDF_MARGIN))
            y -= 4
        y -= 8

    # ---------- Recomendaciones accionables ----------
    y = new_page(y, 120)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(_PDF_BRAND_ACCENT)
    c.drawString(_PDF_MARGIN, y, "Recomendaciones accionables")
    y -= 6
    c.setStrokeColor(_PDF_BRAND_ACCENT)
    c.line(_PDF_MARGIN, y - 2, _PDF_MARGIN + 200, y - 2)
    c.setFillColor(_PDF_BRAND_TEXT)
    y -= 14
    c.setFont("Helvetica", 10)
    for item in analysis.get("recomendaciones_accionables", [])[:10]:
        accion = item.get("accion", "")
        por_que = item.get("por_que", "")
        urgencia = item.get("urgencia", "")
        y = _pdf_draw_wrapped(c, f"• {accion} (Urgencia: {urgencia})", _PDF_MARGIN, y, int(width - 2 * _PDF_MARGIN))
        if por_que:
            y = _pdf_draw_wrapped(c, por_que, _PDF_MARGIN + 12, y, int(width - 2 * _PDF_MARGIN - 12), size=9)
        y -= 6
        if y < _PDF_FOOTER_H + 50:
            y = new_page(y, 50)
            c.setFont("Helvetica", 10)
    y -= 8

    # ---------- Datos faltantes ----------
    faltantes = analysis.get("datos_faltantes", [])
    if faltantes:
        y = new_page(y, 60)
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(_PDF_BRAND_ACCENT)
        c.drawString(_PDF_MARGIN, y, "Datos faltantes")
        y -= 6
        c.setStrokeColor(_PDF_BRAND_ACCENT)
        c.line(_PDF_MARGIN, y - 2, _PDF_MARGIN + 100, y - 2)
        c.setFillColor(_PDF_BRAND_TEXT)
        y -= 14
        c.setFont("Helvetica", 10)
        for s in faltantes[:5]:
            y = _pdf_draw_wrapped(c, f"• {s}", _PDF_MARGIN, y, int(width - 2 * _PDF_MARGIN))
            y -= 4

    c.showPage()


@app.get("/analysis/{analysis_id}/pdf")
def analysis_pdf(request: Request, analysis_id: int):
    user = require_user(request)
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM analyses WHERE id = ? AND user_id = ?",
            (analysis_id, user["id"]),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")

    summary = json.loads(row["summary_json"])
    analysis = json.loads(row["analysis_json"])
    user_dict = dict(user)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    _pdf_build_analysis_pdf(c, width, height, user_dict, dict(row), summary, analysis)
    c.save()
    buffer.seek(0)

    safe_hotel = re.sub(r"[^\w\s-]", "", (user_dict.get("hotel_name") or "informe"))
    safe_hotel = re.sub(r"[-\s]+", "-", safe_hotel).strip()[:40] or "informe"
    report_date = (row["created_at"] or "")[:10]
    filename = f"dragonne-informe-{safe_hotel}-{report_date}.pdf"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(buffer, media_type="application/pdf", headers=headers)


# ---------- API v1 (documentada en /docs y /redoc) ----------
@api_v1.get("/me", summary="Perfil del usuario asociado a la API key")
def api_me(user: sqlite3.Row = Depends(get_api_user)):
    """Devuelve el perfil del usuario autenticado por API key (solo campos no sensibles)."""
    return {
        "id": user["id"],
        "email": user["email"],
        "hotel_name": user["hotel_name"],
        "plan": user["plan"],
        "hotel_size": user["hotel_size"],
        "hotel_category": user["hotel_category"],
        "hotel_location": user["hotel_location"],
    }


@api_v1.post("/analyze", summary="Ejecutar análisis de reportes")
async def api_analyze(
    user: sqlite3.Row = Depends(get_api_user),
    business_context: str = Form(""),
    files: List[UploadFile] = File(...),
):
    """
    Sube uno o más reportes (CSV/Excel) y devuelve el análisis en JSON.
    Mismo límite de plan que en la web (días, archivos, número de análisis).
    """
    user = _user_row_as_dict(user)
    if not files:
        raise HTTPException(status_code=400, detail="Sube al menos un reporte.")
    try:
        summary = summarize_reports(files)
        enforce_plan(user, summary)
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
        combined_business_context = business_context or ""
        if user["plan"] == "free":
            plan_for_model = "free_30"
        elif user["plan"] == "pro":
            plan_for_model = "pro_90"
        else:
            plan_for_model = "pro_180"
        analysis = call_openai(summary, combined_business_context, hotel_context, plan_for_model)
        title = f"{summary['reports_detected']} reporte(s) · {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        analysis_id, share_token = save_analysis(user["id"], title, user["plan"], summary, analysis, files)
        return {
            "ok": True,
            "analysis_id": analysis_id,
            "title": title,
            "summary": summary,
            "analysis": analysis,
            "plan": user["plan"],
            "share_url": f"{public_share_base_url()}/s/{share_token}",
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo completar el análisis. Intenta más tarde.")


@api_v1.get("/analyses", summary="Listar análisis del usuario")
def api_list_analyses(user: sqlite3.Row = Depends(get_api_user)):
    """Lista los análisis del usuario (últimos 50)."""
    with db() as conn:
        rows = conn.execute(
            "SELECT id, title, plan_at_analysis, file_count, days_covered, created_at FROM analyses WHERE user_id = ? ORDER BY created_at DESC LIMIT 50",
            (user["id"],),
        ).fetchall()
    return {
        "ok": True,
        "analyses": [
            {
                "id": row["id"],
                "title": row["title"],
                "plan_at_analysis": row["plan_at_analysis"],
                "file_count": row["file_count"],
                "days_covered": row["days_covered"],
                "created_at": row["created_at"],
            }
            for row in rows
        ],
    }


@api_v1.get("/analyses/{analysis_id}", summary="Obtener un análisis por ID")
def api_get_analysis(analysis_id: int, user: sqlite3.Row = Depends(get_api_user)):
    """Devuelve el JSON completo de un análisis (summary + analysis)."""
    with db() as conn:
        row = conn.execute("SELECT * FROM analyses WHERE id = ? AND user_id = ?", (analysis_id, user["id"])).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    return {
        "ok": True,
        "id": row["id"],
        "title": row["title"],
        "created_at": row["created_at"],
        "summary": json.loads(row["summary_json"]),
        "analysis": json.loads(row["analysis_json"]),
    }


@api_v1.get("/analyses/{analysis_id}/pdf", summary="Descargar PDF del análisis")
def api_analysis_pdf(analysis_id: int, user: sqlite3.Row = Depends(get_api_user)):
    """Genera y devuelve el PDF del análisis (mismo formato que la web: branding, tabla resumen, hotel y fecha)."""
    with db() as conn:
        row = conn.execute("SELECT * FROM analyses WHERE id = ? AND user_id = ?", (analysis_id, user["id"])).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    summary = json.loads(row["summary_json"])
    analysis = json.loads(row["analysis_json"])
    user_dict = dict(user)
    row_dict = dict(row)
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    _pdf_build_analysis_pdf(c, width, height, user_dict, row_dict, summary, analysis)
    c.save()
    buffer.seek(0)
    safe_hotel = re.sub(r"[^\w\s-]", "", (user_dict.get("hotel_name") or "informe"))
    safe_hotel = re.sub(r"[-\s]+", "-", safe_hotel).strip()[:40] or "informe"
    report_date = (row["created_at"] or "")[:10]
    filename = f"dragonne-informe-{safe_hotel}-{report_date}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


app.include_router(api_v1)


@app.post("/billing/create-checkout-session")
def create_checkout_session(request: Request, billing_cycle: str = Form(...), plan_tier: str = Form("pro")):
    user = require_user(request)
    if plan_tier == "pro_plus":
        if not STRIPE_PRO_PLUS_PRICE_ID:
            raise HTTPException(status_code=500, detail="Pro+ no configurado (STRIPE_PRO_PLUS_PRICE_ID)")
        price_id = STRIPE_PRO_PLUS_PRICE_ID
    else:
        if billing_cycle not in {"monthly", "annual"}:
            raise HTTPException(status_code=400, detail="Ciclo inválido")
        price_id = STRIPE_MONTHLY_PRICE_ID if billing_cycle == "monthly" else STRIPE_ANNUAL_PRICE_ID
        if not price_id:
            raise HTTPException(status_code=500, detail="Falta configurar el price_id de Stripe (Pro)")
    customer_id = ensure_stripe_customer(user)
    payload = {
        "mode": "subscription",
        "customer": customer_id,
        "success_url": f"{APP_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{APP_URL}/app",
        "line_items[0][price]": price_id,
        "line_items[0][quantity]": 1,
        "allow_promotion_codes": "true",
        "metadata[user_id]": str(user["id"]),
        "metadata[billing_cycle]": billing_cycle if plan_tier != "pro_plus" else "monthly",
        "metadata[plan_tier]": plan_tier,
    }
    if TRIAL_DAYS > 0 and plan_tier != "pro_plus":
        payload["subscription_data[trial_period_days]"] = TRIAL_DAYS
    session = stripe_request("POST", "/v1/checkout/sessions", payload)
    return JSONResponse({"ok": True, "url": session["url"]})


@app.get("/billing/success", response_class=HTMLResponse)
def billing_success(request: Request):
    user = require_user(request)
    return templates.TemplateResponse("billing_success.html", {"request": request, "user": user})


@app.post("/billing/create-portal-session")
def create_portal_session(request: Request):
    user = require_user(request)
    if not user["stripe_customer_id"]:
        raise HTTPException(status_code=400, detail="No hay cliente de Stripe asociado todavía.")
    session = stripe_request("POST", "/v1/billing_portal/sessions", {
        "customer": user["stripe_customer_id"],
        "return_url": f"{APP_URL}/app",
    })
    return JSONResponse({"ok": True, "url": session["url"]})


@app.post("/billing/webhook")
async def billing_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook no configurado")
    header_parts = dict(item.split("=", 1) for item in sig.split(",") if "=" in item)
    timestamp = header_parts.get("t", "")
    signature = header_parts.get("v1", "")
    signed_payload = f"{timestamp}.{payload.decode()}".encode()
    expected = hmac.new(STRIPE_WEBHOOK_SECRET.encode(), signed_payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Firma inválida")
    event = json.loads(payload.decode())
    event_id = event.get("id")
    event_type = event.get("type")
    with db() as conn:
        exists = conn.execute("SELECT id FROM billing_events WHERE stripe_event_id = ?", (event_id,)).fetchone()
        if exists:
            return Response(status_code=200)
        conn.execute(
            "INSERT INTO billing_events (stripe_event_id, event_type, payload, created_at) VALUES (?, ?, ?, ?)",
            (event_id, event_type or "unknown", payload.decode(), now_iso()),
        )
    obj = event.get("data", {}).get("object", {})
    if event_type in {"checkout.session.completed"}:
        customer_id = obj.get("customer")
        subscription_id = obj.get("subscription")
        if customer_id:
            sync_user_from_stripe_customer(customer_id, subscription_id, "active")
    elif event_type in {"customer.subscription.created", "customer.subscription.updated"}:
        customer_id = obj.get("customer")
        status = obj.get("status", "")
        subscription_id = obj.get("id")
        if customer_id:
            sync_user_from_stripe_customer(customer_id, subscription_id, status)
    elif event_type in {"customer.subscription.deleted"}:
        customer_id = obj.get("customer")
        if customer_id:
            sync_user_from_stripe_customer(customer_id, None, "canceled")
    return Response(status_code=200)


@app.get("/health")
def health():
    """Solo estado básico; no exponer configuración interna."""
    return {"ok": True, "app": APP_NAME}


@app.get("/health/config")
def health_config():
    """Indica si las variables de entorno críticas están definidas (solo sí/no, sin valores)."""
    return {
        "ok": True,
        "openai_configured": bool(OPENAI_API_KEY and OPENAI_API_KEY.strip()),
        "stripe_configured": bool(STRIPE_SECRET_KEY and STRIPE_SECRET_KEY.strip()),
        "stripe_webhook_configured": bool(STRIPE_WEBHOOK_SECRET and STRIPE_WEBHOOK_SECRET.strip()),
        "stripe_pro_price_configured": bool(STRIPE_MONTHLY_PRICE_ID and STRIPE_MONTHLY_PRICE_ID.strip()),
        "stripe_pro_plus_price_configured": bool(STRIPE_PRO_PLUS_PRICE_ID and STRIPE_PRO_PLUS_PRICE_ID.strip()),
    }


@app.get("/admin", response_class=HTMLResponse)
def admin_home(request: Request):
    admin = require_admin(request)
    with db() as conn:
        # Totales globales
        totals_row = conn.execute(
            """
            SELECT
              COUNT(*) AS total_hotels,
              SUM(COALESCE(login_count, 0)) AS total_logins,
              SUM(CASE WHEN last_login_at IS NOT NULL AND last_login_at >= ? THEN 1 ELSE 0 END) AS active_last_30d
            FROM users
            """,
            ((datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),),
        ).fetchone()
        analyses_totals = conn.execute(
            "SELECT COUNT(*) AS total_analyses, COALESCE(SUM(file_count), 0) AS total_files FROM analyses"
        ).fetchone()

        # Usuarios con actividad agregada
        rows = conn.execute(
            """
            SELECT
              u.*,
              COALESCE(a.cnt, 0) AS total_analyses,
              COALESCE(a.files_cnt, 0) AS total_files,
              s.last_activity
            FROM users u
            LEFT JOIN (
              SELECT
                user_id,
                COUNT(*) AS cnt,
                SUM(file_count) AS files_cnt,
                MAX(created_at) AS last_analysis_at
              FROM analyses
              GROUP BY user_id
            ) a ON a.user_id = u.id
            LEFT JOIN (
              SELECT
                user_id,
                MAX(COALESCE(ended_at, last_seen_at)) AS last_activity
              FROM user_sessions
              GROUP BY user_id
            ) s ON s.user_id = u.id
            ORDER BY COALESCE(s.last_activity, u.created_at) DESC
            LIMIT 100
            """
        ).fetchall()

    users = []
    for r in rows:
        users.append({
            "id": r["id"],
            "hotel_name": r["hotel_name"],
            "email": r["email"],
            "plan_label": plan_label(r["plan"]),
            "created_at": r["created_at"],
            "last_login_at": r["last_login_at"],
            "login_count": r["login_count"] or 0,
            "total_analyses": r["total_analyses"],
            "total_files": r["total_files"],
            "last_activity": r["last_activity"],
        })

    totals = {
        "total_hotels": totals_row["total_hotels"],
        "active_last_30d": totals_row["active_last_30d"],
        "total_analyses": analyses_totals["total_analyses"],
        "total_files": analyses_totals["total_files"],
    }

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "current_user": admin,
        "users": users,
        "totals": totals,
    })


@app.get("/admin/users/{user_id}", response_class=HTMLResponse)
def admin_user_detail(request: Request, user_id: int):
    admin = require_admin(request)
    with db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        analysis_rows = conn.execute(
            "SELECT * FROM analyses WHERE user_id = ? ORDER BY created_at DESC LIMIT 50",
            (user_id,),
        ).fetchall()
        sessions = conn.execute(
            "SELECT * FROM user_sessions WHERE user_id = ? ORDER BY started_at DESC LIMIT 50",
            (user_id,),
        ).fetchall()
        stats_row = conn.execute(
            """
            SELECT
              COUNT(*) AS total_analyses,
              COALESCE(SUM(file_count), 0) AS total_files,
              MAX(created_at) AS last_analysis_at
            FROM analyses
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
        last_activity_row = conn.execute(
            "SELECT MAX(COALESCE(ended_at, last_seen_at)) AS last_activity FROM user_sessions WHERE user_id = ?",
            (user_id,),
        ).fetchone()

    analyses_list = []
    for row in analysis_rows:
        try:
            summary = json.loads(row["summary_json"])
        except (TypeError, json.JSONDecodeError):
            summary = {}
        created_raw = row["created_at"] or ""
        created_at_str = created_raw[:19].replace("T", " ") if created_raw else ""
        analyses_list.append({
            "id": row["id"],
            "title": row["title"] or f"Análisis {row['id']}",
            "created_at": created_at_str,
            "file_count": row["file_count"],
            "days_covered": row["days_covered"] if row["days_covered"] is not None else 0,
            "reports_detected": int(summary.get("reports_detected") or 0),
        })

    stats = {
        "total_analyses": stats_row["total_analyses"],
        "total_files": stats_row["total_files"],
        "last_analysis_at": stats_row["last_analysis_at"],
        "last_activity": last_activity_row["last_activity"],
    }

    return templates.TemplateResponse("admin_user_detail.html", {
        "request": request,
        "current_user": admin,
        "user": user,
        "plan_label": plan_label(user["plan"]),
        "analyses": analyses_list,
        "sessions": sessions,
        "stats": stats,
    })


@app.post("/admin/users/{user_id}/plan")
def admin_user_set_plan(request: Request, user_id: int, plan: str = Form(...)):
    require_admin(request)
    plan = (plan or "").strip()
    if plan not in ADMIN_PLAN_VALUES:
        raise HTTPException(status_code=400, detail="Plan no válido")
    with db() as conn:
        u = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not u:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        conn.execute("UPDATE users SET plan = ?, updated_at = ? WHERE id = ?", (plan, now_iso(), user_id))
    return RedirectResponse(f"/admin/users/{user_id}", status_code=303)


@app.post("/admin/users/{user_id}/delete")
def admin_user_delete(request: Request, user_id: int):
    admin = require_admin(request)
    if admin["id"] == user_id:
        return RedirectResponse("/admin?error=no_borrar_self", status_code=303)
    with db() as conn:
        target = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not target:
            return RedirectResponse("/admin?error=usuario_no_encontrado", status_code=303)
        delete_user_and_related(conn, user_id)
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/analyses/{analysis_id}/delete")
def admin_analysis_delete(request: Request, analysis_id: int):
    require_admin(request)
    with db() as conn:
        row = conn.execute("SELECT user_id FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Análisis no encontrado")
        uid = row["user_id"]
        delete_analysis_by_id(conn, analysis_id)
    return RedirectResponse(f"/admin/users/{uid}", status_code=303)


@app.get("/admin/admins", response_class=HTMLResponse)
def admin_admins(request: Request):
    """Lista administradores (fijos + desde panel) y permite dar/quitar acceso."""
    admin = require_admin(request)
    admin_emails_set = ADMIN_EMAILS
    with db() as conn:
        all_users = conn.execute(
            "SELECT id, email, hotel_name, is_admin, created_at FROM users ORDER BY email"
        ).fetchall()
    admins = []
    non_admins = []
    for email in sorted(admin_emails_set):
        admins.append({"email": email, "hotel_name": None, "fijo": True, "user_id": None})
    for r in all_users:
        email_lower = (r["email"] or "").strip().lower()
        if r["is_admin"]:
            if email_lower not in admin_emails_set:
                admins.append({
                    "email": r["email"],
                    "hotel_name": r["hotel_name"],
                    "fijo": False,
                    "user_id": r["id"],
                })
        else:
            if email_lower not in admin_emails_set:
                non_admins.append({
                    "id": r["id"],
                    "email": r["email"],
                    "hotel_name": r["hotel_name"],
                    "created_at": r["created_at"],
                })
    return templates.TemplateResponse("admin_admins.html", {
        "request": request,
        "current_user": admin,
        "admins": admins,
        "non_admins": non_admins,
    })


@app.post("/admin/admins/grant")
def admin_admins_grant(request: Request, user_id: int = Form(...)):
    """Concede acceso admin a un usuario (is_admin=1)."""
    require_admin(request)
    with db() as conn:
        conn.execute("UPDATE users SET is_admin = 1, updated_at = ? WHERE id = ?", (now_iso(), user_id))
    return RedirectResponse("/admin/admins", status_code=303)


@app.post("/admin/admins/revoke")
def admin_admins_revoke(request: Request, user_id: int = Form(...)):
    """Quita acceso admin (is_admin=0). No afecta a los de ADMIN_EMAILS."""
    require_admin(request)
    with db() as conn:
        user = conn.execute("SELECT email FROM users WHERE id = ?", (user_id,)).fetchone()
        if user and user["email"].strip().lower() in ADMIN_EMAILS:
            return RedirectResponse("/admin/admins?error=fijo", status_code=303)
        conn.execute("UPDATE users SET is_admin = 0, updated_at = ? WHERE id = ?", (now_iso(), user_id))
    return RedirectResponse("/admin/admins", status_code=303)


@app.get("/admin/api", response_class=HTMLResponse)
def admin_api(request: Request):
    """Módulo Admin: listar usuarios y aprobar/revocar acceso API."""
    admin = require_admin(request)
    api_key_flash = request.session.pop("api_key_flash", None)
    with db() as conn:
        rows = conn.execute(
            """
            SELECT id, email, hotel_name, plan, api_key, created_at
            FROM users
            ORDER BY hotel_name
            """
        ).fetchall()
    users = []
    for r in rows:
        key = r["api_key"] if r["api_key"] else None
        masked = ("••••••••" + key[-4:] if key and len(key) > 4 else "••••••••") if key else "—"
        users.append({
            "id": r["id"],
            "email": r["email"],
            "hotel_name": r["hotel_name"],
            "plan": r["plan"],
            "api_key": key,
            "api_key_masked": masked,
        })
    return templates.TemplateResponse("admin_api.html", {
        "request": request,
        "current_user": admin,
        "users": users,
        "api_key_flash": api_key_flash,
        "rate_limit_min": API_RATE_LIMIT_PER_MINUTE,
        "rate_limit_day": API_RATE_LIMIT_PER_DAY,
    })


@app.post("/admin/api/grant")
def admin_api_grant(request: Request, user_id: int = Form(...)):
    """Genera una API key para el usuario y la muestra una vez."""
    require_admin(request)
    with db() as conn:
        user = conn.execute("SELECT id, email, hotel_name FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        new_key = secrets.token_urlsafe(32)
        conn.execute("UPDATE users SET api_key = ?, updated_at = ? WHERE id = ?", (new_key, now_iso(), user_id))
    request.session["api_key_flash"] = {"user_id": user_id, "key": new_key}
    return RedirectResponse("/admin/api", status_code=303)


@app.post("/admin/api/revoke")
def admin_api_revoke(request: Request, user_id: int = Form(...)):
    """Revoca el acceso API del usuario (borra la clave)."""
    require_admin(request)
    with db() as conn:
        conn.execute("UPDATE users SET api_key = NULL, updated_at = ? WHERE id = ?", (now_iso(), user_id))
    return RedirectResponse("/admin/api?revoked=1", status_code=303)


@app.post("/admin/api/regenerate")
def admin_api_regenerate(request: Request, user_id: int = Form(...)):
    """Regenera la API key del usuario (la anterior deja de funcionar)."""
    require_admin(request)
    with db() as conn:
        user = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        new_key = secrets.token_urlsafe(32)
        conn.execute("UPDATE users SET api_key = ?, updated_at = ? WHERE id = ?", (new_key, now_iso(), user_id))
    request.session["api_key_flash"] = {"user_id": user_id, "key": new_key}
    return RedirectResponse("/admin/api", status_code=303)
