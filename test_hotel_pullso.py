"""
Integración Pullso: invitación a hotel por token y aceptación en /app/hotel/join.
"""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app import app, db
from services.hotel_pullso import HOTEL_WHATSAPP_MAX_NUMBERS, create_hotel_invite, save_hotel_whatsapp_settings
from services.pullso_whatsapp_user_delivery import validate_wa_slots_and_build_blob

client = TestClient(app)


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}@example.com"


def _signup(email: str, password: str = "password123") -> None:
    client.post(
        "/signup",
        data={
            "email": email,
            "password": password,
            "password_confirm": password,
            "accept_legal": "1",
        },
        follow_redirects=True,
    )


def _user_id(email: str) -> int:
    with db() as conn:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        assert row is not None
        return int(row["id"])


def _onboarding_payload(hotel_label: str) -> dict:
    return {
        "hotel_name": hotel_label,
        "contact_name": "Tester",
        "hotel_size": "pequeño (<=40 llaves)",
        "hotel_category": "boutique",
        "hotel_location": "CDMX",
    }


def test_hotel_invite_join_adds_membership():
    """
    Un admin (A) crea invitación para el correo de B; B se registra y abre el enlace
    de unión: debe quedar como miembro del hotel de A con el rol invitado.
    """
    email_a = _unique_email("hotel-a")
    email_b = _unique_email("hotel-b")
    pwd = "password123"
    label_a = f"Hotel Alpha {uuid.uuid4().hex[:8]}"

    _signup(email_a, pwd)
    client.post("/onboarding", data=_onboarding_payload(label_a), follow_redirects=True)
    uid_a = _user_id(email_a)
    with db() as conn:
        row = conn.execute(
            """
            SELECT hotel_id FROM hotel_members
            WHERE user_id = ? AND role = 'admin'
            ORDER BY hotel_id LIMIT 1
            """,
            (uid_a,),
        ).fetchone()
        assert row is not None
        hotel_id_a = int(row["hotel_id"])

    raw_token, ierr = create_hotel_invite(
        hotel_id=hotel_id_a,
        inviter_user_id=uid_a,
        invitee_email=email_b,
        role="user",
    )
    assert ierr is None
    assert raw_token and len(raw_token) >= 20

    client.post("/logout")

    _signup(email_b, pwd)
    client.post(
        "/onboarding",
        data=_onboarding_payload(f"Hotel Beta {uuid.uuid4().hex[:8]}"),
        follow_redirects=True,
    )
    uid_b = _user_id(email_b)

    r_join = client.get(f"/app/hotel/join?token={raw_token}", follow_redirects=False)
    assert r_join.status_code == 303
    loc = r_join.headers.get("location") or ""
    assert "/app/account" in loc

    with db() as conn:
        m = conn.execute(
            "SELECT role FROM hotel_members WHERE hotel_id = ? AND user_id = ?",
            (hotel_id_a, uid_b),
        ).fetchone()
        assert m is not None
        assert (m["role"] or "").strip() == "user"


def test_hotel_invite_wrong_email_does_not_gain_membership():
    """La invitación está ligada a un correo; otro usuario no debe unirse con el mismo token."""
    email_a = _unique_email("hotel-a-mis")
    email_invited = _unique_email("invited-target")
    email_c = _unique_email("hotel-c-mis")
    pwd = "password123"

    _signup(email_a, pwd)
    client.post(
        "/onboarding",
        data=_onboarding_payload(f"Hotel Mis {uuid.uuid4().hex[:6]}"),
        follow_redirects=True,
    )
    uid_a = _user_id(email_a)
    with db() as conn:
        row = conn.execute(
            """
            SELECT hotel_id FROM hotel_members
            WHERE user_id = ? AND role = 'admin'
            ORDER BY hotel_id LIMIT 1
            """,
            (uid_a,),
        ).fetchone()
        assert row is not None
        hotel_id_a = int(row["hotel_id"])

    raw_token, ierr = create_hotel_invite(
        hotel_id=hotel_id_a,
        inviter_user_id=uid_a,
        invitee_email=email_invited,
        role="user",
    )
    assert ierr is None

    client.post("/logout")
    _signup(email_c, pwd)
    client.post(
        "/onboarding",
        data=_onboarding_payload(f"Hotel Cmis {uuid.uuid4().hex[:6]}"),
        follow_redirects=True,
    )
    uid_c = _user_id(email_c)

    r_join = client.get(f"/app/hotel/join?token={raw_token}", follow_redirects=False)
    assert r_join.status_code == 303

    with db() as conn:
        m = conn.execute(
            "SELECT 1 FROM hotel_members WHERE hotel_id = ? AND user_id = ?",
            (hotel_id_a, uid_c),
        ).fetchone()
        assert m is None


def test_validate_wa_slots_rejects_more_than_three_intended_recipients():
    """No se admiten más de tres filas con número (aunque vengan en la petición)."""
    slots = [
        {"name": "", "prefix": "52", "national": "9811111111"},
        {"name": "", "prefix": "52", "national": "9822222222"},
        {"name": "", "prefix": "52", "national": "9833333333"},
        {"name": "", "prefix": "52", "national": "9844444444"},
    ]
    _, err = validate_wa_slots_and_build_blob(slots, HOTEL_WHATSAPP_MAX_NUMBERS)
    assert err == "too_many"


def test_save_hotel_whatsapp_accepts_named_slots():
    """Tres destinatarios con prefijo + nacional se guardan sin error."""
    email_a = _unique_email("hotel-wa-slots")
    pwd = "password123"
    _signup(email_a, pwd)
    client.post(
        "/onboarding",
        data=_onboarding_payload(f"Hotel WaS {uuid.uuid4().hex[:6]}"),
        follow_redirects=True,
    )
    uid_a = _user_id(email_a)
    with db() as conn:
        row = conn.execute(
            """
            SELECT hotel_id FROM hotel_members
            WHERE user_id = ? AND role = 'admin'
            ORDER BY hotel_id LIMIT 1
            """,
            (uid_a,),
        ).fetchone()
        assert row is not None
        hid = int(row["hotel_id"])

    slots = [
        {"name": "Revenue", "prefix": "52", "national": "5511112222"},
        {"name": "", "prefix": "52", "national": "9983334455"},
        {"name": "", "prefix": "", "national": ""},
    ]
    err = save_hotel_whatsapp_settings(hid, uid_a, slots, True)
    assert err is None
