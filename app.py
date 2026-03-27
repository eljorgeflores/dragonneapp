import json
import logging
import os
import sqlite3
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from config import (
    ANNUAL_PRICE,
    APP_NAME,
    APP_URL,
    BASE_DIR,
    DB_PATH,
    URL_PREFIX,
    FREE_MAX_ANALYSES,
    FREE_MAX_DAYS,
    FREE_MAX_FILES_PER_ANALYSIS,
    MONTHLY_PRICE,
    OPENAI_API_KEY,
    PREMIUM_MONTHLY_PRICE,
    PRO_180_MAX_FILES,
    PRO_90_MAX_FILES,
    RESEND_API_KEY,
    SECRET_KEY,
    SMTP_ENVELOPE_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_SECURITY,
    SMTP_USER,
    smtp_host_tcp_reachable,
    STRIPE_MONTHLY_PRICE_ID,
    STRIPE_PRO_PLUS_PRICE_ID,
    STRIPE_PUBLISHABLE_KEY,
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_SECRET,
    internal_path,
    password_reset_email_delivery_configured,
    resend_sender_plausible,
    url_path,
)


def _configure_application_logging() -> None:
    """Uvicorn sólo adjunta handlers a loggers ``uvicorn*`` (propagate=false).

    El logger raíz queda efectivamente en WARNING sin un StreamHandler propio para INFO,
    así que ``logging.getLogger(__name__).info()`` en módulos de aplicación no aparece
    en Render. Fijamos handlers dedicados (stderr) para auth/correo sin duplicar access logs.
    """
    raw = (os.getenv("LOG_LEVEL") or "INFO").strip().upper()
    level = getattr(logging, raw, logging.INFO)
    if not isinstance(level, int):
        level = logging.INFO
    fmt = logging.Formatter("%(levelname)s %(name)s %(message)s")
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(fmt)
    for name in ("email_smtp", "routes.auth", "app"):
        lg = logging.getLogger(name)
        lg.setLevel(level)
        lg.propagate = False
        if not lg.handlers:
            lg.addHandler(handler)


_configure_application_logging()

from db import db, init_db

# Esquema SQLite al importar el módulo (comportamiento previo a Fase 1).
init_db()

"""
DragonApp — ensamblador FastAPI: middleware, /app, health; routers en routes/*.
Servicios: services/analysis_core, share_service, pdf_service, billing_stripe. Ver docs/dragonapp_phase3.md.
"""

from urllib.parse import quote

from auth_session import is_admin_user, onboarding_pending, require_user
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exception_handlers import http_exception_handler as default_http_exception_handler
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from plan_entitlements import get_effective_plan, get_paid_plan, manual_access_notice_for_account
from plans import max_upload_files_for_plan, plan_label
from services.analysis_core import upload_eligibility
from starlette.middleware.sessions import SessionMiddleware
from seo_helpers import noindex_page_seo
from templating import templates
from time_utils import now_iso


def _sqlite_startup_audit(log: logging.Logger) -> None:
    """Ruta SQLite efectiva (mismo ``DB_PATH`` que ``db.py`` / ``init_db()``)."""
    dp = (os.getenv("DATABASE_PATH") or "").strip()
    dbp = (os.getenv("DB_PATH") or "").strip()
    if dp:
        source = "DATABASE_PATH"
    elif dbp:
        source = "DB_PATH"
    else:
        source = "default(BASE_DIR/data/profitpilot.db)"
    path = Path(DB_PATH)
    try:
        resolved = str(path.resolve())
    except OSError:
        resolved = str(path)
    exists = path.exists()
    size = path.stat().st_size if exists else -1
    users_table = "?"
    user_count = "?"
    open_err = "-"
    try:
        conn = sqlite3.connect(str(path))
        row = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
        if row and row[0]:
            users_table = "Y"
            user_count = str(conn.execute("SELECT COUNT(*) FROM users").fetchone()[0])
        else:
            users_table = "N"
            user_count = "0"
        conn.close()
    except sqlite3.Error as exc:
        open_err = type(exc).__name__
    log.info(
        "DragonApp startup: SQLITE effective_path=%s resolved=%s source=%s "
        "env_DATABASE_PATH_set=%s env_DB_PATH_set=%s file_exists=%s size_bytes=%s "
        "users_table=%s user_count=%s connect_error=%s",
        str(path),
        resolved,
        source,
        "Y" if dp else "N",
        "Y" if dbp else "N",
        "Y" if exists else "N",
        size,
        users_table,
        user_count,
        open_err,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Arranque del worker: vías de envío para recuperación de contraseña (sin secretos)."""
    log = logging.getLogger(__name__)
    _sqlite_startup_audit(log)
    delivery = password_reset_email_delivery_configured()
    smtp_ok = bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)
    resend_ok = bool(RESEND_API_KEY)
    if delivery:
        log.info(
            "DragonApp startup: password_reset_delivery=True smtp=%s resend=%s%s",
            smtp_ok,
            resend_ok,
            (
                f" smtp_security={SMTP_SECURITY} smtp_port={SMTP_PORT}"
                if smtp_ok
                else ""
            ),
        )
        if resend_ok and not resend_sender_plausible():
            log.warning(
                "DragonApp startup: RESEND_API_KEY definida pero RESEND_FROM/EMAIL_FROM no es un remitente "
                "válido para Resend (evita localhost, ejemplo.com; usa un dominio verificado en Resend)."
            )
    else:
        log.warning(
            "DragonApp startup: password_reset_delivery=False — definir SMTP completo "
            "(+ alias EMAIL_*/MAIL_*) o RESEND_API_KEY para enviar correo de recuperación."
        )
    if (os.getenv("RENDER_SERVICE_ID") or "").strip() or (
        os.getenv("RENDER_EXTERNAL_HOSTNAME") or ""
    ).strip():
        log.info(
            "DragonApp startup: entorno Render detectado. Si escalas a varias instancias o el disco "
            "no es persistente, SQLite puede diverger (por ejemplo registro en un dyno y olvidé mi "
            "contraseña en otro). Usa una instancia, disco persistente o base gestionada."
        )
    yield


app = FastAPI(
    title=APP_NAME,
    description="API para ejecutar análisis de reportes hoteleros, listar análisis y descargar PDFs. Autenticación por API key (header X-API-Key o Authorization: Bearer <key>).",
    version="1.0",
    docs_url="/docs",
    redoc_url=None,  # servimos ReDoc a mano con URL absoluta del schema para que cargue bien
    openapi_url="/openapi.json",
    lifespan=lifespan,
)
# Cookie de sesión: Secure si APP_URL es https. En local con http://127.0.0.1 y .env de producción,
# las cookies Secure no se envían → usar SESSION_INSECURE_COOKIES=1 (solo desarrollo).
_app_url_lower = (APP_URL or "").strip().lower()
_session_insecure = os.getenv("SESSION_INSECURE_COOKIES", "").strip().lower() in ("1", "true", "yes")
_https_only = _app_url_lower.startswith("https://") and not _session_insecure
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, same_site="lax", https_only=_https_only)
# En Render/nginx: TRUST_PROXY_HEADERS=1 para que X-Forwarded-* ajuste el host/esquema vistos por la app
# (enlaces absolutos en correos de recuperación de contraseña).
_trust_proxy = os.getenv("TRUST_PROXY_HEADERS", "").strip().lower() in ("1", "true", "yes")
if _trust_proxy:
    from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
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
async def http_exception_handler(request: Request, exc: HTTPException):
    """Para 401 (no autenticado): redirigir a login en peticiones HTML; devolver JSON con redirect en API/fetch."""
    if exc.status_code == 401:
        accept = (request.headers.get("accept") or "").lower()
        wants_html = "text/html" in accept and "application/json" not in accept
        raw_path = request.url.path or ""
        path = internal_path(raw_path)
        if wants_html or path.startswith("/app") or path.startswith("/admin") or path == "/":
            next_url = path if path and path != "/" else "/app"
            return RedirectResponse(
                url=f"{url_path('/login')}?next={quote(next_url, safe='/')}",
                status_code=303,
            )
        return JSONResponse(
            {"ok": False, "error": exc.detail or "Debes iniciar sesión", "redirect": url_path("/login")},
            status_code=401,
        )
    return await default_http_exception_handler(request, exc)



@app.get("/app/account", response_class=HTMLResponse)
def account_page(request: Request):
    """Mi cuenta: perfil, editar datos, y opciones de plan (Pro y Pro+)."""
    user = require_user(request)
    if onboarding_pending(user):
        return RedirectResponse(url_path("/onboarding"), status_code=303)
    _seo = noindex_page_seo("/app/account", "Mi cuenta — DRAGONNÉ", "Área privada del panel Pullso.")
    eff = get_effective_plan(user)
    paid = get_paid_plan(user)
    return templates.TemplateResponse("account.html", {
        "request": request,
        "user": user,
        "effective_plan": eff,
        "paid_plan": paid,
        "plan_label": plan_label(eff),
        "paid_plan_label": plan_label(paid),
        "manual_access_notice": manual_access_notice_for_account(user),
        "monthly_price": MONTHLY_PRICE,
        "premium_monthly_price": PREMIUM_MONTHLY_PRICE,
        "stripe_publishable_key": STRIPE_PUBLISHABLE_KEY,
        **_seo,
    })


@app.get("/app", response_class=HTMLResponse)
def dashboard(request: Request):
    user = require_user(request)
    if onboarding_pending(user):
        return RedirectResponse(url_path("/onboarding"), status_code=303)
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
        _created = row["created_at"]
        _days = row["days_covered"]
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
    eff = get_effective_plan(user)
    _seo = noindex_page_seo("/app", "Panel Pullso — DRAGONNÉ", "Área autenticada (no indexar).")
    return templates.TemplateResponse("app.html", {
        "request": request,
        "user": user,
        "effective_plan": eff,
        "is_admin": is_admin_user(user),
        "analyses": formatted,
        "plan_label": plan_label(eff),
        "max_files_per_analysis": max_upload_files_for_plan(eff),
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
        **_seo,
    })


from routes.admin import router as admin_router
from routes.analysis import router as analysis_router
from routes.api import router as api_v1_router
from routes.auth import router as auth_router
from routes.billing import router as billing_router
from routes.consulting import router as consulting_router
from routes.marketing import router as marketing_router
from routes.revenue_report_preview import router as revenue_report_preview_router

app.include_router(api_v1_router)
app.include_router(billing_router)
app.include_router(marketing_router)
app.include_router(auth_router)
app.include_router(consulting_router)
app.include_router(admin_router)
app.include_router(analysis_router)
app.include_router(revenue_report_preview_router)


@app.get("/health")
def health():
    """Solo estado básico; no exponer configuración interna."""
    return {"ok": True, "app": APP_NAME}


@app.get("/health/config")
def health_config(smtp_probe: bool = Query(False)):
    """Indica si las variables de entorno críticas están definidas (solo sí/no, sin valores).

    smtp_probe=true — prueba TCP al servidor SMTP (~2 s); útil si el correo no sale y el firewall bloquea el puerto.
    """
    out = {
        "ok": True,
        "openai_configured": bool(OPENAI_API_KEY and OPENAI_API_KEY.strip()),
        "stripe_configured": bool(STRIPE_SECRET_KEY and STRIPE_SECRET_KEY.strip()),
        "stripe_webhook_configured": bool(STRIPE_WEBHOOK_SECRET and STRIPE_WEBHOOK_SECRET.strip()),
        "stripe_pro_price_configured": bool(STRIPE_MONTHLY_PRICE_ID and STRIPE_MONTHLY_PRICE_ID.strip()),
        "stripe_pro_plus_price_configured": bool(STRIPE_PRO_PLUS_PRICE_ID and STRIPE_PRO_PLUS_PRICE_ID.strip()),
        "smtp_configured": bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD),
        "smtp_host_set": bool(SMTP_HOST),
        "smtp_user_set": bool(SMTP_USER),
        "smtp_password_set": bool(SMTP_PASSWORD),
        "smtp_envelope_configured": bool((SMTP_ENVELOPE_FROM or SMTP_USER or "").strip()),
        "smtp_security": SMTP_SECURITY,
        "smtp_port": SMTP_PORT,
        "resend_configured": bool(RESEND_API_KEY),
        "resend_sender_plausible": resend_sender_plausible(),
        "password_reset_email_delivery_configured": password_reset_email_delivery_configured(),
        "url_prefix_configured": bool(URL_PREFIX),
    }
    if smtp_probe:
        out["smtp_tcp_reachable"] = smtp_host_tcp_reachable()
    return out
