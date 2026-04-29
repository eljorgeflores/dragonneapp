"""The Circle — onboarding y dashboard privado para Revenue Managers.

En esta etapa el foco es captar, verificar y ordenar perfiles (no marketplace público).
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from auth_session import establish_web_session, get_current_user, is_admin_user, password_hash, require_user, verify_password
from config import LEGAL_DOCS_VERSION, url_path
from db import db
from seo_helpers import noindex_page_seo
from templating import templates
from time_utils import now_iso


router = APIRouter(tags=["circle"])

_CIRCLE_REGISTER_SEO = noindex_page_seo(
    "/circle/register",
    "Regístrate — The Circle",
    "Registro para Revenue Managers (no indexar).",
)
_CIRCLE_LOGIN_SEO = noindex_page_seo(
    "/circle/login",
    "Entrar — The Circle",
    "Inicio de sesión The Circle (no indexar).",
)
_CIRCLE_ONBOARDING_SEO = noindex_page_seo(
    "/circle/onboarding",
    "Onboarding — The Circle",
    "Completar perfil de Revenue Manager (no indexar).",
)
_CIRCLE_DASHBOARD_SEO = noindex_page_seo(
    "/circle/dashboard",
    "Dashboard — The Circle",
    "Panel privado de Revenue Manager (no indexar).",
)
_CIRCLE_ADMIN_SEO = noindex_page_seo(
    "/circle/admin",
    "Admin — The Circle",
    "Revisión de perfiles (no indexar).",
)


def _safe_redirect(default_path: str, next_url: str | None) -> str:
    n = (next_url or "").strip()
    if n.startswith("/") and not n.startswith("//"):
        return n
    return default_path


def _require_revenue_manager(request: Request):
    user = require_user(request)
    role = (user["role"] or "").strip() if "role" in user.keys() else ""
    if role != "revenue_manager" and not is_admin_user(user):
        return RedirectResponse(url_path("/circle/login"), status_code=303)
    return user


def _status_label(status: str) -> str:
    s = (status or "").strip()
    return {
        "draft": "Perfil incompleto",
        "submitted": "Perfil en verificación",
        "verified": "Perfil verificado",
        "needs_changes": "Necesitamos algunos ajustes",
        "inactive": "Perfil pausado",
    }.get(s, "Perfil incompleto")


def _load_profile_for_user(user_id: int):
    with db() as conn:
        return conn.execute(
            "SELECT * FROM revenue_profiles WHERE user_id = ?",
            (user_id,),
        ).fetchone()


def _ensure_profile(user_id: int):
    prof = _load_profile_for_user(user_id)
    if prof:
        return prof
    ts = now_iso()
    with db() as conn:
        conn.execute(
            """
            INSERT INTO revenue_profiles (user_id, status, created_at, updated_at)
            VALUES (?, 'draft', ?, ?)
            """,
            (user_id, ts, ts),
        )
    return _load_profile_for_user(user_id)


def _json_list(raw: Any) -> List[str]:
    if not raw:
        return []
    try:
        v = json.loads(raw) if isinstance(raw, str) else raw
        if isinstance(v, list):
            return [str(x) for x in v if str(x).strip()]
    except Exception:
        pass
    return []


@router.get("/circle/register", response_class=HTMLResponse)
def circle_register_page(request: Request):
    if get_current_user(request):
        return RedirectResponse(url_path("/circle/dashboard"), status_code=303)
    return templates.TemplateResponse(
        "circle/register.html",
        {"request": request, "error": None, "legal_docs_version": LEGAL_DOCS_VERSION, **_CIRCLE_REGISTER_SEO},
    )


@router.post("/circle/register")
def circle_register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(""),
    accept_legal: str = Form(""),
):
    email_norm = email.strip().lower()
    if len(password) < 8:
        return templates.TemplateResponse(
            "circle/register.html",
            {"request": request, "error": "La contraseña debe tener al menos 8 caracteres.", "legal_docs_version": LEGAL_DOCS_VERSION, **_CIRCLE_REGISTER_SEO},
            status_code=400,
        )
    if password != password_confirm:
        return templates.TemplateResponse(
            "circle/register.html",
            {"request": request, "error": "Las contraseñas no coinciden.", "legal_docs_version": LEGAL_DOCS_VERSION, **_CIRCLE_REGISTER_SEO},
            status_code=400,
        )
    if accept_legal != "1":
        return templates.TemplateResponse(
            "circle/register.html",
            {"request": request, "error": "Debes aceptar los Términos y condiciones y la Política de privacidad.", "legal_docs_version": LEGAL_DOCS_VERSION, **_CIRCLE_REGISTER_SEO},
            status_code=400,
        )
    ts = now_iso()
    with db() as conn:
        exists = conn.execute("SELECT id FROM users WHERE LOWER(TRIM(email)) = ?", (email_norm,)).fetchone()
        if exists:
            return templates.TemplateResponse(
                "circle/register.html",
                {"request": request, "error": "Ese correo ya está registrado.", "legal_docs_version": LEGAL_DOCS_VERSION, **_CIRCLE_REGISTER_SEO},
                status_code=400,
            )
        cur = conn.execute(
            """
            INSERT INTO users (
                hotel_name, hotel_size, hotel_category, hotel_location,
                contact_name, email, password_hash, plan, role,
                created_at, updated_at, legal_accepted_at, legal_docs_version
            ) VALUES ('', NULL, NULL, NULL, '', ?, ?, 'free', 'revenue_manager', ?, ?, ?, ?)
            """,
            (email_norm, password_hash(password), ts, ts, ts, LEGAL_DOCS_VERSION),
        )
        user_id = int(cur.lastrowid)
    establish_web_session(request, user_id)
    _ensure_profile(user_id)
    return RedirectResponse(url_path("/circle/onboarding"), status_code=303)


@router.get("/circle/login", response_class=HTMLResponse)
def circle_login_page(request: Request):
    if get_current_user(request):
        return RedirectResponse(url_path("/circle/dashboard"), status_code=303)
    return templates.TemplateResponse(
        "circle/login.html",
        {"request": request, "error": None, **_CIRCLE_LOGIN_SEO},
    )


@router.post("/circle/login")
def circle_login(request: Request, email: str = Form(...), password: str = Form(...)):
    email_norm = email.strip().lower()
    with db() as conn:
        user = conn.execute("SELECT * FROM users WHERE LOWER(TRIM(email)) = ?", (email_norm,)).fetchone()
    if not user or not verify_password(password, user["password_hash"]):
        return templates.TemplateResponse(
            "circle/login.html",
            {"request": request, "error": "Correo o contraseña incorrectos.", **_CIRCLE_LOGIN_SEO},
            status_code=400,
        )
    role = (user["role"] or "").strip() if "role" in user.keys() else ""
    if role != "revenue_manager" and not is_admin_user(user):
        return templates.TemplateResponse(
            "circle/login.html",
            {"request": request, "error": "Esta cuenta no tiene acceso a The Circle.", **_CIRCLE_LOGIN_SEO},
            status_code=403,
        )
    establish_web_session(request, int(user["id"]))
    _ensure_profile(int(user["id"]))
    return RedirectResponse(url_path("/circle/dashboard"), status_code=303)


@router.post("/circle/logout")
def circle_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url_path("/circle/login"), status_code=303)


@router.get("/circle/onboarding", response_class=HTMLResponse)
def circle_onboarding_page(request: Request, step: int = 1):
    user = _require_revenue_manager(request)
    if isinstance(user, RedirectResponse):
        return user

    prof = _ensure_profile(int(user["id"]))
    step = max(1, min(int(step or 1), 7))
    return templates.TemplateResponse(
        "circle/onboarding.html",
        {
            "request": request,
            "user": user,
            "profile": prof,
            "step": step,
            "status_label": _status_label(prof["status"]),
            "hotel_types": _json_list(prof["hotel_types_json"]),
            "specialties": _json_list(prof["specialties_json"]),
            "tools": _json_list(prof["tools_json"]),
            "languages": _json_list(prof["languages_json"]),
            "work_models": _json_list(prof["work_models_json"]),
            "delivery_modes": _json_list(prof["delivery_modes_json"]),
            "error": None,
            **_CIRCLE_ONBOARDING_SEO,
        },
    )


@router.post("/circle/onboarding")
async def circle_onboarding_save(request: Request, step: int = Form(1), nav: str = Form("next")):
    user = _require_revenue_manager(request)
    if isinstance(user, RedirectResponse):
        return user
    prof = _ensure_profile(int(user["id"]))
    step = max(1, min(int(step or 1), 7))
    ts = now_iso()

    form = await request.form()
    payload = dict(form)

    update: Dict[str, Any] = {"updated_at": ts}
    if step == 1:
        update.update(
            {
                "full_name": (payload.get("full_name") or "").strip(),
                "phone": (payload.get("phone") or "").strip(),
                "city": (payload.get("city") or "").strip(),
                "country": (payload.get("country") or "").strip(),
                "photo_url": (payload.get("photo_url") or "").strip(),
            }
        )
    elif step == 2:
        def _int(x: Any) -> Optional[int]:
            try:
                return int(str(x).strip())
            except Exception:
                return None
        update.update(
            {
                "years_experience": _int(payload.get("years_experience")),
                "current_role": (payload.get("current_role") or "").strip(),
                "properties_managed": _int(payload.get("properties_managed")),
                "hotel_types_json": json.dumps(form.getlist("hotel_types")),
            }
        )
    elif step == 3:
        update["specialties_json"] = json.dumps(form.getlist("specialties"))
    elif step == 4:
        update["tools_json"] = json.dumps(form.getlist("tools"))
    elif step == 5:
        def _int(x: Any) -> Optional[int]:
            try:
                return int(str(x).strip())
            except Exception:
                return None
        update.update(
            {
                "work_models_json": json.dumps(form.getlist("work_models")),
                "delivery_modes_json": json.dumps(form.getlist("delivery_modes")),
                "availability_hours": _int(payload.get("availability_hours")),
                "hourly_rate_mxn": _int(payload.get("hourly_rate_mxn")),
                "monthly_rate_mxn": _int(payload.get("monthly_rate_mxn")),
                "languages_json": json.dumps(form.getlist("languages")),
            }
        )
    elif step == 6:
        update.update(
            {
                "professional_title": (payload.get("professional_title") or "").strip(),
                "bio": (payload.get("bio") or "").strip(),
                "how_help": (payload.get("how_help") or "").strip(),
                "highlights": (payload.get("highlights") or "").strip(),
            }
        )
    elif step == 7 and nav == "submit":
        update["status"] = "submitted"

    with db() as conn:
        sets = ", ".join([f"{k} = ?" for k in update.keys()])
        conn.execute(
            f"UPDATE revenue_profiles SET {sets} WHERE id = ?",
            (*update.values(), int(prof["id"])),
        )

    if step == 7 and nav == "submit":
        return RedirectResponse(url_path("/circle/dashboard"), status_code=303)
    next_step = step + 1 if nav == "next" else max(1, step - 1)
    return RedirectResponse(url_path(f"/circle/onboarding?step={next_step}"), status_code=303)


def _mock_matches(profile_row) -> List[Dict[str, Any]]:
    # Por ahora: genera 0–2 matches potenciales desde proyectos seed.
    specialties = set(_json_list(profile_row["specialties_json"]))
    tools = set(_json_list(profile_row["tools_json"]))
    matches: List[Dict[str, Any]] = []
    with db() as conn:
        projects = conn.execute("SELECT * FROM circle_projects WHERE status = 'open' ORDER BY id DESC LIMIT 5").fetchall()
    for p in projects:
        req_s = set(_json_list(p["required_specialties_json"]))
        req_t = set(_json_list(p["required_tools_json"]))
        score = 0.0
        if req_s:
            score += len(req_s & specialties) / max(1, len(req_s)) * 0.65
        if req_t:
            score += len(req_t & tools) / max(1, len(req_t)) * 0.35
        if score <= 0.20:
            continue
        matches.append(
            {
                "status": "potential",
                "match_score": round(score * 100),
                "hotel_type": p["hotel_type"] or "Hotel",
                "city": p["city"] or "—",
                "scope": p["scope"],
                "estimated_duration": p["estimated_duration"] or "—",
                "work_model": p["work_model"] or "—",
            }
        )
        if len(matches) >= 2:
            break
    return matches


@router.get("/circle/dashboard", response_class=HTMLResponse)
def circle_dashboard(request: Request):
    user = _require_revenue_manager(request)
    if isinstance(user, RedirectResponse):
        return user
    prof = _ensure_profile(int(user["id"]))
    matches = _mock_matches(prof) if prof["status"] in ("verified", "submitted") else []
    return templates.TemplateResponse(
        "circle/dashboard.html",
        {
            "request": request,
            "user": user,
            "profile": prof,
            "status_label": _status_label(prof["status"]),
            "matches": matches,
            "specialties": _json_list(prof["specialties_json"]),
            "tools": _json_list(prof["tools_json"]),
            "hotel_types": _json_list(prof["hotel_types_json"]),
            "languages": _json_list(prof["languages_json"]),
            "work_models": _json_list(prof["work_models_json"]),
            "delivery_modes": _json_list(prof["delivery_modes_json"]),
            **_CIRCLE_DASHBOARD_SEO,
        },
    )


@router.post("/circle/matches/interest")
def circle_match_interest(request: Request, idx: int = Form(0)):
    user = _require_revenue_manager(request)
    if isinstance(user, RedirectResponse):
        return user
    # Mock: sólo confirma interés y muestra modal genérico en dashboard
    return RedirectResponse(url_path("/circle/dashboard?interest=1"), status_code=303)


@router.get("/circle/admin", response_class=HTMLResponse)
def circle_admin(request: Request):
    user = require_user(request)
    if not is_admin_user(user):
        return RedirectResponse(url_path("/circle/login"), status_code=303)
    with db() as conn:
        profiles = conn.execute(
            """
            SELECT rp.*, u.email
            FROM revenue_profiles rp
            JOIN users u ON u.id = rp.user_id
            ORDER BY rp.updated_at DESC
            LIMIT 200
            """
        ).fetchall()
    return templates.TemplateResponse(
        "circle/admin.html",
        {"request": request, "user": user, "profiles": profiles, "status_label": _status_label, **_CIRCLE_ADMIN_SEO},
    )


@router.post("/circle/admin/status")
def circle_admin_status(request: Request, profile_id: int = Form(...), status: str = Form(...)):
    user = require_user(request)
    if not is_admin_user(user):
        return RedirectResponse(url_path("/circle/login"), status_code=303)
    status = (status or "").strip()
    if status not in ("verified", "needs_changes", "inactive", "submitted", "draft"):
        return RedirectResponse(url_path("/circle/admin"), status_code=303)
    with db() as conn:
        conn.execute(
            "UPDATE revenue_profiles SET status = ?, updated_at = ? WHERE id = ?",
            (status, now_iso(), int(profile_id)),
        )
    return RedirectResponse(url_path("/circle/admin"), status_code=303)

