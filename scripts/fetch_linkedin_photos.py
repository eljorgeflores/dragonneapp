#!/usr/bin/env python3
"""
Descarga fotos de perfil de LinkedIn para la sección de equipo/asesores.
Ejecutar desde la raíz del proyecto: python3 scripts/fetch_linkedin_photos.py

Requiere: pip install requests

LinkedIn a veces devuelve HTML sin foto (login wall / rate limit).
Si no se descargan todas, ejecuta de nuevo desde tu máquina o red;
algunas ya están en static/team/ (p. ej. jorge-flores.jpg, joaquin-benitez.jpg).
"""
import re
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Instala requests: pip install requests")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent.parent
TEAM_DIR = BASE_DIR / "static" / "team"
TEAM_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# slug LinkedIn -> nombre de archivo local
PROFILES = [
    ("hefzi-arroyo-3aa8b23aa", "hefzi-dragonne.png"),
    ("vaniadragonne", "vania-dragonne.png"),
    ("jorgefloresacevedo", "jorge-flores.jpg"),
    ("juanjoflores", "juanjo-flores.png"),
    ("joaquinbenitezm", "joaquin-benitez.jpg"),
    ("jorgedecordova", "jorge-decordova.png"),
]


def extract_photo_url(html: str) -> str | None:
    m = re.search(
        r'https://media\.licdn\.com/dms/image[^"\'<> ]+profile-displayphoto[^"\'<> ]*',
        html,
    )
    if not m:
        return None
    url = m.group(0).replace("&amp;", "&")
    return url


def main():
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    for slug, filename in PROFILES:
        path = TEAM_DIR / filename
        url = f"https://www.linkedin.com/in/{slug}/"
        print(f"  {slug} ... ", end="", flush=True)
        try:
            r = session.get(url, timeout=25)
            r.raise_for_status()
            photo_url = extract_photo_url(r.text)
            if not photo_url:
                print("sin foto en HTML")
                continue
            img = session.get(photo_url, timeout=15)
            img.raise_for_status()
            path.write_bytes(img.content)
            print(f"OK -> {path.name}")
        except requests.RequestException as e:
            print(f"error: {e}")
        except Exception as e:
            print(f"error: {e}")

    print("Listo. Fotos en static/team/")


if __name__ == "__main__":
    main()
