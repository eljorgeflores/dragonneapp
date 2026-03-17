# Lista de lanzamiento — DRAGONNÉ

Stack sugerido y pasos en orden para dejar el sitio en producción.

---

## Stack recomendado (simple y suficiente para arrancar)

| Capa | Opción | Notas |
|------|--------|--------|
| **Hosting** | [Render](https://render.com) o [Railway](https://railway.app) | Web Service, conectas el repo y listo. Alternativa: VPS (DigitalOcean, Hetzner) con Nginx + systemd. |
| **Dominio** | El que ya tengas (ej. dragonne.co) | Apuntas CNAME/A al servicio de Render o Railway. |
| **HTTPS** | Incluido en Render/Railway | Si usas VPS: Let's Encrypt (certbot) o Cloudflare delante. |
| **Base de datos** | SQLite (ya está) | El archivo `data/profitpilot.db` se persiste en el disco del servicio. En Render/Railway asegura volumen persistente si lo ofrecen para el path `data/`. |
| **Email** | SendGrid, Resend o Gmail (app password) | Solo para “Recuperar contraseña”. |
| **Pagos** | Stripe | Checkout + Customer Portal + webhook. |
| **Backups** | Script + cron o backup nativo | `scripts/backup_db.py`; opcional: copiar `data/backups/` a S3 o otro almacén. |

No hace falta Redis, colas ni Postgres al inicio. Puedes migrar a Postgres más adelante si el volumen lo pide.

---

## Qué hacer, en orden

### 1. Repo y entorno local

- [ ] Clonar/copiar el proyecto donde vayas a desplegar (o conectar el repo a Render/Railway).
- [ ] Crear `.env` desde `.env.example` y **nunca** subir `.env` a Git (ya está en `.gitignore`).

### 2. Variables de entorno en producción

- [ ] **APP_URL** = `https://tu-dominio.com` (sin barra final). Ej: `https://dragonne.co`
- [ ] **APP_SECRET_KEY** = una cadena larga y aleatoria (generar con `openssl rand -hex 32`).
- [ ] **ADMIN_EMAILS** = tu correo (ej. `jorge@dragonne.co`).
- [ ] **OPENAI_API_KEY** = tu clave de OpenAI (producción).
- [ ] **OPENAI_MODEL** = `gpt-4o` o `gpt-4o-mini` según quieras calidad vs coste.

### 3. Email (recuperar contraseña)

- [ ] Rellenar en `.env`: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`.
- [ ] Probar “Olvidé mi contraseña”: debe llegar el correo con el enlace.
- [ ] Si el enlace da **403**: en Cloudflare/WAF permitir `GET /reset-password/*` (ruta pública).

### 4. Stripe (planes Pro / Pro+)

- [ ] En Stripe Dashboard: modo **live**; crear productos y precios (Pro mensual, Pro anual, Pro+).
- [ ] En `.env`: `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY` (claves **live**).
- [ ] En `.env`: `STRIPE_MONTHLY_PRICE_ID`, `STRIPE_ANNUAL_PRICE_ID`, `STRIPE_PRO_PLUS_PRICE_ID` (los `price_xxx` de cada tarifa).
- [ ] Crear webhook en Stripe: URL `https://tu-dominio.com/billing/webhook`, eventos: `checkout.session.completed`, `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`.
- [ ] Copiar el **Signing secret** del webhook a `STRIPE_WEBHOOK_SECRET` en `.env`.
- [ ] Activar Customer Portal en Stripe (para Facturación desde la app).

### 5. Desplegar la app

**En Render:**

- [ ] New → Web Service; conectar el repo.
- [ ] Build: `pip install -r requirements.txt` (o el comando que use tu proyecto).
- [ ] Start: `uvicorn app:app --host 0.0.0.0 --port $PORT` (Render inyecta `PORT`).
- [ ] Añadir todas las variables de `.env` en **Environment** (secretas no se muestran).
- [ ] Si usas SQLite: en **Disk** añadir un volumen persistente montado en la ruta donde está `data/` (según documentación de Render).

**En Railway:**

- [ ] New Project → deploy from repo.
- [ ] Configurar start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`.
- [ ] Añadir variables de entorno desde el panel.
- [ ] Persistir `data/` si Railway lo permite (volúmenes).

**VPS (Nginx + systemd):**

- [ ] Instalar dependencias, crear `.env`, ejecutar con `uvicorn` o Gunicorn detrás de Nginx.
- [ ] Nginx: proxy a `http://127.0.0.1:8000` y SSL con certbot.
- [ ] Asegurar que el proceso lee `APP_URL` con `https://`.

### 6. Dominio y HTTPS

- [ ] En tu DNS: CNAME (o A) del dominio hacia el host de Render/Railway (te dan la URL).
- [ ] Comprobar que `https://tu-dominio.com` abre la app y que no hay avisos de certificado.

### 7. Comprobaciones finales

- [ ] **Login / Signup / Recuperar contraseña**: flujo completo sin errores.
- [ ] **Subir un reporte** y **ver análisis**: resultado y PDF correctos.
- [ ] **Plan Pro**: clic en upgrade → Stripe Checkout → pago de prueba → vuelta a la app con plan actualizado.
- [ ] **Facturación**: botón “Facturación” abre el portal de Stripe (gestionar pago, cancelar).
- [ ] **Botón WhatsApp** y enlaces del nav (Integraciones, Precios) funcionan.
- [ ] **Backup**: ejecutar una vez `scripts/backup_db.py` y, si quieres, programar cron diario (ver README).

### 8. Opcional: WAF / proxy

- [ ] Si usas Cloudflare (u otro): permitir `/reset-password/*` para que el enlace de recuperar contraseña no devuelva 403.

---

## Resumen rápido

1. `.env` completo (APP_URL, APP_SECRET_KEY, OpenAI, SMTP, Stripe).
2. SMTP para “Recuperar contraseña”.
3. Stripe en vivo: precios + webhook + Customer Portal.
4. Desplegar (Render/Railway o VPS) con variables y, si aplica, disco persistente para `data/`.
5. Dominio apuntando y HTTPS ok.
6. Probar: registro, login, reporte, análisis, pago Pro y facturación.

Cuando todo eso esté hecho, puedes considerar el lanzamiento listo. Si quieres, el siguiente paso es documentar en el README la URL de producción y cualquier detalle específico de tu despliegue (ej. “Desplegado en Render con volumen en `data/`”).
