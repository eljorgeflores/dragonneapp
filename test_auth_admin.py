"""
Tests de flujo usuario final: registro, login, guardado de contraseña,
usuario admin, panel admin (visión general, administradores, acceso API).
Ejecutar: pytest test_auth_admin.py -v
"""
import re
import uuid

import pytest
from fastapi.testclient import TestClient

import config
import templating
from app import app, db

client = TestClient(app)


def test_health_config_smtp_flags():
    r = client.get("/health/config")
    assert r.status_code == 200
    data = r.json()
    for key in (
        "smtp_configured",
        "smtp_host_set",
        "smtp_user_set",
        "smtp_password_set",
        "smtp_envelope_configured",
        "smtp_security",
        "smtp_port",
    ):
        assert key in data
    assert "smtp_tcp_reachable" not in data


def test_health_config_smtp_probe_adds_tcp_flag():
    r = client.get("/health/config?smtp_probe=true")
    assert r.status_code == 200
    data = r.json()
    assert "smtp_tcp_reachable" in data
    assert data["smtp_tcp_reachable"] in (None, True, False)


def _unique_email():
    return f"test-{uuid.uuid4().hex[:10]}@example.com"


def test_url_path_respects_prefix(monkeypatch):
    monkeypatch.setattr(config, "URL_PREFIX", "/sub")
    assert config.url_path("/login") == "/sub/login"
    assert config.url_path("/forgot-password?x=1") == "/sub/forgot-password?x=1"


def test_internal_path_strips_prefix(monkeypatch):
    monkeypatch.setattr(config, "URL_PREFIX", "/sub")
    assert config.internal_path("/sub/app") == "/app"
    assert config.internal_path("/sub") == "/"
    assert config.internal_path("/app") == "/app"


def test_forgot_password_page_form_action_respects_prefix(monkeypatch):
    monkeypatch.setattr(config, "URL_PREFIX", "/sub")
    monkeypatch.setitem(templating.templates.env.globals, "url_prefix", "/sub")
    r = client.get("/forgot-password")
    assert r.status_code == 200
    assert 'action="/sub/forgot-password"' in r.text


def test_401_html_redirect_respects_url_prefix(monkeypatch):
    """Sin sesión: /app + Accept HTML debe redirigir a login con URL_PREFIX en Location."""
    monkeypatch.setattr(config, "URL_PREFIX", "/sub")
    r = client.get("/app", headers={"Accept": "text/html"}, follow_redirects=False)
    assert r.status_code == 303
    loc = r.headers.get("location") or ""
    assert loc.startswith("/sub/login")
    assert "next=%2Fapp" in loc or "next=/app" in loc


def _extract_reset_token_from_html(html: str) -> str | None:
    if not html:
        return None
    m = re.search(r"reset-password\?token=([A-Za-z0-9_-]+)", html)
    if m:
        return m.group(1)
    m = re.search(r"/reset-password/([A-Za-z0-9_-]+)", html)
    if m:
        return m.group(1)
    return None


# --- Signup y onboarding ---


def test_signup_creates_user_and_redirects_to_onboarding():
    email = _unique_email()
    password = "password123"
    r = client.post(
        "/signup",
        data={"email": email, "password": password, "password_confirm": password},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers.get("location") == "/onboarding"
    # Sesión activa
    r_app = client.get("/onboarding", follow_redirects=False)
    assert r_app.status_code == 200


def test_signup_password_too_short():
    email = _unique_email()
    r = client.post(
        "/signup",
        data={"email": email, "password": "short", "password_confirm": "short"},
    )
    assert r.status_code == 400
    assert "8 caracteres" in (r.text or "")


def test_signup_password_mismatch():
    email = _unique_email()
    r = client.post(
        "/signup",
        data={"email": email, "password": "password123", "password_confirm": "other123"},
    )
    assert r.status_code == 400
    assert "no coinciden" in (r.text or "")


def test_signup_duplicate_email():
    email = _unique_email()
    password = "password123"
    client.post("/signup", data={"email": email, "password": password, "password_confirm": password})
    r = client.post("/signup", data={"email": email, "password": password, "password_confirm": password})
    assert r.status_code == 400
    assert "ya está registrado" in (r.text or "")


# --- Login normal y admin ---


def test_login_normal_user_redirects_to_app():
    email = _unique_email()
    password = "password123"
    client.post("/signup", data={"email": email, "password": password, "password_confirm": password})
    # Completar onboarding para que no redirija a /onboarding al ir a /app
    onboarding = {
        "hotel_name": "Hotel Test",
        "contact_name": "Tester",
        "hotel_size": "pequeño (<=40 llaves)",
        "hotel_category": "boutique",
        "hotel_location": "Ciudad Test",
    }
    client.post("/onboarding", data=onboarding)
    client.post("/logout")

    r = client.post("/login", data={"email": email, "password": password}, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers.get("location") == "/app"


def test_login_admin_user_redirects_to_admin():
    email = _unique_email()
    password = "password123"
    client.post("/signup", data={"email": email, "password": password, "password_confirm": password})
    with db() as conn:
        conn.execute("UPDATE users SET is_admin = 1 WHERE email = ?", (email,))
    client.post("/logout")

    r = client.post("/login", data={"email": email, "password": password}, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers.get("location") == "/admin"


def test_login_wrong_password():
    email = _unique_email()
    password = "password123"
    client.post("/signup", data={"email": email, "password": password, "password_confirm": password})
    client.post("/logout")

    r = client.post("/login", data={"email": email, "password": "wrongpassword"})
    assert r.status_code == 400
    assert "incorrectos" in (r.text or "")


# --- Recordar contraseña (forgot + reset) ---


def test_forgot_password_and_reset_flow():
    """Solicitar reset, obtener token (desde HTML o DB) y cambiar contraseña."""
    email = _unique_email()
    password = "password123"
    client.post("/signup", data={"email": email, "password": password, "password_confirm": password})
    client.post("/logout")

    r = client.post("/forgot-password", data={"email": email})
    assert r.status_code == 200
    token = _extract_reset_token_from_html(r.text)
    if not token:
        # SMTP envió el correo y el link no está en HTML; obtenemos el token de la BD
        with db() as conn:
            user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            assert user
            row = conn.execute(
                "SELECT token FROM password_resets WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                (user["id"],),
            ).fetchone()
            assert row
            token = row["token"]
    r_reset = client.post(
        "/reset-password",
        data={
            "token": token,
            "password": "newpassword123",
            "password_confirm": "newpassword123",
        },
        follow_redirects=False,
    )
    assert r_reset.status_code == 303
    assert r_reset.headers.get("location") == "/login"
    r_login = client.post(
        "/login", data={"email": email, "password": "newpassword123"}, follow_redirects=False
    )
    assert r_login.status_code == 303


def test_forgot_password_unknown_email_does_not_leak():
    r = client.post("/forgot-password", data={"email": "noexiste@example.com"})
    assert r.status_code == 200
    # No debe indicar que el correo no existe (seguridad)
    assert "no existe" not in (r.text or "").lower() or "no está registrado" not in (r.text or "").lower()


def test_forgot_password_finds_legacy_email_trim_case():
    """Correo en BD con espacios / mayúsculas debe coincidir con el tecleado normalizado."""
    email = _unique_email()
    password = "password123"
    client.post(
        "/signup",
        data={"email": email, "password": password, "password_confirm": password},
    )
    with db() as conn:
        conn.execute(
            "UPDATE users SET email = ? WHERE email = ?",
            (f"  {email.upper()}  ", email),
        )
    client.post("/logout")
    r = client.post("/forgot-password", data={"email": email})
    assert r.status_code == 200
    # Sin SMTP suele mostrarse el enlace en página (?token= o ruta legacy)
    assert "reset-password" in (r.text or "") and (
        "token=" in (r.text or "") or "/reset-password/" in (r.text or "")
    )


def test_reset_password_get_without_query_redirects():
    r = client.get("/reset-password", follow_redirects=False)
    assert r.status_code == 303
    loc = r.headers.get("location") or ""
    assert "/forgot-password" in loc
    assert "incomplete_link" in loc


def test_reset_password_invalid_token():
    r = client.post(
        "/reset-password",
        data={
            "token": "token-invalido-o-caducado",
            "password": "newpass123",
            "password_confirm": "newpass123",
        },
    )
    assert r.status_code == 200
    assert "válido" in r.text or "nuevo" in r.text


def test_reset_password_expired_token_rejected():
    email = _unique_email()
    password = "password123"
    client.post("/signup", data={"email": email, "password": password, "password_confirm": password})
    client.post("/logout")
    client.post("/forgot-password", data={"email": email})
    with db() as conn:
        row = conn.execute(
            """
            SELECT pr.token FROM password_resets pr
            JOIN users u ON u.id = pr.user_id
            WHERE LOWER(TRIM(u.email)) = ?
            ORDER BY pr.id DESC LIMIT 1
            """,
            (email,),
        ).fetchone()
    assert row
    token = row["token"]
    with db() as conn:
        conn.execute(
            "UPDATE password_resets SET expires_at = ? WHERE token = ?",
            ("2000-01-01T00:00:00+00:00", token),
        )
    r = client.post(
        "/reset-password",
        data={
            "token": token,
            "password": "newpass999",
            "password_confirm": "newpass999",
        },
    )
    assert r.status_code == 200
    assert "válido" in (r.text or "").lower()
    r_ok = client.post("/login", data={"email": email, "password": password}, follow_redirects=False)
    assert r_ok.status_code == 303


def test_delete_user_removes_password_resets():
    email_target = _unique_email()
    email_admin = _unique_email()
    password = "password123"
    client.post(
        "/signup",
        data={"email": email_target, "password": password, "password_confirm": password},
    )
    client.post("/logout")
    client.post(
        "/signup",
        data={"email": email_admin, "password": password, "password_confirm": password},
    )
    with db() as conn:
        conn.execute("UPDATE users SET is_admin = 1 WHERE email = ?", (email_admin,))
        uid_target = conn.execute("SELECT id FROM users WHERE email = ?", (email_target,)).fetchone()["id"]
    client.post("/forgot-password", data={"email": email_target})
    with db() as conn:
        n = conn.execute(
            "SELECT COUNT(*) AS c FROM password_resets WHERE user_id = ?",
            (uid_target,),
        ).fetchone()["c"]
    assert n >= 1
    client.post("/logout")
    client.post("/login", data={"email": email_admin, "password": password})
    r_del = client.post(f"/admin/users/{uid_target}/delete", follow_redirects=False)
    assert r_del.status_code == 303
    with db() as conn:
        n2 = conn.execute(
            "SELECT COUNT(*) AS c FROM password_resets WHERE user_id = ?",
            (uid_target,),
        ).fetchone()["c"]
    assert n2 == 0


def test_admin_send_password_reset_without_smtp_redirects():
    email_admin = _unique_email()
    email_other = _unique_email()
    password = "password123"
    client.post(
        "/signup",
        data={"email": email_other, "password": password, "password_confirm": password},
    )
    with db() as conn:
        uid_other = conn.execute("SELECT id FROM users WHERE email = ?", (email_other,)).fetchone()["id"]
    client.post("/logout")
    client.post(
        "/signup",
        data={"email": email_admin, "password": password, "password_confirm": password},
    )
    with db() as conn:
        conn.execute("UPDATE users SET is_admin = 1 WHERE email = ?", (email_admin,))
    client.post("/logout")
    client.post("/login", data={"email": email_admin, "password": password})
    r = client.post(f"/admin/users/{uid_other}/send-password-reset", follow_redirects=False)
    assert r.status_code == 303
    assert "pwd_reset=smtp" in (r.headers.get("location") or "")


def test_admin_send_password_reset_requires_admin():
    email_user = _unique_email()
    email_other = _unique_email()
    password = "password123"
    client.post(
        "/signup",
        data={"email": email_other, "password": password, "password_confirm": password},
    )
    with db() as conn:
        uid_other = conn.execute("SELECT id FROM users WHERE email = ?", (email_other,)).fetchone()["id"]
    client.post("/logout")
    client.post(
        "/signup",
        data={"email": email_user, "password": password, "password_confirm": password},
    )
    onboarding = {
        "hotel_name": "Hotel",
        "contact_name": "Tester",
        "hotel_size": "pequeño (<=40 llaves)",
        "hotel_category": "boutique",
        "hotel_location": "X",
    }
    client.post("/onboarding", data=onboarding)
    r = client.post(f"/admin/users/{uid_other}/send-password-reset", follow_redirects=False)
    assert r.status_code == 403


# --- Panel admin: solo con sesión admin ---


def test_admin_requires_login():
    client.cookies.clear()
    r = client.get("/admin", follow_redirects=False)
    assert r.status_code in (302, 303)
    assert "/login" in (r.headers.get("location") or "")


def test_admin_requires_admin_role():
    """Usuario normal no puede entrar a /admin."""
    email = _unique_email()
    password = "password123"
    client.post("/signup", data={"email": email, "password": password, "password_confirm": password})
    onboarding = {
        "hotel_name": "Hotel",
        "contact_name": "Tester",
        "hotel_size": "pequeño (<=40 llaves)",
        "hotel_category": "boutique",
        "hotel_location": "X",
    }
    client.post("/onboarding", data=onboarding)
    # Sin is_admin=1
    r = client.get("/admin", follow_redirects=False)
    assert r.status_code == 403


def test_admin_home_ok_when_admin():
    email = _unique_email()
    password = "password123"
    client.post("/signup", data={"email": email, "password": password, "password_confirm": password})
    with db() as conn:
        conn.execute("UPDATE users SET is_admin = 1 WHERE email = ?", (email,))
    client.post("/login", data={"email": email, "password": password})

    r = client.get("/admin")
    assert r.status_code == 200
    assert "Panel admin" in r.text or "admin" in r.text
    assert "Hoteles" in r.text or "usuarios" in r.text


def test_admin_admins_page():
    email = _unique_email()
    password = "password123"
    client.post("/signup", data={"email": email, "password": password, "password_confirm": password})
    with db() as conn:
        conn.execute("UPDATE users SET is_admin = 1 WHERE email = ?", (email,))
    client.post("/login", data={"email": email, "password": password})

    r = client.get("/admin/admins")
    assert r.status_code == 200
    assert "Administradores" in r.text or "admin" in r.text


def test_admin_api_page():
    email = _unique_email()
    password = "password123"
    client.post("/signup", data={"email": email, "password": password, "password_confirm": password})
    with db() as conn:
        conn.execute("UPDATE users SET is_admin = 1 WHERE email = ?", (email,))
    client.post("/login", data={"email": email, "password": password})

    r = client.get("/admin/api")
    assert r.status_code == 200
    assert "API" in r.text or "Acceso" in r.text


# --- Logout ---


def test_logout_clears_session():
    email = _unique_email()
    password = "password123"
    client.post("/signup", data={"email": email, "password": password, "password_confirm": password})
    r_before = client.get("/app", follow_redirects=False)
    assert r_before.status_code in (200, 303)

    client.post("/logout")
    r_after = client.get("/app", follow_redirects=False)
    assert r_after.status_code in (302, 303)
    assert "/login" in (r_after.headers.get("location") or "")
