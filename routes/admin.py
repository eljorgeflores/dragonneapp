"""Panel administración DragonApp (usuarios, API keys, admins)."""
import json
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from admin_ops import ADMIN_PLAN_VALUES, delete_analysis_by_id, delete_user_and_related
from auth_session import require_admin
from config import ADMIN_EMAILS, API_RATE_LIMIT_PER_DAY, API_RATE_LIMIT_PER_MINUTE
from db import db
from plans import plan_label
from templating import templates
from time_utils import now_iso

router = APIRouter(tags=["admin"])


@router.get("/admin", response_class=HTMLResponse)
def admin_home(request: Request):
    admin = require_admin(request)
    with db() as conn:
        totals_row = conn.execute(
            """
            SELECT
              COUNT(*) AS total_hotels,
              SUM(COALESCE(login_count, 0)) AS total_logins,
              SUM(CASE WHEN last_login_at IS NOT NULL AND last_login_at >= ? THEN 1 ELSE 0 END) AS active_last_30d
            FROM users
            """,
            ((datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),),
        ).fetchone()
        analyses_totals = conn.execute(
            "SELECT COUNT(*) AS total_analyses, COALESCE(SUM(file_count), 0) AS total_files FROM analyses"
        ).fetchone()
        rows = conn.execute(
            """
            SELECT
              u.*,
              COALESCE(a.cnt, 0) AS total_analyses,
              COALESCE(a.files_cnt, 0) AS total_files,
              s.last_activity
            FROM users u
            LEFT JOIN (
              SELECT
                user_id,
                COUNT(*) AS cnt,
                SUM(file_count) AS files_cnt,
                MAX(created_at) AS last_analysis_at
              FROM analyses
              GROUP BY user_id
            ) a ON a.user_id = u.id
            LEFT JOIN (
              SELECT
                user_id,
                MAX(COALESCE(ended_at, last_seen_at)) AS last_activity
              FROM user_sessions
              GROUP BY user_id
            ) s ON s.user_id = u.id
            ORDER BY COALESCE(s.last_activity, u.created_at) DESC
            LIMIT 100
            """
        ).fetchall()

    users = []
    for r in rows:
        users.append({
            "id": r["id"],
            "hotel_name": r["hotel_name"],
            "email": r["email"],
            "plan_label": plan_label(r["plan"]),
            "created_at": r["created_at"],
            "last_login_at": r["last_login_at"],
            "login_count": r["login_count"] or 0,
            "total_analyses": r["total_analyses"],
            "total_files": r["total_files"],
            "last_activity": r["last_activity"],
        })

    totals = {
        "total_hotels": totals_row["total_hotels"],
        "active_last_30d": totals_row["active_last_30d"],
        "total_analyses": analyses_totals["total_analyses"],
        "total_files": analyses_totals["total_files"],
    }

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "current_user": admin,
        "users": users,
        "totals": totals,
    })


@router.get("/admin/users/{user_id}", response_class=HTMLResponse)
def admin_user_detail(request: Request, user_id: int):
    admin = require_admin(request)
    with db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        analysis_rows = conn.execute(
            "SELECT * FROM analyses WHERE user_id = ? ORDER BY created_at DESC LIMIT 50",
            (user_id,),
        ).fetchall()
        sessions = conn.execute(
            "SELECT * FROM user_sessions WHERE user_id = ? ORDER BY started_at DESC LIMIT 50",
            (user_id,),
        ).fetchall()
        stats_row = conn.execute(
            """
            SELECT
              COUNT(*) AS total_analyses,
              COALESCE(SUM(file_count), 0) AS total_files,
              MAX(created_at) AS last_analysis_at
            FROM analyses
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
        last_activity_row = conn.execute(
            "SELECT MAX(COALESCE(ended_at, last_seen_at)) AS last_activity FROM user_sessions WHERE user_id = ?",
            (user_id,),
        ).fetchone()

    analyses_list = []
    for row in analysis_rows:
        try:
            summary = json.loads(row["summary_json"])
        except (TypeError, json.JSONDecodeError):
            summary = {}
        created_raw = row["created_at"] or ""
        created_at_str = created_raw[:19].replace("T", " ") if created_raw else ""
        analyses_list.append({
            "id": row["id"],
            "title": row["title"] or f"Análisis {row['id']}",
            "created_at": created_at_str,
            "file_count": row["file_count"],
            "days_covered": row["days_covered"] if row["days_covered"] is not None else 0,
            "reports_detected": int(summary.get("reports_detected") or 0),
        })

    stats = {
        "total_analyses": stats_row["total_analyses"],
        "total_files": stats_row["total_files"],
        "last_analysis_at": stats_row["last_analysis_at"],
        "last_activity": last_activity_row["last_activity"],
    }

    return templates.TemplateResponse("admin_user_detail.html", {
        "request": request,
        "current_user": admin,
        "user": user,
        "plan_label": plan_label(user["plan"]),
        "analyses": analyses_list,
        "sessions": sessions,
        "stats": stats,
    })


@router.post("/admin/users/{user_id}/plan")
def admin_user_set_plan(request: Request, user_id: int, plan: str = Form(...)):
    require_admin(request)
    plan = (plan or "").strip()
    if plan not in ADMIN_PLAN_VALUES:
        raise HTTPException(status_code=400, detail="Plan no válido")
    with db() as conn:
        u = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not u:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        conn.execute("UPDATE users SET plan = ?, updated_at = ? WHERE id = ?", (plan, now_iso(), user_id))
    return RedirectResponse(f"/admin/users/{user_id}", status_code=303)


@router.post("/admin/users/{user_id}/delete")
def admin_user_delete(request: Request, user_id: int):
    admin = require_admin(request)
    if admin["id"] == user_id:
        return RedirectResponse("/admin?error=no_borrar_self", status_code=303)
    with db() as conn:
        target = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not target:
            return RedirectResponse("/admin?error=usuario_no_encontrado", status_code=303)
        delete_user_and_related(conn, user_id)
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/analyses/{analysis_id}/delete")
def admin_analysis_delete(request: Request, analysis_id: int):
    require_admin(request)
    with db() as conn:
        row = conn.execute("SELECT user_id FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Análisis no encontrado")
        uid = row["user_id"]
        delete_analysis_by_id(conn, analysis_id)
    return RedirectResponse(f"/admin/users/{uid}", status_code=303)


@router.get("/admin/admins", response_class=HTMLResponse)
def admin_admins(request: Request):
    admin = require_admin(request)
    admin_emails_set = ADMIN_EMAILS
    with db() as conn:
        all_users = conn.execute(
            "SELECT id, email, hotel_name, is_admin, created_at FROM users ORDER BY email"
        ).fetchall()
    admins = []
    non_admins = []
    for email in sorted(admin_emails_set):
        admins.append({"email": email, "hotel_name": None, "fijo": True, "user_id": None})
    for r in all_users:
        email_lower = (r["email"] or "").strip().lower()
        if r["is_admin"]:
            if email_lower not in admin_emails_set:
                admins.append({
                    "email": r["email"],
                    "hotel_name": r["hotel_name"],
                    "fijo": False,
                    "user_id": r["id"],
                })
        else:
            if email_lower not in admin_emails_set:
                non_admins.append({
                    "id": r["id"],
                    "email": r["email"],
                    "hotel_name": r["hotel_name"],
                    "created_at": r["created_at"],
                })
    return templates.TemplateResponse("admin_admins.html", {
        "request": request,
        "current_user": admin,
        "admins": admins,
        "non_admins": non_admins,
    })


@router.post("/admin/admins/grant")
def admin_admins_grant(request: Request, user_id: int = Form(...)):
    require_admin(request)
    with db() as conn:
        conn.execute("UPDATE users SET is_admin = 1, updated_at = ? WHERE id = ?", (now_iso(), user_id))
    return RedirectResponse("/admin/admins", status_code=303)


@router.post("/admin/admins/revoke")
def admin_admins_revoke(request: Request, user_id: int = Form(...)):
    require_admin(request)
    with db() as conn:
        user = conn.execute("SELECT email FROM users WHERE id = ?", (user_id,)).fetchone()
        if user and user["email"].strip().lower() in ADMIN_EMAILS:
            return RedirectResponse("/admin/admins?error=fijo", status_code=303)
        conn.execute("UPDATE users SET is_admin = 0, updated_at = ? WHERE id = ?", (now_iso(), user_id))
    return RedirectResponse("/admin/admins", status_code=303)


@router.get("/admin/api", response_class=HTMLResponse)
def admin_api(request: Request):
    admin = require_admin(request)
    api_key_flash = request.session.pop("api_key_flash", None)
    with db() as conn:
        rows = conn.execute(
            """
            SELECT id, email, hotel_name, plan, api_key, created_at
            FROM users
            ORDER BY hotel_name
            """
        ).fetchall()
    users = []
    for r in rows:
        key = r["api_key"] if r["api_key"] else None
        masked = ("••••••••" + key[-4:] if key and len(key) > 4 else "••••••••") if key else "—"
        users.append({
            "id": r["id"],
            "email": r["email"],
            "hotel_name": r["hotel_name"],
            "plan": r["plan"],
            "api_key": key,
            "api_key_masked": masked,
        })
    return templates.TemplateResponse("admin_api.html", {
        "request": request,
        "current_user": admin,
        "users": users,
        "api_key_flash": api_key_flash,
        "rate_limit_min": API_RATE_LIMIT_PER_MINUTE,
        "rate_limit_day": API_RATE_LIMIT_PER_DAY,
    })


@router.post("/admin/api/grant")
def admin_api_grant(request: Request, user_id: int = Form(...)):
    require_admin(request)
    with db() as conn:
        user = conn.execute("SELECT id, email, hotel_name FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        new_key = secrets.token_urlsafe(32)
        conn.execute("UPDATE users SET api_key = ?, updated_at = ? WHERE id = ?", (new_key, now_iso(), user_id))
    request.session["api_key_flash"] = {"user_id": user_id, "key": new_key}
    return RedirectResponse("/admin/api", status_code=303)


@router.post("/admin/api/revoke")
def admin_api_revoke(request: Request, user_id: int = Form(...)):
    require_admin(request)
    with db() as conn:
        conn.execute("UPDATE users SET api_key = NULL, updated_at = ? WHERE id = ?", (now_iso(), user_id))
    return RedirectResponse("/admin/api?revoked=1", status_code=303)


@router.post("/admin/api/regenerate")
def admin_api_regenerate(request: Request, user_id: int = Form(...)):
    require_admin(request)
    with db() as conn:
        user = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        new_key = secrets.token_urlsafe(32)
        conn.execute("UPDATE users SET api_key = ?, updated_at = ? WHERE id = ?", (new_key, now_iso(), user_id))
    request.session["api_key_flash"] = {"user_id": user_id, "key": new_key}
    return RedirectResponse("/admin/api", status_code=303)
