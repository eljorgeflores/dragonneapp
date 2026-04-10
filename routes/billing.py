"""Checkout, portal y webhook Stripe (URLs sin prefijo; mismas rutas que antes)."""
import hashlib
import hmac
import json

from fastapi import APIRouter, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

from auth_session import require_user
from config import (
    APP_URL,
    STRIPE_ANNUAL_PRICE_ID,
    STRIPE_MONTHLY_PRICE_ID,
    STRIPE_PRO_PLUS_PRICE_ID,
    STRIPE_WEBHOOK_SECRET,
    TRIAL_DAYS,
)
from db import db
from services.billing_stripe import ensure_stripe_customer, stripe_request, sync_user_from_stripe_customer
from seo_helpers import noindex_page_seo
from templating import templates
from time_utils import now_iso

router = APIRouter(tags=["billing"])


@router.post("/billing/create-checkout-session")
def create_checkout_session(request: Request, billing_cycle: str = Form(...), plan_tier: str = Form("pro")):
    user = require_user(request)
    if plan_tier == "pro_plus":
        if not STRIPE_PRO_PLUS_PRICE_ID:
            raise HTTPException(status_code=500, detail="Pro+ no configurado (STRIPE_PRO_PLUS_PRICE_ID)")
        price_id = STRIPE_PRO_PLUS_PRICE_ID
    else:
        if billing_cycle not in {"monthly", "annual"}:
            raise HTTPException(status_code=400, detail="Ciclo inválido")
        price_id = STRIPE_MONTHLY_PRICE_ID if billing_cycle == "monthly" else STRIPE_ANNUAL_PRICE_ID
        if not price_id:
            raise HTTPException(status_code=500, detail="Falta configurar el price_id de Stripe (Pro)")
    customer_id = ensure_stripe_customer(user)
    payload = {
        "mode": "subscription",
        "customer": customer_id,
        "success_url": f"{APP_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{APP_URL}/app",
        "line_items[0][price]": price_id,
        "line_items[0][quantity]": 1,
        "allow_promotion_codes": "true",
        "metadata[user_id]": str(user["id"]),
        "metadata[billing_cycle]": billing_cycle if plan_tier != "pro_plus" else "monthly",
        "metadata[plan_tier]": plan_tier,
    }
    if TRIAL_DAYS > 0 and plan_tier != "pro_plus":
        payload["subscription_data[trial_period_days]"] = TRIAL_DAYS
    session = stripe_request("POST", "/v1/checkout/sessions", payload)
    return JSONResponse({"ok": True, "url": session["url"]})


@router.get("/billing/success", response_class=HTMLResponse)
def billing_success(request: Request):
    user = require_user(request)
    return templates.TemplateResponse(
        "billing_success.html",
        {
            "request": request,
            "user": user,
            **noindex_page_seo(
                "/billing/success",
                "Pago exitoso — Pullso",
                "Confirmación de checkout (no indexar).",
            ),
        },
    )


@router.post("/billing/create-portal-session")
def create_portal_session(request: Request):
    user = require_user(request)
    if not user["stripe_customer_id"]:
        raise HTTPException(status_code=400, detail="No hay cliente de Stripe asociado todavía.")
    session = stripe_request("POST", "/v1/billing_portal/sessions", {
        "customer": user["stripe_customer_id"],
        "return_url": f"{APP_URL}/app",
    })
    return JSONResponse({"ok": True, "url": session["url"]})


@router.post("/billing/webhook")
async def billing_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook no configurado")
    header_parts = dict(item.split("=", 1) for item in sig.split(",") if "=" in item)
    timestamp = header_parts.get("t", "")
    signature = header_parts.get("v1", "")
    signed_payload = f"{timestamp}.{payload.decode()}".encode()
    expected = hmac.new(STRIPE_WEBHOOK_SECRET.encode(), signed_payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Firma inválida")
    event = json.loads(payload.decode())
    event_id = event.get("id")
    event_type = event.get("type")
    with db() as conn:
        exists = conn.execute("SELECT id FROM billing_events WHERE stripe_event_id = ?", (event_id,)).fetchone()
        if exists:
            return Response(status_code=200)
        conn.execute(
            "INSERT INTO billing_events (stripe_event_id, event_type, payload, created_at) VALUES (?, ?, ?, ?)",
            (event_id, event_type or "unknown", payload.decode(), now_iso()),
        )
    obj = event.get("data", {}).get("object", {})
    if event_type in {"checkout.session.completed"}:
        customer_id = obj.get("customer")
        subscription_id = obj.get("subscription")
        if customer_id:
            sync_user_from_stripe_customer(customer_id, subscription_id, "active")
    elif event_type in {"customer.subscription.created", "customer.subscription.updated"}:
        customer_id = obj.get("customer")
        status = obj.get("status", "")
        subscription_id = obj.get("id")
        if customer_id:
            sync_user_from_stripe_customer(customer_id, subscription_id, status)
    elif event_type in {"customer.subscription.deleted"}:
        customer_id = obj.get("customer")
        if customer_id:
            sync_user_from_stripe_customer(customer_id, None, "canceled")
    return Response(status_code=200)
