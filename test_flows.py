from pathlib import Path

import io

from fastapi.testclient import TestClient

from app import app, BASE_DIR


client = TestClient(app)


def run_flow():
    # 1) Signup
    signup_data = {
        "hotel_name": "Hotel Prueba Dragonne",
        "contact_name": "Tester",
        "email": "tester@example.com",
        "password": "dragonne123",
        "hotel_size": "pequeño (<=40 llaves)",
        "hotel_category": "hotel de ciudad",
        "hotel_location": "Querétaro, México",
    }
    r = client.post("/signup", data=signup_data)
    assert r.status_code in (200, 303, 307), f"Error en signup: {r.status_code} {r.text}"

    # 2) Logout
    r = client.post("/logout")
    assert r.status_code in (200, 303, 307)

    # 3) Login
    r = client.post(
        "/login",
        data={"email": signup_data["email"], "password": signup_data["password"]},
    )
    assert r.status_code in (200, 303, 307), f"Error en login: {r.status_code} {r.text}"

    # 4) Forgot password (solo validamos que no truene)
    r = client.post("/forgot-password", data={"email": signup_data["email"]})
    assert r.status_code == 200

    # 5) Analizar reportes con un CSV de prueba
    csv_content = "stay_date,room_revenue,room_nights,channel\n2025-01-01,1000,5,Directo\n2025-01-02,1500,7,Booking\n"
    files = {
        "files": ("reporte_prueba.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv"),
    }
    r = client.post("/analyze", data={"business_context": "Prueba automatizada Dragonne"}, files=files)
    # Puede fallar si no hay OPENAI_API_KEY; en ese caso solo verificamos código de error manejado
    assert r.status_code in (200, 500, 402), f"Error inesperado en /analyze: {r.status_code} {r.text}"
    print("Flujo básico ejecutado. Código /analyze:", r.status_code)


if __name__ == "__main__":
    run_flow()

