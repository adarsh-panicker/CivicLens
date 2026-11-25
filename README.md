# CivicLens — Plain-English Local Policy & Budget Simulator

Built for the **Creators AI Winter Challenge**.

CivicLens transforms dense municipal budget PDFs, zoning bills, and school board proposals into an interactive, plain-English decision simulator. Residents can explore line items with page citations, test budget trade-offs with live sliders, inspect downstream fiscal/grant-cliff warnings, ask citation-grounded questions, and generate personalized public-comment letters.

## Stack
- **Backend:** Python, FastAPI, PyMuPDF (`fitz`), Pydantic, HTTPX (supports Gemini or OpenAI structured JSON outputs with a built-in deterministic/heuristic fallback).
- **Frontend:** React, TypeScript, Vite, Recharts, Lucide Icons.

## Quick Start

### 1. Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
# Optional: copy .env.example to .env and add GEMINI_API_KEY or OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`.
