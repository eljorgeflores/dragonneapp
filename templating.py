"""Motor Jinja2 compartido (evita import circular app ↔ routes)."""
from fastapi.templating import Jinja2Templates

from config import APP_URL, BASE_DIR, URL_PREFIX

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.globals["app_url"] = (APP_URL or "").rstrip("/") or None
templates.env.globals["url_prefix"] = URL_PREFIX or ""
