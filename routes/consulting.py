"""
Consultoría (fuera del núcleo DragonApp SaaS).

Rutas aisladas en este módulo para poder extraerlas a otro ASGI/despliegue sin tocar
el resto de routers. Ver docs/dragonapp_phase1.md y docs/dragonapp_phase2.md.
"""
import importlib
import importlib.util
import json
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

import config
from config import BASE_DIR, url_path
from db import db
from email_smtp import send_consulting_lead_email, send_hospitality_diagnosis_report
import hospitality_diagnosis_i18n as hd_i18n
from marketing_context import marketing_page_context
from seo_helpers import absolute_url, breadcrumb_list_node, graph_consulting_lang, graph_homepage, organization_node
from services.hospitality_diagnosis_compute import compute_hospitality_diagnosis
from templating import templates
from hospitality_problem_deck_i18n import get_hospitality_problem_deck_copy
from vertical_landings_content import VERTICAL_SLUGS, calendar_url, get_vertical_landing_copy

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
    contact_form_url = (
        url_path("/consultoria/contacto") if plang == "es" else url_path("/consulting/contact")
    )

    return templates.TemplateResponse(
        "consulting.html",
        {
            "request": request,
            "current_year": datetime.now(timezone.utc).year,
            "lang": lang,
            "t": t,
            "calendar_url": calendar_url(),
            "lead_form_action": lead_path,
            "contact_form_url": contact_form_url,
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


def render_consulting_contact_form(request: Request, lang: str = "es"):
    if lang not in ("es", "en"):
        lang = "es"
    trans = _consulting_translations()
    t = trans.get(lang) or trans.get("es")
    t = _DefaultT(t) if t else _DefaultT()
    plang = "en" if lang == "en" else "es"
    lead_path = url_path("/consultoria/lead")
    if plang == "en":
        meta_title = "Contact — DRAGONNÉ"
        meta_description = "Tell us what you need. We'll reply with a clear next step."
        canonical_url = absolute_url("/consulting/contact")
        html_lang = "en"
        og_locale = "en_US"
        og_locale_alternate = "es_MX"
    else:
        meta_title = "Contacto — DRAGONNÉ"
        meta_description = "Cuéntanos qué necesitas. Te respondemos con un siguiente paso claro."
        canonical_url = absolute_url("/consultoria/contacto")
        html_lang = "es-MX"
        og_locale = "es_MX"
        og_locale_alternate = "en_US"
    hreflang_alternates = [
        {"hreflang": "es", "href": absolute_url("/consultoria/contacto")},
        {"hreflang": "en", "href": absolute_url("/consulting/contact")},
        {"hreflang": "x-default", "href": absolute_url("/consultoria/contacto")},
    ]
    return templates.TemplateResponse(
        "consulting_form.html",
        {
            "request": request,
            "current_year": datetime.now(timezone.utc).year,
            "lang": lang,
            "t": t,
            "calendar_url": calendar_url(),
            "lead_form_action": lead_path,
            "meta_title": meta_title,
            "meta_description": meta_description,
            "canonical_url": canonical_url,
            "robots_meta": "index, follow",
            "og_title": meta_title,
            "og_description": meta_description,
            "og_locale": og_locale,
            "og_locale_alternate": og_locale_alternate,
            "twitter_title": meta_title,
            "twitter_description": meta_description,
            "html_lang": html_lang,
            "hreflang_alternates": hreflang_alternates,
        },
    )


def render_hospitality_problem_deck_page(request: Request, lang: str):
    """Landing tipo diapositivas (sales deck) para hospitalidad: /hoteles/ventas, /hotels/sales."""
    if lang not in ("es", "en"):
        lang = "es"
    d = get_hospitality_problem_deck_copy(lang)
    v = get_vertical_landing_copy("hospitality", lang)
    ctx = marketing_page_context()
    path_es = "/hoteles/ventas"
    path_en = "/hotels/sales"
    canonical_url = absolute_url(path_es if lang == "es" else path_en)
    consulting_home = url_path("/consultoria") if lang == "es" else url_path("/consulting")
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            organization_node(),
            breadcrumb_list_node(
                [
                    ("Inicio" if lang == "es" else "Home", absolute_url("/consultoria" if lang == "es" else "/consulting")),
                    (d["breadcrumb_name"], canonical_url),
                ]
            ),
        ],
    }
    hreflang_alternates = [
        {"hreflang": "es", "href": absolute_url(path_es)},
        {"hreflang": "en", "href": absolute_url(path_en)},
        {"hreflang": "x-default", "href": absolute_url(path_es)},
    ]
    html_lang = "es-MX" if lang == "es" else "en"
    og_locale = "es_MX" if lang == "es" else "en_US"
    og_locale_alternate = "en_US" if lang == "es" else "es_MX"
    trans = _consulting_translations()
    raw_t = trans.get(lang) or trans.get("es")
    t = _DefaultT(raw_t) if raw_t else _DefaultT()
    return templates.TemplateResponse(
        "hospitality_problem_deck.html",
        {
            "request": request,
            **ctx,
            "lang": lang,
            "t": t,
            "d": d,
            "v": v,
            "calendar_url": calendar_url(),
            "meta_title": d["meta_title"],
            "meta_description": d["meta_description"],
            "meta_keywords": (
                "Dragonné, hotel independiente, revenue, consultoría hospitalidad, tiempo, talento, competencia"
                if lang == "es"
                else "Dragonné, independent hotel, revenue, hospitality consulting, time, talent, competition"
            ),
            "canonical_url": canonical_url,
            "robots_meta": "index, follow",
            "og_title": d["meta_title"],
            "og_description": d["meta_description"],
            "og_locale": og_locale,
            "og_locale_alternate": og_locale_alternate,
            "twitter_title": d["meta_title"],
            "twitter_description": d["meta_description"],
            "html_lang": html_lang,
            "hreflang_alternates": hreflang_alternates,
            "structured_data": structured,
            "og_image_alt": f"DRAGONNÉ — {d['breadcrumb_name']}",
        },
    )


def render_vertical_landing_page(request: Request, lang: str, slug: str):
    """Landing de vertical DRAGONNÉ (consultoría): /consultoria/{slug} y /consulting/{slug}."""
    if lang not in ("es", "en"):
        lang = "es"
    if slug not in VERTICAL_SLUGS:
        raise HTTPException(status_code=404)
    v = get_vertical_landing_copy(slug, lang)
    trans = _consulting_translations()
    raw_t = trans.get(lang) or trans.get("es")
    t = _DefaultT(raw_t) if raw_t else _DefaultT()

    consulting_home = url_path("/consultoria") if lang == "es" else url_path("/consulting")
    if slug == "hospitality":
        path_es = "/hoteles"
        path_en = "/hotels"
    else:
        path_es = f"/consultoria/{slug}"
        path_en = f"/consulting/{slug}"
    canonical_url = absolute_url(path_es if lang == "es" else path_en)
    home_label = "Inicio" if lang == "es" else "Home"
    home_path = "/consultoria" if lang == "es" else "/consulting"
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            organization_node(),
            breadcrumb_list_node([
                (home_label, absolute_url(home_path)),
                (v["breadcrumb_name"], canonical_url),
            ]),
        ],
    }
    hreflang_alternates = [
        {"hreflang": "es", "href": absolute_url(path_es)},
        {"hreflang": "en", "href": absolute_url(path_en)},
        {"hreflang": "x-default", "href": absolute_url(path_es)},
    ]
    ctx = marketing_page_context()
    meta_title = v["meta_title"]
    meta_description = v["meta_description"]
    og_locale = "es_MX" if lang == "es" else "en_US"
    og_locale_alternate = "en_US" if lang == "es" else "es_MX"
    html_lang = "es-MX" if lang == "es" else "en"
    return templates.TemplateResponse(
        "vertical_landing.html",
        {
            "request": request,
            **ctx,
            "lang": lang,
            "t": t,
            "v": v,
            "vertical_slug": slug,
            "consulting_home": consulting_home,
            "lead_anchor": url_path("/consultoria/contacto") if lang == "es" else url_path("/consulting/contact"),
            "calendar_url": calendar_url(),
            "meta_title": meta_title,
            "meta_description": meta_description,
            "meta_keywords": (
                "Dragonné, consultoría estratégica, hospitalidad, startups, SMBs, medios, posicionamiento"
                if lang == "es"
                else "Dragonné, strategy consulting, hospitality, startups, SMBs, media positioning"
            ),
            "canonical_url": canonical_url,
            "robots_meta": "index, follow",
            "og_title": meta_title,
            "og_description": meta_description,
            "og_image_alt": f"{v['breadcrumb_name']} — DRAGONNÉ",
            "og_locale": og_locale,
            "og_locale_alternate": og_locale_alternate,
            "twitter_title": meta_title,
            "twitter_description": meta_description,
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


@router.get("/consultoria/contacto", response_class=HTMLResponse)
def consulting_contact_es(request: Request):
    return render_consulting_contact_form(request, lang="es")


@router.get("/consulting/contact", response_class=HTMLResponse)
def consulting_contact_en(request: Request):
    return render_consulting_contact_form(request, lang="en")


@router.get("/hoteles", response_class=HTMLResponse)
def consulting_vertical_hospitality_es(request: Request):
    return render_vertical_landing_page(request, "es", "hospitality")


@router.get("/hotels", response_class=HTMLResponse)
def consulting_vertical_hospitality_en(request: Request):
    return render_vertical_landing_page(request, "en", "hospitality")


@router.get("/hoteles/ventas", response_class=HTMLResponse)
def hospitality_sales_deck_es(request: Request):
    return render_hospitality_problem_deck_page(request, "es")


@router.get("/hotels/sales", response_class=HTMLResponse)
def hospitality_sales_deck_en(request: Request):
    return render_hospitality_problem_deck_page(request, "en")


def render_hospitality_diagnosis_page(request: Request, lang: str):
    """Landing de diagnóstico gratuito (lead gen): /hoteles/diagnostico, /hotels/diagnosis."""
    if lang not in ("es", "en"):
        lang = "es"
    v = get_vertical_landing_copy("hospitality", lang)
    # En local iteramos copy; recarga el módulo para reflejar cambios sin reiniciar uvicorn.
    if (config.APP_URL or "").startswith(("http://127.0.0.1", "http://localhost")):
        try:
            importlib.reload(hd_i18n)
        except Exception:
            pass
    d = hd_i18n.get_hospitality_diagnosis_page(lang)
    ctx = marketing_page_context()
    path_es = "/hoteles/diagnostico"
    path_en = "/hotels/diagnosis"
    canonical_url = absolute_url(path_es if lang == "es" else path_en)
    consulting_home = url_path("/consultoria") if lang == "es" else url_path("/consulting")
    hotels_home = url_path("/hoteles") if lang == "es" else url_path("/hotels")
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            organization_node(),
            breadcrumb_list_node(
                [
                    ("Inicio" if lang == "es" else "Home", absolute_url("/consultoria" if lang == "es" else "/consulting")),
                    (
                        v["breadcrumb_name"],
                        absolute_url("/hoteles" if lang == "es" else "/hotels"),
                    ),
                    (d["breadcrumb_name"], canonical_url),
                ]
            ),
        ],
    }
    hreflang_alternates = [
        {"hreflang": "es", "href": absolute_url(path_es)},
        {"hreflang": "en", "href": absolute_url(path_en)},
        {"hreflang": "x-default", "href": absolute_url(path_es)},
    ]
    html_lang = "es-MX" if lang == "es" else "en"
    og_locale = "es_MX" if lang == "es" else "en_US"
    og_locale_alternate = "en_US" if lang == "es" else "es_MX"
    trans = _consulting_translations()
    raw_t = trans.get(lang) or trans.get("es")
    t = _DefaultT(raw_t) if raw_t else _DefaultT()
    diag_submit_url = url_path("/hoteles/diagnostico" if lang == "es" else "/hotels/diagnosis")
    # Copy vive en Python (hospitality_diagnosis_i18n); sin recarga del proceso el HTML queda viejo.
    # Evita además que el navegador cachee esta página durante iteraciones de copy.
    _no_store = {"Cache-Control": "no-store, max-age=0", "Pragma": "no-cache"}
    return templates.TemplateResponse(
        "hospitality_diagnosis.html",
        {
            "request": request,
            **ctx,
            "lang": lang,
            "t": t,
            "v": v,
            "d": d,
            "calendar_url": calendar_url(),
            "consulting_home": consulting_home,
            "hotels_home": hotels_home,
            "consulting_nav_prefix": consulting_home,
            "consulting_header_lang_es": url_path(path_es),
            "consulting_header_lang_en": url_path(path_en),
            "diag_submit_url": diag_submit_url,
            "meta_title": d["meta_title"],
            "meta_description": d["meta_description"],
            "meta_keywords": (
                "diagnóstico posicionamiento online, hotel, OTAs, comisiones, revenue, canal directo, hospitalidad"
                if lang == "es"
                else "online positioning diagnosis, hotel, OTAs, commissions, revenue, direct channel, hospitality"
            ),
            "canonical_url": canonical_url,
            "robots_meta": "index, follow",
            "og_title": d["meta_title"],
            "og_description": d["meta_description"],
            "og_locale": og_locale,
            "og_locale_alternate": og_locale_alternate,
            "twitter_title": d["meta_title"],
            "twitter_description": d["meta_description"],
            "html_lang": html_lang,
            "hreflang_alternates": hreflang_alternates,
            "structured_data": structured,
            "og_image_alt": (
                "Diagnóstico inicial de posicionamiento online para hoteles"
                if lang == "es"
                else "Initial online positioning diagnosis for hotels"
            ),
        },
        headers=_no_store,
    )


@router.get("/hoteles/diagnostico", response_class=HTMLResponse)
def hospitality_diagnosis_landing_es(request: Request):
    return render_hospitality_diagnosis_page(request, "es")


@router.get("/hotels/diagnosis", response_class=HTMLResponse)
def hospitality_diagnosis_landing_en(request: Request):
    return render_hospitality_diagnosis_page(request, "en")


def _fmt_diag_money(n: float, lang: str) -> str:
    if lang == "es":
        return f"${n:,.0f} MXN /año (orientativo)"
    return f"${n:,.0f} MXN /yr (indicative)"


def _fmt_diag_growth_parts(n: float, g: float, lang: str) -> tuple[str, str]:
    pct = round(g * 1000) / 10
    if lang == "es":
        main = f"${n:,.0f} MXN /año en ventas adicionales estimadas"
        sub = f"(≈{pct}% sobre ingresos actuales)"
    else:
        main = f"${n:,.0f} MXN/yr in estimated additional sales"
        sub = f"(≈{pct}% of current revenue)"
    return main, sub


def _fmt_diag_growth(n: float, g: float, lang: str) -> str:
    main, sub = _fmt_diag_growth_parts(n, g, lang)
    return f"{main} {sub}"


def _fmt_diag_plain_mxn(n: float) -> str:
    return f"${n:,.0f} MXN"


def _hospitality_diag_formula_blocks(
    lang: str,
    rooms: float,
    adr: float,
    occ: float,
    pct_ota: float,
    nums: dict[str, float],
) -> tuple[str, str]:
    """
    Texto multilínea (sin HTML) para mostrar en el panel de éxito del diagnóstico:
    desglose alineado con compute_hospitality_diagnosis (rev_year, savings, growth).
    """
    rev = float(nums["rev_year_mxn"])
    comm = float(nums["avg_ota_commission"])
    sav = float(nums["savings_mxn"])
    gro = float(nums["growth_mxn"])
    g = float(nums["growth_rate"])
    gpct = round(g * 1000) / 10
    rooms_s = str(int(rooms)) if float(rooms) == int(rooms) else f"{rooms:g}"
    occ_s = str(int(occ)) if float(occ) == int(occ) else f"{occ:.1f}".rstrip("0").rstrip(".")
    adr_s = f"{adr:,.0f}"
    pct_s = str(int(pct_ota)) if float(pct_ota) == int(pct_ota) else f"{pct_ota:.1f}".rstrip("0").rstrip(".")
    mx = _fmt_diag_plain_mxn

    if lang == "es":
        savings = (
            "① Ingreso anual estimado\n"
            f"   {rooms_s} hab. × 365 noches × {occ_s}% ocupación × ${adr_s} ADR\n"
            f"   ≈ {mx(rev)} /año\n\n"
            "② Comisión OTAs orientativa (escenario prudente)\n"
            f"   ingreso × {pct_s}% (ventas por OTAs) × {comm:.1f}% (comisión media declarada) × ½\n"
            f"   → {mx(sav)} /año (orientativo)"
        )
        growth = (
            "③ Potencial de más ventas (mismo ingreso base, escenario de mejora)\n"
            f"   {mx(rev)} /año × {gpct:.1f}% (mix y directo optimizables)\n"
            f"   → {mx(gro)} /año (orientativo)"
        )
    else:
        savings = (
            "① Estimated annual revenue\n"
            f"   {rooms_s} rooms × 365 nights × {occ_s}% occupancy × ${adr_s} ADR\n"
            f"   ≈ {mx(rev)} /yr\n\n"
            "② Indicative OTA commission (prudent scenario)\n"
            f"   revenue × {pct_s}% (OTA sales) × {comm:.1f}% (declared average commission) × ½\n"
            f"   → {mx(sav)} /yr (indicative)"
        )
        growth = (
            "③ Potential additional sales (same revenue base, upside scenario)\n"
            f"   {mx(rev)} /yr × {gpct:.1f}% (improvable mix and direct)\n"
            f"   → {mx(gro)} /yr (indicative)"
        )
    return savings, growth


_ALLOWED_HOTEL_CATEGORY = frozenset(
    {
        "boutique",
        "business",
        "city",
        "budget",
        "all_inclusive",
        "luxury",
        "beach",
    }
)


def _hotel_category_display(lang: str, slug: str) -> str:
    if not slug or slug not in _ALLOWED_HOTEL_CATEGORY:
        return ""
    d = hd_i18n.get_hospitality_diagnosis_page(lang if lang in ("es", "en") else "es")
    labels = d.get("hotel_category_labels") or {}
    return str(labels.get(slug) or "").strip()


def _hospitality_diag_email_context_line(lang: str, location: str, cat_label: str) -> str:
    loc = (location or "").strip()
    cat = (cat_label or "").strip()
    if not loc and not cat:
        return ""
    if lang == "es":
        if cat and loc:
            return f"Contexto que compartiste: {cat} · {loc}."
        if cat:
            return f"Contexto que compartiste: {cat}."
        return f"Ubicación declarada: {loc}."
    if cat and loc:
        return f"Context you shared: {cat} · {loc}."
    if cat:
        return f"Context you shared: {cat}."
    return f"Location provided: {loc}."


async def _hospitality_diagnosis_submit(request: Request, lang: str) -> JSONResponse:
    if lang not in ("es", "en"):
        lang = "es"
    try:
        body: dict[str, Any] = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "invalid_json"}, status_code=400)
    if (body.get("website") or body.get("url") or "").strip():
        return JSONResponse({"ok": True, "ignored": True})
    contact_name = (body.get("contact_name") or "").strip()
    contact_email = (body.get("contact_email") or "").strip().lower()
    contact_phone = (body.get("contact_phone") or "").strip()[:120]
    hotel = (body.get("hotel") or "").strip()
    hotel_location = (body.get("hotel_location") or "").strip()[:160]
    cat_slug = (body.get("hotel_category") or "").strip().lower()[:40]
    if cat_slug not in _ALLOWED_HOTEL_CATEGORY:
        cat_slug = ""
    cat_display = _hotel_category_display(lang, cat_slug)
    if not contact_name or not contact_email or not hotel:
        return JSONResponse({"ok": False, "error": "missing_fields"}, status_code=400)
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", contact_email):
        return JSONResponse({"ok": False, "error": "invalid_email"}, status_code=400)
    phone_digits = re.sub(r"\D", "", contact_phone)
    if len(phone_digits) < 10:
        return JSONResponse({"ok": False, "error": "invalid_phone"}, status_code=400)
    try:
        rooms = float(body.get("rooms"))
        adr = float(body.get("adr"))
        pct_ota = float(body.get("pct_ota"))
    except (TypeError, ValueError):
        return JSONResponse({"ok": False, "error": "invalid_numbers"}, status_code=400)
    if rooms < 1 or adr <= 0 or pct_ota < 0:
        return JSONResponse({"ok": False, "error": "invalid_numbers"}, status_code=400)
    occ_raw = body.get("occ")
    if occ_raw in (None, ""):
        return JSONResponse({"ok": False, "error": "invalid_numbers"}, status_code=400)
    try:
        occ = float(occ_raw)
    except (TypeError, ValueError):
        return JSONResponse({"ok": False, "error": "invalid_numbers"}, status_code=400)
    if occ < 1 or occ > 100:
        return JSONResponse({"ok": False, "error": "invalid_numbers"}, status_code=400)
    numotas_raw = body.get("numotas")
    try:
        numotas = int(float(numotas_raw)) if numotas_raw not in (None, "") else 2
    except (TypeError, ValueError):
        numotas = 2
    otas = body.get("otas")
    if not isinstance(otas, list):
        otas = []
    clean_otas: list[dict[str, Any]] = []
    for row in otas[:8]:
        if not isinstance(row, dict):
            continue
        clean_otas.append(
            {
                "name": str(row.get("name") or "")[:80],
                "comm": row.get("comm"),
            }
        )
    payload = {
        "rooms": rooms,
        "adr": adr,
        "occ": occ,
        "pct_ota": pct_ota,
        "pct_direct": body.get("pct_direct"),
        "otas": clean_otas,
        "hotel": hotel[:200],
        "hotel_location": hotel_location[:160],
        "hotel_category": cat_slug,
        "numotas": numotas,
        "has_web": (body.get("has_web") or "unsure")[:12],
        "web_be": (body.get("web_be") or "unsure")[:12],
        "pay": (body.get("pay") or "unsure")[:12],
        "pms": str(body.get("pms") or "")[:120],
        "cm": str(body.get("cm") or "")[:120],
    }
    try:
        nums = compute_hospitality_diagnosis(payload)
    except Exception:
        return JSONResponse({"ok": False, "error": "compute"}, status_code=400)
    v = get_vertical_landing_copy("hospitality", lang)
    savings_line = _fmt_diag_money(nums["savings_mxn"], lang)
    growth_main, growth_sub = _fmt_diag_growth_parts(
        nums["growth_mxn"], nums["growth_rate"], lang
    )
    growth_line = f"{growth_main} {growth_sub}"
    savings_formula, growth_formula = _hospitality_diag_formula_blocks(
        lang, rooms, adr, occ, pct_ota, nums
    )
    diag_ui = hd_i18n.get_hospitality_diagnosis_page(lang)
    result_narrative = str(diag_ui.get("res_story_intro") or "")
    facts_rows: list[tuple[str, str]] = [
        (v["diag_l_hotel"], hotel[:120]),
    ]
    if hotel_location:
        facts_rows.append(
            (
                str(diag_ui.get("diag_facts_location") or ""),
                hotel_location[:160],
            )
        )
    if cat_display:
        facts_rows.append(
            (
                str(diag_ui.get("diag_facts_category") or ""),
                cat_display,
            )
        )
    facts_rows.extend(
        [
            (v["diag_l_rooms"], str(int(rooms)) if rooms == int(rooms) else str(rooms)),
            (v["diag_l_adr"], str(adr)),
            (v["diag_l_occ"], str(occ)),
            ("% OTAs" if lang == "en" else "% ventas OTAs", str(pct_ota)),
        ]
    )
    if contact_phone:
        facts_rows.append(
            ("Teléfono" if lang == "es" else "Phone", contact_phone),
        )
    disclaimer = v["diag_disclaimer"]
    context_line = _hospitality_diag_email_context_line(lang, hotel_location, cat_display)
    meet_url = calendar_url()
    now = datetime.now(timezone.utc).isoformat()
    store = {
        **payload,
        "contact_name": contact_name[:200],
        "contact_email": contact_email,
        "contact_phone": contact_phone,
        "lang": lang,
    }
    with db() as conn:
        conn.execute(
            """INSERT INTO hospitality_diag_submissions (
                created_at, lang, contact_name, contact_email, contact_phone,
                hotel_name, savings_mxn, growth_mxn, growth_rate, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                now,
                lang,
                contact_name[:200],
                contact_email,
                contact_phone or None,
                hotel[:200],
                nums["savings_mxn"],
                nums["growth_mxn"],
                nums["growth_rate"],
                json.dumps(store, ensure_ascii=False)[:12000],
            ),
        )
    sent = send_hospitality_diagnosis_report(
        to_email=contact_email,
        contact_name=contact_name[:200],
        lang=lang,
        hotel_name=hotel[:200],
        savings_line=savings_line,
        growth_line=growth_line,
        facts_rows=facts_rows,
        disclaimer=disclaimer,
        result_narrative=result_narrative,
        context_line=context_line,
        meeting_url=meet_url,
    )
    if not sent:
        return JSONResponse(
            {
                "ok": False,
                "error": "email_delivery",
                "saved": True,
                "savings_line": savings_line,
                "growth_line": growth_line,
                "growth_main": growth_main,
                "growth_sub": growth_sub,
                "savings_formula": savings_formula,
                "growth_formula": growth_formula,
                "hotel_name": hotel.strip()[:200],
            },
            status_code=503,
        )
    return JSONResponse(
        {
            "ok": True,
            "savings_line": savings_line,
            "growth_line": growth_line,
            "growth_main": growth_main,
            "growth_sub": growth_sub,
            "savings_formula": savings_formula,
            "growth_formula": growth_formula,
            "hotel_name": hotel.strip()[:200],
        }
    )


@router.post("/hoteles/diagnostico")
async def hospitality_diagnosis_submit_es(request: Request):
    return await _hospitality_diagnosis_submit(request, "es")


@router.post("/hotels/diagnosis")
async def hospitality_diagnosis_submit_en(request: Request):
    return await _hospitality_diagnosis_submit(request, "en")


@router.get("/hoteles/reto")
def hospitality_sales_deck_legacy_es():
    return RedirectResponse(url_path("/hoteles/ventas"), status_code=301)


@router.get("/hotels/challenge")
def hospitality_sales_deck_legacy_en():
    return RedirectResponse(url_path("/hotels/sales"), status_code=301)


@router.get("/consultoria/hospitality")
def consulting_vertical_hospitality_legacy_es():
    return RedirectResponse(url_path("/hoteles"), status_code=301)


@router.get("/consulting/hospitality")
def consulting_vertical_hospitality_legacy_en():
    return RedirectResponse(url_path("/hotels"), status_code=301)


@router.get("/consultoria/{vertical_slug}", response_class=HTMLResponse)
def consulting_vertical_es(request: Request, vertical_slug: str):
    return render_vertical_landing_page(request, "es", vertical_slug)


@router.get("/consulting/{vertical_slug}", response_class=HTMLResponse)
def consulting_vertical_en(request: Request, vertical_slug: str):
    return render_vertical_landing_page(request, "en", vertical_slug)


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
