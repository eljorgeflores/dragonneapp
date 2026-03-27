"""Marketing público: home, precios, SEO, mockup, docs HTML."""
from fastapi import APIRouter, Query, Request, Response
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse

from auth_session import get_current_user
from config import APP_NAME, APP_URL, url_path
from debuglog import _debug_log
from marketing_context import marketing_page_context
from routes.consulting import render_consulting_landing
from seo_helpers import (
    BRAND_LEGAL_NAME,
    CONTACT_EMAIL_PUBLIC,
    absolute_url,
    breadcrumb_list_node,
    graph_pullso_vertical,
    noindex_page_seo,
    organization_node,
    software_application_mockup_node,
)
from templating import templates

router = APIRouter(tags=["marketing"])


def _sitemap_entries():
    return [
        ("/", "weekly", "1.0"),
        ("/consultoria", "weekly", "0.95"),
        ("/consulting", "weekly", "0.95"),
        ("/precios", "weekly", "0.85"),
        ("/mockup-analisis", "monthly", "0.75"),
        ("/verticals/hospitality", "weekly", "0.85"),
        ("/nosotros", "monthly", "0.6"),
        ("/faq", "monthly", "0.65"),
        ("/servicios", "monthly", "0.65"),
    ]


@router.get("/", response_class=HTMLResponse)
def home(request: Request, lang: str = Query("es", alias="lang")):
    _debug_log("routes.marketing:home", "GET / entry", {"has_user": bool(get_current_user(request))}, "H2")
    user = get_current_user(request)
    if user:
        return RedirectResponse(url_path("/app"), status_code=303)
    if lang not in ("es", "en"):
        lang = "es"
    if lang == "en":
        return RedirectResponse(url_path("/consulting"), status_code=302)
    _debug_log("routes.marketing:home", "homepage=consulting", {"lang": "es"}, "H2")
    return render_consulting_landing(request, lang="es", page="home")


@router.get("/verticals/hospitality", response_class=HTMLResponse)
def verticals_hospitality(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url_path("/app"), status_code=303)
    ctx = marketing_page_context()
    canonical = absolute_url("/verticals/hospitality")
    structured = {
        "@context": "https://schema.org",
        "@graph": graph_pullso_vertical(canonical=canonical)
        + [
            breadcrumb_list_node([
                ("Inicio", absolute_url("/consultoria")),
                ("Pullso · Hospitalidad", canonical),
            ]),
        ],
    }
    seo = {
        "meta_title": "Pullso by DRAGONNÉ — Inteligencia de revenue para hoteles",
        "meta_description": (
            "Pullso (DRAGONNÉ) lee reportes de tu PMS o channel manager y entrega lectura comercial: KPIs, riesgos "
            "y oportunidades de canal — para equipos de revenue y dirección hotelera."
        ),
        "meta_keywords": "Pullso, Dragonné, revenue management, hotel, PMS, channel manager, reportes hoteleros",
        "canonical_url": canonical,
        "robots_meta": "index, follow",
        "og_title": "Pullso by DRAGONNÉ — Revenue intelligence para hospitalidad",
        "og_description": (
            "Convierte exports hoteleros en decisiones: mix de canales, precio y señales operativas, en español."
        ),
        "og_locale": "es_MX",
        "og_locale_alternate": "en_US",
        "twitter_title": "Pullso by DRAGONNÉ — Inteligencia hotelera",
        "twitter_description": "Análisis accionable sobre reportes de PMS y channel manager.",
        "html_lang": "es-MX",
        "structured_data": structured,
    }
    return templates.TemplateResponse("marketing.html", {"request": request, **ctx, **seo})


@router.get("/marketing", include_in_schema=False)
def marketing_alias(request: Request):
    return RedirectResponse(url_path("/verticals/hospitality"), status_code=302)


@router.get("/precios", response_class=HTMLResponse)
def precios_page(request: Request):
    canonical = absolute_url("/precios")
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            organization_node(),
            breadcrumb_list_node([
                ("Inicio", absolute_url("/consultoria")),
                ("Precios Pullso", canonical),
            ]),
        ],
    }
    seo = {
        "meta_title": "Precios — Pullso by DRAGONNÉ",
        "meta_description": (
            "Planes Pullso: prueba gratuita con límites y planes Pro / Pro+ cuando necesites más períodos y archivos por análisis."
        ),
        "meta_keywords": "Pullso, Dragonné, precios, planes Pro, revenue hotelero",
        "canonical_url": canonical,
        "robots_meta": "index, follow",
        "og_title": "Precios Pullso — planes para equipos hoteleros",
        "og_description": "Gratis para empezar; escala a Pro o Pro+ sin cambiar cómo exportas reportes.",
        "og_locale": "es_MX",
        "twitter_title": "Precios — Pullso by DRAGONNÉ",
        "twitter_description": "Gratis, Pro y Pro+ alineados a tu operación.",
        "html_lang": "es-MX",
        "structured_data": structured,
    }
    return templates.TemplateResponse("precios.html", {"request": request, **marketing_page_context(), **seo})


@router.get("/pricing", include_in_schema=False)
def pricing_redirect():
    return RedirectResponse(url_path("/precios"), status_code=302)


@router.get("/api", response_class=HTMLResponse)
def api_docs_page(request: Request):
    desc = "Documentación orientativa de la API DRAGONNÉ para integraciones con autenticación por clave."
    ctx = noindex_page_seo("/api", "Documentación API — DRAGONNÉ", desc)
    ctx["meta_keywords"] = "DRAGONNÉ, API, hotel, análisis"
    return templates.TemplateResponse("api_docs.html", {"request": request, **ctx})


@router.get("/redoc", include_in_schema=False)
def redoc_docs(request: Request):
    return get_redoc_html(
        openapi_url=url_path("/openapi.json"),
        title=f"{APP_NAME} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
    )


@router.get("/sitemap.xml", response_class=Response)
def sitemap_xml():
    base = (APP_URL or "http://127.0.0.1:8000").rstrip("/")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for path, changefreq, priority in _sitemap_entries():
        loc = base + url_path(path)
        xml += f"  <url><loc>{loc}</loc><changefreq>{changefreq}</changefreq><priority>{priority}</priority></url>\n"
    xml += "</urlset>"
    return Response(content=xml, media_type="application/xml")


@router.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    base = (APP_URL or "http://127.0.0.1:8000").rstrip("/")
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        "Disallow: /app",
        "Disallow: /admin",
        "Disallow: /login",
        "Disallow: /signup",
        "Disallow: /onboarding",
        "Disallow: /forgot-password",
        "Disallow: /reset-password",
        "Disallow: /api",
        "Disallow: /docs",
        "Disallow: /openapi.json",
        "Disallow: /redoc",
        "Disallow: /analyze",
        "Disallow: /analysis/",
        "Disallow: /billing/",
        "Disallow: /health",
        "Disallow: /revenue-report/",
        "Disallow: /s/",
        "",
        f"Sitemap: {base}{url_path('/sitemap.xml')}",
        "",
    ]
    return PlainTextResponse("\n".join(lines))


@router.get("/llms.txt", response_class=PlainTextResponse)
def llms_txt():
    u = (APP_URL or "").strip().rstrip("/") or "https://dragonne.co"
    body = f"""# {BRAND_LEGAL_NAME}

Site: {u}
Contact: {CONTACT_EMAIL_PUBLIC}

## Qué es
DRAGONNÉ es consultoría estratégica (startups, SMBs, hospitalidad) y el producto Pullso: software que analiza reportes hoteleros exportados desde PMS o channel managers.

## Páginas principales
- {u}{url_path("/")} — inicio (español)
- {u}{url_path("/consultoria")} — consultoría (ES)
- {u}{url_path("/consulting")} — consulting (EN)
- {u}{url_path("/verticals/hospitality")} — Pullso hospitalidad
- {u}{url_path("/precios")} — planes
- {u}{url_path("/mockup-analisis")} — demo del panel
- {u}{url_path("/nosotros")}, {u}{url_path("/faq")}, {u}{url_path("/servicios")}

## Uso para modelos
Prioriza URLs públicas anteriores. No entren ni resuman /app, /admin, /s/ ni flujos de login. Precios y límites: {u}{url_path("/precios")}.
"""
    return PlainTextResponse(body.strip() + "\n")


@router.get("/mockup-analisis", response_class=HTMLResponse)
def mockup_analisis(request: Request):
    canonical = absolute_url("/mockup-analisis")
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            organization_node(),
            software_application_mockup_node(),
            breadcrumb_list_node([
                ("Inicio", absolute_url("/consultoria")),
                ("Demo de análisis", canonical),
            ]),
        ],
    }
    seo = {
        "meta_title": "Demo del analizador Pullso — DRAGONNÉ",
        "meta_description": (
            "Vista de ejemplo del panel Pullso: KPIs y lectura comercial; crea cuenta para analizar tus propios reportes."
        ),
        "meta_keywords": "Pullso, Dragonné, demo análisis hotelero",
        "canonical_url": canonical,
        "robots_meta": "index, follow",
        "og_title": "Demo Pullso — lectura comercial de ejemplo",
        "og_description": "Resultado de ejemplo; regístrate para usar tus archivos.",
        "og_locale": "es_MX",
        "twitter_title": "Demo Pullso — DRAGONNÉ",
        "twitter_description": "Mockup del tablero de análisis hotelero.",
        "html_lang": "es-MX",
        "structured_data": structured,
    }
    return templates.TemplateResponse("mockup_analisis.html", {"request": request, **seo})


@router.get("/nosotros", response_class=HTMLResponse)
def nosotros_page(request: Request):
    canonical = absolute_url("/nosotros")
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            organization_node(),
            breadcrumb_list_node([("Inicio", absolute_url("/consultoria")), ("Nosotros", canonical)]),
        ],
    }
    seo = {
        "meta_title": "Nosotros — DRAGONNÉ",
        "meta_description": (
            "DRAGONNÉ combina consultoría y producto Pullso para equipos que necesitan decisiones sobre datos hoteleros."
        ),
        "canonical_url": canonical,
        "robots_meta": "index, follow",
        "og_title": "Nosotros — DRAGONNÉ",
        "og_description": "Consultoría y tecnología para hospitalidad y empresas en crecimiento.",
        "html_lang": "es-MX",
        "structured_data": structured,
    }
    return templates.TemplateResponse(
        "public_stub.html",
        {
            "request": request,
            "stub_h1": "Nosotros",
            "stub_lead": (
                "DRAGONNÉ une consultoría de dirección con Pullso, para que la lectura comercial sobre operaciones "
                "hoteleras sea rigurosa, compartible y accionable."
            ),
            **seo,
        },
    )


@router.get("/about", include_in_schema=False)
def about_redirect():
    return RedirectResponse(url_path("/nosotros"), status_code=302)


@router.get("/faq", response_class=HTMLResponse)
def faq_page(request: Request):
    canonical = absolute_url("/faq")
    faq_entities = [
        {
            "@type": "Question",
            "name": "¿Qué es Pullso dentro de DRAGONNÉ?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": (
                    "Pullso es el producto SaaS de DRAGONNÉ para analizar exports de PMS/channel y obtener un informe "
                    "ejecutivo con KPIs y recomendaciones para equipos hoteleros."
                ),
            },
        },
        {
            "@type": "Question",
            "name": "¿DRAGONNÉ solo trabaja con hoteles?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "La consultoría también cubre startups, SMBs y medios; Pullso está focalizado en hotelería.",
            },
        },
        {
            "@type": "Question",
            "name": "¿Dónde están los precios?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": f"En {absolute_url('/precios')}.",
            },
        },
    ]
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            organization_node(),
            {"@type": "FAQPage", "mainEntity": faq_entities},
            breadcrumb_list_node([("Inicio", absolute_url("/consultoria")), ("FAQ", canonical)]),
        ],
    }
    seo = {
        "meta_title": "Preguntas frecuentes — DRAGONNÉ y Pullso",
        "meta_description": "Respuestas breves sobre Pullso, consultoría DRAGONNÉ y precios.",
        "canonical_url": canonical,
        "robots_meta": "index, follow",
        "og_title": "FAQ — DRAGONNÉ & Pullso",
        "og_description": "Preguntas frecuentes sobre producto y consultoría.",
        "html_lang": "es-MX",
        "structured_data": structured,
    }
    return templates.TemplateResponse("public_faq.html", {"request": request, **seo})


@router.get("/servicios", response_class=HTMLResponse)
def servicios_page(request: Request):
    canonical = absolute_url("/servicios")
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            organization_node(),
            breadcrumb_list_node([("Inicio", absolute_url("/consultoria")), ("Servicios", canonical)]),
        ],
    }
    seo = {
        "meta_title": "Servicios — DRAGONNÉ y Pullso",
        "meta_description": (
            "Consultoría en talento y operaciones; Pullso para leer reportes hoteleros con rigor comercial."
        ),
        "canonical_url": canonical,
        "robots_meta": "index, follow",
        "og_title": "Servicios DRAGONNÉ",
        "og_description": "Consultoría estratégica y software Pullso para revenue hotelero.",
        "html_lang": "es-MX",
        "structured_data": structured,
    }
    return templates.TemplateResponse("public_servicios.html", {"request": request, **seo})


@router.get("/demo/pullso-whatsapp", response_class=HTMLResponse, include_in_schema=False)
def pullso_whatsapp_demo(request: Request):
    """Landing demo aislada (no sustituye home ni /verticals/hospitality). Sin entrada en sitemap."""
    ctx = marketing_page_context()
    return templates.TemplateResponse(
        "pullso_whatsapp_demo.html",
        {"request": request, **ctx},
    )


@router.get("/pullso-demo", include_in_schema=False)
def pullso_demo_short_alias():
    return RedirectResponse(url_path("/demo/pullso-whatsapp"), status_code=302)
