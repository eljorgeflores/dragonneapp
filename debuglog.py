"""Logs locales opcionales para depuración (no afectan producción)."""
import json
import time
from typing import Any, Dict, Optional

from config import BASE_DIR


def _debug_log(location: str, message: str, data: Optional[Dict] = None, hypothesis_id: Optional[str] = None, run_id: Optional[str] = None):
    try:
        _log_path = BASE_DIR / ".cursor" / "debug-95cdbc.log"
        payload = {"sessionId": "95cdbc", "timestamp": int(time.time() * 1000), "location": location, "message": message, "data": data or {}, "hypothesisId": hypothesis_id or "", "runId": run_id or ""}
        with open(_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _dbg(location: str, message: str, data: Optional[Dict] = None, hypothesis_id: Optional[str] = None):
    try:
        log_path = BASE_DIR / ".cursor" / "debug-b78cbe.log"
        payload = {"sessionId": "b78cbe", "timestamp": int(time.time() * 1000), "location": location, "message": message, "data": data or {}, "hypothesisId": hypothesis_id or ""}
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
