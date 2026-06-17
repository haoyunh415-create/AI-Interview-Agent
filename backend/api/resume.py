"""API routes for resume analysis — text-based and PDF upload."""

import asyncio

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from backend.session_store import create_session, get_orchestrator
from core.api_key import resolve_api_key

router = APIRouter()


class AnalyzeRequest(BaseModel):
    resume_text: str
    api_key: str = ""
    provider: str | None = None
    model: str | None = None


class AnalyzeResponse(BaseModel):
    session_id: str
    profile: dict


class PdfAnalyzeResponse(BaseModel):
    session_id: str
    profile: dict
    filename: str
    text_length: int


# ═════════════════════════════════════════════════════
# Text-based resume analysis (existing)
# ═════════════════════════════════════════════════════


@router.post("/resume/analyze", response_model=AnalyzeResponse)
async def analyze_resume(req: AnalyzeRequest) -> AnalyzeResponse:
    if not req.resume_text.strip():
        raise HTTPException(400, "Resume text is required")

    effective_key = resolve_api_key(req.api_key)
    session_id = create_session(effective_key, provider=req.provider, model=req.model)
    orch = get_orchestrator(session_id)
    if orch is None:
        raise HTTPException(500, "Failed to create session")

    try:
        profile = await asyncio.to_thread(orch.analyze_resume, req.resume_text)
        return AnalyzeResponse(session_id=session_id, profile=profile or {})
    except Exception as e:
        raise HTTPException(500, str(e)) from e


# ═════════════════════════════════════════════════════
# PDF upload + analysis
# ═════════════════════════════════════════════════════


@router.post("/resume/analyze/pdf", response_model=PdfAnalyzeResponse)
async def analyze_resume_pdf(
    file: UploadFile = File(...),
    api_key: str = Form(""),
    provider: str | None = Form(None),
    model: str | None = Form(None),
) -> PdfAnalyzeResponse:
    """Upload a PDF resume, extract text server-side, and analyze it.

    Accepts ``multipart/form-data`` with fields:
    - ``file``: the PDF file
    - ``api_key``: (optional) LLM API key — falls back to server env
    - ``provider``: (optional) LLM provider
    - ``model``: (optional) model name

    Requires ``PyMuPDF`` (already listed in ``requirements.txt``).
    """
    effective_key = resolve_api_key(api_key)

    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(400, f"Failed to read file: {e}")

    if len(content) == 0:
        raise HTTPException(400, "Empty file")

    if len(content) > 20 * 1024 * 1024:  # 20MB
        raise HTTPException(400, "File too large (max 20MB)")

    # Extract text using PyMuPDF
    text = _extract_pdf_text(content)
    if not text.strip():
        raise HTTPException(400, "Could not extract any text from the PDF")

    # Analyze
    session_id = create_session(effective_key, provider=provider, model=model)
    orch = get_orchestrator(session_id)
    if orch is None:
        raise HTTPException(500, "Failed to create session")

    try:
        profile = orch.analyze_resume(text)
        return PdfAnalyzeResponse(
            session_id=session_id,
            profile=profile or {},
            filename=file.filename,
            text_length=len(text),
        )
    except Exception as e:
        raise HTTPException(500, str(e)) from e


# ═════════════════════════════════════════════════════
# PDF text extraction
# ═════════════════════════════════════════════════════


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from a PDF file using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise HTTPException(
            500,
            "PDF extraction requires PyMuPDF. Install: pip install PyMuPDF",
        )

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages: list[str] = []
        for _i, page in enumerate(doc):
            text = page.get_text().strip()
            if text:
                pages.append(text)
        doc.close()
        return "\n\n".join(pages)
    except Exception as e:
        raise HTTPException(400, f"Failed to parse PDF: {e}")
