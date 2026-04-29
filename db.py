"""
Capa de persistencia SQLite para DragonApp.

Fase 1: context manager `db()` + esquema inicial. Sin ORM.
Deuda (Fase 2): migraciones versionadas; posible split de consultas por dominio (users, analyses).
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager

from config import DB_PATH


@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hotel_name TEXT NOT NULL,
                hotel_size TEXT,
                hotel_category TEXT,
                hotel_location TEXT,
                contact_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                plan TEXT NOT NULL DEFAULT 'free',
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                last_login_at TEXT,
                login_count INTEGER NOT NULL DEFAULT 0,
                is_admin INTEGER NOT NULL DEFAULT 0,
                role TEXT NOT NULL DEFAULT 'hotel_lead',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT,
                plan_at_analysis TEXT NOT NULL,
                file_count INTEGER NOT NULL,
                days_covered INTEGER NOT NULL,
                summary_json TEXT NOT NULL,
                analysis_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                share_token TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS uploaded_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                original_name TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(analysis_id) REFERENCES analyses(id)
            );

            CREATE TABLE IF NOT EXISTS billing_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stripe_event_id TEXT UNIQUE,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                ended_at TEXT,
                request_count INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )
        for col in [
            "hotel_size",
            "hotel_category",
            "hotel_location",
            "last_login_at",
            "login_count",
            "is_admin",
            "api_key",
            "hotel_stars",
            "hotel_location_context",
            "hotel_pms",
            "hotel_channel_manager",
            "hotel_booking_engine",
            "hotel_tech_other",
            "hotel_google_business_url",
            "hotel_expedia_url",
            "hotel_booking_url",
            # Pullso Brief: número destino en WhatsApp (E.164, p. ej. +52999...)
            "pullso_whatsapp_to",
            "pullso_whatsapp_opt_in",
            "pullso_whatsapp_opt_in_at",
            "manual_plan_override",
            "manual_plan_expires_at",
            "manual_plan_note",
            "manual_plan_updated_at",
        ]:
            try:
                if col in ["login_count", "is_admin", "hotel_stars", "pullso_whatsapp_opt_in"]:
                    conn.execute(f"ALTER TABLE users ADD COLUMN {col} INTEGER DEFAULT 0")
                else:
                    conn.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
            except sqlite3.OperationalError:
                pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN manual_plan_updated_by INTEGER")
        except sqlite3.OperationalError:
            pass
        for legal_col in ("legal_accepted_at", "legal_docs_version"):
            try:
                conn.execute(f"ALTER TABLE users ADD COLUMN {legal_col} TEXT")
            except sqlite3.OperationalError:
                pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN hotel_room_count INTEGER")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN hotel_ota_commissions_json TEXT")
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE analyses ADD COLUMN share_token TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_analyses_share_token ON analyses(share_token) WHERE share_token IS NOT NULL"
            )
        except sqlite3.OperationalError:
            pass

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT NOT NULL UNIQUE,
                expires_at TEXT NOT NULL,
                used INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS login_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL,
                purpose TEXT NOT NULL DEFAULT 'magic_link',
                expires_at TEXT NOT NULL,
                used_at TEXT,
                created_at TEXT NOT NULL,
                requested_ip TEXT,
                user_agent TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id),
                UNIQUE(token_hash)
            );
            """
        )
        try:
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_login_tokens_user_purpose ON login_tokens(user_id, purpose)"
            )
        except sqlite3.OperationalError:
            pass
        # Leads consultoría (/consultoria) — fuera del núcleo SaaS; ver docs/dragonapp_phase1.md
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS consulting_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                company TEXT,
                type TEXT,
                message TEXT,
                phone TEXT,
                lang TEXT,
                created_at TEXT NOT NULL
            );
            """
        )

        # The Circle — Revenue Manager marketplace (perfiles, proyectos y matches)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS revenue_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                full_name TEXT,
                phone TEXT,
                city TEXT,
                country TEXT,
                photo_url TEXT,
                professional_title TEXT,
                bio TEXT,
                how_help TEXT,
                highlights TEXT,
                years_experience INTEGER,
                current_role TEXT,
                hotel_types_json TEXT,
                properties_managed INTEGER,
                specialties_json TEXT,
                tools_json TEXT,
                languages_json TEXT,
                hourly_rate_mxn INTEGER,
                monthly_rate_mxn INTEGER,
                availability_hours INTEGER,
                work_models_json TEXT,
                delivery_modes_json TEXT,
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )
        try:
            conn.execute("ALTER TABLE revenue_profiles ADD COLUMN delivery_modes_json TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_revenue_profiles_status ON revenue_profiles(status)"
            )
        except sqlite3.OperationalError:
            pass

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS circle_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hotel_name TEXT,
                hotel_type TEXT,
                city TEXT,
                scope TEXT NOT NULL,
                required_specialties_json TEXT,
                required_tools_json TEXT,
                work_model TEXT,
                estimated_duration TEXT,
                budget_range TEXT,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL
            );
            """
        )
        try:
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_circle_projects_status ON circle_projects(status)"
            )
        except sqlite3.OperationalError:
            pass

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS circle_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                revenue_profile_id INTEGER NOT NULL,
                match_score REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'potential',
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES circle_projects(id),
                FOREIGN KEY(revenue_profile_id) REFERENCES revenue_profiles(id)
            );
            """
        )
        try:
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_circle_matches_profile_status ON circle_matches(revenue_profile_id, status)"
            )
        except sqlite3.OperationalError:
            pass

        # Seed mínimo de proyectos mock (solo si no hay ninguno)
        try:
            row = conn.execute("SELECT COUNT(*) AS c FROM circle_projects").fetchone()
            count = int(row["c"]) if row else 0
        except Exception:
            count = 0
        if count == 0:
            conn.executemany(
                """
                INSERT INTO circle_projects (
                    hotel_name, hotel_type, city, scope, required_specialties_json,
                    required_tools_json, work_model, estimated_duration, budget_range,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
                """,
                [
                    (
                        "Hotel Boutique (confidencial)",
                        "Boutique",
                        "CDMX",
                        "Optimización de pricing y mix de canales + reportes ejecutivos",
                        json.dumps(["Pricing", "Distribución", "Reportes comerciales"]),
                        json.dumps(["Duetto", "Excel / Google Sheets"]),
                        "Mensual",
                        "3 meses",
                        "$20k–$40k MXN/mes",
                        "2026-04-25T00:00:00Z",
                    ),
                    (
                        "Hotel Urbano (confidencial)",
                        "Urbano",
                        "Guadalajara",
                        "Auditoría comercial + quick wins para ADR y ocupación",
                        json.dumps(["Auditoría comercial", "Pricing"]),
                        json.dumps(["Booking.com Extranet", "Expedia Partner Central"]),
                        "Por alcance",
                        "2 a 3 semanas",
                        "$12k–$25k MXN",
                        "2026-04-25T00:00:00Z",
                    ),
                ],
            )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS hospitality_diag_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                lang TEXT NOT NULL,
                contact_name TEXT NOT NULL,
                contact_email TEXT NOT NULL,
                contact_phone TEXT,
                hotel_name TEXT NOT NULL,
                savings_mxn REAL NOT NULL,
                growth_mxn REAL NOT NULL,
                growth_rate REAL NOT NULL,
                payload_json TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pullso_whatsapp_waitlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                company TEXT,
                whatsapp TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL
            );
            """
        )
        try:
            conn.execute("ALTER TABLE pullso_yc_leads RENAME TO pullso_mvp_leads")
        except sqlite3.OperationalError:
            pass
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pullso_mvp_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                hotel_name TEXT NOT NULL,
                hotel_url TEXT,
                pms TEXT,
                channel_manager TEXT,
                booking_engine TEXT,
                lang TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        try:
            conn.execute("ALTER TABLE pullso_mvp_leads ADD COLUMN email TEXT")
        except sqlite3.OperationalError:
            pass

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_run_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                analysis_id INTEGER UNIQUE,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_run_log_user_created ON analysis_run_log(user_id, created_at)"
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO analysis_run_log (user_id, analysis_id, created_at)
            SELECT user_id, id, created_at FROM analyses
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_whatsapp_sends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                analysis_id INTEGER NOT NULL,
                phone_e164 TEXT NOT NULL,
                channel TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(analysis_id) REFERENCES analyses(id)
            );
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_wa_sends_lookup "
            "ON analysis_whatsapp_sends(user_id, analysis_id, phone_e164, created_at)"
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS hotels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                pullso_whatsapp_to TEXT,
                pullso_whatsapp_opt_in INTEGER NOT NULL DEFAULT 0,
                pullso_whatsapp_opt_in_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS hotel_members (
                hotel_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                PRIMARY KEY (hotel_id, user_id),
                FOREIGN KEY (hotel_id) REFERENCES hotels(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_hotel_members_user ON hotel_members(user_id)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS hotel_invites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hotel_id INTEGER NOT NULL,
                email_norm TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                token_hash TEXT NOT NULL UNIQUE,
                expires_at TEXT NOT NULL,
                accepted_at TEXT,
                created_by INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (hotel_id) REFERENCES hotels(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            );
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_hotel_invites_hotel_email ON hotel_invites(hotel_id, email_norm)"
        )
        try:
            conn.execute("ALTER TABLE analyses ADD COLUMN hotel_id INTEGER REFERENCES hotels(id)")
        except sqlite3.OperationalError:
            pass
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_analyses_hotel_id ON analyses(hotel_id)"
        )
        try:
            from services.hotel_pullso import migrate_legacy_users_to_hotels

            migrate_legacy_users_to_hotels(conn)
        except Exception:
            pass

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pms_inbound_routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                hotel_id INTEGER,
                token TEXT NOT NULL UNIQUE,
                pms_vendor TEXT NOT NULL DEFAULT '',
                notify_whatsapp INTEGER NOT NULL DEFAULT 1,
                last_analysis_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (hotel_id) REFERENCES hotels(id),
                FOREIGN KEY (last_analysis_id) REFERENCES analyses(id)
            );
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_pms_inbound_routes_user ON pms_inbound_routes(user_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_pms_inbound_user_hotel ON pms_inbound_routes(user_id, hotel_id)"
        )
        # Una inbox por (usuario, hotel): rellenar hotel_id heredado y deduplicar.
        try:
            conn.execute(
                """
                UPDATE pms_inbound_routes SET hotel_id = (
                    SELECT hm.hotel_id FROM hotel_members hm
                    WHERE hm.user_id = pms_inbound_routes.user_id
                    ORDER BY hm.hotel_id LIMIT 1
                )
                WHERE hotel_id IS NULL
                AND EXISTS (
                    SELECT 1 FROM hotel_members hm2 WHERE hm2.user_id = pms_inbound_routes.user_id
                )
                """
            )
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute(
                """
                DELETE FROM pms_inbound_routes WHERE rowid NOT IN (
                    SELECT MIN(rowid) FROM pms_inbound_routes GROUP BY user_id, hotel_id
                )
                """
            )
        except sqlite3.OperationalError:
            pass
