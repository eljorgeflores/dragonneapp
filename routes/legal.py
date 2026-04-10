"""Páginas públicas: Términos y condiciones, Política de privacidad."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from config import LEGAL_DOCS_VERSION, url_path
from seo_helpers import absolute_url
from templating import templates

router = APIRouter(tags=["legal"])


def _legal_seo(path: str, title: str, description: str) -> dict:
    canonical = absolute_url(path)
    return {
        "meta_title": title,
        "meta_description": description,
        "canonical_url": canonical,
        "robots_meta": "index, follow",
        "og_title": title,
        "og_description": description,
        "twitter_title": title,
        "twitter_description": description,
        "html_lang": "es-MX",
    }


@router.get("/terminos", response_class=HTMLResponse)
def terms_page(request: Request):
    """Términos y condiciones de uso de Pullso."""
    seo = _legal_seo(
        "/terminos",
        "Términos y condiciones — Pullso by Dragonné",
        "Condiciones de uso del servicio Pullso: planes, uso aceptable, suspensión por mal uso y limitaciones.",
    )
    return templates.TemplateResponse(
        "legal_terms.html",
        {
            "request": request,
            "legal_docs_version": LEGAL_DOCS_VERSION,
            "terms_url": url_path("/terminos"),
            "privacy_url": url_path("/privacidad"),
            **seo,
        },
    )


@router.get("/privacidad", response_class=HTMLResponse)
def privacy_page(request: Request):
    """Política de privacidad."""
    seo = _legal_seo(
        "/privacidad",
        "Política de privacidad — Pullso by Dragonné",
        "Cómo tratamos tus datos personales al usar Pullso: finalidades, proveedores, derechos y conservación.",
    )
    return templates.TemplateResponse(
        "legal_privacy.html",
        {
            "request": request,
            "legal_docs_version": LEGAL_DOCS_VERSION,
            "terms_url": url_path("/terminos"),
            "privacy_url": url_path("/privacidad"),
            **seo,
        },
    )
