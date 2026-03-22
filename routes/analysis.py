"""Rutas web del flujo de análisis; la lógica pesada permanece en app.py (web_*)."""
from typing import List

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

router = APIRouter(tags=["analysis_web"])


@router.post("/analyze")
async def analyze(request: Request, business_context: str = Form(""), files: List[UploadFile] = File(...)):
    from app import web_analyze

    return await web_analyze(request, business_context, files)


@router.get("/analysis/{analysis_id}")
def analysis_detail(request: Request, analysis_id: int):
    from app import web_analysis_detail_json

    return web_analysis_detail_json(request, analysis_id)


@router.post("/analysis/{analysis_id}/share")
def ensure_analysis_share_link(request: Request, analysis_id: int):
    from app import web_analysis_share_ensure

    return web_analysis_share_ensure(request, analysis_id)


@router.post("/analysis/{analysis_id}/share-email")
async def email_share_link(request: Request, analysis_id: int, to_email: str = Form(...)):
    from app import web_analysis_share_email

    return await web_analysis_share_email(request, analysis_id, to_email)


@router.get("/s/{share_token}", response_class=HTMLResponse)
def shared_analysis_view(request: Request, share_token: str):
    from app import web_shared_analysis_page

    return web_shared_analysis_page(request, share_token)


@router.get("/analysis/{analysis_id}/pdf")
def analysis_pdf(request: Request, analysis_id: int):
    from app import web_analysis_pdf_download

    return web_analysis_pdf_download(request, analysis_id)
