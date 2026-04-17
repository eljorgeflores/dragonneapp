"""Webhook de correo entrante (PMS programado) y API mínima de configuración en /app."""
from __future__ import annotations

import hmac
import json
from typing import Any, List, Optional

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import JSONResponse

from auth_session import require_user
from config import PMS_INBOUND_WEBHOOK_SECRET
from plan_entitlements import get_effective_plan, pms_scheduled_reports_entitled
from services.hotel_pullso import get_current_hotel_id
from services.pms_inbound_service import (
    ensure_route_for_hotel,
    inbound_address_for_token,
    plan_usage_hints,
    process_inbound_email_payload,
    update_route_settings,
)

router = APIRouter(tags=["pms_inbound"])


def _webhook_secret_ok(request: Request) -> bool:
    secret = (PMS_INBOUND_WEBHOOK_SECRET or "").strip()
    if not secret:
        return False
    auth = (request.headers.get("authorization") or "").strip()
    if auth.lower().startswith("bearer "):
        got = auth[7:].strip()
        return hmac.compare_digest(got, secret)
    hdr = (request.headers.get("x-pullso-inbound-secret") or "").strip()
    if hdr:
        return hmac.compare_digest(hdr, secret)
    q = (request.query_params.get("secret") or "").strip()
    if q:
        return hmac.compare_digest(q, secret)
    return False


@router.post("/webhooks/pms-inbound-email")
async def pms_inbound_email_webhook(request: Request):
    """
    Recibe JSON estilo Postmark Inbound (To / OriginalRecipient + Attachments base64)
    o multipart con campo `payload` JSON + archivos sueltos para pruebas.
    """
    if not _webhook_secret_ok(request):
        raise HTTPException(status_code=401, detail="Webhook no autorizado.")

    ctype = (request.headers.get("content-type") or "").lower()
    to_field = ""
    attachments: Any = []
    multipart_files: Optional[List[UploadFile]] = None

    if "multipart/form-data" in ctype:
        form = await request.form()
        raw_payload = form.get("payload")
        if isinstance(raw_payload, str) and raw_payload.strip():
            try:
                body = json.loads(raw_payload)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="payload JSON inválido.")
            to_field = str(body.get("OriginalRecipient") or body.get("To") or "")
            attachments = body.get("Attachments") or []
        else:
            to_field = str(form.get("To") or form.get("to") or "")
        multipart_files = []
        for key, val in form.multi_items():
            if key in ("payload", "To", "to"):
                continue
            if hasattr(val, "filename") and getattr(val, "filename", None):
                multipart_files.append(val)  # type: ignore[arg-type]
    else:
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Cuerpo JSON inválido.")
        to_field = str(body.get("OriginalRecipient") or body.get("To") or "")
        attachments = body.get("Attachments") or []

    result = process_inbound_email_payload(
        to_field=to_field,
        attachments_json=attachments,
        multipart_files=multipart_files,
    )
    if not result.get("ok"):
        code = int(result.get("status_code") or 422)
        if code == 402:
            return JSONResponse(result, status_code=402)
        return JSONResponse(result, status_code=422)
    return JSONResponse(result)


@router.get("/app/pms-automation/status")
def pms_automation_status(request: Request):
    user = require_user(request)
    if not pms_scheduled_reports_entitled(user):
        return JSONResponse({"ok": True, "unlocked": False})
    uid = int(user["id"])
    hid = get_current_hotel_id(request, uid)
    try:
        row = ensure_route_for_hotel(uid, hid)
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    eff = get_effective_plan(user)
    hints = plan_usage_hints(eff)
    return JSONResponse({
        "ok": True,
        "unlocked": True,
        "inbound_email": inbound_address_for_token(str(row["token"])),
        "pms_vendor": str(row["pms_vendor"] or ""),
        "notify_whatsapp": bool(int(row["notify_whatsapp"] or 0)),
        "last_analysis_id": row["last_analysis_id"],
        "plan": eff,
        **hints,
    })


@router.post("/app/pms-automation/configure")
def pms_automation_configure(
    request: Request,
    pms_vendor: str = Form("mews"),
    notify_whatsapp: str = Form("1"),
):
    user = require_user(request)
    if not pms_scheduled_reports_entitled(user):
        raise HTTPException(status_code=403, detail="Tu plan no incluye automatización por correo desde el PMS.")
    uid = int(user["id"])
    hid = get_current_hotel_id(request, uid)
    try:
        ensure_route_for_hotel(uid, hid)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    nw = str(notify_whatsapp).strip().lower() in ("1", "true", "yes", "on")
    updated = update_route_settings(uid, pms_vendor=pms_vendor, notify_whatsapp=nw, hotel_id=hid)
    if not updated:
        raise HTTPException(status_code=500, detail="No se pudo guardar la configuración.")
    eff = get_effective_plan(user)
    return JSONResponse({
        "ok": True,
        "pms_vendor": str(updated["pms_vendor"] or ""),
        "notify_whatsapp": bool(int(updated["notify_whatsapp"] or 0)),
        "inbound_email": inbound_address_for_token(str(updated["token"])),
        **plan_usage_hints(eff),
    })
