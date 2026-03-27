"""Enlaces públicos de análisis, plantilla compartida y envío por correo."""
from __future__ import annotations

import json
import re
import secrets

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from auth_session import require_user
from config import APP_URL, SMTP_HOST, SMTP_PASSWORD, SMTP_USER
from db import db
from email_smtp import send_analysis_share_link_email
from seo_helpers import noindex_page_seo
from templating import templates

_SHARE_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def public_share_base_url() -> str:
    return (APP_URL or "http://127.0.0.1:8000").rstrip("/")


def looks_like_email(addr: str) -> bool:
    s = (addr or "").strip()
    return bool(s) and len(s) <= 254 and bool(_SHARE_EMAIL_RE.match(s))


def analysis_detail_json_response(request: Request, analysis_id: int) -> JSONResponse:
    user = require_user(request)
    with db() as conn:
        row = conn.execute("SELECT * FROM analyses WHERE id = ? AND user_id = ?", (analysis_id, user["id"])).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    stoken = row["share_token"] if row["share_token"] else None
    share_url = f"{public_share_base_url()}/s/{stoken}" if stoken else None
    return JSONResponse({
        "ok": True,
        "summary": json.loads(row["summary_json"]),
        "analysis": json.loads(row["analysis_json"]),
        "id": row["id"],
        "title": row["title"],
        "created_at": row["created_at"],
        "plan": row["plan_at_analysis"] or "free",
        "share_url": share_url,
    })


def ensure_share_link_response(request: Request, analysis_id: int) -> JSONResponse:
    user = require_user(request)
    with db() as conn:
        row = conn.execute(
            "SELECT share_token FROM analyses WHERE id = ? AND user_id = ?",
            (analysis_id, user["id"]),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Análisis no encontrado")
        token = row["share_token"]
        if not token:
            token = secrets.token_urlsafe(24)
            conn.execute("UPDATE analyses SET share_token = ? WHERE id = ?", (token, analysis_id))
    return JSONResponse({"ok": True, "share_url": f"{public_share_base_url()}/s/{token}"})


def share_analysis_by_email_response(request: Request, analysis_id: int, to_email: str) -> JSONResponse:
    user = require_user(request)
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        raise HTTPException(
            status_code=503,
            detail="El envío por correo no está configurado en el servidor. Usa “Abrir en mi correo” o configura SMTP (.env).",
        )
    to_clean = (to_email or "").strip()
    if not looks_like_email(to_clean):
        raise HTTPException(status_code=400, detail="Correo no válido.")
    uid = int(user["id"])
    hotel_label = (user["hotel_name"] or "").strip() or "Hotel"
    with db() as conn:
        row = conn.execute(
            "SELECT share_token FROM analyses WHERE id = ? AND user_id = ?",
            (analysis_id, uid),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Análisis no encontrado")
        token = row["share_token"]
        if not token:
            token = secrets.token_urlsafe(24)
            conn.execute("UPDATE analyses SET share_token = ? WHERE id = ?", (token, analysis_id))
    share_url = f"{public_share_base_url()}/s/{token}"
    if not send_analysis_share_link_email(to_clean, share_url, hotel_label):
        raise HTTPException(status_code=500, detail="No se pudo enviar el correo. Intenta más tarde.")
    return JSONResponse({"ok": True, "message": "Correo enviado."})


def shared_analysis_page_response(request: Request, share_token: str):
    with db() as conn:
        row = conn.execute(
            "SELECT title, summary_json, analysis_json, created_at FROM analyses WHERE share_token = ?",
            (share_token,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Enlace no válido o expirado.")
    summary = json.loads(row["summary_json"])
    analysis = json.loads(row["analysis_json"])
    created = (row["created_at"] or "")[:19].replace("T", " ")
    title = row["title"] or "Informe compartido"
    share_path = f"/s/{share_token}"
    seo = noindex_page_seo(
        share_path,
        f"{title} — compartido",
        "Vista de solo lectura con token; no indexar.",
    )
    return templates.TemplateResponse(
        "share_public.html",
        {
            "request": request,
            "page_title": title,
            "created_at": created,
            "summary": summary,
            "analysis": analysis,
            **seo,
        },
    )
