"""
Tests: login con magic link (token hash, un solo uso, caducidad) y compatibilidad con login por contraseña.
"""
import uuid

from fastapi.testclient import TestClient

import config
import email_smtp
from app import app, db
from auth_session import (
    MagicLinkConsumeResult,
    consume_magic_link_token,
    create_magic_link_token,
    hash_login_token,
    magic_link_rate_limiter,
)
from time_utils import now_iso

client = TestClient(app)


def _unique_email():
    return f"ml-{uuid.uuid4().hex[:10]}@example.com"


def _signup_and_onboard(email: str, password: str):
    client.post(
        "/signup",
        data={"email": email, "password": password, "password_confirm": password, "accept_legal": "1"},
        follow_redirects=True,
    )
    client.post(
        "/onboarding",
        data={
            "hotel_name": "Hotel ML",
            "contact_name": "Tester",
            "hotel_size": "pequeño (<=40 llaves)",
            "hotel_category": "boutique",
            "hotel_location": "X",
        },
    )
    client.post("/logout", follow_redirects=True)


def test_hash_login_token_stable():
    h = hash_login_token("abc")
    assert len(h) == 64
    assert hash_login_token("abc") == h


def test_consume_magic_link_happy_path():
    email = _unique_email()
    with db() as conn:
        conn.execute(
            """
            INSERT INTO users (hotel_name, contact_name, email, password_hash, plan, created_at, updated_at)
            VALUES ('H', 'C', ?, 'x', 'free', ?, ?)
            """,
            (email, now_iso(), now_iso()),
        )
        uid = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()["id"]
    raw = create_magic_link_token(uid, requested_ip="1.2.3.4", user_agent="pytest")
    res, got_uid = consume_magic_link_token(raw)
    assert res == MagicLinkConsumeResult.OK
    assert got_uid == uid
    res2, _ = consume_magic_link_token(raw)
    assert res2 == MagicLinkConsumeResult.ALREADY_USED


def test_consume_magic_link_expired():
    email = _unique_email()
    with db() as conn:
        conn.execute(
            """
            INSERT INTO users (hotel_name, contact_name, email, password_hash, plan, created_at, updated_at)
            VALUES ('H', 'C', ?, 'x', 'free', ?, ?)
            """,
            (email, now_iso(), now_iso()),
        )
        uid = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()["id"]
    raw = create_magic_link_token(uid)
    th = hash_login_token(raw)
    with db() as conn:
        conn.execute(
            "UPDATE login_tokens SET expires_at = ? WHERE token_hash = ?",
            ("2000-01-01T00:00:00+00:00", th),
        )
    res, _ = consume_magic_link_token(raw)
    assert res == MagicLinkConsumeResult.EXPIRED


def test_request_magic_link_unknown_email_neutral(monkeypatch):
    monkeypatch.setattr(email_smtp, "_send_via_resend", lambda *a, **k: True)
    r = client.post("/login/magic-link", data={"email": "noexist-zz@example.com"})
    assert r.status_code == 200
    assert "Si existe una cuenta para este correo" in (r.text or "")
    assert "no está registrado" not in (r.text or "").lower()


def test_request_magic_link_existing_user_sends_email(monkeypatch):
    monkeypatch.setattr(config, "RESEND_API_KEY", "re_test", raising=False)
    monkeypatch.setattr(config, "EMAIL_FROM", "DRAGONNÉ <onboarding@resend.dev>", raising=False)
    sent = {"n": 0}

    def _stub_send(to, subj, text, html, **kwargs):
        sent["n"] += 1
        assert "login/magic-link/consume" in text
        assert to.endswith("@example.com")
        return True

    monkeypatch.setattr(email_smtp, "_send_via_resend", _stub_send)
    email = _unique_email()
    password = "password123"
    client.post(
        "/signup",
        data={"email": email, "password": password, "password_confirm": password, "accept_legal": "1"},
        follow_redirects=True,
    )
    client.post("/logout", follow_redirects=True)
    r = client.post("/login/magic-link", data={"email": email})
    assert r.status_code == 200
    assert sent["n"] == 1
    assert "Si existe una cuenta para este correo" in (r.text or "")
    with db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM login_tokens WHERE user_id = (SELECT id FROM users WHERE email = ?)",
            (email,),
        ).fetchone()
    assert row["c"] == 1


def test_magic_link_consume_logs_in_and_single_use():
    email = _unique_email()
    password = "password123"
    _signup_and_onboard(email, password)
    with db() as conn:
        uid = conn.execute("SELECT id FROM users WHERE LOWER(TRIM(email)) = ?", (email,)).fetchone()["id"]
    raw = create_magic_link_token(uid)
    r = client.get(f"/login/magic-link/consume?token={raw}", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers.get("location") == "/app"
    r_app = client.get("/app", follow_redirects=False)
    assert r_app.status_code == 200
    r2 = client.get(f"/login/magic-link/consume?token={raw}", follow_redirects=False)
    assert r2.status_code == 303
    assert "magic_link_error=1" in (r2.headers.get("location") or "")


def test_magic_link_next_open_redirect_rejected():
    email = _unique_email()
    password = "password123"
    _signup_and_onboard(email, password)
    with db() as conn:
        uid = conn.execute("SELECT id FROM users WHERE LOWER(TRIM(email)) = ?", (email,)).fetchone()["id"]
    raw = create_magic_link_token(uid)
    r = client.get(
        f"/login/magic-link/consume?token={raw}&next=https://evil.test/phish",
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers.get("location") == "/app"


def test_magic_link_consume_invalid_token_redirects_login():
    r = client.get("/login/magic-link/consume?token=not-a-real-token-at-all-xx", follow_redirects=False)
    assert r.status_code == 303
    assert "magic_link_error=1" in (r.headers.get("location") or "")


def test_magic_link_path_variant_consume():
    email = _unique_email()
    password = "password123"
    _signup_and_onboard(email, password)
    with db() as conn:
        uid = conn.execute("SELECT id FROM users WHERE LOWER(TRIM(email)) = ?", (email,)).fetchone()["id"]
    raw = create_magic_link_token(uid)
    r = client.get(f"/login/magic-link/consume/{raw}", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers.get("location") == "/app"


def test_magic_link_rate_limit_neutral_response(monkeypatch):
    monkeypatch.setattr(magic_link_rate_limiter, "max_per_email", 1)
    monkeypatch.setattr(magic_link_rate_limiter, "max_per_ip", 1000)
    with magic_link_rate_limiter._lock:
        magic_link_rate_limiter._by_email.clear()
        magic_link_rate_limiter._by_ip.clear()
    email = _unique_email()
    client.post("/login/magic-link", data={"email": email})
    r = client.post("/login/magic-link", data={"email": email})
    assert r.status_code == 200
    assert "Si existe una cuenta" in (r.text or "")


def test_password_login_and_logout_still_work():
    email = _unique_email()
    password = "password123"
    _signup_and_onboard(email, password)
    r = client.post("/login", data={"email": email, "password": password}, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers.get("location") == "/app"
    client.post("/logout", follow_redirects=True)
    r_after = client.get("/app", follow_redirects=False)
    assert r_after.status_code in (302, 303)


def test_login_page_shows_magic_link_primary():
    r = client.get("/login")
    assert r.status_code == 200
    assert "Enviar enlace de acceso" in r.text
    assert "/login/magic-link" in r.text
    assert "Entrar con contraseña" in r.text


def test_delete_user_removes_login_tokens():
    email_target = _unique_email()
    email_admin = _unique_email()
    password = "password123"
    client.post(
        "/signup",
        data={"email": email_target, "password": password, "password_confirm": password, "accept_legal": "1"},
    )
    with db() as conn:
        uid_target = conn.execute("SELECT id FROM users WHERE email = ?", (email_target,)).fetchone()["id"]
    create_magic_link_token(uid_target)
    with db() as conn:
        n = conn.execute(
            "SELECT COUNT(*) AS c FROM login_tokens WHERE user_id = ?",
            (uid_target,),
        ).fetchone()["c"]
    assert n >= 1
    client.post("/logout")
    client.post(
        "/signup",
        data={"email": email_admin, "password": password, "password_confirm": password, "accept_legal": "1"},
    )
    with db() as conn:
        conn.execute("UPDATE users SET is_admin = 1 WHERE email = ?", (email_admin,))
    client.post("/logout")
    client.post("/login", data={"email": email_admin, "password": password})
    client.post(f"/admin/users/{uid_target}/delete", follow_redirects=False)
    with db() as conn:
        n2 = conn.execute(
            "SELECT COUNT(*) AS c FROM login_tokens WHERE user_id = ?",
            (uid_target,),
        ).fetchone()["c"]
    assert n2 == 0
