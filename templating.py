"""Motor Jinja2 compartido (evita import circular app ↔ routes)."""
from fastapi.templating import Jinja2Templates

from config import APP_URL, BASE_DIR, URL_PREFIX, url_path
from seo_helpers import default_og_image_absolute

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.globals["app_url"] = (APP_URL or "").rstrip("/") or None
templates.env.globals["url_prefix"] = URL_PREFIX or ""
templates.env.globals["url_path"] = url_path
templates.env.globals["default_og_image_absolute"] = default_og_image_absolute
