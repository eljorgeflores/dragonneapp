#!/usr/bin/env python3
"""
Copia la base de datos a data/backups/ con fecha y hora.
Mantiene solo los últimos N backups (por defecto 30).
Uso: python scripts/backup_db.py
Cron (diario a las 2:00): 0 2 * * * cd /ruta/al/proyecto && .venv/bin/python scripts/backup_db.py
"""
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Carpeta del proyecto (donde está app.py)
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "profitpilot.db"
BACKUP_DIR = BASE_DIR / "data" / "backups"
KEEP_LAST = 30  # Cuántos backups conservar


def main():
    if not DB_PATH.exists():
        print(f"No se encontró la base de datos en {DB_PATH}", file=sys.stderr)
        sys.exit(1)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"profitpilot_{stamp}.db"
    shutil.copy2(DB_PATH, backup_path)
    print(f"Backup creado: {backup_path}")
    # Rotar: dejar solo los últimos KEEP_LAST
    backups = sorted(BACKUP_DIR.glob("profitpilot_*.db"), key=lambda p: p.stat().st_mtime)
    for old in backups[:-KEEP_LAST]:
        old.unlink()
        print(f"Eliminado backup antiguo: {old.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
