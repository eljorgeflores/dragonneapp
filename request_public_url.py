"""Origen HTTP público para enlaces (p. ej. reset password) detrás de proxy o en local."""
from fastapi import Request


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
    return str(request.base_url).rstrip("/")
