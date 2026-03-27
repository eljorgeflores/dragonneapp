"""
Tests explícitos: plan efectivo, overrides manuales, API /me, admin override, enforce_plan.

Mapa rápido → tests:
  A1–A3, A4, A8: effective_* (+ paid_pro + manual pro_plus)
  A5–A6: expired override
  A7: override sin expiración / futura
  B9: update_billing_plan_does_not_clear_manual
  B10: billing_raises_effective_* / api me pro_plus case
  B11: remove_override_dict / admin clear
  C12–C14: api_v1_me_*
  D15–D16: admin_manual_override_* 
  D17: effective_plan_expired_* (fila histórica + stored_manual_override_plan)
  E18–E19: enforce_plan_free_billing_with_pro_override / pro_plus_billing
  E20–F21: post_analyze_response_* / enforce_plan_matches_*

Ejecutar solo este archivo:
  pytest test_plan_entitlements.py -v
"""
from __future__ import annotations

import io
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import app, db
from plan_entitlements import (
    get_active_manual_plan,
    get_effective_plan,
    get_paid_plan,
    manual_override_is_configured,
    stored_manual_override_plan,
)
from services.analysis_core import enforce_plan, user_row_as_dict

client = TestClient(app)


def _unique_email() -> str:
    return f"plan-t-{uuid.uuid4().hex[:12]}@example.com"


def _iso_utc_future() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=400)).replace(microsecond=0).isoformat()


def _iso_utc_past() -> str:
    return "2000-01-01T00:00:00+00:00"


def _signup(email: str, password: str = "password123") -> None:
    client.post(
        "/signup",
        data={"email": email, "password": password, "password_confirm": password},
        follow_redirects=True,
    )


def _onboarding_complete() -> dict:
    return {
        "hotel_name": "Hotel Plan Test",
        "contact_name": "Tester",
        "hotel_size": "pequeño (<=40 llaves)",
        "hotel_category": "boutique",
        "hotel_location": "CDMX",
    }


def _user_id_by_email(email: str) -> int:
    with db() as conn:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        assert row
        return int(row["id"])


def _fetch_user_row(uid: int):
    with db() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()


# --- A. Resolución de plan efectivo (dict / sin BD) ---


def test_effective_plan_free_plus_manual_pro_is_pro():
    u = {"plan": "free", "manual_plan_override": "pro", "manual_plan_expires_at": None}
    assert get_effective_plan(u) == "pro"


def test_effective_plan_free_plus_manual_pro_plus_is_pro_plus():
    u = {"plan": "free", "manual_plan_override": "pro_plus", "manual_plan_expires_at": None}
    assert get_effective_plan(u) == "pro_plus"


def test_effective_plan_paid_pro_plus_manual_pro_stays_pro_plus_no_downgrade():
    u = {
        "plan": "pro_plus",
        "manual_plan_override": "pro",
        "manual_plan_expires_at": None,
    }
    assert get_effective_plan(u) == "pro_plus"


def test_effective_plan_paid_pro_plus_manual_pro_plus_stays_pro_plus():
    u = {
        "plan": "pro_plus",
        "manual_plan_override": "pro_plus",
        "manual_plan_expires_at": None,
    }
    assert get_effective_plan(u) == "pro_plus"


def test_effective_plan_paid_pro_manual_pro_plus_is_pro_plus():
    u = {"plan": "pro", "manual_plan_override": "pro_plus", "manual_plan_expires_at": None}
    assert get_effective_plan(u) == "pro_plus"


def test_effective_plan_expired_override_free_billing_returns_free():
    u = {
        "plan": "free",
        "manual_plan_override": "pro_plus",
        "manual_plan_expires_at": _iso_utc_past(),
    }
    assert get_active_manual_plan(u) is None
    assert get_effective_plan(u) == "free"


def test_effective_plan_expired_override_pro_billing_returns_pro():
    u = {
        "plan": "pro",
        "manual_plan_override": "pro_plus",
        "manual_plan_expires_at": _iso_utc_past(),
    }
    assert get_active_manual_plan(u) is None
    assert get_effective_plan(u) == "pro"
    assert stored_manual_override_plan(u) == "pro_plus"
    assert manual_override_is_configured(u) is True


def test_effective_plan_override_no_expiry_stays_active():
    u = {
        "plan": "free",
        "manual_plan_override": "pro",
        "manual_plan_expires_at": None,
    }
    assert get_active_manual_plan(u) == "pro"
    assert get_effective_plan(u) == "pro"


def test_effective_plan_override_future_expiry_stays_active():
    u = {
        "plan": "free",
        "manual_plan_override": "pro",
        "manual_plan_expires_at": _iso_utc_future(),
    }
    assert get_active_manual_plan(u) == "pro"


def test_effective_plan_no_override_matches_billing():
    assert get_effective_plan({"plan": "free"}) == "free"
    assert get_effective_plan({"plan": "pro"}) == "pro"
    assert get_effective_plan({"plan": "pro_plus"}) == "pro_plus"


def test_paid_plan_is_only_users_plan_column_semantics():
    u = {"plan": "pro_plus", "manual_plan_override": "pro"}
    assert get_paid_plan(u) == "pro_plus"


# --- B. Persistencia billing vs manual ---


def test_update_billing_plan_does_not_clear_manual_override_columns():
    email = _unique_email()
    _signup(email)
    uid = _user_id_by_email(email)
    note = "cortesía QA"
    with db() as conn:
        conn.execute(
            """
            UPDATE users SET
              manual_plan_override = ?,
              manual_plan_expires_at = ?,
              manual_plan_note = ?
            WHERE id = ?
            """,
            ("pro_plus", None, note, uid),
        )
        conn.execute("UPDATE users SET plan = ? WHERE id = ?", ("pro", uid))
    with db() as conn:
        row = conn.execute(
            "SELECT plan, manual_plan_override, manual_plan_note FROM users WHERE id = ?",
            (uid,),
        ).fetchone()
    assert row["plan"] == "pro"
    assert row["manual_plan_override"] == "pro_plus"
    assert row["manual_plan_note"] == note


def test_billing_raises_effective_when_override_inferior():
    u = {"plan": "pro_plus", "manual_plan_override": "pro", "manual_plan_expires_at": None}
    assert get_effective_plan(u) == "pro_plus"


def test_remove_override_dict_effective_equals_billing():
    """Sin columnas manual => solo billing (comportamiento lógico previo a fila con NULL)."""
    u = {"plan": "pro", "manual_plan_override": None, "manual_plan_expires_at": None}
    assert get_effective_plan(u) == "pro"


# --- C. API /api/v1/me ---


def test_api_v1_me_plan_and_billing_plan_match_base_effective_matches_all_when_no_override():
    email = _unique_email()
    _signup(email)
    client.post("/onboarding", data=_onboarding_complete(), follow_redirects=True)
    uid = _user_id_by_email(email)
    api_key = f"k-{uuid.uuid4().hex}"
    with db() as conn:
        conn.execute("UPDATE users SET api_key = ? WHERE id = ?", (api_key, uid))
    r = client.get("/api/v1/me", headers={"X-API-Key": api_key})
    assert r.status_code == 200
    j = r.json()
    assert j["plan"] == "free"
    assert j["billing_plan"] == "free"
    assert j["effective_plan"] == "free"


def test_api_v1_me_with_active_override_plan_differs_from_effective_when_applicable():
    email = _unique_email()
    _signup(email)
    client.post("/onboarding", data=_onboarding_complete(), follow_redirects=True)
    uid = _user_id_by_email(email)
    api_key = f"k-{uuid.uuid4().hex}"
    with db() as conn:
        conn.execute(
            """
            UPDATE users SET api_key = ?, manual_plan_override = ?, manual_plan_expires_at = ?
            WHERE id = ?
            """,
            (api_key, "pro_plus", None, uid),
        )
    r = client.get("/api/v1/me", headers={"X-API-Key": api_key})
    assert r.status_code == 200
    j = r.json()
    assert j["plan"] == "free"
    assert j["billing_plan"] == "free"
    assert j["effective_plan"] == "pro_plus"
    assert j["plan"] != j["effective_plan"]


def test_api_v1_me_paid_pro_plus_override_pro_effective_stays_pro_plus():
    email = _unique_email()
    _signup(email)
    client.post("/onboarding", data=_onboarding_complete(), follow_redirects=True)
    uid = _user_id_by_email(email)
    api_key = f"k-{uuid.uuid4().hex}"
    with db() as conn:
        conn.execute(
            """
            UPDATE users SET plan = ?, api_key = ?, manual_plan_override = ?, manual_plan_expires_at = ?
            WHERE id = ?
            """,
            ("pro_plus", api_key, "pro", None, uid),
        )
    r = client.get("/api/v1/me", headers={"X-API-Key": api_key})
    j = r.json()
    assert j["plan"] == "pro_plus"
    assert j["billing_plan"] == "pro_plus"
    assert j["effective_plan"] == "pro_plus"


# --- D. Admin override flow ---


def test_admin_manual_override_save_sets_audit_columns_and_data():
    email_target = _unique_email()
    email_admin = _unique_email()
    password = "password123"
    _signup(email_target)
    uid_target = _user_id_by_email(email_target)
    client.post("/logout", follow_redirects=True)
    _signup(email_admin)
    uid_admin = _user_id_by_email(email_admin)
    with db() as conn:
        conn.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (uid_admin,))
    client.post("/logout", follow_redirects=True)
    client.post("/login", data={"email": email_admin, "password": password}, follow_redirects=True)

    exp = _iso_utc_future()
    # datetime-local sin TZ: mismo formato que admin puede enviar
    exp_local = exp.replace("+00:00", "")[:16]
    r = client.post(
        f"/admin/users/{uid_target}/manual-plan-override",
        data={
            "manual_plan": "pro",
            "manual_expires_at": exp_local,
            "manual_plan_note": "trial interno",
        },
        follow_redirects=False,
    )
    assert r.status_code == 303

    with db() as conn:
        row = conn.execute(
            """
            SELECT plan, manual_plan_override, manual_plan_expires_at, manual_plan_note,
                   manual_plan_updated_at, manual_plan_updated_by
            FROM users WHERE id = ?
            """,
            (uid_target,),
        ).fetchone()
    assert row["plan"] == "free"
    assert row["manual_plan_override"] == "pro"
    assert row["manual_plan_note"] == "trial interno"
    assert row["manual_plan_expires_at"]
    assert row["manual_plan_updated_at"]
    assert row["manual_plan_updated_by"] == uid_admin


def test_expired_override_persists_in_db_but_is_not_active_for_entitlements():
    """D17: caducado → sin efecto en acceso; filas manual_* conservadas (integridad histórica)."""
    email = _unique_email()
    _signup(email)
    uid = _user_id_by_email(email)
    with db() as conn:
        conn.execute(
            """
            UPDATE users SET manual_plan_override = ?, manual_plan_expires_at = ?, manual_plan_note = ?
            WHERE id = ?
            """,
            ("pro_plus", _iso_utc_past(), "vencido", uid),
        )
    row = _fetch_user_row(uid)
    user = user_row_as_dict(row)
    assert get_active_manual_plan(user) is None
    assert stored_manual_override_plan(user) == "pro_plus"
    assert manual_override_is_configured(user) is True
    assert get_effective_plan(user) == "free"


def test_admin_clear_override_clears_manual_fields_keeps_users_plan():
    email_target = _unique_email()
    email_admin = _unique_email()
    password = "password123"
    _signup(email_target)
    uid_target = _user_id_by_email(email_target)
    with db() as conn:
        conn.execute(
            """
            UPDATE users SET plan = ?, manual_plan_override = ?, manual_plan_note = ?
            WHERE id = ?
            """,
            ("pro", "pro_plus", "x", uid_target),
        )
    client.post("/logout", follow_redirects=True)
    _signup(email_admin)
    uid_admin = _user_id_by_email(email_admin)
    with db() as conn:
        conn.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (uid_admin,))
    client.post("/logout", follow_redirects=True)
    client.post("/login", data={"email": email_admin, "password": password}, follow_redirects=True)

    r = client.post(
        f"/admin/users/{uid_target}/manual-plan-override",
        data={"manual_plan": "clear", "manual_expires_at": "", "manual_plan_note": ""},
        follow_redirects=False,
    )
    assert r.status_code == 303

    with db() as conn:
        row = conn.execute(
            """
            SELECT plan, manual_plan_override, manual_plan_expires_at, manual_plan_note,
                   manual_plan_updated_at, manual_plan_updated_by
            FROM users WHERE id = ?
            """,
            (uid_target,),
        ).fetchone()
    assert row["plan"] == "pro"
    assert row["manual_plan_override"] is None
    assert row["manual_plan_expires_at"] is None
    assert row["manual_plan_note"] is None
    assert row["manual_plan_updated_at"]
    assert row["manual_plan_updated_by"] == uid_admin


# --- E. enforce_plan (límites según plan efectivo) ---


def _summary_pro_friendly(total_files: int, days: int) -> dict:
    return {
        "total_files": total_files,
        "overall_days_covered": days,
        "max_days_covered": days,
    }


def test_enforce_plan_free_billing_with_active_pro_override_allows_multi_file_like_pro():
    """Escenario 18: límites de Pro, no de free."""
    email = _unique_email()
    _signup(email)
    uid = _user_id_by_email(email)
    with db() as conn:
        conn.execute(
            """
            UPDATE users SET plan = ?, manual_plan_override = ?, manual_plan_expires_at = ?
            WHERE id = ?
            """,
            ("free", "pro", None, uid),
        )
    row = _fetch_user_row(uid)
    user = user_row_as_dict(row)
    summary = _summary_pro_friendly(total_files=3, days=50)
    enforce_plan(user, summary)


def test_enforce_plan_pro_plus_billing_with_inferior_pro_override_keeps_pro_plus_limits():
    """Escenario 19: 150 días rechazados en Pro, aceptados en Pro+."""
    email = _unique_email()
    _signup(email)
    uid = _user_id_by_email(email)
    with db() as conn:
        conn.execute(
            """
            UPDATE users SET plan = ?, manual_plan_override = ?, manual_plan_expires_at = ?
            WHERE id = ?
            """,
            ("pro_plus", "pro", None, uid),
        )
    row = _fetch_user_row(uid)
    user = user_row_as_dict(row)
    assert get_effective_plan(user) == "pro_plus"
    summary = _summary_pro_friendly(total_files=2, days=150)
    enforce_plan(user, summary)
    # Con efectivo Pro (si hubiera downgrade) 150 días fallarían
    user_fake_pro = {**user, "plan": "pro", "manual_plan_override": None, "manual_plan_expires_at": None}
    with pytest.raises(HTTPException) as ei:
        enforce_plan(user_fake_pro, summary)
    assert ei.value.status_code == 402


# --- F. analyze JSON contract (monkeypatch OpenAI) ---


def test_post_analyze_response_includes_plan_billing_plan_effective_plan(monkeypatch):
    """Escenario 20: contrato JSON al cerrar análisis."""
    from services import analysis_service

    email = _unique_email()
    password = "password123"
    _signup(email)
    client.post("/onboarding", data=_onboarding_complete(), follow_redirects=True)
    uid = _user_id_by_email(email)
    with db() as conn:
        conn.execute(
            """
            UPDATE users SET manual_plan_override = ?, manual_plan_expires_at = ?
            WHERE id = ?
            """,
            ("pro", None, uid),
        )

    monkeypatch.setattr(
        analysis_service,
        "call_openai",
        lambda *a, **k: {
            "resumen_ejecutivo": "ok",
            "metricas_clave": [],
            "senal_de_upgrade": {},
        },
    )

    csv_content = "stay_date,room_revenue,room_nights,channel\n2025-01-01,1000,5,Directo\n"
    files = {
        "files": ("one.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv"),
    }
    r = client.post("/analyze", data={"business_context": ""}, files=files)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("ok") is True
    assert data["plan"] == "free"
    assert data["billing_plan"] == "free"
    assert data["effective_plan"] == "pro"


def test_enforce_plan_matches_get_effective_plan_for_same_user_row():
    """Escenario 21: misma fila — límites aplicados = plan efectivo (regresión indirecta)."""
    email = _unique_email()
    _signup(email)
    uid = _user_id_by_email(email)
    with db() as conn:
        conn.execute(
            """
            UPDATE users SET plan = ?, manual_plan_override = ?, manual_plan_expires_at = ?
            WHERE id = ?
            """,
            ("free", "pro_plus", None, uid),
        )
    row = _fetch_user_row(uid)
    user = user_row_as_dict(row)
    eff = get_effective_plan(user)
    assert eff == "pro_plus"
    summary = _summary_pro_friendly(total_files=4, days=100)
    enforce_plan(user, summary)
    user_effective_free = {**user, "manual_plan_override": None}
    with pytest.raises(HTTPException):
        enforce_plan(user_effective_free, summary)
