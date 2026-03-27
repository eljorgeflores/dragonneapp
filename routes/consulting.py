"""
Consultoría (fuera del núcleo DragonApp SaaS).

Rutas aisladas en este módulo para poder extraerlas a otro ASGI/despliegue sin tocar
el resto de routers. Ver docs/dragonapp_phase1.md y docs/dragonapp_phase2.md.
"""
import importlib.util
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse

from config import BASE_DIR, url_path
from db import db
from email_smtp import send_consulting_lead_email
from seo_helpers import absolute_url, graph_consulting_lang, graph_homepage
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


def render_consulting_landing(
    request: Request,
    lang: str = "es",
    *,
    page: str = "consultoria",
):
    """Landing corporativa. `page`: home (/), consultoria (/consultoria) o consulting (/consulting)."""
    if lang not in ("es", "en"):
        lang = "es"
    if page not in ("home", "consultoria", "consulting"):
        page = "consultoria"
    trans = _consulting_translations()
    t = trans.get(lang) or trans.get("es")
    if not t:
        t = _DefaultT()
    else:
        t = _DefaultT(t)

    url_es = absolute_url("/consultoria")
    url_en = absolute_url("/consulting")
    url_root = absolute_url("/")

    if page == "consulting":
        canonical_url = url_en
        html_lang = "en"
        og_locale = "en_US"
        og_locale_alternate = "es_MX"
        plang = "en"
    elif page == "home":
        canonical_url = url_root
        html_lang = "es-MX"
        og_locale = "es_MX"
        og_locale_alternate = "en_US"
        plang = "es"
    else:
        canonical_url = url_es
        html_lang = "es-MX"
        og_locale = "es_MX"
        og_locale_alternate = "en_US"
        plang = "es"

    hreflang_alternates = [
        {"hreflang": "es", "href": url_es},
        {"hreflang": "en", "href": url_en},
        {"hreflang": "x-default", "href": url_es},
    ]

    if plang == "en":
        meta_title = "DRAGONNÉ — Consulting for startups, SMBs & hospitality"
        meta_description = (
            "DRAGONNÉ advises early-stage startups, SMBs and hospitality operators on talent, technology "
            "and profitability — from diagnosis to execution, with clear deliverables."
        )
        og_title = "DRAGONNÉ — Strategy consulting & hospitality advisory"
        og_description = meta_description
        og_image_alt = "DRAGONNÉ — brand and headline about vision and talent"
    else:
        meta_title = "DRAGONNÉ — Consultoría en talento, tecnología y rentabilidad"
        meta_description = (
            "DRAGONNÉ acompaña a startups, pymes y hoteleros: prioridades claras, implementación tecnológica "
            "y rentabilidad, con entregables accionables para dirección y equipos comerciales."
        )
        og_title = "DRAGONNÉ — Consultoría estratégica para equipos en crecimiento"
        og_description = meta_description
        og_image_alt = "DRAGONNÉ — isotipo y mensaje de marca"

    if page == "home":
        structured = {"@context": "https://schema.org", "@graph": graph_homepage()}
    else:
        structured = {
            "@context": "https://schema.org",
            "@graph": graph_consulting_lang(lang=plang, canonical=canonical_url),
        }

    lead_path = url_path("/consultoria/lead")

    return templates.TemplateResponse(
        "consulting.html",
        {
            "request": request,
            "current_year": datetime.now(timezone.utc).year,
            "lang": lang,
            "t": t,
            "lead_form_action": lead_path,
            "meta_title": meta_title,
            "meta_description": meta_description,
            "meta_keywords": (
                "consultoría estratégica, startups, SMBs, hospitalidad, revenue, tecnología hotelera, México, LatAm"
                if plang == "es"
                else "strategy consulting, early-stage startups, SMBs, hospitality, hotel technology, LatAm"
            ),
            "canonical_url": canonical_url,
            "robots_meta": "index, follow",
            "og_title": og_title,
            "og_description": og_description,
            "og_image_alt": og_image_alt,
            "og_locale": og_locale,
            "og_locale_alternate": og_locale_alternate,
            "twitter_title": og_title,
            "twitter_description": og_description,
            "html_lang": html_lang,
            "hreflang_alternates": hreflang_alternates,
            "structured_data": structured,
        },
    )


@router.get("/consultoria", response_class=HTMLResponse)
def consulting_es_page(request: Request):
    return render_consulting_landing(request, lang="es", page="consultoria")


@router.get("/consulting", response_class=HTMLResponse)
def consulting_en_page(request: Request):
    return render_consulting_landing(request, lang="en", page="consulting")


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
