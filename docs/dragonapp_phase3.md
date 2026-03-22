# DragonApp — Fase 3 (servicios + routers billing/API)

## Plan ejecutado

1. **Análisis:** pipeline (`parse_file`, `summarize_reports`, `call_openai`, `save_analysis`, límites de plan) en `services/analysis_core.py`. Flujo web en `services/analysis_service.py`. Compartir y correo en `services/share_service.py`. PDF en `services/pdf_service.py`. `routes/analysis.py` solo enruta.
2. **Billing:** `services/billing_stripe.py` (HTTP Stripe + sync plan) y `routes/billing.py` (mismas URLs `/billing/*`).
3. **API v1:** `routes/api.py` con prefijo `/api/v1` (mismos paths que antes).
4. **Templates:** huérfanas movidas a `templates/legacy/` (sin borrar).
5. **`app.py`:** panel `/app`, `/app/account`, health, middleware; imports de `upload_eligibility` desde `analysis_core`.

## Riesgos

| Área | Riesgo | Mitigación |
|------|--------|------------|
| Imports circulares | Medio | Servicios no importan `app`; `routes/*` importan servicios. |
| Stripe | Bajo | Misma lógica y URLs; solo cambió módulo. |
| PDF web vs API | Bajo | Una implementación en `pdf_service.streaming_pdf_response_for_owned_analysis`. |
| Tests / demos | Bajo | `test_analyze_report` importa `services.analysis_core`. |

## Desarrollo local y cookies de sesión

Si en `.env` tienes `APP_URL=https://…` (producción) pero corres `uvicorn` en **http://127.0.0.1**, el navegador/cliente HTTP no envía cookies marcadas `Secure`, y fallan POST con sesión (`/onboarding`, `/analyze`, etc.).

Opciones:

1. Arrancar con cookie no Secure solo en dev: `SESSION_INSECURE_COOKIES=1 uvicorn app:app --reload`
2. O usar `APP_URL=http://127.0.0.1:8000` en un `.env.local` / variable de entorno al desarrollar.

**No** uses `SESSION_INSECURE_COOKIES=1` en producción HTTPS.

## Deuda (Fase 4)

- Extraer renderizado del dashboard (`/app`) a `routes/dashboard.py` o `services/dashboard_context.py`.
- Opcional: `services/openai_analysis.py` solo con `call_openai` + `HOTEL_PROMPT` para acortar `analysis_core`.
- Revisar `templates/legacy/*` y borrar tras auditoría.
- Unificar `public_share_base_url` si se centraliza en `config` o `templating`.
