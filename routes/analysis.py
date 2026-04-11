"""Rutas web del flujo de análisis (capa delgada → services)."""
from typing import List

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from admin_ops import delete_analysis_by_id
from auth_session import require_user
from db import db
from services.analysis_service import run_web_analyze
from services.pdf_service import streaming_pdf_response_for_owned_analysis
from services.share_service import (
    analysis_detail_json_response,
    ensure_share_link_response,
    shared_analysis_page_response,
    share_analysis_by_email_response,
)

router = APIRouter(tags=["analysis_web"])


@router.post("/analyze")
async def analyze(request: Request, business_context: str = Form(""), files: List[UploadFile] = File(...)):
    return await run_web_analyze(request, business_context, files)


@router.get("/analysis/{analysis_id}")
def analysis_detail(request: Request, analysis_id: int):
    return analysis_detail_json_response(request, analysis_id)


@router.delete("/analysis/{analysis_id}")
def delete_analysis_owned(request: Request, analysis_id: int):
    user = require_user(request)
    with db() as conn:
        row = conn.execute(
            "SELECT id FROM analyses WHERE id = ? AND user_id = ?",
            (analysis_id, user["id"]),
        ).fetchone()
        if not row:
            return JSONResponse(
                {"ok": False, "error": "Lectura no encontrada o no tienes permiso para borrarla."},
                status_code=404,
            )
        delete_analysis_by_id(conn, analysis_id)
    return JSONResponse({"ok": True})


@router.post("/analysis/{analysis_id}/share")
def ensure_analysis_share_link(request: Request, analysis_id: int):
    return ensure_share_link_response(request, analysis_id)


@router.post("/analysis/{analysis_id}/share-email")
async def email_share_link(request: Request, analysis_id: int, to_email: str = Form(...)):
    return share_analysis_by_email_response(request, analysis_id, to_email)


@router.get("/s/{share_token}", response_class=HTMLResponse)
def shared_analysis_view(request: Request, share_token: str):
    return shared_analysis_page_response(request, share_token)


@router.get("/analysis/{analysis_id}/pdf")
def analysis_pdf(request: Request, analysis_id: int):
    user = require_user(request)
    return streaming_pdf_response_for_owned_analysis(user, analysis_id)
