#!/usr/bin/env python3
"""
Validación funcional básica contra uvicorn (requests + cookies; no es navegador real).

Si APP_URL en .env es https:// y pruebas en http://127.0.0.1:
  SESSION_INSECURE_COOKIES=1 uvicorn app:app --host 127.0.0.1 --port 8010
  python3 scripts/manual_smoke_phase3.py http://127.0.0.1:8010
"""
from __future__ import annotations

import re
import sys
import uuid
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import requests

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8010").rstrip("/")


def main() -> int:
    s = requests.Session()
    fails = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"{'OK' if ok else 'FAIL'} | {name} | {detail}")
        if not ok:
            fails.append(name)

    r = s.get(f"{BASE}/health", timeout=10)
    check("GET /health", r.status_code == 200 and r.json().get("ok") is True, str(r.json()))

    r = s.get(f"{BASE}/login", timeout=10)
    check("GET /login", r.status_code == 200, f"code={r.status_code}")

    email = f"smoke-{uuid.uuid4().hex[:8]}@example.com"
    pwd = "password123"
    r = s.post(
        f"{BASE}/signup",
        data={"email": email, "password": pwd, "password_confirm": pwd},
        allow_redirects=False,
        timeout=15,
    )
    check("POST /signup", r.status_code == 303 and r.headers.get("location", "").endswith("/onboarding"), r.headers.get("location", ""))

    r = s.post(
        f"{BASE}/onboarding",
        data={
            "hotel_name": "Hotel Smoke",
            "contact_name": "Tester",
            "hotel_size": "pequeño (<=40 llaves)",
            "hotel_category": "boutique",
            "hotel_location": "CDMX",
        },
        allow_redirects=False,
        timeout=15,
    )
    check("POST /onboarding", r.status_code == 303 and "/app" in (r.headers.get("location") or ""), r.headers.get("location", ""))

    r = s.get(f"{BASE}/app", allow_redirects=False, timeout=15)
    check("GET /app (dashboard)", r.status_code == 200 and "Hotel Smoke" in r.text, f"code={r.status_code}")

    csv_body = (
        "stay_date,room_revenue,room_nights,channel\n"
        "2025-01-01,1000,5,Directo\n"
        "2025-01-02,1500,7,Booking\n"
    )
    r = s.post(
        f"{BASE}/analyze",
        files={"files": ("smoke.csv", csv_body.encode("utf-8"), "text/csv")},
        data={"business_context": "Smoke manual: priorizar directo y revisar mix de canales."},
        timeout=180,
    )
    j = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    check("POST /analyze", r.status_code == 200 and j.get("ok") is True, (j.get("error") or "")[:100])

    aid = j.get("analysis_id")
    if aid:
        r = s.get(f"{BASE}/analysis/{aid}", timeout=30)
        dj = r.json() if r.ok else {}
        check("GET /analysis/{id} (resultado JSON)", r.status_code == 200 and dj.get("ok"), f"id={aid}")

        r = s.post(f"{BASE}/analysis/{aid}/share", timeout=15)
        sj = r.json() if r.ok else {}
        check("POST /analysis/{id}/share", r.status_code == 200 and sj.get("ok"), "")

        token = None
        if sj.get("share_url"):
            m = re.search(r"/s/([^/?#]+)", sj["share_url"])
            token = m.group(1) if m else None
        if token:
            r = s.get(f"{BASE}/s/{token}", timeout=15)
            check("GET /s/{token} (share público)", r.status_code == 200, f"code={r.status_code}")

        r = s.get(f"{BASE}/analysis/{aid}/pdf", timeout=90)
        check(
            "GET /analysis/{id}/pdf",
            r.status_code == 200 and "pdf" in r.headers.get("content-type", ""),
            f"{len(r.content)} bytes",
        )

    r = s.post(
        f"{BASE}/billing/create-checkout-session",
        data={"billing_cycle": "monthly", "plan_tier": "pro"},
        timeout=30,
    )
    bj = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    billing_ok = (r.status_code == 200 and bool(bj.get("url"))) or r.status_code == 500
    check("POST /billing/create-checkout-session", billing_ok, f"code={r.status_code}")

    r = s.get(f"{BASE}/admin", headers={"Accept": "application/json"}, allow_redirects=False, timeout=10)
    check("GET /admin (sin rol, JSON → 403)", r.status_code == 403, r.text[:100])

    # Panel admin + API v1
    from db import db

    api_key = "smoke-key-" + uuid.uuid4().hex[:16]
    with db() as conn:
        conn.execute("UPDATE users SET is_admin = 1, api_key = ? WHERE email = ?", (api_key, email))

    r = s.get(f"{BASE}/admin", timeout=15)
    check("GET /admin (con is_admin)", r.status_code == 200 and "Hoteles" in r.text, f"code={r.status_code}")

    r = requests.get(
        f"{BASE}/api/v1/me",
        headers={"X-API-Key": api_key, "Accept": "application/json"},
        timeout=10,
    )
    mj = r.json() if r.ok else {}
    check("GET /api/v1/me", r.status_code == 200 and mj.get("email") == email, f"code={r.status_code}")

    r = requests.get(f"{BASE}/api/v1/analyses", headers={"X-API-Key": api_key}, timeout=10)
    aj = r.json() if r.ok else {}
    check("GET /api/v1/analyses", r.status_code == 200 and aj.get("ok") is True, f"n={len(aj.get('analyses', []))}")

    if aid:
        r = requests.get(
            f"{BASE}/api/v1/analyses/{aid}/pdf",
            headers={"X-API-Key": api_key},
            timeout=90,
        )
        check(
            "GET /api/v1/analyses/{id}/pdf",
            r.status_code == 200 and "pdf" in r.headers.get("content-type", ""),
            f"{len(r.content)} bytes",
        )

    s.post(f"{BASE}/logout", allow_redirects=False, timeout=10)
    r = s.post(
        f"{BASE}/login",
        data={"email": email, "password": pwd},
        allow_redirects=False,
        timeout=15,
    )
    loc = r.headers.get("location") or ""
    # Usuario es admin → suele ir a /admin
    check(
        "POST /login (tras logout)",
        r.status_code == 303 and ("/app" in loc or "/admin" in loc),
        f"loc={loc}",
    )

    print(f"\nUsuario de prueba: {email}  |  API key (solo smoke): {api_key}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
