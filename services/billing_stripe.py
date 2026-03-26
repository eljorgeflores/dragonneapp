"""Cliente HTTP Stripe y sincronización de plan en SQLite (usado por billing y webhook)."""
from __future__ import annotations

import sqlite3
from typing import Any, Dict, Optional

import requests

from config import (
    STRIPE_ANNUAL_PRICE_ID,
    STRIPE_MONTHLY_PRICE_ID,
    STRIPE_PRO_PLUS_PRICE_ID,
    STRIPE_SECRET_KEY,
)
from db import db
from time_utils import now_iso


def stripe_request(method: str, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
    if not STRIPE_SECRET_KEY:
        raise RuntimeError("Falta STRIPE_SECRET_KEY")
    response = requests.request(
        method,
        f"https://api.stripe.com{path}",
        auth=(STRIPE_SECRET_KEY, ""),
        data=data,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def ensure_stripe_customer(user: sqlite3.Row) -> str:
    if user["stripe_customer_id"]:
        return user["stripe_customer_id"]
    customer = stripe_request("POST", "/v1/customers", {
        "email": user["email"],
        "name": user["contact_name"],
        "metadata[user_id]": str(user["id"]),
        "metadata[hotel_name]": user["hotel_name"],
    })
    customer_id = customer["id"]
    with db() as conn:
        conn.execute("UPDATE users SET stripe_customer_id = ?, updated_at = ? WHERE id = ?", (customer_id, now_iso(), user["id"]))
    return customer_id


def sync_user_from_stripe_customer(customer_id: str, subscription_id: Optional[str], status: str) -> None:
    plan = "free"
    if status in {"active", "trialing", "past_due"} and subscription_id:
        try:
            sub = stripe_request("GET", f"/v1/subscriptions/{subscription_id}")
            items = sub.get("items", {}).get("data", [])
            if items:
                price_obj = items[0].get("price")
                price_id = price_obj.get("id", "") if isinstance(price_obj, dict) else (price_obj or "")
                if price_id == STRIPE_PRO_PLUS_PRICE_ID:
                    plan = "pro_plus"
                elif price_id in (STRIPE_MONTHLY_PRICE_ID, STRIPE_ANNUAL_PRICE_ID):
                    plan = "pro"
                else:
                    plan = "pro"
        except Exception:
            plan = "pro"
    elif status in {"active", "trialing", "past_due"}:
        plan = "pro"
    with db() as conn:
        conn.execute(
            "UPDATE users SET plan = ?, stripe_subscription_id = ?, updated_at = ? WHERE stripe_customer_id = ?",
            (plan, subscription_id, now_iso(), customer_id),
        )
