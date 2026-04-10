"""Rutas de marca para el PDF/HTML. Sustituye los PNG por los oficiales cuando los tengas."""
from __future__ import annotations

from pathlib import Path

from config import BASE_DIR

# Directorio dedicado: coloca aquí logo claro (portada oscura) y logo oscuro (interiores claros).
REVENUE_BRAND_DIR = BASE_DIR / "static" / "branding" / "revenue-report"

# Nombres esperados (opcional). Si no existen, se usan fallbacks.
LOGO_FOR_DARK_BG = REVENUE_BRAND_DIR / "logo-for-dark-bg.png"  # wordmark claro sobre portada oscura
LOGO_FOR_LIGHT_BG = REVENUE_BRAND_DIR / "logo-for-light-bg.png"  # wordmark oscuro en headers
ISOTIPO = REVENUE_BRAND_DIR / "isotipo.png"

# Fallback: wordmark actual del sitio (oscuro sobre claro aproximado)
_FALLBACK_WORDMARK = BASE_DIR / "static" / "branding" / "pullso-logo.png"


def resolve_logo_cover() -> Path:
    """Logo visible sobre fondo oscuro (típicamente claro/blanco)."""
    if LOGO_FOR_DARK_BG.exists():
        return LOGO_FOR_DARK_BG
    return _FALLBACK_WORDMARK if _FALLBACK_WORDMARK.exists() else REVENUE_BRAND_DIR


def resolve_logo_interior() -> Path:
    """Logo en header de páginas claras (típicamente oscuro)."""
    if LOGO_FOR_LIGHT_BG.exists():
        return LOGO_FOR_LIGHT_BG
    return _FALLBACK_WORDMARK if _FALLBACK_WORDMARK.exists() else REVENUE_BRAND_DIR


def file_uri(path: Path) -> str:
    """URI file:// para img src en HTML→PDF."""
    return path.resolve().as_uri()
