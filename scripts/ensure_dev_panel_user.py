#!/usr/bin/env python3
"""
Crea o actualiza un usuario para entrar al panel en esta máquina (SQLite local).

La BD del repo suele tener solo cuentas de test (@example.com): tu correo/clave
de producción NO existen aquí. Este script deja credenciales fijas para UI local.

Uso (desde la raíz del repo):
  python3 scripts/ensure_dev_panel_user.py

Variables opcionales:
  DEV_PANEL_EMAIL    (default: panel@local.dev)
  DEV_PANEL_PASSWORD (default: PanelLocal2024!)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from auth_session import password_hash  # noqa: E402
from config import LEGAL_DOCS_VERSION  # noqa: E402
from db import db  # noqa: E402
from time_utils import now_iso  # noqa: E402

DEFAULT_EMAIL = "panel@local.dev"
DEFAULT_PASSWORD = "PanelLocal2024!"


def main() -> int:
    email = (os.getenv("DEV_PANEL_EMAIL") or DEFAULT_EMAIL).strip().lower()
    password = os.getenv("DEV_PANEL_PASSWORD") or DEFAULT_PASSWORD
    if len(password) < 8:
        print("La contraseña debe tener al menos 8 caracteres.", file=sys.stderr)
        return 1

    ph = password_hash(password)
    now = now_iso()
    with db() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE LOWER(TRIM(email)) = ?", (email,)
        ).fetchone()
        if row:
            uid = row["id"]
            conn.execute(
                """UPDATE users SET password_hash = ?, hotel_name = ?, contact_name = ?,
                   updated_at = ? WHERE id = ?""",
                (ph, "Hotel demo local", "Usuario panel", now, uid),
            )
            print(f"Actualizado usuario id={uid} email={email}")
        else:
            cur = conn.execute(
                """
                INSERT INTO users (
                    hotel_name, hotel_size, hotel_category, hotel_location,
                    contact_name, email, password_hash, plan, created_at, updated_at,
                    legal_accepted_at, legal_docs_version
                ) VALUES (?, NULL, NULL, NULL, ?, ?, ?, 'free', ?, ?, ?, ?)
                """,
                ("Hotel demo local", "Usuario panel", email, ph, now, now, now, LEGAL_DOCS_VERSION),
            )
            print(f"Creado usuario id={cur.lastrowid} email={email}")

    print()
    print("Entra en: http://127.0.0.1:8000/login")
    print("  Correo:   ", email)
    print("  Contraseña:", password)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
