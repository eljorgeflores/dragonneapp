# DragonApp — Fase 2 (routers incrementales)

## Objetivo

Separar rutas del monolito `app.py` en `routes/*.py` **sin cambiar URLs**, formularios públicos ni comportamiento de Stripe/auth.

## Routers montados en `app.py`

| Módulo | Contenido |
|--------|-----------|
| `routes/marketing.py` | `/`, `/marketing`, `/precios`, `/pricing` → 302 `/precios`, `/api`, `/redoc`, sitemap, robots, `/mockup-analisis` |
| `routes/auth.py` | `/signup`, `/login`, `/logout`, forgot/reset, `/onboarding` |
| `routes/consulting.py` | `/consultoria`, `/consulting`, `POST /consultoria/lead` (tag `consulting_parent`, aislado del SaaS) |
| `routes/admin.py` | Todo `/admin/*` |
| `routes/analysis.py` | `POST /analyze`, `/analysis/*`, `/s/{token}`, PDF web (delega en `web_*` en `app.py`) |

La lógica pesada de análisis y PDF sigue en `app.py` como funciones **`web_analyze`**, **`web_analysis_detail_json`**, **`web_analysis_share_ensure`**, **`web_analysis_share_email`**, **`web_shared_analysis_page`**, **`web_analysis_pdf_download`** (sin decorador `@app`).

## `/precios` vs `/pricing`

- **Canónico:** `/precios` + plantilla `precios.html`.
- **`/pricing`:** solo `RedirectResponse("/precios", status_code=302)`, `include_in_schema=False` (sin ruido en OpenAPI).

## Consultoría vs producto

- Código y rutas en `routes/consulting.py`; tag de router `consulting_parent` para filtrar en OpenAPI o futuros despliegues.
- Próximo paso seguro: montar el mismo router en una app ASGI mínima o subdominio, compartiendo solo `db`, `config`, `templating` y `email_smtp` — **sin** mezclar handlers con `routes/auth` o `routes/analysis`.

## Plantillas

### En uso (referenciadas desde Python)

`marketing.html`, `precios.html`, `api_docs.html`, `mockup_analisis.html`, `consulting.html`, `signup.html`, `login.html`, `forgot_password.html`, `reset_password.html`, `onboarding.html`, `app.html`, `account.html`, `billing_success.html`, `share_public.html`, `admin.html`, `admin_user_detail.html`, `admin_admins.html`, `admin_api.html`, `base.html` (extends), `partials/demo_resultado_analisis.html` (si lo incluye alguna plantilla viva).

### Huérfanas (no hay `TemplateResponse` en el código)

`index.html`, `landing.html`, `dashboard.html`, `register.html`, `package_detail.html`.

### Duplicidad / consolidar

- **`pricing.html`:** no referenciada; la página viva es `precios.html`. Opciones: borrar tras comprobar enlaces externos / git history, o redirigir contenido a `precios.html` y eliminar duplicado.
- **`landing.html`:** solapa concepto con `marketing.html`; fusionar solo si se unifica copy y rutas.

### Borrado

No borrar huérfanas en esta fase; tras grep en repo + staging, eliminar en Fase 3 si no hay referencias en docs ni enlaces públicos.

## Tests

- **`conftest.py`:** fuerza `APP_URL=http://testserver` antes de imports para que las cookies de sesión no lleven `Secure` cuando `.env` tiene `https://…` (TestClient es HTTP).
- **`test_auth_admin.py`:** `follow_redirects=False` donde se aserta `303`; `client.cookies.clear()` en `test_admin_requires_login` (cliente compartido).

## Manejo `HTTPException`

El handler personalizado solo trata **401**; el resto delega en `fastapi.exception_handlers.http_exception_handler` (evita re-lanzar `raise exc` bajo middleware async).

## Riesgos y pendientes (Fase 3)

- Extraer `api_v1` y billing a `routes/` o paquete `billing/`.
- Mover helpers PDF a módulo dedicado si crece.
- Revisar imports tardíos `from app import web_*` en `routes/analysis.py` (aceptable de momento; alternativa: paquete `services/analysis_handlers.py`).
- Depurar templates huérfanas y `pricing.html`.
- Opcional: `TestClient` por test o fixture para no depender de `cookies.clear()`.
