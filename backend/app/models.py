from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class BudgetLineItem(BaseModel):
    id: str
    category: str
    official_title: str
    plain_english_title: str
    plain_english_summary: str
    current_amount_musd: float = Field(..., description="Amount in millions USD")
    min_pct_change: float = -30.0
    max_pct_change: float = 30.0
    page_number: int = 1
    source_excerpt: str = ""
    impact_metric_name: str = "Service Capacity"
    impact_per_10pct: str = "Adjusts service coverage and staffing proportionally."
    tradeoff_note: str = ""


class DocumentAnalysis(BaseModel):
    document_id: str
    title: str
    jurisdiction: str
    fiscal_year: str
    total_budget_musd: float
    executive_summary: str
    page_count: int
    line_items: list[BudgetLineItem]
    key_tensions: list[str]
    extraction_mode: Literal["llm", "heuristic", "sample"] = "heuristic"


class SimulationRequest(BaseModel):
    document_id: str
    adjustments_pct: dict[str, float] = Field(
        default_factory=dict,
        description="Mapping of line_item.id -> percentage change (e.g. {'transit': 5.0})",
    )
    balance_mode: Literal["strict_balanced", "reserve_buffer"] = "strict_balanced"


class SimulatedLineResult(BaseModel):
    id: str
    category: str
    plain_english_title: str
    baseline_musd: float
    simulated_musd: float
    delta_musd: float
    delta_pct: float
    projected_impact: str


class SimulationResponse(BaseModel):
    document_id: str
    baseline_total_musd: float
    simulated_total_musd: float
    net_variance_musd: float
    tax_rate_impact_pct: float
    household_annual_impact_usd: float
    reserve_drawdown_musd: float
    tradeoff_warnings: list[str]
    results: list[SimulatedLineResult]


class QARequest(BaseModel):
    document_id: str
    question: str


class Citation(BaseModel):
    page_number: int
    excerpt: str
    line_item_id: str | None = None


class QAResponse(BaseModel):
    answer: str
    citations: list[Citation]
    mode: Literal["llm", "grounded_fallback"] = "grounded_fallback"


class LetterRequest(BaseModel):
    document_id: str
    resident_name: str = "Concerned Resident"
    neighborhood: str = "District 3"
    recipient_role: str = "City Council & Budget Committee"
    tone: Literal["constructive", "urgent", "data_driven"] = "constructive"
    adjustments_pct: dict[str, float] = Field(default_factory=dict)
    personal_priority: str = ""


class LetterResponse(BaseModel):
    subject: str
    letter_body: str
    mode: Literal["llm", "template"] = "template"
