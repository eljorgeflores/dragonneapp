"""JSON → HTML (Jinja2)."""
from __future__ import annotations

from typing import Any, Dict

from templating import templates

from .brand_assets import file_uri, resolve_logo_cover, resolve_logo_interior


def render_revenue_report_html(report: Dict[str, Any], extra: Dict[str, Any] | None = None) -> str:
    extra = extra or {}
    logo_cover = resolve_logo_cover()
    logo_interior = resolve_logo_interior()
    ctx = {
        "report": report,
        "logo_cover_src": file_uri(logo_cover) if logo_cover.is_file() else "",
        "logo_interior_src": file_uri(logo_interior) if logo_interior.is_file() else "",
        **extra,
    }
    return templates.get_template("revenue_report/dragonne_report.html").render(**ctx)
