"""Operaciones de borrado para panel admin (análisis, usuario completo)."""
from pathlib import Path

ADMIN_PLAN_VALUES = frozenset({"free", "pro", "pro_plus"})


def _delete_uploaded_files_for_analysis(conn, analysis_id: int) -> None:
    rows = conn.execute("SELECT stored_path FROM uploaded_files WHERE analysis_id = ?", (analysis_id,)).fetchall()
    for r in rows:
        try:
            p = Path(r["stored_path"])
            if p.is_file():
                p.unlink()
        except OSError:
            pass
    conn.execute("DELETE FROM uploaded_files WHERE analysis_id = ?", (analysis_id,))


def delete_analysis_by_id(conn, analysis_id: int) -> bool:
    row = conn.execute("SELECT id FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
    if not row:
        return False
    # Conserva la fila de cupo mensual (generations_this_month); el id ya no apunta a analyses.
    conn.execute("UPDATE analysis_run_log SET analysis_id = NULL WHERE analysis_id = ?", (analysis_id,))
    conn.execute("DELETE FROM analysis_whatsapp_sends WHERE analysis_id = ?", (analysis_id,))
    _delete_uploaded_files_for_analysis(conn, analysis_id)
    conn.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
    return True


def delete_user_and_related(conn, user_id: int) -> bool:
    rows = conn.execute("SELECT id FROM analyses WHERE user_id = ?", (user_id,)).fetchall()
    for r in rows:
        _delete_uploaded_files_for_analysis(conn, r["id"])
    conn.execute("DELETE FROM analysis_run_log WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM analysis_whatsapp_sends WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM analyses WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM hotel_invites WHERE created_by = ?", (user_id,))
    hotel_ids = [int(r["hotel_id"]) for r in conn.execute("SELECT hotel_id FROM hotel_members WHERE user_id = ?", (user_id,)).fetchall()]
    conn.execute("DELETE FROM hotel_members WHERE user_id = ?", (user_id,))
    for hid in hotel_ids:
        if not conn.execute("SELECT 1 FROM hotel_members WHERE hotel_id = ?", (hid,)).fetchone():
            conn.execute("DELETE FROM hotel_invites WHERE hotel_id = ?", (hid,))
            conn.execute("DELETE FROM hotels WHERE id = ?", (hid,))
    conn.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM password_resets WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM login_tokens WHERE user_id = ?", (user_id,))
    cur = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    return cur.rowcount > 0
