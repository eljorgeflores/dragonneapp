"""
Integración: DELETE /analysis/{id} con sesión (propietario), 404 ajeno, 401 sin login.
Ejecutar: pytest test_analysis_delete.py -v
"""
from __future__ import annotations

import json
import uuid

from fastapi.testclient import TestClient

from app import app, db
from time_utils import now_iso

client = TestClient(app)


def _unique_email() -> str:
    return f"del-t-{uuid.uuid4().hex[:12]}@example.com"


def _signup(email: str, password: str = "password123") -> None:
    client.post(
        "/signup",
        data={"email": email, "password": password, "password_confirm": password, "accept_legal": "1"},
        follow_redirects=True,
    )


def _onboarding_data() -> dict:
    return {
        "hotel_name": "Hotel Delete Test",
        "contact_name": "Tester",
        "hotel_size": "pequeño (<=40 llaves)",
        "hotel_category": "boutique",
        "hotel_location": "CDMX",
    }


def _user_id(email: str) -> int:
    with db() as conn:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        assert row is not None
        return int(row["id"])


def _insert_minimal_analysis(user_id: int) -> int:
    ts = now_iso()
    summary = {"reports_detected": 1, "total_files": 1, "overall_days_covered": 7, "max_days_covered": 7}
    analysis = {"resumen_ejecutivo": "Mínimo para prueba de borrado."}
    with db() as conn:
        cur = conn.execute(
            """
            INSERT INTO analyses (
                user_id, title, plan_at_analysis, file_count, days_covered,
                summary_json, analysis_json, created_at, share_token
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)
            """,
            (
                user_id,
                "Lectura de prueba borrado",
                "free",
                1,
                7,
                json.dumps(summary, ensure_ascii=False),
                json.dumps(analysis, ensure_ascii=False),
                ts,
            ),
        )
        return int(cur.lastrowid)


def _login(client_: TestClient, email: str, password: str = "password123") -> None:
    r = client_.post("/login", data={"email": email, "password": password}, follow_redirects=False)
    assert r.status_code in (302, 303), r.text


def test_delete_owned_analysis_returns_ok_and_removes_row():
    email = _unique_email()
    _signup(email)
    client.post("/onboarding", data=_onboarding_data(), follow_redirects=True)
    uid = _user_id(email)
    aid = _insert_minimal_analysis(uid)

    _login(client, email)
    r = client.delete(f"/analysis/{aid}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("ok") is True

    with db() as conn:
        row = conn.execute("SELECT id FROM analyses WHERE id = ?", (aid,)).fetchone()
        assert row is None


def test_delete_analysis_returns_404_for_other_users_analysis():
    c_owner = TestClient(app)
    c_other = TestClient(app)
    e_owner = _unique_email()
    e_other = _unique_email()
    c_owner.post(
        "/signup",
        data={
            "email": e_owner,
            "password": "password123",
            "password_confirm": "password123",
            "accept_legal": "1",
        },
        follow_redirects=True,
    )
    c_owner.post("/onboarding", data=_onboarding_data(), follow_redirects=True)
    uid_owner = _user_id(e_owner)
    aid = _insert_minimal_analysis(uid_owner)

    c_other.post(
        "/signup",
        data={
            "email": e_other,
            "password": "password123",
            "password_confirm": "password123",
            "accept_legal": "1",
        },
        follow_redirects=True,
    )
    c_other.post("/onboarding", data=_onboarding_data(), follow_redirects=True)

    _login(c_other, e_other)
    r = c_other.delete(f"/analysis/{aid}")
    assert r.status_code == 404, r.text
    assert r.json().get("ok") is False

    with db() as conn:
        row = conn.execute("SELECT id FROM analyses WHERE id = ?", (aid,)).fetchone()
        assert row is not None


def test_delete_analysis_requires_session():
    email = _unique_email()
    _signup(email)
    client.post("/onboarding", data=_onboarding_data(), follow_redirects=True)
    uid = _user_id(email)
    aid = _insert_minimal_analysis(uid)

    anon = TestClient(app)
    r = anon.delete(f"/analysis/{aid}")
    assert r.status_code == 401

    with db() as conn:
        row = conn.execute("SELECT id FROM analyses WHERE id = ?", (aid,)).fetchone()
        assert row is not None
