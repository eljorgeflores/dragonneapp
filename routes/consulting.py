"""
Consultoría (fuera del núcleo DragonApp SaaS).

Rutas aisladas en este módulo para poder extraerlas a otro ASGI/despliegue sin tocar
el resto de routers. Ver docs/dragonapp_phase1.md y docs/dragonapp_phase2.md.
"""
import importlib.util
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse

from config import BASE_DIR, CONSULTING_CALENDAR_URL
from db import db
from email_smtp import send_consulting_lead_email
from templating import templates

router = APIRouter(tags=["consulting_parent"])


def _consulting_translations():
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
    def __missing__(self, key):
        return ""


@router.get("/consultoria", response_class=HTMLResponse)
def consulting_landing(request: Request, lang: str = Query("es", alias="lang")):
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


@router.get("/consulting", response_class=HTMLResponse)
def consulting_landing_en(request: Request, lang: str = Query("en", alias="lang")):
    return consulting_landing(request=request, lang=lang)


@router.post("/consultoria/lead", name="consulting_lead_submit")
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
        pass
    return JSONResponse({"ok": True})
