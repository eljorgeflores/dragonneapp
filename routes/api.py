"""API REST v1 documentada en /docs (mismo prefijo /api/v1)."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from auth_session import get_api_user
from db import db
from plan_entitlements import get_effective_plan, get_paid_plan, plan_for_openai_model
from services.analysis_core import (
    call_openai,
    enforce_plan,
    save_analysis,
    summarize_reports,
    user_row_as_dict,
)
from services.pdf_service import streaming_pdf_response_for_owned_analysis
from services.share_service import public_share_base_url

router = APIRouter(prefix="/api/v1", tags=["API v1"])


@router.get("/me", summary="Perfil del usuario asociado a la API key")
def api_me(user: sqlite3.Row = Depends(get_api_user)):
    """
    `plan` y `billing_plan` reflejan `users.plan` (facturación / Stripe).
    `effective_plan` aplica a límites y análisis (máximo entre base y override manual vigente).
    """
    billing = get_paid_plan(user)
    return {
        "id": user["id"],
        "email": user["email"],
        "hotel_name": user["hotel_name"],
        "plan": billing,
        "billing_plan": billing,
        "effective_plan": get_effective_plan(user),
        "hotel_size": user["hotel_size"],
        "hotel_category": user["hotel_category"],
        "hotel_location": user["hotel_location"],
    }


@router.post("/analyze", summary="Ejecutar análisis de reportes")
async def api_analyze(
    user: sqlite3.Row = Depends(get_api_user),
    business_context: str = Form(""),
    files: List[UploadFile] = File(...),
):
    """
    Sube uno o más reportes (CSV/Excel) y devuelve el análisis en JSON.
    Mismo límite de plan que en la web (días, archivos, número de análisis).

    Respuesta: `plan` y `billing_plan` = `users.plan`; `effective_plan` = plan aplicado al análisis.
    """
    user = user_row_as_dict(user)
    if not files:
        raise HTTPException(status_code=400, detail="Carga al menos un archivo CSV o Excel.")
    try:
        summary = summarize_reports(files)
        enforce_plan(user, summary)
        hotel_context = {
            "hotel_nombre": user["hotel_name"],
            "hotel_tamano": user["hotel_size"] or "",
            "hotel_categoria": user["hotel_category"] or "",
            "hotel_ubicacion": user["hotel_location"] or "",
            "hotel_estrellas": user.get("hotel_stars") or 0,
            "hotel_ubicacion_destino": user.get("hotel_location_context") or "",
            "hotel_pms": user.get("hotel_pms") or "",
            "hotel_channel_manager": user.get("hotel_channel_manager") or "",
            "hotel_booking_engine": user.get("hotel_booking_engine") or "",
            "hotel_tech_other": user.get("hotel_tech_other") or "",
            "hotel_google_business_url": user.get("hotel_google_business_url") or "",
            "hotel_expedia_url": user.get("hotel_expedia_url") or "",
            "hotel_booking_url": user.get("hotel_booking_url") or "",
        }
        combined_business_context = business_context or ""
        effective = get_effective_plan(user)
        plan_for_model = plan_for_openai_model(effective)
        analysis = call_openai(summary, combined_business_context, hotel_context, plan_for_model)
        nrep = summary["reports_detected"]
        title = f"Lectura comercial · {nrep} fuente{'s' if nrep != 1 else ''} · {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        analysis_id, share_token = save_analysis(user["id"], title, effective, summary, analysis, files)
        billing = get_paid_plan(user)
        return {
            "ok": True,
            "analysis_id": analysis_id,
            "title": title,
            "summary": summary,
            "analysis": analysis,
            "plan": billing,
            "billing_plan": billing,
            "effective_plan": effective,
            "share_url": f"{public_share_base_url()}/s/{share_token}",
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo completar el análisis. Intenta más tarde.")


@router.get("/analyses", summary="Listar análisis del usuario")
def api_list_analyses(user: sqlite3.Row = Depends(get_api_user)):
    """Lista los análisis del usuario (últimos 50)."""
    with db() as conn:
        rows = conn.execute(
            "SELECT id, title, plan_at_analysis, file_count, days_covered, created_at FROM analyses WHERE user_id = ? ORDER BY created_at DESC LIMIT 50",
            (user["id"],),
        ).fetchall()
    return {
        "ok": True,
        "analyses": [
            {
                "id": row["id"],
                "title": row["title"],
                "plan_at_analysis": row["plan_at_analysis"],
                "file_count": row["file_count"],
                "days_covered": row["days_covered"],
                "created_at": row["created_at"],
            }
            for row in rows
        ],
    }


@router.get("/analyses/{analysis_id}", summary="Obtener un análisis por ID")
def api_get_analysis(analysis_id: int, user: sqlite3.Row = Depends(get_api_user)):
    """Devuelve el JSON completo de un análisis (summary + analysis)."""
    with db() as conn:
        row = conn.execute("SELECT * FROM analyses WHERE id = ? AND user_id = ?", (analysis_id, user["id"])).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    return {
        "ok": True,
        "id": row["id"],
        "title": row["title"],
        "created_at": row["created_at"],
        "summary": json.loads(row["summary_json"]),
        "analysis": json.loads(row["analysis_json"]),
    }


@router.get("/analyses/{analysis_id}/pdf", summary="Descargar PDF del análisis")
def api_analysis_pdf(analysis_id: int, user: sqlite3.Row = Depends(get_api_user)):
    """Genera y devuelve el PDF del análisis (mismo formato que la web: branding, tabla resumen, hotel y fecha)."""
    return streaming_pdf_response_for_owned_analysis(user, analysis_id)
