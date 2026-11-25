export interface BudgetLineItem {
  id: string;
  category: string;
  official_title: string;
  plain_english_title: string;
  plain_english_summary: string;
  current_amount_musd: number;
  min_pct_change: number;
  max_pct_change: number;
  page_number: number;
  source_excerpt: string;
  impact_metric_name: string;
  impact_per_10pct: string;
  tradeoff_note: string;
}

export interface DocumentAnalysis {
  document_id: string;
  title: string;
  jurisdiction: string;
  fiscal_year: string;
  total_budget_musd: number;
  executive_summary: string;
  page_count: number;
  line_items: BudgetLineItem[];
  key_tensions: string[];
  extraction_mode: "llm" | "heuristic" | "sample";
}

export interface SimulatedLineResult {
  id: string;
  category: string;
  plain_english_title: string;
  baseline_musd: number;
  simulated_musd: number;
  delta_musd: number;
  delta_pct: number;
  projected_impact: string;
}

export interface SimulationResponse {
  document_id: string;
  baseline_total_musd: number;
  simulated_total_musd: number;
  net_variance_musd: number;
  tax_rate_impact_pct: number;
  household_annual_impact_usd: number;
  reserve_drawdown_musd: number;
  tradeoff_warnings: string[];
  results: SimulatedLineResult[];
}

export interface Citation {
  page_number: number;
  excerpt: string;
  line_item_id?: string | null;
}

export interface QAResponse {
  answer: string;
  citations: Citation[];
  mode: "llm" | "grounded_fallback";
}

export interface LetterResponse {
  subject: string;
  letter_body: string;
  mode: "llm" | "template";
}
