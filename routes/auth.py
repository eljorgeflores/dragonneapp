"""Registro, login, logout, onboarding, recuperación de contraseña."""
import json
import logging
import os
from urllib.parse import quote, urlparse

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from auth_session import (
    MagicLinkConsumeResult,
    client_ip_from_request,
    consume_magic_link_token,
    consume_reset_token,
    create_magic_link_token,
    create_reset_token,
    establish_web_session,
    get_current_user,
    is_admin_user,
    login_rate_limiter,
    magic_link_rate_limiter,
    onboarding_pending,
    password_hash,
    require_user,
    verify_password,
)
import config
from config import (
    LEGAL_DOCS_VERSION,
    MAGIC_LINK_TTL_MINUTES,
    PASSWORD_RESET_TOKEN_TTL_HOURS,
    magic_link_consume_public_path,
    password_reset_email_delivery_configured,
    reset_password_public_path,
    url_path,
)
from db import db
from debuglog import _debug_log, fd2ebf_log
from email_smtp import send_magic_link_email, send_password_reset_email
from request_public_url import origin_for_user_facing_links
from seo_helpers import noindex_page_seo
from templating import templates
from time_utils import now_iso

_log = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])

_LOGIN_SEO = noindex_page_seo("/login", "Entrar — Pullso", "Inicio de sesión al panel Pullso (no indexar).")
_SIGNUP_SEO = noindex_page_seo("/signup", "Crear cuenta — Pullso", "Registro de usuario (no indexar).")
_ONBOARDING_SEO = noindex_page_seo("/onboarding", "Completar perfil — Pullso", "Formulario post-registro (no indexar).")


def _signup_template_ctx(request: Request, *, error: str | None = None) -> dict:
    return {"request": request, "error": error, "legal_docs_version": LEGAL_DOCS_VERSION, **_SIGNUP_SEO}
_FORGOT_SEO = noindex_page_seo("/forgot-password", "Recuperar contraseña — Pullso", "Recuperación de acceso (no indexar).")
_RESET_SEO = noindex_page_seo("/reset-password", "Nueva contraseña — Pullso", "Restablecer contraseña (no indexar).")

# Coincide correos guardados con espacios o mayúsculas heredadas
_SQL_USER_BY_EMAIL_NORM = "SELECT * FROM users WHERE LOWER(TRIM(email)) = ?"


def _email_domain_for_log(addr: str) -> str:
    a = (addr or "").strip().lower()
    return a.rsplit("@", 1)[-1] if "@" in a else "invalid"


def _safe_next_url(raw: str) -> str:
    n = (raw or "").strip()
    if n.startswith("/") and not n.startswith("//"):
        return n
    return ""


def _token_prefix_for_log(t: str) -> str:
    s = (t or "").strip()
    if not s:
        return "?"
    return (s[:12] + "…") if len(s) > 12 else s


def _login_template_ctx(
    request: Request,
    *,
    error: str | None = None,
    next_safe: str = "",
    magic_link_info: bool = False,
    magic_link_delivery_warning: bool = False,
    magic_link_error: str | None = None,
) -> dict:
    return {
        "request": request,
        "error": error,
        "next": next_safe,
        "magic_link_info": magic_link_info,
        "magic_link_delivery_warning": magic_link_delivery_warning,
        "magic_link_error": magic_link_error,
        "magic_link_ttl_minutes": MAGIC_LINK_TTL_MINUTES,
        **_LOGIN_SEO,
    }


@router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    if get_current_user(request):
        return RedirectResponse(url_path("/app"), status_code=303)
    return templates.TemplateResponse("signup.html", _signup_template_ctx(request))


@router.post("/signup")
def signup(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(""),
    accept_legal: str = Form(""),
):
    email = email.strip().lower()
    if len(password) < 8:
        return templates.TemplateResponse(
            "signup.html",
            _signup_template_ctx(request, error="La contraseña debe tener al menos 8 caracteres."),
            status_code=400,
        )
    if password != password_confirm:
        return templates.TemplateResponse(
            "signup.html",
            _signup_template_ctx(request, error="Las contraseñas no coinciden."),
            status_code=400,
        )
    if accept_legal != "1":
        return templates.TemplateResponse(
            "signup.html",
            _signup_template_ctx(
                request,
                error="Debes aceptar los Términos y condiciones y la Política de privacidad para crear una cuenta.",
            ),
            status_code=400,
        )
    accepted_at = now_iso()
    with db() as conn:
        exists = conn.execute(
            "SELECT id FROM users WHERE LOWER(TRIM(email)) = ?", (email,)
        ).fetchone()
        if exists:
            return templates.TemplateResponse(
                "signup.html",
                _signup_template_ctx(request, error="Ese correo ya está registrado."),
                status_code=400,
            )
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
                updated_at,
                legal_accepted_at,
                legal_docs_version
            ) VALUES ('', NULL, NULL, NULL, '', ?, ?, 'free', ?, ?, ?, ?)
            """,
            (email, password_hash(password), accepted_at, accepted_at, accepted_at, LEGAL_DOCS_VERSION),
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
    next_safe = _safe_next_url(next_url)
    magic_link_error = None
    if (request.query_params.get("magic_link_error") or "").strip() == "1":
        magic_link_error = (
            "El enlace de acceso no es válido o ha caducado. Solicita uno nuevo desde aquí."
        )
    return templates.TemplateResponse(
        "login.html",
        _login_template_ctx(request, next_safe=next_safe, magic_link_error=magic_link_error),
    )


@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), next_url: str = Form("", alias="next")):
    next_safe = _safe_next_url(next_url)
    if login_rate_limiter.is_blocked(request):
        return templates.TemplateResponse(
            "login.html",
            _login_template_ctx(
                request,
                error="Demasiados intentos. Espera unos minutos e intenta de nuevo.",
                next_safe=next_safe,
            ),
            status_code=429,
        )
    email_norm = email.strip().lower()
    with db() as conn:
        user = conn.execute(_SQL_USER_BY_EMAIL_NORM, (email_norm,)).fetchone()
    if not user or not verify_password(password, user["password_hash"]):
        login_rate_limiter.record_failed(request)
        return templates.TemplateResponse(
            "login.html",
            _login_template_ctx(
                request,
                error="Correo o contraseña incorrectos.",
                next_safe=next_safe,
            ),
            status_code=400,
        )
    establish_web_session(request, user["id"])
    redirect_to = next_safe or "/app"
    if not next_safe and is_admin_user(user):
        redirect_to = "/admin"
    _debug_log("routes.auth:login", "POST login success", {"redirect_to": redirect_to}, "H3")
    return RedirectResponse(url_path(redirect_to), status_code=303)


@router.post("/login/magic-link", response_class=HTMLResponse)
def login_magic_link_post(
    request: Request,
    email: str = Form(...),
    next_url: str = Form("", alias="next"),
):
    next_safe = _safe_next_url(next_url)
    email_norm = email.strip().lower()
    limited, lim_reason = magic_link_rate_limiter.record_and_check_limited(request, email_norm)
    if limited:
        _log.warning(
            "magic_link.rate_limited reason=%s domain=%s ip_prefix=%s",
            lim_reason,
            _email_domain_for_log(email_norm),
            (client_ip_from_request(request) or "")[:32],
        )
        return templates.TemplateResponse(
            "login.html",
            _login_template_ctx(request, next_safe=next_safe, magic_link_info=True),
        )

    _log.info("magic_link.requested domain=%s", _email_domain_for_log(email_norm))
    delivery_ok = password_reset_email_delivery_configured()

    try:
        with db() as conn:
            user = conn.execute(_SQL_USER_BY_EMAIL_NORM, (email_norm,)).fetchone()
        if not user:
            _log.info("magic_link.unknown_email domain=%s", _email_domain_for_log(email_norm))
            return templates.TemplateResponse(
                "login.html",
                _login_template_ctx(request, next_safe=next_safe, magic_link_info=True),
            )

        _log.info(
            "magic_link.user_found user_id=%s domain=%s",
            user["id"],
            _email_domain_for_log(email_norm),
        )
        token = create_magic_link_token(
            user["id"],
            requested_ip=client_ip_from_request(request),
            user_agent=request.headers.get("user-agent"),
        )
        _log.info(
            "magic_link.token_issued user_id=%s prefix=%s",
            user["id"],
            _token_prefix_for_log(token),
        )
        base = origin_for_user_facing_links(request)
        consume_base = magic_link_consume_public_path()
        q_suffix = f"?token={quote(token, safe='')}"
        if next_safe:
            q_suffix += f"&next={quote(next_safe, safe='')}"
        magic_url = f"{base}{consume_base}{q_suffix}"
        magic_url_alt = f"{base}{consume_base}/{token}"
        if next_safe:
            magic_url_alt += f"?next={quote(next_safe, safe='')}"
        email_sent = send_magic_link_email(
            email_norm,
            magic_url,
            magic_link_fallback=magic_url_alt,
            ttl_minutes=MAGIC_LINK_TTL_MINUTES,
        )
        if email_sent:
            _log.info(
                "magic_link.email_sent user_id=%s domain=%s",
                user["id"],
                _email_domain_for_log(email_norm),
            )
        else:
            _log.warning(
                "magic_link.email_failed user_id=%s domain=%s delivery_configured=%s",
                user["id"],
                _email_domain_for_log(email_norm),
                delivery_ok,
            )
        delivery_warn = bool(delivery_ok and not email_sent)
        return templates.TemplateResponse(
            "login.html",
            _login_template_ctx(
                request,
                next_safe=next_safe,
                magic_link_info=True,
                magic_link_delivery_warning=delivery_warn,
            ),
        )
    except Exception:
        _log.exception(
            "magic_link.request_error domain=%s",
            _email_domain_for_log(email_norm),
        )
        return templates.TemplateResponse(
            "login.html",
            _login_template_ctx(
                request,
                next_safe=next_safe,
                magic_link_info=True,
                magic_link_delivery_warning=delivery_ok,
            ),
        )


def _magic_link_consume(request: Request, token: str, next_raw: str):
    next_safe = _safe_next_url(next_raw)
    prefix = _token_prefix_for_log(token)
    result, user_id = consume_magic_link_token(token)
    if result == MagicLinkConsumeResult.OK and user_id is not None:
        with db() as conn:
            user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            _log.error("magic_link.user_missing_after_consume user_id=%s", user_id)
            return RedirectResponse(url_path("/login?magic_link_error=1"), status_code=303)
        establish_web_session(request, user["id"])
        redirect_to = next_safe or "/app"
        if not next_safe and is_admin_user(user):
            redirect_to = "/admin"
        _log.info(
            "magic_link.token_consumed user_id=%s prefix=%s",
            user["id"],
            prefix,
        )
        return RedirectResponse(url_path(redirect_to), status_code=303)

    if result == MagicLinkConsumeResult.EXPIRED:
        _log.info("magic_link.token_expired prefix=%s", prefix)
    elif result == MagicLinkConsumeResult.ALREADY_USED:
        _log.info("magic_link.token_reused prefix=%s", prefix)
    else:
        _log.info("magic_link.token_invalid prefix=%s", prefix)
    return RedirectResponse(url_path("/login?magic_link_error=1"), status_code=303)


@router.get("/login/magic-link/consume")
def login_magic_link_consume_get(
    request: Request,
    token: str | None = Query(None),
    next_url: str = Query("", alias="next"),
):
    t = (token or "").strip()
    if not t:
        _log.info("magic_link.token_invalid reason=missing_query")
        return RedirectResponse(url_path("/login?magic_link_error=1"), status_code=303)
    return _magic_link_consume(request, t, next_url)


@router.get("/login/magic-link/consume/{token}")
def login_magic_link_consume_path(
    request: Request,
    token: str,
    next_url: str = Query("", alias="next"),
):
    return _magic_link_consume(request, (token or "").strip(), next_url)


@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    if get_current_user(request):
        return RedirectResponse(url_path("/app"), status_code=303)
    notice = (request.query_params.get("notice") or "").strip().lower()
    _smtp = bool(config.SMTP_HOST and config.SMTP_USER and config.SMTP_PASSWORD)
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
            **_FORGOT_SEO,
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
        **_FORGOT_SEO,
    }


@router.post("/forgot-password", response_class=HTMLResponse)
def forgot_password(request: Request, email: str = Form(...)):
    email = email.strip().lower()
    reset_link = None
    reset_link_alt = None
    email_sent = False
    smtp_configured = bool(
        config.SMTP_HOST and config.SMTP_USER and config.SMTP_PASSWORD
    )
    delivery_ok = password_reset_email_delivery_configured()
    # #region agent log
    fd2ebf_log(
        "routes/auth.py:forgot_password",
        "start",
        {
            "delivery_ok": delivery_ok,
            "smtp_configured": smtp_configured,
            "resend_key_set": bool(config.RESEND_API_KEY),
            "render_hosted": bool((os.getenv("RENDER_SERVICE_ID") or "").strip()),
        },
        "H1,H3",
    )
    # #endregion

    try:
        with db() as conn:
            user = conn.execute(_SQL_USER_BY_EMAIL_NORM, (email,)).fetchone()
        # #region agent log
        fd2ebf_log(
            "routes/auth.py:forgot_password",
            "after_user_lookup",
            {"user_found": bool(user)},
            "H2",
        )
        # #endregion
        if not user:
            # #region agent log
            fd2ebf_log(
                "routes/auth.py:forgot_password",
                "unknown_email_branch",
                {"delivery_ok": delivery_ok},
                "H2",
            )
            # #endregion
            _log.info(
                "forgot_password_metrics %s",
                json.dumps(
                    {
                        "branch": "unknown_email",
                        "smtp_configured": smtp_configured,
                        "resend_configured": bool(config.RESEND_API_KEY),
                    },
                    ensure_ascii=False,
                ),
            )
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
        # #region agent log
        _pu = urlparse(reset_link)
        fd2ebf_log(
            "routes/auth.py:forgot_password",
            "reset_links_built",
            {
                "link_scheme": _pu.scheme or "",
                "link_host": _pu.netloc or "",
                "reset_path_len": len(reset_path),
                "url_prefix_configured": bool(config.URL_PREFIX),
            },
            "H6",
        )
        # #endregion
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
        fd2ebf_log(
            "routes/auth.py:forgot_password",
            "after_send",
            {"email_sent": email_sent, "delivery_ok": delivery_ok},
            "H4,H5",
        )
        # #endregion
        _log.info(
            "forgot_password_metrics %s",
            json.dumps(
                {
                    "branch": "user_found",
                    "smtp_configured": smtp_configured,
                    "resend_configured": bool(config.RESEND_API_KEY),
                    "email_sent": email_sent,
                },
                ensure_ascii=False,
            ),
        )
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
            {"request": request, "token": token, "error": "Las contraseñas no coinciden.", **_RESET_SEO},
        )
    if len(password) < 8:
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "token": token, "error": "La contraseña debe tener al menos 8 caracteres.", **_RESET_SEO},
        )
    user_id = consume_reset_token(token)
    if not user_id:
        return templates.TemplateResponse(
            "reset_password.html",
            {
                "request": request,
                "token": None,
                "error": "El enlace ya no es válido. Solicita uno nuevo.",
                **_RESET_SEO,
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
    return templates.TemplateResponse(
        "reset_password.html", {"request": request, "token": t, "error": None, **_RESET_SEO}
    )


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
    return templates.TemplateResponse(
        "reset_password.html", {"request": request, "token": t, "error": None, **_RESET_SEO}
    )


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
        return templates.TemplateResponse(
            "onboarding.html", {"request": request, "error": None, "user": user, "editing": True, **_ONBOARDING_SEO}
        )
    return templates.TemplateResponse(
        "onboarding.html", {"request": request, "error": None, "user": user, "editing": False, **_ONBOARDING_SEO}
    )


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
        return templates.TemplateResponse(
            "onboarding.html",
            {
                "request": request,
                "error": "Nombre del hotel y contacto son obligatorios.",
                "user": user,
                "editing": False,
                **_ONBOARDING_SEO,
            },
            status_code=400,
        )
    if not hotel_size or not hotel_category:
        return templates.TemplateResponse(
            "onboarding.html",
            {
                "request": request,
                "error": "Indica el tamaño y la categoría de tu hotel para personalizar las recomendaciones.",
                "user": user,
                "editing": False,
                **_ONBOARDING_SEO,
            },
            status_code=400,
        )
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
