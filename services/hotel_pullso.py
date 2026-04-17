"""Hoteles Pullso: slug, miembros (admin/user), WhatsApp compartido e invitaciones por correo."""
from __future__ import annotations

import logging
import re
import secrets
import sqlite3
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional, Tuple

from fastapi import Request

from auth_session import hash_login_token
from db import db
from time_utils import now_iso

_log = logging.getLogger(__name__)

SESSION_HOTEL_KEY = "current_hotel_id"
HOTEL_WHATSAPP_MAX_NUMBERS = 3
INVITE_TTL_DAYS = 7


def _norm_email(s: str) -> str:
    return (s or "").strip().lower()


def slugify_parts(name: str, location: str, user_id: int) -> str:
    raw = f"{name}-{location}-{user_id}"
    s = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    s = (s or f"hotel-{user_id}").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return (s or f"hotel-{user_id}")[:72]


def _allocate_unique_slug(conn, name: str, location: str, user_id: int) -> str:
    base = slugify_parts(name, location, user_id)
    cand = base
    n = 2
    while True:
        row = conn.execute("SELECT 1 FROM hotels WHERE slug = ?", (cand,)).fetchone()
        if not row:
            return cand
        cand = f"{base}-{n}"
        n += 1


def migrate_legacy_users_to_hotels(conn) -> None:
    """Un hotel por usuario existente + admin; copia WhatsApp desde users; enlaza analyses."""
    users = conn.execute("SELECT id FROM users").fetchall()
    for ur in users:
        uid = int(ur["id"])
        if conn.execute("SELECT 1 FROM hotel_members WHERE user_id = ?", (uid,)).fetchone():
            continue
        u = conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
        if not u:
            continue
        name = (u["hotel_name"] or "").strip() or f"Hotel {uid}"
        loc = (u["hotel_location"] or "").strip()
        slug = _allocate_unique_slug(conn, name, loc, uid)
        wa = u["pullso_whatsapp_to"]
        opt = int(u["pullso_whatsapp_opt_in"] or 0)
        opt_at = u["pullso_whatsapp_opt_in_at"]
        cur = conn.execute(
            """
            INSERT INTO hotels (slug, display_name, pullso_whatsapp_to, pullso_whatsapp_opt_in,
                pullso_whatsapp_opt_in_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (slug, name, wa, opt, opt_at, now_iso(), now_iso()),
        )
        hid = int(cur.lastrowid)
        conn.execute(
            "INSERT INTO hotel_members (hotel_id, user_id, role) VALUES (?, ?, 'admin')",
            (hid, uid),
        )
        try:
            conn.execute(
                "UPDATE analyses SET hotel_id = ? WHERE user_id = ? AND (hotel_id IS NULL OR hotel_id = 0)",
                (hid, uid),
            )
        except Exception:
            pass


def list_hotels_for_user(user_id: int) -> List[sqlite3.Row]:
    with db() as conn:
        return conn.execute(
            """
            SELECT h.*, hm.role AS member_role
            FROM hotels h
            JOIN hotel_members hm ON hm.hotel_id = h.id
            WHERE hm.user_id = ?
            ORDER BY h.id
            """,
            (user_id,),
        ).fetchall()


def membership(conn, user_id: int, hotel_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM hotel_members WHERE user_id = ? AND hotel_id = ?",
        (user_id, hotel_id),
    ).fetchone()


def user_is_hotel_admin(user_id: int, hotel_id: int) -> bool:
    with db() as conn:
        m = membership(conn, user_id, hotel_id)
        return bool(m and (m["role"] or "").strip() == "admin")


def ensure_default_hotel_session(request: Request, user_id: int) -> None:
    """Si el usuario tiene hoteles y no hay hotel activo en sesión, elige el primero."""
    with db() as conn:
        row = conn.execute(
            """
            SELECT hotel_id FROM hotel_members WHERE user_id = ? ORDER BY hotel_id LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        if not row:
            request.session.pop(SESSION_HOTEL_KEY, None)
            return
        hid = int(row["hotel_id"])
        cur = request.session.get(SESSION_HOTEL_KEY)
        if cur is None:
            request.session[SESSION_HOTEL_KEY] = hid
            return
        try:
            cur_i = int(cur)
        except (TypeError, ValueError):
            request.session[SESSION_HOTEL_KEY] = hid
            return
        ok = conn.execute(
            "SELECT 1 FROM hotel_members WHERE user_id = ? AND hotel_id = ?",
            (user_id, cur_i),
        ).fetchone()
        if not ok:
            request.session[SESSION_HOTEL_KEY] = hid


def get_current_hotel_id(request: Request, user_id: int) -> Optional[int]:
    ensure_default_hotel_session(request, user_id)
    raw = request.session.get(SESSION_HOTEL_KEY)
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def load_hotel_row(hotel_id: int) -> Optional[Any]:
    with db() as conn:
        return conn.execute("SELECT * FROM hotels WHERE id = ?", (hotel_id,)).fetchone()


def sync_hotels_after_onboarding(request: Request, user_id: int) -> None:
    """
    Tras guardar perfil en onboarding: crea hotel si no hay membresía, o actualiza display_name
    del hotel admin objetivo (sesión actual o el de menor id).
    """
    with db() as conn:
        u = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not u:
            return
        name = (u["hotel_name"] or "").strip() or f"Hotel {user_id}"
        loc = (u["hotel_location"] or "").strip()
        hid = request.session.get(SESSION_HOTEL_KEY)
        target: Optional[int] = None
        if hid is not None:
            try:
                hid_i = int(hid)
            except (TypeError, ValueError):
                hid_i = None
            if hid_i is not None and membership(conn, user_id, hid_i) and (
                membership(conn, user_id, hid_i)["role"] or ""
            ).strip() == "admin":
                target = hid_i
        if target is None:
            row = conn.execute(
                """
                SELECT h.id FROM hotels h
                JOIN hotel_members hm ON hm.hotel_id = h.id
                WHERE hm.user_id = ? AND hm.role = 'admin'
                ORDER BY h.id LIMIT 1
                """,
                (user_id,),
            ).fetchone()
            target = int(row["id"]) if row else None
        if target is None:
            slug = _allocate_unique_slug(conn, name, loc, user_id)
            wa = u["pullso_whatsapp_to"]
            opt = int(u["pullso_whatsapp_opt_in"] or 0)
            opt_at = u["pullso_whatsapp_opt_in_at"]
            cur = conn.execute(
                """
                INSERT INTO hotels (slug, display_name, pullso_whatsapp_to, pullso_whatsapp_opt_in,
                    pullso_whatsapp_opt_in_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (slug, name, wa, opt, opt_at, now_iso(), now_iso()),
            )
            target = int(cur.lastrowid)
            conn.execute(
                "INSERT INTO hotel_members (hotel_id, user_id, role) VALUES (?, ?, 'admin')",
                (target, user_id),
            )
            request.session[SESSION_HOTEL_KEY] = target
        conn.execute(
            "UPDATE hotels SET display_name = ?, updated_at = ? WHERE id = ?",
            (name, now_iso(), target),
        )


def save_hotel_whatsapp_settings(
    hotel_id: int, user_id: int, slots: List[Dict[str, str]], opt_in: bool
) -> Optional[str]:
    """Persiste WhatsApp del hotel (JSON con nombre + teléfono); solo admin del hotel."""
    from services.pullso_whatsapp_user_delivery import (
        validate_wa_slots_and_build_blob,
        wa_slots_have_any_national_digits,
    )

    if not user_is_hotel_admin(user_id, hotel_id):
        return "forbidden"
    if not opt_in:
        if wa_slots_have_any_national_digits(slots):
            return "consent_required"
        with db() as conn:
            conn.execute(
                """
                UPDATE hotels SET pullso_whatsapp_to = NULL, pullso_whatsapp_opt_in = 0,
                pullso_whatsapp_opt_in_at = NULL, updated_at = ? WHERE id = ?
                """,
                (now_iso(), hotel_id),
            )
        return None
    blob, err = validate_wa_slots_and_build_blob(slots, HOTEL_WHATSAPP_MAX_NUMBERS)
    if err == "too_many":
        return "too_many"
    if err == "invalid_phone":
        return "invalid_phone"
    if err == "empty_recipients" or not blob:
        return "empty_recipients"
    with db() as conn:
        conn.execute(
            """
            UPDATE hotels SET pullso_whatsapp_to = ?, pullso_whatsapp_opt_in = 1,
            pullso_whatsapp_opt_in_at = ?, updated_at = ? WHERE id = ?
            """,
            (blob, now_iso(), now_iso(), hotel_id),
        )
    return None


def create_hotel_invite(
    *,
    hotel_id: int,
    inviter_user_id: int,
    invitee_email: str,
    role: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Crea invitación y devuelve (token_plano, error_code).
    error_code: forbidden | invalid_email | invalid_role | smtp_missing
    """
    if not user_is_hotel_admin(inviter_user_id, hotel_id):
        return None, "forbidden"
    em = _norm_email(invitee_email)
    if not em or "@" not in em:
        return None, "invalid_email"
    role = (role or "user").strip().lower()
    if role not in ("admin", "user"):
        return None, "invalid_role"
    raw = secrets.token_urlsafe(32)
    th = hash_login_token(raw)
    exp = (datetime.now(timezone.utc) + timedelta(days=INVITE_TTL_DAYS)).isoformat()
    with db() as conn:
        conn.execute(
            "DELETE FROM hotel_invites WHERE hotel_id = ? AND email_norm = ? AND accepted_at IS NULL",
            (hotel_id, em),
        )
        conn.execute(
            """
            INSERT INTO hotel_invites (hotel_id, email_norm, role, token_hash, expires_at, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (hotel_id, em, role, th, exp, inviter_user_id, now_iso()),
        )
    return raw, None


def accept_hotel_invite_token_with_hotel(
    raw_token: str, user_id: int, user_email: str
) -> Tuple[str, Optional[int]]:
    """
    Como accept_hotel_invite_token pero devuelve (código, hotel_id) con hotel_id si quedó vinculado.
    """
    secret = (raw_token or "").strip()
    if len(secret) < 20:
        return "not_found", None
    th = hash_login_token(secret)
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM hotel_invites WHERE token_hash = ?",
            (th,),
        ).fetchone()
        if not row:
            return "not_found", None
        if row["accepted_at"]:
            hid = int(row["hotel_id"])
            if conn.execute(
                "SELECT 1 FROM hotel_members WHERE hotel_id = ? AND user_id = ?",
                (hid, user_id),
            ).fetchone():
                return "ok", hid
            return "used", None
        exp_raw = row["expires_at"]
        try:
            exp_s = (str(exp_raw) if exp_raw is not None else "").replace("Z", "+00:00")
            exp = datetime.fromisoformat(exp_s)
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return "not_found", None
        if exp <= datetime.now(timezone.utc):
            return "expired", None
        if _norm_email(user_email) != (row["email_norm"] or ""):
            return "email_mismatch", None
        hid = int(row["hotel_id"])
        if conn.execute(
            "SELECT 1 FROM hotel_members WHERE hotel_id = ? AND user_id = ?",
            (hid, user_id),
        ).fetchone():
            conn.execute(
                "UPDATE hotel_invites SET accepted_at = ? WHERE id = ?",
                (now_iso(), row["id"]),
            )
            return "ok", hid
        conn.execute(
            "INSERT INTO hotel_members (hotel_id, user_id, role) VALUES (?, ?, ?)",
            (hid, user_id, (row["role"] or "user").strip()),
        )
        conn.execute(
            "UPDATE hotel_invites SET accepted_at = ? WHERE id = ?",
            (now_iso(), row["id"]),
        )
    return "ok", hid


def accept_hotel_invite_token(raw_token: str, user_id: int, user_email: str) -> str:
    """Vincula usuario al hotel del invite. Retorna 'ok' | 'not_found' | 'expired' | 'email_mismatch' | 'used'."""
    code, _ = accept_hotel_invite_token_with_hotel(raw_token, user_id, user_email)
    return code
