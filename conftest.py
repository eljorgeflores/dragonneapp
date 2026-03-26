"""
Pytest: APP_URL en HTTP para que SessionMiddleware no marque cookies Secure
(igual que en desarrollo local). Usar 127.0.0.1:8000 y no "testserver": si APP_URL
fuera http://testserver, los enlaces de recuperación de contraseña seguirían con host
testserver (inválido fuera de TestClient). Starlette TestClient sigue usando host
testserver en la petición; origin_for_user_facing_links sustituye por APP_URL.
"""
import os

os.environ["APP_URL"] = "http://127.0.0.1:8000"
