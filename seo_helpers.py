"""
Helpers SEO: URLs absolutas, noindex reutilizable, JSON-LD (@graph).
Patrón: en cada ruta pública pasar meta_title, meta_description, canonical_url, robots_meta;
opcional og_image, hreflang_alternates, structured_data (dict con @context + @graph).
"""
from __future__ import annotations

from typing import Any

from config import APP_URL, url_path

DEFAULT_OG_IMAGE_PATH = "/static/branding/og-social-preview.png"
BRAND_LOGO_PATH = "/static/branding/dragonne-wordmark.png"
BRAND_LEGAL_NAME = "DRAGONNÉ"
CONTACT_EMAIL_PUBLIC = "jorge@dragonne.co"


def absolute_url(route: str) -> str:
    base = (APP_URL or "").strip().rstrip("/")
    r = (route or "").strip()
    if not r.startswith("/"):
        r = "/" + r
    return f"{base}{url_path(r)}"


def default_og_image_absolute() -> str:
    return absolute_url(DEFAULT_OG_IMAGE_PATH)


def brand_logo_absolute() -> str:
    return absolute_url(BRAND_LOGO_PATH)


def noindex_page_seo(path: str, title: str, description: str) -> dict[str, Any]:
    u = absolute_url(path)
    return {
        "meta_title": title,
        "meta_description": description,
        "canonical_url": u,
        "robots_meta": "noindex, nofollow",
        "og_title": title,
        "og_description": description,
        "twitter_title": title,
        "twitter_description": description,
    }


def organization_node() -> dict[str, Any]:
    return {
        "@type": "Organization",
        "@id": absolute_url("/") + "#organization",
        "name": BRAND_LEGAL_NAME,
        "legalName": BRAND_LEGAL_NAME,
        "url": absolute_url("/"),
        "logo": brand_logo_absolute(),
        "email": CONTACT_EMAIL_PUBLIC,
        "description": (
            "DRAGONNÉ acompaña equipos en crecimiento (startups, SMBs, hospitalidad) y ofrece Pullso, "
            "software que analiza reportes hoteleros para lectura comercial accionable."
        ),
    }


def website_node() -> dict[str, Any]:
    return {
        "@type": "WebSite",
        "@id": absolute_url("/") + "#website",
        "url": absolute_url("/"),
        "name": BRAND_LEGAL_NAME,
        "publisher": {"@id": organization_node()["@id"]},
        "inLanguage": ["es-MX", "en"],
    }


def professional_service_node(*, lang: str, page_url: str) -> dict[str, Any]:
    en = lang == "en"
    return {
        "@type": "ProfessionalService",
        "@id": page_url + "#professional-service",
        "name": BRAND_LEGAL_NAME + (" — Consulting" if en else " — Consultoría"),
        "url": page_url,
        "image": default_og_image_absolute(),
        "provider": {"@id": organization_node()["@id"]},
        "areaServed": ["México", "Latin America", "LATAM"],
        "description": (
            "Consultoría: talento, operaciones, tecnología y rentabilidad con entregables claros."
            if not en
            else "Consulting: talent, operations, technology and profitability with clear deliverables."
        ),
    }


def software_application_mockup_node() -> dict[str, Any]:
    return {
        "@type": "SoftwareApplication",
        "@id": absolute_url("/mockup-analisis") + "#software",
        "name": "Pullso by DRAGONNÉ",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "url": absolute_url("/mockup-analisis"),
        "image": default_og_image_absolute(),
        "publisher": {"@id": organization_node()["@id"]},
        "description": (
            "Demostración del panel: resumen ejecutivo y métricas a partir de reportes hoteleros de ejemplo."
        ),
    }


def graph_pullso_vertical(*, canonical: str) -> list[dict[str, Any]]:
    return [
        organization_node(),
        {
            "@type": "SoftwareApplication",
            "@id": canonical + "#pullso",
            "name": "Pullso by DRAGONNÉ",
            "url": canonical,
            "applicationCategory": "BusinessApplication",
            "operatingSystem": "Web",
            "publisher": {"@id": organization_node()["@id"]},
            "description": (
                "Pullso convierte exports de PMS y channel manager en lectura comercial con KPIs y recomendaciones."
            ),
            "image": default_og_image_absolute(),
        },
    ]


def breadcrumb_list_node(items: list[tuple[str, str]]) -> dict[str, Any]:
    elements = []
    for i, (name, u) in enumerate(items, start=1):
        elements.append({"@type": "ListItem", "position": i, "name": name, "item": u})
    return {"@type": "BreadcrumbList", "itemListElement": elements}


def graph_homepage() -> list[dict[str, Any]]:
    return [organization_node(), website_node()]


def graph_consulting_lang(*, lang: str, canonical: str) -> list[dict[str, Any]]:
    return [
        organization_node(),
        professional_service_node(lang=lang, page_url=canonical),
    ]
