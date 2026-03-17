# DRAGONNÉ SaaS

Versión SaaS en español latino para que hoteles suban reportes descargados desde PMS o channel manager y reciban lectura comercial con lenguaje hotelero.

## Qué ya incluye

- Registro, inicio de sesión y recuperación de contraseña.
- App web clara, minimalista y en español latino.
- Upload de `.csv`, `.xlsx`, `.xls`, `.xlsm`.
- Límites por plan:
  - **Gratis:** 1 reporte de hasta 30 días, máximo 3 reportes guardados para comparar.
  - **Pro (19 USD/mes):** 5 reportes de máximo 90 días cada uno, 10 reportes guardados para comparar.
  - **Pro + (49 USD/mes):** 5 reportes de hasta 180 días cada uno, 10 reportes guardados para comparar.
- Planes Pro con Stripe Checkout y portal de facturación.
- Webhook para activar y desactivar plan Pro.
- Botón bloqueado de `Conectar PMS / Channel · Próximamente`.
- Prompt hotelero para devolver:
  - resumen ejecutivo
  - métricas clave
  - hallazgos prioritarios
  - oportunidades directo vs OTA
  - riesgos detectados
  - recomendaciones accionables
  - datos faltantes
  - señal de upgrade

## Arranque

```bash
cd profitpilot_saas
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Carga tus variables en `.env` y luego expórtalas o usa tu método favorito para cargarlas.

```bash
export $(grep -v '^#' .env | xargs)
uvicorn app:app --host 0.0.0.0 --port 8000
```

## Cómo dejar Stripe funcional

### 1) Crea productos y precios en Stripe

En Stripe Dashboard crea un producto `DRAGONNÉ Pro` con los precios recurrentes que vayas a usar (por ejemplo: 19 USD y 49 USD al mes, según tus tiers).

Guarda ambos `price_id` y colócalos en:

- `STRIPE_MONTHLY_PRICE_ID`
- `STRIPE_ANNUAL_PRICE_ID`

### 2) Configura URLs

Pon tu dominio real en:

- `APP_URL=https://tu-dominio.com`

### 3) Crea el webhook

En Stripe configura un endpoint:

- `https://tu-dominio.com/billing/webhook`

Escucha al menos estos eventos:

- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`

Copia el secret del webhook en:

- `STRIPE_WEBHOOK_SECRET`

### 4) Activa Customer Portal

Activa el portal de clientes en Stripe para que el botón **Facturación** permita cambiar método de pago, cancelar o revisar facturas.

### 5) Qué son los Price IDs y qué pones en .env

La app **no** redirige a enlaces fijos tipo `buy.stripe.com/...`. Cuando el usuario hace clic en "Pro mensual", "Pro anual" o "Pro+", el backend llama a la API de Stripe para **crear una sesión de Checkout** y devuelve una URL de pago (distinta cada vez). Para eso necesita saber **qué producto/precio cobrar**: eso es el **Price ID**.

- En Stripe, cada **tarifa** de un producto tiene un ID que empieza por `price_` (ej. `price_1ABC123xyz`).
- En tu `.env` debes poner:
  - **STRIPE_MONTHLY_PRICE_ID**: el Price ID del plan Pro mensual (ej. 19 USD/mes).
  - **STRIPE_ANNUAL_PRICE_ID**: el Price ID del plan Pro anual.
  - **STRIPE_PRO_PLUS_PRICE_ID**: el Price ID del plan Pro+ (ej. 49 USD/mes).
- Dónde verlos: en Stripe → Productos → tu producto → la tarifa (mensual o anual) → copia el "Precio ID" (Price ID).
- Los **enlaces** `https://buy.stripe.com/...` que generas en Stripe son **Payment Links** opcionales (para compartir por email, web, etc.). La app usa los Price IDs para crear el checkout desde el panel; no necesita esos enlaces para funcionar.

## Email (recuperar contraseña)

Si configuras SMTP en `.env`, el enlace de “Olvidé mi contraseña” se envía por correo. Si no, el enlace se muestra en pantalla (solo para pruebas).

Variables en `.env`:

- `SMTP_HOST` – servidor (ej. `smtp.gmail.com`, `smtp.sendgrid.net`)
- `SMTP_PORT` – normalmente `587`
- `SMTP_USER` – usuario / API key según el proveedor
- `SMTP_PASSWORD` – contraseña o API key
- `EMAIL_FROM` – remitente (ej. `DRAGONNÉ <noreply@tu-dominio.com>`)

Funciona con Gmail (contraseña de aplicación), SendGrid, Resend, Amazon SES, etc.

## Backups de la base de datos

El script `scripts/backup_db.py` copia `data/profitpilot.db` a `data/backups/profitpilot_YYYYMMDD_HHMMSS.db` y mantiene solo los últimos 30 backups.

**Ejecución manual** (desde la carpeta del proyecto):

```bash
cd /Users/jorgeflores/Downloads/dragonne_ready_to_launch   # o la ruta donde tengas el proyecto
.venv/bin/python scripts/backup_db.py
```

**Backups automáticos diarios (cron):** esa línea no se pega en la terminal; se añade al crontab. Pasos:

1. Abre el editor de cron: `crontab -e`
2. Si te pregunta, elige un editor (nano es sencillo).
3. Al final del archivo, añade **una sola línea** (sustituye la ruta por la de tu proyecto):

   ```
   0 2 * * * cd /Users/jorgeflores/Downloads/dragonne_ready_to_launch && .venv/bin/python scripts/backup_db.py
   ```

   Significa: todos los días a las 2:00, ejecutar el backup.
4. Guarda y cierra (en nano: Ctrl+O, Enter, Ctrl+X).

Conviene además copiar la carpeta `data/backups/` a otro servidor o disco (Dropbox, S3, etc.) si quieres protección extra.

## API pública

La API está documentada en **/docs** (Swagger) y **/redoc**. Es pública en el sentido de que cualquiera puede leer la documentación, pero **solo los usuarios autorizados** pueden consumirla: un administrador asigna una API key desde **Admin → Acceso API** (dar acceso = generar clave; se muestra una sola vez).

- **Límites por estándares de industria**: 60 peticiones/minuto y 1000/día por clave (configurables con `API_RATE_LIMIT_PER_MINUTE` y `API_RATE_LIMIT_PER_DAY` en `.env`).
- Si se excede el límite, la API responde **429** con `Retry-After`.

## Seguridad

- **Headers**: Se envían X-Content-Type-Options, X-Frame-Options, X-XSS-Protection y Referrer-Policy.
- **Sesión**: La cookie de sesión usa `Secure` cuando `APP_URL` es HTTPS.
- **Login**: Límite de intentos fallidos por IP (6 en 5 minutos) para mitigar fuerza bruta.
- **Subidas**: Solo se aceptan `.csv`, `.xlsx`, `.xls`, `.xlsm` y un tamaño máximo por archivo (por defecto 50 MB, configurable con `MAX_UPLOAD_MB`).
- **Errores**: Las respuestas 500 no exponen detalles internos; el mensaje es genérico.
- **/health**: No expone configuración interna (OpenAI, Stripe, etc.).
- **SQL**: Todas las consultas usan parámetros; no hay concatenación de entrada del usuario.

## Recomendación de despliegue

Para primeros hoteles, esta app ya puede vivir bien en:

- Render
- Railway
- Fly.io
- un VPS con Nginx + systemd

## Administradores

El correo **jorge@dragonne.co** está en `.env.example` como admin fijo (`ADMIN_EMAILS=jorge@dragonne.co`). Asegúrate de tener `ADMIN_EMAILS` en tu `.env`. Desde **Admin → Administradores** puedes dar o quitar acceso admin a otros usuarios registrados; los de `ADMIN_EMAILS` no se pueden revocar desde el panel.

## Antes de conectar APIs y compartir con los primeros hoteles

Revisa esto antes de poner el dominio en producción:

| Revisión | Qué hacer |
|----------|-----------|
| **1. .env nunca en Git** | El proyecto incluye `.gitignore` para que `.env`, `data/` y `uploads/` no se suban. Si usas Git, confirma que `.env` no está en el repositorio. |
| **2. APP_URL y APP_SECRET_KEY** | En producción pon `APP_URL=https://tu-dominio.com` (sin barra final) y `APP_SECRET_KEY` con un valor largo y aleatorio (no el de ejemplo). |
| **3. Stripe en vivo** | Cambia a claves `sk_live_...` y `pk_live_...`, configura el webhook en `https://tu-dominio.com/billing/webhook` y usa los `price_id` reales de tus productos. |
| **4. Recuperar contraseña** | Configura SMTP en `.env` (ver sección "Email" en este README). Si está configurado, el enlace se envía por correo; si no, se muestra en pantalla (solo pruebas). **Si el enlace devuelve 403:** suele ser el proxy/WAF (p. ej. Cloudflare) bloqueando `GET /reset-password/*`. Permite esa ruta en el firewall o en las reglas de seguridad (es pública, el token va en la URL). |
| **5. Copia de la base de datos** | Usa el script `scripts/backup_db.py` y, si quieres, un cron diario. Ver sección "Backups de la base de datos" en este README. |
| **6. HTTPS** | En el dominio usa siempre HTTPS (Let’s Encrypt, Cloudflare o el que ofrezca tu hosting). |
| **7. Probar un flujo completo** | Crea cuenta → inicia sesión → sube un reporte → revisa el análisis y el PDF → (opcional) flujo de pago Pro en Stripe. Así ves que todo encaja antes de compartir el link. |

Nada de esto requiere ser dev: son comprobaciones de configuración y un par de pruebas manuales.

## Notas reales

- La base de datos es SQLite para acelerar el lanzamiento. Para más volumen, migra a Postgres.
- El motor hoy interpreta reportes por heurística. Conforme veas PMS/channel reales, amplía alias y mappings.
- El análisis usa tu API key en backend. El hotel nunca mete su key.
