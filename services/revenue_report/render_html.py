"""JSON → HTML (Jinja2)."""
from __future__ import annotations

from typing import Any, Dict

from templating import templates

from .brand_assets import file_uri, resolve_logo_cover, resolve_logo_interior
from .display_util import derive_closing_strategic_implication, derive_executive_highlights
from .section_visibility import compute_revenue_report_sections, filter_executive_highlights


def render_revenue_report_html(report: Dict[str, Any], extra: Dict[str, Any] | None = None) -> str:
    extra = extra or {}
    logo_cover = resolve_logo_cover()
    logo_interior = resolve_logo_interior()
    lectura = extra.get("lectura_operativa")
    sections = compute_revenue_report_sections(report, lectura)
    raw_hl = derive_executive_highlights(report)
    highlights_f = filter_executive_highlights(raw_hl)
    sections["show_executive_highlights"] = bool(highlights_f)
    ctx = {
        "report": report,
        "logo_cover_src": file_uri(logo_cover) if logo_cover.is_file() else "",
        "logo_interior_src": file_uri(logo_interior) if logo_interior.is_file() else "",
        "closing_strategic_implication": derive_closing_strategic_implication(report),
        **extra,
        **sections,
        "executive_highlights": highlights_f,
    }
    return templates.get_template("revenue_report/dragonne_report.html").render(**ctx)
