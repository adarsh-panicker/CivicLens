import { useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  Check,
  Copy,
  Download,
  FileText,
  MessageSquareText,
  RotateCcw,
  Send,
  SlidersHorizontal,
  Upload,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type {
  DocumentAnalysis,
  LetterResponse,
  QAResponse,
  SimulationResponse,
} from "./types";

export default function App() {
  const [doc, setDoc] = useState<DocumentAnalysis | null>(null);
  const [adjustments, setAdjustments] = useState<Record<string, number>>({});
  const [balanceMode, setBalanceMode] = useState<"strict_balanced" | "reserve_buffer">("strict_balanced");
  const [sim, setSim] = useState<SimulationResponse | null>(null);
  const [loadingDoc, setLoadingDoc] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [rightTab, setRightTab] = useState<"chart" | "qa" | "letter">("chart");

  // Q&A state
  const [question, setQuestion] = useState("What happens if we cut Affordable Housing by 10%?");
  const [qaResult, setQaResult] = useState<QAResponse | null>(null);
  const [loadingQa, setLoadingQa] = useState(false);

  // Public comment letter state
  const [residentName, setResidentName] = useState("Jordan Patel");
  const [neighborhood, setNeighborhood] = useState("District 3 (Oak Corridor)");
  const [tone, setTone] = useState<"constructive" | "urgent" | "data_driven">("constructive");
  const [personalPriority, setPersonalPriority] = useState(
    "Evening bus frequency directly affects shift workers and students in our neighborhood."
  );
  const [letter, setLetter] = useState<LetterResponse | null>(null);
  const [loadingLetter, setLoadingLetter] = useState(false);
  const [copied, setCopied] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  async function loadSample() {
    setLoadingDoc(true);
    setError(null);
    try {
      const res = await fetch("/api/sample");
      if (!res.ok) throw new Error("Failed to load sample budget");
      const data: DocumentAnalysis = await res.json();
      setDoc(data);
      setAdjustments({});
      setQaResult(null);
      setLetter(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      setLoadingDoc(false);
    }
  }

  useEffect(() => {
    void loadSample();
  }, []);

  useEffect(() => {
    if (!doc) return;
    let cancelled = false;
    async function runSim() {
      try {
        const res = await fetch("/api/simulate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            document_id: doc!.document_id,
            adjustments_pct: adjustments,
            balance_mode: balanceMode,
          }),
        });
        if (!res.ok) return;
        const data: SimulationResponse = await res.json();
        if (!cancelled) setSim(data);
      } catch {
        // Ignore transient network errors while dragging sliders
      }
    }
    void runSim();
    return () => {
      cancelled = true;
    };
  }, [doc, adjustments, balanceMode]);

  async function handleFileUpload(file: File) {
    setLoadingDoc(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(errBody.detail || "PDF upload failed");
      }
      const data: DocumentAnalysis = await res.json();
      setDoc(data);
      setAdjustments({});
      setQaResult(null);
      setLetter(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoadingDoc(false);
    }
  }

  async function askQuestion() {
    if (!doc || !question.trim()) return;
    setLoadingQa(true);
    try {
      const res = await fetch("/api/qa", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document_id: doc.document_id, question }),
      });
      if (!res.ok) throw new Error("Q&A request failed");
      setQaResult(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Q&A error");
    } finally {
      setLoadingQa(false);
    }
  }

  async function generateLetter() {
    if (!doc) return;
    setLoadingLetter(true);
    try {
      const res = await fetch("/api/letter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          document_id: doc.document_id,
          resident_name: residentName,
          neighborhood,
          tone,
          adjustments_pct: adjustments,
          personal_priority: personalPriority,
        }),
      });
      if (!res.ok) throw new Error("Letter generation failed");
      setLetter(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Letter error");
    } finally {
      setLoadingLetter(false);
    }
  }

  const chartData = useMemo(() => {
    if (!sim) return [];
    return sim.results.map((r) => ({
      name: r.category,
      Baseline: r.baseline_musd,
      "Your Proposal": r.simulated_musd,
    }));
  }, [sim]);

  async function goHome() {
    setRightTab("chart");
    await loadSample();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <div className="container">
      <header className="header">
        <button
          type="button"
          className="logo-btn"
          onClick={() => void goHome()}
          title="Return to CivicLens Home"
          aria-label="Return to CivicLens Home"
        >
          <svg
            width="46"
            height="46"
            viewBox="0 0 48 48"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <rect width="48" height="48" rx="12" fill="#FACC15" />
            <path
              d="M24 9L11 16V19H37V16L24 9Z"
              fill="#3B0764"
            />
            <rect x="14" y="21" width="4" height="12" rx="1" fill="#581C87" />
            <rect x="22" y="21" width="4" height="12" rx="1" fill="#581C87" />
            <rect x="30" y="21" width="4" height="12" rx="1" fill="#581C87" />
            <rect x="11" y="34" width="26" height="4" rx="1.5" fill="#3B0764" />
            <circle cx="34" cy="14" r="6" fill="#7C3AED" stroke="#FEF08A" strokeWidth="2" />
            <path d="M38.5 18.5L42 22" stroke="#FEF08A" strokeWidth="2.4" strokeLinecap="round" />
          </svg>
          <div>
            <h1>CivicLens</h1>
            <p>
              Plain-English Local Policy &amp; Budget Simulator — translate dense municipal PDFs,
              test trade-offs, and generate public-comment letters.
            </p>
          </div>
        </button>

        <div className="actions">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            style={{ display: "none" }}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void handleFileUpload(f);
            }}
          />
          <button
            className="btn btn-primary"
            onClick={() => fileInputRef.current?.click()}
            disabled={loadingDoc}
          >
            <Upload size={16} />
            {loadingDoc ? "Parsing PDF..." : "Upload Policy / Budget PDF"}
          </button>
          <button className="btn btn-secondary" onClick={() => void loadSample()} disabled={loadingDoc}>
            <FileText size={16} />
            Sample City Budget
          </button>
          <a className="btn btn-secondary" href="/api/sample-pdf" download>
            <Download size={16} />
            Sample PDF
          </a>
        </div>
      </header>

      {error && (
        <div className="warning-box" style={{ marginBottom: 16 }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {doc && (
        <>
          {/* Document Summary */}
          <section className="card" style={{ marginBottom: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 10 }}>
              <div>
                <span className="badge">{doc.jurisdiction} • {doc.fiscal_year}</span>
                <h2 style={{ margin: "6px 0 4px", fontSize: "1.25rem" }}>{doc.title}</h2>
              </div>
              <span className="badge" style={{ alignSelf: "flex-start" }}>
                Mode: {doc.extraction_mode.toUpperCase()} • {doc.page_count} page(s)
              </span>
            </div>
            <p style={{ margin: "6px 0 10px", color: "var(--muted)" }}>{doc.executive_summary}</p>
            {doc.key_tensions.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {doc.key_tensions.map((t, idx) => (
                  <span
                    key={idx}
                    style={{
                      fontSize: "0.82rem",
                      background: "#f1f5f9",
                      padding: "5px 10px",
                      borderRadius: 8,
                    }}
                  >
                    • {t}
                  </span>
                ))}
              </div>
            )}
          </section>

          {/* KPI Strip */}
          {sim && (
            <section className="kpi-grid">
              <div className="card">
                <div className="kpi-label">Baseline Total</div>
                <div className="kpi-value">${sim.baseline_total_musd.toFixed(2)}M</div>
              </div>
              <div className="card">
                <div className="kpi-label">Your Simulated Budget</div>
                <div className="kpi-value">${sim.simulated_total_musd.toFixed(2)}M</div>
              </div>
              <div className="card">
                <div className="kpi-label">Net Variance</div>
                <div
                  className="kpi-value"
                  style={{
                    color:
                      sim.net_variance_musd > 0
                        ? "var(--danger)"
                        : sim.net_variance_musd < 0
                        ? "var(--success)"
                        : "var(--text)",
                  }}
                >
                  {sim.net_variance_musd >= 0 ? "+" : ""}
                  ${sim.net_variance_musd.toFixed(2)}M
                </div>
              </div>
              <div className="card">
                <div className="kpi-label">Est. Household Tax Impact</div>
                <div className="kpi-value">
                  {sim.household_annual_impact_usd >= 0 ? "+" : ""}$
                  {sim.household_annual_impact_usd.toFixed(0)}/yr
                </div>
              </div>
            </section>
          )}

          {/* Main 2-column workspace */}
          <div className="main-grid">
            {/* Left: Interactive Budget Sliders */}
            <section className="card">
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: 10,
                  marginBottom: 14,
                }}
              >
                <h3 style={{ margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
                  <SlidersHorizontal size={18} />
                  Interactive Budget &amp; Policy Sliders
                </h3>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <select
                    className="select"
                    style={{ width: "auto", padding: "6px 10px", fontSize: "0.82rem" }}
                    value={balanceMode}
                    onChange={(e) =>
                      setBalanceMode(e.target.value as "strict_balanced" | "reserve_buffer")
                    }
                  >
                    <option value="strict_balanced">Strict Balanced (Tax Offset)</option>
                    <option value="reserve_buffer">Use Rainy-Day Reserve ($18M)</option>
                  </select>
                  <button
                    className="btn btn-outline"
                    style={{ padding: "6px 10px", fontSize: "0.82rem" }}
                    onClick={() => setAdjustments({})}
                  >
                    <RotateCcw size={14} /> Reset
                  </button>
                </div>
              </div>

              {doc.line_items.map((item) => {
                const pct = adjustments[item.id] ?? 0;
                const simLine = sim?.results.find((r) => r.id === item.id);
                return (
                  <div className="line-item" key={item.id}>
                    <div className="line-item-top">
                      <div>
                        <span className="badge">{item.category} • p.{item.page_number}</span>
                        <h4 style={{ margin: "4px 0 2px" }}>{item.plain_english_title}</h4>
                        <div style={{ fontSize: "0.78rem", color: "var(--muted)" }}>
                          Official: {item.official_title}
                        </div>
                      </div>
                      <div style={{ textAlign: "right", minWidth: 110 }}>
                        <div style={{ fontWeight: 700, fontSize: "1.05rem" }}>
                          ${(simLine?.simulated_musd ?? item.current_amount_musd).toFixed(2)}M
                        </div>
                        <div
                          style={{
                            fontSize: "0.8rem",
                            fontWeight: 600,
                            color: pct > 0 ? "var(--primary)" : pct < 0 ? "var(--danger)" : "var(--muted)",
                          }}
                        >
                          {pct > 0 ? "+" : ""}
                          {pct.toFixed(0)}% ({pct === 0 ? "Baseline" : `${(simLine?.delta_musd ?? 0) >= 0 ? "+" : ""}$${(simLine?.delta_musd ?? 0).toFixed(2)}M`})
                        </div>
                      </div>
                    </div>

                    <p style={{ margin: "8px 0 6px", fontSize: "0.88rem" }}>
                      {item.plain_english_summary}
                    </p>

                    <div className="slider-row">
                      <span style={{ fontSize: "0.78rem", color: "var(--muted)", width: 42 }}>
                        {item.min_pct_change}%
                      </span>
                      <input
                        type="range"
                        min={item.min_pct_change}
                        max={item.max_pct_change}
                        step={1}
                        value={pct}
                        onChange={(e) =>
                          setAdjustments((prev) => ({
                            ...prev,
                            [item.id]: Number(e.target.value),
                          }))
                        }
                      />
                      <span style={{ fontSize: "0.78rem", color: "var(--muted)", width: 42, textAlign: "right" }}>
                        +{item.max_pct_change}%
                      </span>
                    </div>

                    <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginTop: 6 }}>
                      <strong>{item.impact_metric_name}:</strong>{" "}
                      {simLine?.projected_impact || item.impact_per_10pct}
                    </div>
                  </div>
                );
              })}
            </section>

            {/* Right: Trade-off Chart, Citation Q&A, Public Comment Letter */}
            <section className="card">
              <div className="tabs">
                <button
                  className={`tab ${rightTab === "chart" ? "active" : ""}`}
                  onClick={() => setRightTab("chart")}
                >
                  Trade-Off Visualizer
                </button>
                <button
                  className={`tab ${rightTab === "qa" ? "active" : ""}`}
                  onClick={() => setRightTab("qa")}
                >
                  Citation Q&amp;A
                </button>
                <button
                  className={`tab ${rightTab === "letter" ? "active" : ""}`}
                  onClick={() => setRightTab("letter")}
                >
                  Public Comment Letter
                </button>
              </div>

              {rightTab === "chart" && (
                <div>
                  <div style={{ width: "100%", height: 320 }}>
                    <ResponsiveContainer>
                      <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-15} textAnchor="end" />
                        <YAxis tick={{ fontSize: 11 }} unit="M" />
                        <Tooltip formatter={(val: number) => `$${val.toFixed(2)}M`} />
                        <Legend />
                        <Bar dataKey="Baseline" fill="#a855f7" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="Your Proposal" fill="#eab308" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>

                  <h4 style={{ margin: "16px 0 8px", display: "flex", alignItems: "center", gap: 6 }}>
                    <AlertTriangle size={16} color="#d97706" />
                    Downstream Trade-Off Alerts
                  </h4>
                  {sim && sim.tradeoff_warnings.length > 0 ? (
                    sim.tradeoff_warnings.map((w, i) => (
                      <div className="warning-box" key={i}>
                        {w}
                      </div>
                    ))
                  ) : (
                    <p style={{ fontSize: "0.88rem", color: "var(--muted)" }}>
                      No fiscal or grant-cliff warnings triggered under your current adjustments.
                    </p>
                  )}
                </div>
              )}

              {rightTab === "qa" && (
                <div>
                  <p style={{ fontSize: "0.88rem", color: "var(--muted)", marginTop: 0 }}>
                    Ask anything about this proposal. Answers are grounded with page citations.
                  </p>
                  <div style={{ display: "flex", gap: 8 }}>
                    <input
                      className="input"
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && void askQuestion()}
                      placeholder="e.g. What happens to evening bus service?"
                    />
                    <button
                      className="btn btn-primary"
                      onClick={() => void askQuestion()}
                      disabled={loadingQa}
                    >
                      <Send size={15} />
                      {loadingQa ? "..." : "Ask"}
                    </button>
                  </div>

                  {qaResult && (
                    <div style={{ marginTop: 16 }}>
                      <div
                        style={{
                          whiteSpace: "pre-line",
                          background: "var(--surface-alt)",
                          padding: 14,
                          borderRadius: 10,
                          border: "1px solid var(--border)",
                          fontSize: "0.9rem",
                        }}
                      >
                        {qaResult.answer}
                      </div>
                      {qaResult.citations.map((c, idx) => (
                        <div className="citation" key={idx}>
                          <strong>Page {c.page_number}:</strong> “{c.excerpt}”
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {rightTab === "letter" && (
                <div>
                  <p style={{ fontSize: "0.88rem", color: "var(--muted)", marginTop: 0 }}>
                    Generate a personalized public-comment email reflecting your exact slider choices.
                  </p>
                  <div style={{ display: "grid", gap: 10 }}>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <input
                        className="input"
                        value={residentName}
                        onChange={(e) => setResidentName(e.target.value)}
                        placeholder="Your Name"
                      />
                      <input
                        className="input"
                        value={neighborhood}
                        onChange={(e) => setNeighborhood(e.target.value)}
                        placeholder="Neighborhood / District"
                      />
                    </div>
                    <select
                      className="select"
                      value={tone}
                      onChange={(e) =>
                        setTone(e.target.value as "constructive" | "urgent" | "data_driven")
                      }
                    >
                      <option value="constructive">Tone: Constructive &amp; Collaborative</option>
                      <option value="data_driven">Tone: Data-Driven &amp; Analytical</option>
                      <option value="urgent">Tone: Urgent Community Appeal</option>
                    </select>
                    <textarea
                      className="textarea"
                      value={personalPriority}
                      onChange={(e) => setPersonalPriority(e.target.value)}
                      placeholder="Why this matters to you or your neighborhood..."
                    />
                    <button
                      className="btn btn-primary"
                      onClick={() => void generateLetter()}
                      disabled={loadingLetter}
                    >
                      <MessageSquareText size={16} />
                      {loadingLetter ? "Drafting Letter..." : "Generate Public Comment Letter"}
                    </button>
                  </div>

                  {letter && (
                    <div style={{ marginTop: 16 }}>
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: 8,
                        }}
                      >
                        <strong style={{ fontSize: "0.9rem" }}>{letter.subject}</strong>
                        <button
                          className="btn btn-outline"
                          style={{ padding: "5px 10px", fontSize: "0.8rem" }}
                          onClick={() => {
                            void navigator.clipboard.writeText(
                              `Subject: ${letter.subject}\n\n${letter.letter_body}`
                            );
                            setCopied(true);
                            setTimeout(() => setCopied(false), 2000);
                          }}
                        >
                          {copied ? <Check size={14} /> : <Copy size={14} />}
                          {copied ? "Copied" : "Copy"}
                        </button>
                      </div>
                      <pre
                        style={{
                          whiteSpace: "pre-wrap",
                          fontFamily: "inherit",
                          fontSize: "0.88rem",
                          background: "var(--surface-alt)",
                          padding: 14,
                          borderRadius: 10,
                          border: "1px solid var(--border)",
                          margin: 0,
                        }}
                      >
                        {letter.letter_body}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </section>
          </div>
        </>
      )}

      <footer className="footer">
        Made by Adarsh Panicker • CivicLens
      </footer>
    </div>
  );
}
