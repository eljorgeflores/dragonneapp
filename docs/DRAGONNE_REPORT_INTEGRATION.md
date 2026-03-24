# Dragonné Revenue Report — integración en este repo

El kit original vive en este archivo como referencia de producto. La implementación concreta está en:

| Capa | Ubicación |
|------|-----------|
| Contrato JSON | `schemas/revenue_report.schema.json` |
| Prompt analista | `services/revenue_report/prompt.py` |
| Validación + esquema OpenAI strict | `services/revenue_report/schema_util.py` |
| IA (Responses API) | `services/revenue_report/openai_generate.py` |
| Fallback desde análisis panel legacy | `services/revenue_report/fallback.py` |
| HTML (Jinja2) | `templates/revenue_report/dragonne_report.html` |
| CSS marca | `static/css/revenue_report.css` |
| PDF (HTML → PDF) | `services/revenue_report/render_pdf.py` |
| Assets configurables | `static/branding/revenue-report/` (ver `README` ahí) |
| Mock visual | `GET /revenue-report/mock` |

Flujo: datos + análisis legacy → (opcional) segunda llamada OpenAI con schema revenue → JSON validado → template → PDF. Si falla validación o IA, se usa `fallback.py` y se revalida.

Variables de entorno:

- `REVENUE_REPORT_USE_LEGACY_PDF=1` — al descargar un análisis, usa solo el PDF antiguo (tablero legacy), no el informe revenue.
- `REVENUE_REPORT_SKIP_AI=1` — no llama a OpenAI para el JSON revenue; solo mapeo desde el análisis del panel + validación.
- `REVENUE_REPORT_PDF_ENGINE=xhtml` — si tienes `xhtml2pdf` instalado, intenta render desde el HTML/CSS (opcional).
- Sin `OPENAI_API_KEY` o si falla la IA/validación, se usa **fallback** y se valida de nuevo antes del PDF.
