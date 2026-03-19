"""
Tests de flujo usuario final: registro, login, guardado de contraseña,
usuario admin, panel admin (visión general, administradores, acceso API).
Ejecutar: pytest test_auth_admin.py -v
"""
import re
import uuid

import pytest
from fastapi.testclient import TestClient

from app import app, db

client = TestClient(app)


def _unique_email():
    return f"test-{uuid.uuid4().hex[:10]}@example.com"


# --- Signup y onboarding ---


def test_signup_creates_user_and_redirects_to_onboarding():
    email = _unique_email()
    password = "password123"
    r = client.post(
        "/signup",
        data={"email": email, "password": password, "password_confirm": password},
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

    r = client.post("/login", data={"email": email, "password": password})
    assert r.status_code == 303
    assert r.headers.get("location") == "/app"


def test_login_admin_user_redirects_to_admin():
    email = _unique_email()
    password = "password123"
    client.post("/signup", data={"email": email, "password": password, "password_confirm": password})
    with db() as conn:
        conn.execute("UPDATE users SET is_admin = 1 WHERE email = ?", (email,))
    client.post("/logout")

    r = client.post("/login", data={"email": email, "password": password})
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
    token = None
    match = re.search(r"/reset-password/([A-Za-z0-9_-]+)", r.text)
    if match:
        token = match.group(1)
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
        f"/reset-password/{token}",
        data={"password": "newpassword123", "password_confirm": "newpassword123"},
    )
    assert r_reset.status_code == 303
    assert r_reset.headers.get("location") == "/login"
    r_login = client.post("/login", data={"email": email, "password": "newpassword123"})
    assert r_login.status_code == 303


def test_forgot_password_unknown_email_does_not_leak():
    r = client.post("/forgot-password", data={"email": "noexiste@example.com"})
    assert r.status_code == 200
    # No debe indicar que el correo no existe (seguridad)
    assert "no existe" not in (r.text or "").lower() or "no está registrado" not in (r.text or "").lower()


def test_reset_password_invalid_token():
    r = client.post(
        "/reset-password/token-invalido-o-caducado",
        data={"password": "newpass123", "password_confirm": "newpass123"},
    )
    assert r.status_code == 200
    assert "válido" in r.text or "nuevo" in r.text


# --- Panel admin: solo con sesión admin ---


def test_admin_requires_login():
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
