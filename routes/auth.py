"""Registro, login, logout, onboarding, recuperación de contraseña."""
import json
import logging

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from auth_session import (
    create_reset_token,
    consume_reset_token,
    get_current_user,
    is_admin_user,
    login_rate_limiter,
    onboarding_pending,
    password_hash,
    require_user,
    verify_password,
)
from config import (
    PASSWORD_RESET_TOKEN_TTL_HOURS,
    RESEND_API_KEY,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_USER,
    password_reset_email_delivery_configured,
    reset_password_public_path,
    url_path,
)
from db import db
from debuglog import _debug_log
from email_smtp import send_password_reset_email

_log = logging.getLogger(__name__)
from request_public_url import origin_for_user_facing_links
from templating import templates
from time_utils import now_iso

router = APIRouter(tags=["auth"])

# Coincide correos guardados con espacios o mayúsculas heredadas
_SQL_USER_BY_EMAIL_NORM = "SELECT * FROM users WHERE LOWER(TRIM(email)) = ?"


@router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    if get_current_user(request):
        return RedirectResponse(url_path("/app"), status_code=303)
    return templates.TemplateResponse("signup.html", {"request": request, "error": None})


@router.post("/signup")
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
        exists = conn.execute(
            "SELECT id FROM users WHERE LOWER(TRIM(email)) = ?", (email,)
        ).fetchone()
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
    return RedirectResponse(url_path("/onboarding"), status_code=303)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next_url: str = Query("", alias="next")):
    user = get_current_user(request)
    if user:
        return RedirectResponse(
            url_path("/admin" if is_admin_user(user) else "/app"),
            status_code=303,
        )
    next_safe = next_url.strip() if next_url and next_url.strip().startswith("/") and not next_url.strip().startswith("//") else ""
    return templates.TemplateResponse("login.html", {"request": request, "error": None, "next": next_safe})


@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), next_url: str = Form("", alias="next")):
    if login_rate_limiter.is_blocked(request):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Demasiados intentos. Espera unos minutos e intenta de nuevo."}, status_code=429)
    with db() as conn:
        user = conn.execute(_SQL_USER_BY_EMAIL_NORM, (email.strip().lower(),)).fetchone()
    if not user or not verify_password(password, user["password_hash"]):
        login_rate_limiter.record_failed(request)
        return templates.TemplateResponse("login.html", {"request": request, "error": "Correo o contraseña incorrectos."}, status_code=400)
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
    if not next_safe and is_admin_user(user):
        redirect_to = "/admin"
    _debug_log("routes.auth:login", "POST login success", {"redirect_to": redirect_to}, "H3")
    return RedirectResponse(url_path(redirect_to), status_code=303)


@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    if get_current_user(request):
        return RedirectResponse(url_path("/app"), status_code=303)
    notice = (request.query_params.get("notice") or "").strip().lower()
    _smtp = bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)
    return templates.TemplateResponse(
        "forgot_password.html",
        {
            "request": request,
            "sent": False,
            "error": None,
            "reset_link": None,
            "reset_link_alt": None,
            "smtp_configured": _smtp,
            "email_delivery_configured": password_reset_email_delivery_configured(),
            "reset_ttl_hours": PASSWORD_RESET_TOKEN_TTL_HOURS,
            "unknown_email": False,
            "link_notice_incomplete": notice == "incomplete_link",
        },
    )


def _forgot_template_ctx(
    request: Request,
    *,
    sent: bool,
    error: str | None,
    reset_link: str | None,
    email_sent: bool,
    smtp_configured: bool,
    email_delivery_configured: bool,
    unknown_email: bool,
    reset_link_alt: str | None = None,
    link_notice_incomplete: bool = False,
) -> dict:
    return {
        "request": request,
        "sent": sent,
        "error": error,
        "reset_link": reset_link,
        "reset_link_alt": reset_link_alt,
        "email_sent": email_sent,
        "smtp_configured": smtp_configured,
        "email_delivery_configured": email_delivery_configured,
        "reset_ttl_hours": PASSWORD_RESET_TOKEN_TTL_HOURS,
        "unknown_email": unknown_email,
        "link_notice_incomplete": link_notice_incomplete,
    }


@router.post("/forgot-password", response_class=HTMLResponse)
def forgot_password(request: Request, email: str = Form(...)):
    email = email.strip().lower()
    reset_link = None
    reset_link_alt = None
    email_sent = False
    smtp_configured = bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)
    delivery_ok = password_reset_email_delivery_configured()

    try:
        with db() as conn:
            user = conn.execute(_SQL_USER_BY_EMAIL_NORM, (email,)).fetchone()
        if not user:
            # #region agent log
            _log.info(
                "forgot_password_metrics %s",
                json.dumps(
                    {
                        "branch": "unknown_email",
                        "smtp_configured": smtp_configured,
                        "resend_configured": bool(RESEND_API_KEY),
                    },
                    ensure_ascii=False,
                ),
            )
            # #endregion
            return templates.TemplateResponse(
                "forgot_password.html",
                _forgot_template_ctx(
                    request,
                    sent=True,
                    error=None,
                    reset_link=None,
                    email_sent=False,
                    smtp_configured=smtp_configured,
                    email_delivery_configured=delivery_ok,
                    unknown_email=True,
                    reset_link_alt=None,
                    link_notice_incomplete=False,
                ),
            )
        if not delivery_ok:
            _log.warning(
                "forgot_password: hay usuario pero no hay SMTP completo ni RESEND_API_KEY; "
                "solo enlace en pantalla."
            )
        token = create_reset_token(user["id"])
        base = origin_for_user_facing_links(request)
        # Query ?token= suele pasar mejor WAF/proxies; ruta con token como respaldo (correos que cortan ?token=)
        reset_path = reset_password_public_path()
        reset_link = f"{base}{reset_path}?token={token}"
        reset_link_alt = f"{base}{reset_path}/{token}"
        email_sent = send_password_reset_email(
            email,
            reset_link,
            reset_link_fallback=reset_link_alt,
        )
        if delivery_ok and not email_sent:
            _log.warning(
                "forgot_password: canal de correo configurado pero el envío falló; "
                "revisar logs (Resend HTTP o SMTP)."
            )
        # #region agent log
        _log.info(
            "forgot_password_metrics %s",
            json.dumps(
                {
                    "branch": "user_found",
                    "smtp_configured": smtp_configured,
                    "resend_configured": bool(RESEND_API_KEY),
                    "email_sent": email_sent,
                },
                ensure_ascii=False,
            ),
        )
        # #endregion
        # Conservar reset_link en la plantilla aunque el SMTP devuelva True (spam, demora,
        # “éxito” engañoso del proveedor): respaldo en la misma pantalla.
        return templates.TemplateResponse(
            "forgot_password.html",
            _forgot_template_ctx(
                request,
                sent=True,
                error=None,
                reset_link=reset_link,
                email_sent=email_sent,
                smtp_configured=smtp_configured,
                email_delivery_configured=delivery_ok,
                unknown_email=False,
                reset_link_alt=reset_link_alt,
                link_notice_incomplete=False,
            ),
        )
    except Exception:
        _log.exception("forgot_password: error al generar token o plantilla")
        return templates.TemplateResponse(
            "forgot_password.html",
            _forgot_template_ctx(
                request,
                sent=False,
                error="Algo falló al generar el enlace. Vuelve a intentar; si el servidor no tiene correo configurado, se mostrará un enlace en pantalla.",
                reset_link=reset_link,
                email_sent=False,
                smtp_configured=smtp_configured,
                email_delivery_configured=delivery_ok,
                unknown_email=False,
                reset_link_alt=reset_link_alt,
                link_notice_incomplete=False,
            ),
        )


def _reset_password_submit(
    request: Request,
    token: str,
    password: str,
    password_confirm: str,
):
    token = (token or "").strip()
    if password != password_confirm:
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "token": token, "error": "Las contraseñas no coinciden."},
        )
    if len(password) < 8:
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "token": token, "error": "La contraseña debe tener al menos 8 caracteres."},
        )
    user_id = consume_reset_token(token)
    if not user_id:
        return templates.TemplateResponse(
            "reset_password.html",
            {
                "request": request,
                "token": None,
                "error": "El enlace ya no es válido. Solicita uno nuevo.",
            },
        )
    with db() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
            (password_hash(password), now_iso(), user_id),
        )
    return RedirectResponse(url_path("/login"), status_code=303)


@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_page_query(request: Request, token: str | None = Query(None)):
    t = (token or "").strip()
    if not t:
        return RedirectResponse(
            url_path("/forgot-password?notice=incomplete_link"),
            status_code=303,
        )
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": t, "error": None})


@router.post("/reset-password", response_class=HTMLResponse)
def reset_password_form(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
):
    return _reset_password_submit(request, token, password, password_confirm)


@router.get("/reset-password/{token}", response_class=HTMLResponse)
def reset_password_page(request: Request, token: str):
    t = (token or "").strip()
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": t, "error": None})


@router.post("/reset-password/{token}", response_class=HTMLResponse)
def reset_password(request: Request, token: str, password: str = Form(...), password_confirm: str = Form(...)):
    return _reset_password_submit(request, token, password, password_confirm)


@router.post("/logout")
def logout(request: Request):
    session_id = request.session.get("session_id")
    if session_id:
        with db() as conn:
            conn.execute(
                "UPDATE user_sessions SET ended_at = ?, last_seen_at = ?, request_count = request_count + 1 WHERE id = ?",
                (now_iso(), now_iso(), session_id),
            )
    request.session.clear()
    return RedirectResponse(url_path("/"), status_code=303)


@router.get("/onboarding", response_class=HTMLResponse)
def onboarding_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url_path("/login"), status_code=303)
    if not onboarding_pending(user):
        return templates.TemplateResponse("onboarding.html", {"request": request, "error": None, "user": user, "editing": True})
    return templates.TemplateResponse("onboarding.html", {"request": request, "error": None, "user": user, "editing": False})


@router.post("/onboarding")
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
        return RedirectResponse(url_path("/login"), status_code=303)
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
    return RedirectResponse(url_path("/app"), status_code=303)
