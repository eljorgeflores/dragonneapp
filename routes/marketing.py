"""Marketing público: home, precios, SEO, mockup, docs HTML."""
from fastapi import APIRouter, Request, Response
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse

from auth_session import get_current_user
from config import APP_NAME, APP_URL
from debuglog import _debug_log
from marketing_context import marketing_page_context
from templating import templates

router = APIRouter(tags=["marketing"])


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    _debug_log("routes.marketing:home", "GET / entry", {"has_user": bool(get_current_user(request))}, "H2")
    user = get_current_user(request)
    if user:
        return RedirectResponse("/app", status_code=303)
    ctx = marketing_page_context()
    _debug_log("routes.marketing:home", "marketing context keys", {"keys": list(ctx.keys())}, "H2")
    return templates.TemplateResponse("marketing.html", {"request": request, **ctx})


@router.get("/marketing", response_class=HTMLResponse)
def marketing_alias(request: Request):
    return home(request)


@router.get("/precios", response_class=HTMLResponse)
def precios_page(request: Request):
    return templates.TemplateResponse("precios.html", {"request": request, **marketing_page_context()})


@router.get("/pricing", include_in_schema=False)
def pricing_redirect():
    """Slug inglés → página canónica en español /precios (ver docs/dragonapp_phase2.md)."""
    return RedirectResponse("/precios", status_code=302)


@router.get("/api", response_class=HTMLResponse)
def api_docs_page(request: Request):
    return templates.TemplateResponse("api_docs.html", {"request": request})


@router.get("/redoc", include_in_schema=False)
def redoc_docs(request: Request):
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{APP_NAME} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
    )


@router.get("/sitemap.xml", response_class=Response)
def sitemap_xml():
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


@router.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    base = (APP_URL or "http://127.0.0.1:8000").rstrip("/")
    return PlainTextResponse(
        "User-agent: *\nAllow: /\nDisallow: /app\nDisallow: /admin\nDisallow: /s/\nSitemap: " + base + "/sitemap.xml\n"
    )


@router.get("/mockup-analisis", response_class=HTMLResponse)
def mockup_analisis(request: Request):
    return templates.TemplateResponse("mockup_analisis.html", {"request": request})
