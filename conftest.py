"""
Pytest: APP_URL en HTTP para que SessionMiddleware no marque cookies Secure;
TestClient usa http://testserver y no enviaría cookies Secure (rompe login/onboarding).
"""
import os

os.environ["APP_URL"] = "http://testserver"
