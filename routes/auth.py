"""Registro, login, logout, onboarding, recuperación de contraseña."""
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
from config import APP_URL, SMTP_HOST, SMTP_PASSWORD, SMTP_USER
from db import db
from debuglog import _debug_log
from email_smtp import send_password_reset_email
from templating import templates
from time_utils import now_iso

router = APIRouter(tags=["auth"])


@router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    if get_current_user(request):
        return RedirectResponse("/app", status_code=303)
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


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next_url: str = Query("", alias="next")):
    user = get_current_user(request)
    if user:
        return RedirectResponse("/admin" if is_admin_user(user) else "/app", status_code=303)
    next_safe = next_url.strip() if next_url and next_url.strip().startswith("/") and not next_url.strip().startswith("//") else ""
    return templates.TemplateResponse("login.html", {"request": request, "error": None, "next": next_safe})


@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), next_url: str = Form("", alias="next")):
    if login_rate_limiter.is_blocked(request):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Demasiados intentos. Espera unos minutos e intenta de nuevo."}, status_code=429)
    with db() as conn:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
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
    return RedirectResponse(redirect_to, status_code=303)


@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    if get_current_user(request):
        return RedirectResponse("/app", status_code=303)
    return templates.TemplateResponse("forgot_password.html", {"request": request, "sent": False, "error": None, "reset_link": None, "smtp_configured": bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)})


@router.post("/forgot-password", response_class=HTMLResponse)
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
            reset_link = None
        return templates.TemplateResponse("forgot_password.html", {"request": request, "sent": True, "error": None, "reset_link": reset_link, "email_sent": email_sent, "smtp_configured": smtp_configured})
    except Exception:
        return templates.TemplateResponse("forgot_password.html", {
            "request": request, "sent": False, "error": "Algo falló al generar el enlace. Vuelve a intentar; si el servidor no tiene correo configurado, se mostrará un enlace en pantalla.", "reset_link": reset_link, "email_sent": False, "smtp_configured": smtp_configured
        })


@router.get("/reset-password/{token}", response_class=HTMLResponse)
def reset_password_page(request: Request, token: str):
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token, "error": None})


@router.post("/reset-password/{token}", response_class=HTMLResponse)
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
    return RedirectResponse("/", status_code=303)


@router.get("/onboarding", response_class=HTMLResponse)
def onboarding_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
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
