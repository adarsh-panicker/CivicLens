from __future__ import annotations

import json
import os
import re
import uuid
import httpx

from app.models import (
    BudgetLineItem,
    Citation,
    DocumentAnalysis,
    LetterRequest,
    LetterResponse,
    QAResponse,
)
from app.pdf_parser import PageText


def _get_provider() -> tuple[str, str, str] | None:
    """Return (provider, api_key, model) if configured, else None."""
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if gemini_key:
        return ("gemini", gemini_key, os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    if openai_key:
        return ("openai", openai_key, os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    return None


async def _call_llm_json(prompt: str) -> dict | None:
    provider = _get_provider()
    if not provider:
        return None
    kind, api_key, model = provider

    async with httpx.AsyncClient(timeout=45.0) as client:
        if kind == "gemini":
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:generateContent?key={api_key}"
            )
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.2,
                },
            }
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)

        if kind == "openai":
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}"}
            payload = {
                "model": model,
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": "You are CivicLens, a precise civic policy and municipal budget analyst. Always output valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
            }
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            return json.loads(text)

    return None


def _heuristic_extract(filename: str, pages: list[PageText]) -> DocumentAnalysis:
    """Fallback structured extractor that parses dollar figures & sections from arbitrary PDFs."""
    full_text = "\n\n".join(f"[Page {p.page_number}]\n{p.text}" for p in pages)
    doc_id = f"doc-{uuid.uuid4().hex[:8]}"

    # Find sections with dollar amounts like $42.00M, $42 Million, $42,000,000
    money_pattern = re.compile(
        r"(?P<label>[A-Za-z0-9 &,\-/]{4,70})[:\-\s]+\$(?P<num>\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?P<unit>million|billion|m|b|k)?",
        re.IGNORECASE,
    )

    items: list[BudgetLineItem] = []
    seen_labels: set[str] = set()

    for page in pages:
        for match in money_pattern.finditer(page.text):
            label = match.group("label").strip(" :-•\n\t")
            if len(label) < 4 or label.lower() in seen_labels:
                continue
            if any(skip in label.lower() for skip in ["total", "general fund", "page", "fiscal"]):
                continue

            raw_num = float(match.group("num").replace(",", ""))
            unit = (match.group("unit") or "").lower()
            if unit in ("billion", "b"):
                amount_musd = raw_num * 1000.0
            elif unit in ("million", "m"):
                amount_musd = raw_num
            elif unit == "k":
                amount_musd = raw_num / 1000.0
            elif raw_num > 100_000:
                amount_musd = raw_num / 1_000_000.0
            else:
                amount_musd = raw_num

            if amount_musd <= 0.05:
                continue

            seen_labels.add(label.lower())
            snippet_start = max(0, match.start() - 40)
            snippet_end = min(len(page.text), match.end() + 140)
            excerpt = " ".join(page.text[snippet_start:snippet_end].split())

            item_id = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")[:28] or f"item_{len(items)+1}"
            items.append(
                BudgetLineItem(
                    id=item_id,
                    category=_infer_category(label),
                    official_title=label,
                    plain_english_title=label.title(),
                    plain_english_summary=f"Extracted from page {page.page_number}: {excerpt[:160]}",
                    current_amount_musd=round(amount_musd, 2),
                    page_number=page.page_number,
                    source_excerpt=excerpt,
                    impact_metric_name="Program Capacity",
                    impact_per_10pct="Adjusts funding and service delivery proportionally.",
                )
            )
            if len(items) >= 8:
                break
        if len(items) >= 8:
            break

    if not items:
        items = [
            BudgetLineItem(
                id="general_programs",
                category="Operations",
                official_title="Document Policy & Program Allocation",
                plain_english_title="Core Program Allocation",
                plain_english_summary=(
                    "No explicit dollar tables were detected in this PDF; a baseline placeholder "
                    "was created so you can explore policy trade-offs and Q&A."
                ),
                current_amount_musd=10.0,
                page_number=1,
                source_excerpt=full_text[:220].replace("\n", " "),
            )
        ]

    total = round(sum(i.current_amount_musd for i in items), 2)
    return DocumentAnalysis(
        document_id=doc_id,
        title=filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title(),
        jurisdiction="Uploaded Municipality / Agency",
        fiscal_year="Extracted Document",
        total_budget_musd=total,
        executive_summary=(
            f"Parsed {len(pages)} page(s) from '{filename}' and identified {len(items)} "
            f"major budget/policy items totaling ${total:.2f}M."
        ),
        page_count=len(pages),
        line_items=items,
        key_tensions=[
            "Trade-offs depend on balancing program expansion against local revenue or reserve limits.",
            "Add a GEMINI_API_KEY or OPENAI_API_KEY in backend/.env for deeper semantic clause extraction.",
        ],
        extraction_mode="heuristic",
    )


def _infer_category(label: str) -> str:
    low = label.lower()
    if any(k in low for k in ["transit", "bus", "rail", "road", "mobility", "transport"]):
        return "Transportation"
    if any(k in low for k in ["housing", "rent", "homeless", "zoning"]):
        return "Housing"
    if any(k in low for k in ["police", "fire", "ems", "safety", "crisis"]):
        return "Public Safety"
    if any(k in low for k in ["school", "education", "youth", "student", "stem"]):
        return "Education"
    if any(k in low for k in ["park", "climate", "tree", "water", "green", "environment"]):
        return "Climate & Parks"
    return "Operations"


async def analyze_document(filename: str, pages: list[PageText]) -> DocumentAnalysis:
    """Extract structured budget/policy line items via LLM if available, else heuristic parser."""
    joined_pages = "\n\n".join(f"--- PAGE {p.page_number} ---\n{p.text}" for p in pages)[:28000]
    prompt = f"""
Analyze the following local government budget, zoning bill, or school board proposal.
Return a JSON object with this exact schema:
{{
  "title": "string",
  "jurisdiction": "string",
  "fiscal_year": "string",
  "executive_summary": "2-3 plain-English sentences summarizing what this proposal does and why it matters to residents",
  "key_tensions": ["2-4 concise bullet strings about the biggest trade-offs or risks"],
  "line_items": [
    {{
      "id": "short_snake_case_id",
      "category": "Transportation | Housing | Public Safety | Education | Climate & Parks | Operations",
      "official_title": "exact or close official name from document",
      "plain_english_title": "short jargon-free title",
      "plain_english_summary": "1-2 sentences in plain English explaining what residents actually get",
      "current_amount_musd": 12.5,
      "page_number": 1,
      "source_excerpt": "short verbatim quote from that page",
      "impact_metric_name": "e.g. Service Hours or Households Served",
      "impact_per_10pct": "concrete real-world effect of a 10% change",
      "tradeoff_note": "short note on risks or matching-grant cliffs if any"
    }}
  ]
}}

Document ({filename}):
{joined_pages}
"""
    try:
        parsed = await _call_llm_json(prompt)
    except Exception:
        parsed = None

    if parsed and parsed.get("line_items"):
        items = [BudgetLineItem(**item) for item in parsed["line_items"]]
        total = round(sum(i.current_amount_musd for i in items), 2)
        return DocumentAnalysis(
            document_id=f"doc-{uuid.uuid4().hex[:8]}",
            title=parsed.get("title") or filename,
            jurisdiction=parsed.get("jurisdiction") or "Local Government",
            fiscal_year=parsed.get("fiscal_year") or "Current Cycle",
            total_budget_musd=total,
            executive_summary=parsed.get("executive_summary") or "",
            page_count=len(pages),
            line_items=items,
            key_tensions=parsed.get("key_tensions") or [],
            extraction_mode="llm",
        )

    return _heuristic_extract(filename, pages)


async def answer_question(
    doc: DocumentAnalysis, pages: list[PageText] | None, question: str
) -> QAResponse:
    """Answer a resident's question grounded in document line items and page excerpts."""
    context_blocks = [
        f"[Page {item.page_number} | id={item.id}] {item.plain_english_title} (${item.current_amount_musd:.2f}M): "
        f"{item.plain_english_summary} Excerpt: {item.source_excerpt} Tradeoff: {item.tradeoff_note}"
        for item in doc.line_items
    ]
    if pages:
        for p in pages[:6]:
            context_blocks.append(f"[Raw Page {p.page_number}] {p.text[:1500]}")

    prompt = f"""
Answer the resident's question in plain, non-partisan English using ONLY the provided document context.
Return JSON:
{{
  "answer": "clear 2-4 sentence answer",
  "citations": [
    {{"page_number": 1, "excerpt": "short supporting quote", "line_item_id": "optional_id"}}
  ]
}}

Question: {question}

Context:
{chr(10).join(context_blocks)}
"""
    try:
        parsed = await _call_llm_json(prompt)
    except Exception:
        parsed = None

    if parsed and parsed.get("answer"):
        citations = [Citation(**c) for c in parsed.get("citations", [])]
        return QAResponse(answer=parsed["answer"], citations=citations, mode="llm")

    # Grounded keyword-matching fallback
    q_words = {w for w in re.findall(r"[a-z0-9]+", question.lower()) if len(w) > 2}
    scored: list[tuple[int, BudgetLineItem]] = []
    for item in doc.line_items:
        haystack = (
            f"{item.official_title} {item.plain_english_title} "
            f"{item.plain_english_summary} {item.source_excerpt} {item.tradeoff_note}"
        ).lower()
        score = sum(1 for w in q_words if w in haystack)
        scored.append((score, item))
    scored.sort(key=lambda pair: pair[0], reverse=True)

    top_items = [item for score, item in scored[:2] if score > 0] or doc.line_items[:2]
    answer_parts = [
        f"Based on {doc.title} ({doc.jurisdiction}), here is what the proposal says:"
    ]
    citations: list[Citation] = []
    for item in top_items:
        answer_parts.append(
            f"• {item.plain_english_title} (${item.current_amount_musd:.2f}M, Page {item.page_number}): "
            f"{item.plain_english_summary}"
            + (f" Note: {item.tradeoff_note}" if item.tradeoff_note else "")
        )
        citations.append(
            Citation(
                page_number=item.page_number,
                excerpt=item.source_excerpt or item.plain_english_summary,
                line_item_id=item.id,
            )
        )

    return QAResponse(
        answer="\n".join(answer_parts),
        citations=citations,
        mode="grounded_fallback",
    )


async def generate_public_comment_letter(
    doc: DocumentAnalysis, req: LetterRequest
) -> LetterResponse:
    """Generate a personalized public-comment letter reflecting the user's simulated budget changes."""
    changes_summary = []
    for item in doc.line_items:
        pct = req.adjustments_pct.get(item.id, 0.0)
        if abs(pct) >= 0.5:
            new_amt = item.current_amount_musd * (1.0 + pct / 100.0)
            changes_summary.append(
                f"{item.plain_english_title}: {pct:+.1f}% (${item.current_amount_musd:.2f}M -> ${new_amt:.2f}M)"
            )

    changes_text = "; ".join(changes_summary) if changes_summary else "Keep baseline allocations with stronger transparency"

    prompt = f"""
Write a concise, persuasive public-comment letter from a resident to {req.recipient_role} regarding "{doc.title}" ({doc.jurisdiction}).
Tone: {req.tone}
Resident: {req.resident_name} ({req.neighborhood})
Requested budget adjustments: {changes_text}
Personal priority note: {req.personal_priority or 'None provided'}

Return JSON:
{{
  "subject": "email subject line",
  "letter_body": "complete formatted letter with greeting and sign-off"
}}
"""
    try:
        parsed = await _call_llm_json(prompt)
    except Exception:
        parsed = None

    if parsed and parsed.get("letter_body"):
        return LetterResponse(
            subject=parsed.get("subject", f"Public Comment on {doc.title}"),
            letter_body=parsed["letter_body"],
            mode="llm",
        )

    tone_opening = {
        "constructive": "Thank you for your work preparing the proposed budget and for considering resident feedback.",
        "urgent": "I am writing to urge immediate revisions before the upcoming vote.",
        "data_driven": "After reviewing the line-item figures and downstream trade-offs in the proposal, I submit the following analysis.",
    }[req.tone]

    bullet_lines = (
        "\n".join(f"  - {c}" for c in changes_summary)
        if changes_summary
        else "  - Maintain balanced investments while protecting core transit and housing services."
    )
    priority_para = f"\n\nIn particular, {req.personal_priority.strip()}" if req.personal_priority.strip() else ""

    letter_body = (
        f"Dear {req.recipient_role},\n\n"
        f"As a resident of {req.neighborhood}, I am writing regarding the {doc.title} for {doc.jurisdiction}. "
        f"{tone_opening}\n\n"
        f"Specifically, I encourage the committee to adopt the following adjustments:\n"
        f"{bullet_lines}"
        f"{priority_para}\n\n"
        f"These targeted adjustments reflect community priorities while keeping long-term fiscal trade-offs transparent.\n\n"
        f"Sincerely,\n"
        f"{req.resident_name}\n"
        f"{req.neighborhood}"
    )
    return LetterResponse(
        subject=f"Public Comment: {doc.title} ({req.neighborhood})",
        letter_body=letter_body,
        mode="template",
    )
