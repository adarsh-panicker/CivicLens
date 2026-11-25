from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.llm_service import (
    analyze_document,
    answer_question,
    generate_public_comment_letter,
)
from app.models import (
    DocumentAnalysis,
    LetterRequest,
    LetterResponse,
    QARequest,
    QAResponse,
    SimulationRequest,
    SimulationResponse,
)
from app.pdf_parser import PageText, build_sample_budget_pdf_bytes, extract_pdf_pages
from app.sample_data import get_sample_municipal_budget
from app.simulator import run_budget_simulation

load_dotenv()

app = FastAPI(
    title="CivicLens API",
    description="Plain-English Local Policy & Budget Simulator",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for active hackathon demo session
DOCUMENTS: dict[str, DocumentAnalysis] = {}
RAW_PAGES: dict[str, list[PageText]] = {}

# Pre-seed sample document
_sample = get_sample_municipal_budget()
DOCUMENTS[_sample.document_id] = _sample


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "civiclens-api"}


@app.get("/api/sample", response_model=DocumentAnalysis)
def load_sample() -> DocumentAnalysis:
    sample = get_sample_municipal_budget()
    DOCUMENTS[sample.document_id] = sample
    return sample


@app.get("/api/sample-pdf")
def download_sample_pdf() -> Response:
    pdf_bytes = build_sample_budget_pdf_bytes()
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=northbridge_fy27_budget.pdf"},
    )


@app.post("/api/upload", response_model=DocumentAnalysis)
async def upload_pdf(file: UploadFile = File(...)) -> DocumentAnalysis:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a valid .pdf file.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        pages = extract_pdf_pages(pdf_bytes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {exc}") from exc

    analysis = await analyze_document(file.filename, pages)
    DOCUMENTS[analysis.document_id] = analysis
    RAW_PAGES[analysis.document_id] = pages
    return analysis


@app.post("/api/simulate", response_model=SimulationResponse)
def simulate(req: SimulationRequest) -> SimulationResponse:
    doc = DOCUMENTS.get(req.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found. Load sample or upload a PDF first.")
    return run_budget_simulation(doc, req)


@app.post("/api/qa", response_model=QAResponse)
async def qa(req: QARequest) -> QAResponse:
    doc = DOCUMENTS.get(req.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    return await answer_question(doc, RAW_PAGES.get(req.document_id), req.question)


@app.post("/api/letter", response_model=LetterResponse)
async def letter(req: LetterRequest) -> LetterResponse:
    doc = DOCUMENTS.get(req.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return await generate_public_comment_letter(doc, req)
