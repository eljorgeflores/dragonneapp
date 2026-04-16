from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from auth_session import get_api_user
from config import (
    KAPSO_API_KEY,
    KAPSO_PHONE_NUMBER_ID,
    KAPSO_WEBHOOK_SECRET,
    KAPSO_WEBHOOK_VERIFY_TOKEN,
    KAPSO_WHATSAPP_BASE_URL,
)

_log = logging.getLogger(__name__)

router = APIRouter(tags=["whatsapp"])


@router.get("/kapso/whatsapp/webhook", include_in_schema=False)
def kapso_whatsapp_webhook_verify(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
):
    """
    Verificación estilo Meta Cloud API:
    - GET con hub.mode=subscribe
    - hub.verify_token debe coincidir con KAPSO_WEBHOOK_VERIFY_TOKEN
    - devolver hub.challenge como texto
    """
    if not KAPSO_WEBHOOK_VERIFY_TOKEN:
        raise HTTPException(status_code=500, detail="Webhook de Kapso no configurado (falta KAPSO_WEBHOOK_VERIFY_TOKEN).")
    if (hub_mode or "").strip() != "subscribe":
        raise HTTPException(status_code=400, detail="Modo inválido.")
    if (hub_verify_token or "").strip() != KAPSO_WEBHOOK_VERIFY_TOKEN:
        raise HTTPException(status_code=403, detail="Token inválido.")
    if not (hub_challenge or "").strip():
        raise HTTPException(status_code=400, detail="Challenge faltante.")
    return (hub_challenge or "").strip()


@router.post("/kapso/whatsapp/webhook", include_in_schema=False)
async def kapso_whatsapp_webhook_receive(request: Request):
    """
    Recepción de webhooks (delivery status, mensajes entrantes, etc.).
    Por ahora: aceptar y loguear un resumen mínimo para depurar.
    """
    raw = await request.body()
    sig = (request.headers.get("x-webhook-signature") or "").strip()
    idem = (request.headers.get("x-idempotency-key") or "").strip()
    event_hdr = (request.headers.get("x-webhook-event") or "").strip()
    if KAPSO_WEBHOOK_SECRET:
        if not sig:
            raise HTTPException(status_code=401, detail="Falta X-Webhook-Signature.")
        expected = hmac.new(KAPSO_WEBHOOK_SECRET.encode("utf-8"), raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise HTTPException(status_code=401, detail="Firma inválida.")
    else:
        # Desarrollo: permitir sin secreto (no recomendado en prod).
        if sig:
            _log.warning("kapso.webhook: firma presente pero KAPSO_WEBHOOK_SECRET no configurado; se omite verificación.")

    try:
        payload = await request.json()
    except Exception:
        payload = None
    kind = "unknown"
    if isinstance(payload, dict):
        if payload.get("object"):
            kind = str(payload.get("object"))
        elif payload.get("type"):
            kind = str(payload.get("type"))
    _log.info(
        "kapso.whatsapp.webhook received event=%s kind=%s idempotency=%s has_payload=%s",
        event_hdr or "-",
        kind,
        (idem[:18] + "…" if len(idem) > 18 else (idem or "-")),
        "Y" if payload else "N",
    )
    return {"ok": True}


class SendTextRequest(BaseModel):
    to: str = Field(..., min_length=5, max_length=32, description="Número destino en formato E.164 sin + opcional, o con +. Ej: 15551234567 o +15551234567.")
    body: str = Field(..., min_length=1, max_length=4096, description="Texto del mensaje.")
    preview_url: bool = Field(False, description="Si True, habilita previsualización de URLs (si aplica).")


class SendTemplateRequest(BaseModel):
    to: str = Field(
        ...,
        min_length=5,
        max_length=32,
        description="Número destino en E.164 (con + opcional). Ej: +529981864670.",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=512,
        description="Nombre del template aprobado (Meta). Ej: hello_world o pullso_brief_ping.",
    )
    language: str = Field(
        "en_US",
        min_length=2,
        max_length=16,
        description="Código de idioma del template (p. ej. en_US, es_MX).",
    )
    # Por ahora solo soportamos templates sin variables (o con variables vacías).


def _normalize_e164_or_raise(to_raw: str) -> str:
    t = (to_raw or "").strip()
    t = t[1:] if t.startswith("+") else t
    if not t.isdigit() or len(t) < 10:
        raise HTTPException(status_code=400, detail="Número 'to' inválido. Usa E.164 (p. ej. +52999...).")
    return t


@router.post("/api/v1/whatsapp/send-text", summary="Enviar un WhatsApp (texto) vía Kapso", tags=["API v1"])
def api_send_whatsapp_text(
    payload: SendTextRequest,
    _user=Depends(get_api_user),
):
    """
    Endpoint de prueba para validar que el número de Kapso está listo y que tu proyecto puede enviar mensajes.
    Autenticación: API key de Pullso (header X-API-Key).
    """
    if not KAPSO_API_KEY:
        raise HTTPException(status_code=500, detail="Falta KAPSO_API_KEY en el servidor.")
    if not KAPSO_PHONE_NUMBER_ID:
        raise HTTPException(status_code=500, detail="Falta KAPSO_PHONE_NUMBER_ID en el servidor.")
    base = (KAPSO_WHATSAPP_BASE_URL or "").strip().rstrip("/")
    if not base:
        raise HTTPException(status_code=500, detail="Falta KAPSO_WHATSAPP_BASE_URL en el servidor.")

    to_norm = _normalize_e164_or_raise(payload.to)

    url = f"{base}/{KAPSO_PHONE_NUMBER_ID}/messages"
    body: Dict[str, Any] = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_norm,
        "type": "text",
        "text": {"body": payload.body},
    }
    if payload.preview_url:
        body["text"]["preview_url"] = True

    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.post(url, headers={"X-API-Key": KAPSO_API_KEY}, json=body)
        if r.status_code >= 400:
            detail: Optional[str] = None
            try:
                detail = r.text[:1200]
            except Exception:
                detail = None
            raise HTTPException(status_code=502, detail=f"Kapso error {r.status_code}: {detail or 'sin detalle'}")
        data = r.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"No se pudo enviar por Kapso: {type(exc).__name__}")

    return {"ok": True, "kapso": data}


@router.post("/api/v1/whatsapp/send-template", summary="Enviar un WhatsApp (template) vía Kapso", tags=["API v1"])
def api_send_whatsapp_template(
    payload: SendTemplateRequest,
    _user=Depends(get_api_user),
):
    """
    Envía un template aprobado por Meta.
    Útil para salir del bloqueo de la ventana de 24 horas (no-template messages).
    """
    if not KAPSO_API_KEY:
        raise HTTPException(status_code=500, detail="Falta KAPSO_API_KEY en el servidor.")
    if not KAPSO_PHONE_NUMBER_ID:
        raise HTTPException(status_code=500, detail="Falta KAPSO_PHONE_NUMBER_ID en el servidor.")
    base = (KAPSO_WHATSAPP_BASE_URL or "").strip().rstrip("/")
    if not base:
        raise HTTPException(status_code=500, detail="Falta KAPSO_WHATSAPP_BASE_URL en el servidor.")

    to_norm = _normalize_e164_or_raise(payload.to)
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Template 'name' faltante.")
    lang = (payload.language or "").strip() or "en_US"

    url = f"{base}/{KAPSO_PHONE_NUMBER_ID}/messages"
    body: Dict[str, Any] = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_norm,
        "type": "template",
        "template": {
            "name": name,
            "language": {"code": lang},
        },
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.post(url, headers={"X-API-Key": KAPSO_API_KEY}, json=body)
        if r.status_code >= 400:
            detail: Optional[str] = None
            try:
                detail = r.text[:1200]
            except Exception:
                detail = None
            raise HTTPException(status_code=502, detail=f"Kapso error {r.status_code}: {detail or 'sin detalle'}")
        data = r.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"No se pudo enviar template por Kapso: {type(exc).__name__}")

    return {"ok": True, "kapso": data}

