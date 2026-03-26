"""Origen HTTP público para enlaces (p. ej. reset password) detrás de proxy o en local."""
from urllib.parse import urlparse

from fastapi import Request

import config


def origin_for_user_facing_links(request: Request) -> str:
    """
    Prefiere cabeceras de proxy; si no, Request.base_url.
    Evita enlaces rotos cuando APP_URL en .env no coincide con el host real de acceso.
    """
    fwd_host = (request.headers.get("x-forwarded-host") or "").strip()
    if fwd_host:
        host = fwd_host.split(",")[0].strip()
        proto = (request.headers.get("x-forwarded-proto") or "").strip().lower()
        if proto not in ("http", "https"):
            proto = request.url.scheme
        return f"{proto}://{host}".rstrip("/")
    base = str(request.base_url).rstrip("/")
    # TestClient de Starlette usa host "testserver"; el correo debe llevar APP_URL (p. ej. 127.0.0.1:8000).
    if (request.url.hostname or "").lower() == "testserver":
        app_raw = (config.APP_URL or "").strip().rstrip("/")
        if app_raw.startswith(("http://", "https://")):
            try:
                pu = urlparse(app_raw)
                if pu.netloc:
                    return f"{pu.scheme}://{pu.netloc}".rstrip("/")
            except Exception:
                pass
    return base
