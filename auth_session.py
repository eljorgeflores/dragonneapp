"""Sesión web, contraseñas, límites de login/API y comprobación admin."""
import hashlib
import hmac
import secrets
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

from fastapi import Header, HTTPException, Request

from config import (
    ADMIN_EMAILS,
    API_RATE_LIMIT_PER_DAY,
    API_RATE_LIMIT_PER_MINUTE,
    MAGIC_LINK_RATE_LIMIT_EMAIL,
    MAGIC_LINK_RATE_LIMIT_IP,
    MAGIC_LINK_RATE_LIMIT_WINDOW_SEC,
    MAGIC_LINK_TTL_MINUTES,
    PASSWORD_RESET_TOKEN_TTL_HOURS,
)
from db import db
from time_utils import now_iso

MAGIC_LINK_PURPOSE = "magic_link"


class MagicLinkConsumeResult(str, Enum):
    OK = "ok"
    NOT_FOUND = "not_found"
    EXPIRED = "expired"
    ALREADY_USED = "already_used"


def hash_login_token(raw: str) -> str:
    """Hash SHA-256 hex del secreto en claro (nunca persistir el token bruto)."""
    return hashlib.sha256((raw or "").encode("utf-8")).hexdigest()


def create_magic_link_token(
    user_id: int,
    *,
    requested_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> str:
    raw = secrets.token_urlsafe(32)
    th = hash_login_token(raw)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=MAGIC_LINK_TTL_MINUTES)).isoformat()
    ua = (user_agent or "")[:512] or None
    ip = (requested_ip or "")[:64] or None
    with db() as conn:
        conn.execute(
            """
            INSERT INTO login_tokens (user_id, token_hash, purpose, expires_at, created_at, requested_ip, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, th, MAGIC_LINK_PURPOSE, expires_at, now_iso(), ip, ua),
        )
    return raw


def consume_magic_link_token(raw: str) -> Tuple[MagicLinkConsumeResult, Optional[int]]:
    """
    Valida y consume un token de magic link (un solo uso).
    Devuelve (resultado, user_id) con user_id solo si OK.
    """
    secret = (raw or "").strip()
    if not secret or len(secret) < 20:
        return MagicLinkConsumeResult.NOT_FOUND, None
    th = hash_login_token(secret)
    with db() as conn:
        row = conn.execute(
            """
            SELECT * FROM login_tokens
            WHERE token_hash = ? AND purpose = ?
            """,
            (th, MAGIC_LINK_PURPOSE),
        ).fetchone()
        if not row:
            return MagicLinkConsumeResult.NOT_FOUND, None
        if row["used_at"]:
            return MagicLinkConsumeResult.ALREADY_USED, None
        exp_raw = row["expires_at"]
        try:
            exp_s = (str(exp_raw) if exp_raw is not None else "").replace("Z", "+00:00")
            exp = datetime.fromisoformat(exp_s)
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            else:
                exp = exp.astimezone(timezone.utc)
        except (ValueError, TypeError):
            return MagicLinkConsumeResult.NOT_FOUND, None
        if exp <= datetime.now(timezone.utc):
            return MagicLinkConsumeResult.EXPIRED, None
        cur = conn.execute(
            "UPDATE login_tokens SET used_at = ? WHERE id = ? AND used_at IS NULL",
            (now_iso(), row["id"]),
        )
        if cur.rowcount == 0:
            return MagicLinkConsumeResult.ALREADY_USED, None
        return MagicLinkConsumeResult.OK, int(row["user_id"])


def password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, password_hash_value: str) -> bool:
    try:
        salt, stored = password_hash_value.split("$", 1)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000).hex()
        return hmac.compare_digest(digest, stored)
    except Exception:
        return False


def create_reset_token(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = (
        datetime.now(timezone.utc) + timedelta(hours=PASSWORD_RESET_TOKEN_TTL_HOURS)
    ).isoformat()
    with db() as conn:
        conn.execute(
            """
            INSERT INTO password_resets (user_id, token, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, token, expires_at, now_iso()),
        )
    return token


def consume_reset_token(token: str) -> Optional[int]:
    """Marca el token usado y devuelve user_id, o None si no existe, caducó o ya se usó."""
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM password_resets WHERE token = ? AND used = 0",
            (token,),
        ).fetchone()
        if not row:
            return None
        exp_raw = row["expires_at"]
        try:
            exp_s = (str(exp_raw) if exp_raw is not None else "").replace("Z", "+00:00")
            exp = datetime.fromisoformat(exp_s)
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            else:
                exp = exp.astimezone(timezone.utc)
        except (ValueError, TypeError):
            return None
        if exp <= datetime.now(timezone.utc):
            return None
        cur = conn.execute(
            "UPDATE password_resets SET used = 1 WHERE id = ? AND used = 0",
            (row["id"],),
        )
        if cur.rowcount == 0:
            return None
        return int(row["user_id"])


def establish_web_session(request: Request, user_id: int) -> int:
    """Misma sesión que login por contraseña: last_login, user_sessions y cookies de sesión."""
    with db() as conn:
        conn.execute(
            "UPDATE users SET last_login_at = ?, login_count = COALESCE(login_count, 0) + 1, updated_at = ? WHERE id = ?",
            (now_iso(), now_iso(), user_id),
        )
        cur = conn.execute(
            "INSERT INTO user_sessions (user_id, started_at, last_seen_at, request_count) VALUES (?, ?, ?, ?)",
            (user_id, now_iso(), now_iso(), 1),
        )
        session_id = cur.lastrowid
    request.session["user_id"] = user_id
    request.session["session_id"] = session_id
    return session_id


def get_current_user(request: Request) -> Optional[sqlite3.Row]:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    with db() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def require_user(request: Request) -> sqlite3.Row:
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Debes iniciar sesión")
    return user


def onboarding_pending(user: sqlite3.Row) -> bool:
    name = (user["hotel_name"] or "").strip() if user["hotel_name"] is not None else ""
    contact = (user["contact_name"] or "").strip() if user["contact_name"] is not None else ""
    return not name or not contact


class APIRateLimiter:
    def __init__(self, per_minute: int = 60, per_day: int = 1000):
        self.per_minute = per_minute
        self.per_day = per_day
        self._data: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()

    def _day_start(self) -> str:
        return datetime.now(timezone.utc).date().isoformat()

    def check_and_consume(self, api_key: str) -> None:
        now = time.time()
        today = self._day_start()
        with self._lock:
            rec = self._data.get(api_key)
            if not rec:
                rec = {"minute_count": 0, "minute_ts": now, "day_count": 0, "day_date": today}
                self._data[api_key] = rec
            if now - rec["minute_ts"] >= 60:
                rec["minute_count"] = 0
                rec["minute_ts"] = now
            if rec["day_date"] != today:
                rec["day_count"] = 0
                rec["day_date"] = today
            rec["minute_count"] += 1
            rec["day_count"] += 1
            if rec["minute_count"] > self.per_minute:
                raise HTTPException(
                    status_code=429,
                    detail=f"Límite por minuto excedido ({self.per_minute} req/min). Intenta más tarde.",
                    headers={"Retry-After": "60"},
                )
            if rec["day_count"] > self.per_day:
                raise HTTPException(
                    status_code=429,
                    detail=f"Límite diario excedido ({self.per_day} req/día). Mañana se reinicia.",
                    headers={"Retry-After": "86400"},
                )


api_rate_limiter = APIRateLimiter(per_minute=API_RATE_LIMIT_PER_MINUTE, per_day=API_RATE_LIMIT_PER_DAY)

LOGIN_RATE_LIMIT_ATTEMPTS = 6
LOGIN_RATE_LIMIT_WINDOW_SEC = 300


def client_ip_from_request(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return (request.scope.get("client") or ("", 0))[0] or "unknown"


class LoginRateLimiter:
    def __init__(self, max_attempts: int = 6, window_sec: int = 300):
        self.max_attempts = max_attempts
        self.window_sec = window_sec
        self._attempts: Dict[str, List[float]] = {}
        self._lock = Lock()

    def _client_ip(self, request: Request) -> str:
        return client_ip_from_request(request)

    def is_blocked(self, request: Request) -> bool:
        ip = self._client_ip(request)
        now = time.time()
        with self._lock:
            if ip not in self._attempts:
                return False
            self._attempts[ip] = [t for t in self._attempts[ip] if now - t < self.window_sec]
            return len(self._attempts[ip]) >= self.max_attempts

    def record_failed(self, request: Request) -> None:
        ip = self._client_ip(request)
        now = time.time()
        with self._lock:
            if ip not in self._attempts:
                self._attempts[ip] = []
            self._attempts[ip] = [t for t in self._attempts[ip] if now - t < self.window_sec]
            self._attempts[ip].append(now)


login_rate_limiter = LoginRateLimiter(max_attempts=LOGIN_RATE_LIMIT_ATTEMPTS, window_sec=LOGIN_RATE_LIMIT_WINDOW_SEC)


class MagicLinkRateLimiter:
    """Límite por correo normalizado y por IP al solicitar enlaces mágicos."""

    def __init__(self, max_per_email: int, max_per_ip: int, window_sec: int):
        self.max_per_email = max_per_email
        self.max_per_ip = max_per_ip
        self.window_sec = window_sec
        self._by_email: Dict[str, List[float]] = {}
        self._by_ip: Dict[str, List[float]] = {}
        self._lock = Lock()

    def _client_ip(self, request: Request) -> str:
        return client_ip_from_request(request)

    def _prune(self, bucket: Dict[str, List[float]], key: str, now: float) -> None:
        if key not in bucket:
            return
        bucket[key] = [t for t in bucket[key] if now - t < self.window_sec]
        if not bucket[key]:
            del bucket[key]

    def record_and_check_limited(self, request: Request, email_norm: str) -> Tuple[bool, Optional[str]]:
        """
        Registra este intento y devuelve (limitado, 'ip'|'email'|None).
        El intento en exceso también cuenta para ventana deslizante.
        """
        ip = self._client_ip(request)
        now = time.time()
        en = (email_norm or "").strip().lower()
        with self._lock:
            self._prune(self._by_ip, ip, now)
            self._prune(self._by_email, en, now)
            if ip not in self._by_ip:
                self._by_ip[ip] = []
            self._by_ip[ip].append(now)
            if len(self._by_ip[ip]) > self.max_per_ip:
                return True, "ip"
            if en:
                if en not in self._by_email:
                    self._by_email[en] = []
                self._by_email[en].append(now)
                if len(self._by_email[en]) > self.max_per_email:
                    return True, "email"
            return False, None


magic_link_rate_limiter = MagicLinkRateLimiter(
    max_per_email=MAGIC_LINK_RATE_LIMIT_EMAIL,
    max_per_ip=MAGIC_LINK_RATE_LIMIT_IP,
    window_sec=MAGIC_LINK_RATE_LIMIT_WINDOW_SEC,
)


def get_api_user(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
) -> sqlite3.Row:
    key = x_api_key
    if not key and authorization and authorization.startswith("Bearer "):
        key = authorization[7:].strip()
    if not key:
        raise HTTPException(status_code=401, detail="Falta API key. Usa el header X-API-Key o Authorization: Bearer <tu_key>.")
    with db() as conn:
        user = conn.execute("SELECT * FROM users WHERE api_key = ?", (key,)).fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="API key inválida o no autorizada. Solicita acceso en la web.")
    api_rate_limiter.check_and_consume(key)
    if onboarding_pending(user):
        raise HTTPException(status_code=403, detail="Completa el onboarding antes de usar la API.")
    return user


def is_admin_user(user: sqlite3.Row) -> bool:
    if user["is_admin"]:
        return True
    if ADMIN_EMAILS and user["email"].strip().lower() in ADMIN_EMAILS:
        return True
    return False


def require_admin(request: Request) -> sqlite3.Row:
    user = require_user(request)
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador.")
    return user
