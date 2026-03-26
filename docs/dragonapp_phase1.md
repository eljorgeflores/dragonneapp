# DragonApp — auditoría y Fase 1 (estructura)

## 1. Diagnóstico breve

- **Stack**: FastAPI + Jinja2 + JS/CSS estáticos + SQLite; un solo módulo grande `app.py` con rutas HTML, API `/api/v1`, lógica de análisis, Stripe, PDF y admin.
- **Estado**: Funcional y cohesivo; el principal riesgo de mantenimiento es **acoplamiento** (todo en un archivo) y **convivencia** de producto SaaS hoteles con **activos de consultoría / parent company**.
- **Fase 1** (esta entrega): extraer **config** y **db**, documentar alcance, mover un **partial** de plantilla sin tocar URLs ni flujos críticos.

## 2. Fuera de alcance DragonApp (extraer o ignorar)

| Artefacto | Notas |
|-----------|--------|
| `templates/consulting.html` | Landing consultoría; marcada en plantilla + este doc. |
| `consulting_i18n.py` | Solo usado por consultoría. |
| Rutas `/consultoria`, `/consulting`, `POST /consultoria/lead` | No son flujo hotel SaaS; dependen de `consulting_leads` en SQLite. |
| `CONSULTING_CALENDAR_URL` en `config.py` | Config compartida hasta extracción. |
| `scripts/fetch_linkedin_photos.py` | Utilidad ad-hoc; no core producto. |

**No eliminado en Fase 1** (cambio destructivo): las rutas y tablas siguen activas; solo quedan **marcadas** y **documentadas** para un paquete futuro (otro repo o subdominio).

## 3. Duplicados / solapes / legado

| Tema | Detalle |
|------|---------|
| **Home marketing** | `GET /` y `GET /marketing` apuntan al mismo handler (`marketing.html`). Intencional alias. |
| **Precios** | `precios.html` en `/precios`; `GET /pricing` redirige (slug inglés). `templates/pricing.html` existe pero **no** referenciada por `app.py` → candidata a borrar o unificar en Fase 2. |
| **Landings huérfanas** | `index.html`, `landing.html`, `dashboard.html`, `register.html`, `package_detail.html` **no** aparecen en `TemplateResponse` → legado / prototipos; revisar antes de borrar. |
| **DB name** | Archivo `profitpilot.db` y copy “ProfitPilot” en `dashboard.html` legado; producto actual DRAGONNÉ. Renombrar DB es **destructivo** sin migración explícita → Fase 2+. |
| **OpenAPI vs HTML** | `/api` página docs HTML; `/docs` Swagger; `/redoc` ReDoc — no solapan, complementan. |

## 4. Estructura objetivo (roadmap)

```
app.py              # entry mínimo: FastAPI, middleware, include_router
config.py           # ✓ Fase 1
db.py               # ✓ Fase 1
routes/             # Fase 2: auth, dashboard, analysis, billing, admin, api, marketing
services/           # Fase 2+: analysis, file, pdf, email, stripe, auth
utils/              # Fase 2+: helpers, formatting, security
templates/
  base.html
  partials/         # ✓ Fase 1 (demo resultado)
  marketing/        # Fase 2 (mover sin romper paths de una tacada)
  auth/
  app/
  admin/
static/
  css/ js/ img/     # Fase 2 (actualizar referencias en base.html)
```

## 5. Cambios realizados (Fase 1)

- **`config.py`**: variables de entorno, rutas base, límites de planes, Stripe/SMTP/API/consulting URL.
- **`db.py`**: `db()` + `init_db()` (misma semántica que antes).
- **`app.py`**: importa `config` y `db`, llama `init_db()` al cargar; docstring de deuda; bloque comentado para consultoría; eliminado `contextmanager` no usado.
- **`templates/partials/demo_resultado_analisis.html`**: movido desde `_demo_resultado_analisis.html`; includes actualizados en `marketing.html`, `mockup_analisis.html`.
- **`templates/consulting.html`**: comentario Jinja de fuera de alcance.
- **Este documento** en `docs/dragonapp_phase1.md`.

## 6. Pendientes Fase 2 (sugeridos)

1. Extraer **APIRouter** por dominio (`routes/admin.py`, etc.) y `app.include_router` sin cambiar paths.
2. Mover plantillas a subcarpetas con **grep sistemático** de `TemplateResponse` / `extends` / `include`.
3. Partir `static/styles.css` o mover a `static/css/` + una pasada de búsqueda de URLs.
4. Servicios: `stripe_request` / `ensure_stripe_customer` → `services/stripe_service.py`.
5. Depurar templates huérfanas (`pricing.html` vs `precios.html`, `index.html`, etc.).
6. Paquete **consultoría**: rutas + plantilla + i18n + tabla `consulting_leads` en micro-app o flag `ENABLE_CONSULTING_ROUTES`.

## 7. Cómo verificar

```bash
python3 -m py_compile app.py config.py db.py
uvicorn app:app --reload
```

Comprobar: login, `/app`, análisis, `/admin`, Stripe webhook/checkout si aplica, `/` marketing, `/mockup-analisis`.
