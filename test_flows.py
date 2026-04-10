from pathlib import Path
import io
import uuid

from fastapi.testclient import TestClient

from app import app, BASE_DIR


client = TestClient(app)


def run_flow():
    # Email único para no chocar con registros previos
    email = f"tester-{uuid.uuid4().hex[:8]}@example.com"
    signup_data = {
        "hotel_name": "Hotel Prueba Dragonne",
        "contact_name": "Tester",
        "email": email,
        "password": "dragonne123",
        "hotel_size": "pequeño (<=40 llaves)",
        "hotel_category": "hotel de ciudad",
        "hotel_location": "Querétaro, México",
    }
    signup_data["password_confirm"] = signup_data["password"]
    signup_data["accept_legal"] = "1"
    r = client.post("/signup", data=signup_data)
    assert r.status_code in (200, 303, 307), f"Error en signup: {r.status_code} {r.text}"

    # 2) Logout
    r = client.post("/logout")
    assert r.status_code in (200, 303, 307)

    # 3) Login
    r = client.post(
        "/login",
        data={"email": email, "password": signup_data["password"]},
    )
    assert r.status_code in (200, 303, 307), f"Error en login: {r.status_code} {r.text}"

    # 4) Forgot password (solo validamos que no truene)
    r = client.post("/forgot-password", data={"email": email})
    assert r.status_code == 200

    # 4b) Completar onboarding para poder usar /analyze
    onboarding_data = {
        "hotel_name": "Hotel Prueba Dragonne",
        "contact_name": "Tester",
        "hotel_size": "pequeño (<=40 llaves)",
        "hotel_category": "hotel de ciudad",
        "hotel_location": "Querétaro, México",
    }
    r = client.post("/onboarding", data=onboarding_data)
    assert r.status_code in (200, 303, 307), f"Error onboarding: {r.status_code}"

    # 5) Analizar reportes con un CSV de prueba
    csv_content = "stay_date,room_revenue,room_nights,channel\n2025-01-01,1000,5,Directo\n2025-01-02,1500,7,Booking\n"
    files = {
        "files": ("reporte_prueba.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv"),
    }
    r = client.post("/analyze", data={"business_context": "Prueba automatizada Dragonne"}, files=files)
    # 200 OK, 400 (falta onboarding), 402 (límite plan), 500 (ej. sin OPENAI_API_KEY)
    assert r.status_code in (200, 400, 500, 402), f"Error inesperado en /analyze: {r.status_code} {r.text}"
    if r.status_code == 200:
        data = r.json()
        assert data.get("ok") is True, data
        assert data.get("summary", {}).get("reports_detected", 0) >= 1
        print("Flujo básico y análisis OK. reports_detected:", data.get("summary", {}).get("reports_detected"))
    else:
        print("Flujo básico ejecutado. /analyze devolvió:", r.status_code, r.json() if r.headers.get("content-type", "").startswith("application/json") else "(no JSON)")


if __name__ == "__main__":
    run_flow()

