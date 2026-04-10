"""Orquestación del flujo web POST /analyze (dashboard)."""
from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from auth_session import onboarding_pending, require_user
from debuglog import _dbg, _debug_log
from plan_entitlements import get_effective_plan, get_paid_plan, plan_for_openai_model
from services.analysis_core import (
    call_openai,
    enforce_plan,
    release_reserved_generation_row,
    require_business_context,
    reserve_monthly_generation_or_raise,
    save_analysis,
    summarize_reports,
    user_row_as_dict,
)
from services.share_service import public_share_base_url


async def run_web_analyze(request: Request, business_context: str, files: List[UploadFile]) -> JSONResponse:
    _debug_log("services.analysis_service", "POST /analyze entry", {"files_count": len(files) if files else 0}, "H4")
    _dbg("services.analysis_service", "entry", {"files_count": len(files) if files else 0, "filenames": [getattr(f, "filename", None) for f in (files or [])]}, "H_A")
    user = user_row_as_dict(require_user(request))
    if onboarding_pending(user):
        _dbg("services.analysis_service", "early_return", {"reason": "onboarding_pending"}, "H_C")
        return JSONResponse({"ok": False, "error": "Completa los datos de tu hotel primero.", "redirect": "/onboarding"}, status_code=400)
    if not files:
        _dbg("services.analysis_service", "early_return", {"reason": "no_files"}, "H_A")
        return JSONResponse({"ok": False, "error": "Sube al menos un reporte."}, status_code=400)
    reserved_run_log_id = None
    try:
        combined_business_context = require_business_context(business_context)
        summary = summarize_reports(files)
        _dbg("services.analysis_service", "after_summarize", {"reports_detected": summary.get("reports_detected"), "total_files": summary.get("total_files")}, "H_B")
        enforce_plan(user, summary)
        effective = get_effective_plan(user)
        reserved_run_log_id = reserve_monthly_generation_or_raise(user["id"], effective)
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
        plan_for_model = plan_for_openai_model(effective)
        _dbg("services.analysis_service", "before_call_openai", {}, "H_D")
        analysis = call_openai(summary, combined_business_context, hotel_context, plan_for_model)
        n = summary["reports_detected"]
        title = f"Lectura comercial · {n} fuente{'s' if n != 1 else ''} · {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        analysis_id, share_token = save_analysis(
            user["id"], title, effective, summary, analysis, files, reserved_run_log_id=reserved_run_log_id
        )
        reserved_run_log_id = None
        created_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")[:19].replace("T", " ")
        share_url = f"{public_share_base_url()}/s/{share_token}"
        _debug_log("services.analysis_service", "POST /analyze success", {"analysis_id": analysis_id}, "H4")
        _dbg("services.analysis_service", "success", {"analysis_id": analysis_id}, "H_D")
        billing = get_paid_plan(user)
        return JSONResponse({
            "ok": True,
            "analysis_id": analysis_id,
            "title": title,
            "created_at": created_at,
            "summary": summary,
            "analysis": analysis,
            "plan": billing,
            "billing_plan": billing,
            "effective_plan": effective,
            "share_url": share_url,
        })
    except HTTPException as e:
        if reserved_run_log_id is not None:
            release_reserved_generation_row(reserved_run_log_id, user["id"])
        _dbg("services.analysis_service", "http_exception", {"detail": e.detail, "status_code": e.status_code}, "H_C")
        return JSONResponse({"ok": False, "error": e.detail}, status_code=e.status_code)
    except ValueError as e:
        if reserved_run_log_id is not None:
            release_reserved_generation_row(reserved_run_log_id, user["id"])
        _dbg("services.analysis_service", "value_error", {"message": str(e)}, "H_B")
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    except Exception as e:
        if reserved_run_log_id is not None:
            release_reserved_generation_row(reserved_run_log_id, user["id"])
        import traceback
        traceback.print_exc()
        _debug_log("services.analysis_service", "POST /analyze exception", {"error": str(e)}, "H4")
        _dbg("services.analysis_service", "exception", {"exc_type": type(e).__name__, "exc_msg": str(e)}, "H_B")
        err_msg = str(e).strip() if str(e) else "Error desconocido"
        return JSONResponse({"ok": False, "error": f"No se pudo completar el análisis. Intenta de nuevo más tarde. ({err_msg})"}, status_code=500)
