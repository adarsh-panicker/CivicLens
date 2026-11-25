from __future__ import annotations

from app.models import (
    DocumentAnalysis,
    SimulatedLineResult,
    SimulationRequest,
    SimulationResponse,
)

# Typical mid-size municipality assumptions for translating $M variance into household tax impact
ESTIMATED_TAXABLE_HOUSEHOLDS = 85_000
AVG_ANNUAL_PROPERTY_TAX_USD = 4_200.0
RAINY_DAY_RESERVE_MUSD = 18.0


def run_budget_simulation(
    doc: DocumentAnalysis, req: SimulationRequest
) -> SimulationResponse:
    """Deterministically compute budget deltas, tax impacts, and policy trade-off warnings."""
    results: list[SimulatedLineResult] = []
    baseline_total = 0.0
    simulated_total = 0.0
    warnings: list[str] = []

    for item in doc.line_items:
        raw_pct = req.adjustments_pct.get(item.id, 0.0)
        clamped_pct = max(item.min_pct_change, min(item.max_pct_change, raw_pct))

        baseline = round(item.current_amount_musd, 2)
        simulated = round(baseline * (1.0 + clamped_pct / 100.0), 2)
        delta = round(simulated - baseline, 2)

        baseline_total += baseline
        simulated_total += simulated

        if abs(clamped_pct) < 0.01:
            impact_text = "No change from baseline proposal."
        else:
            direction = "Increase" if clamped_pct > 0 else "Reduction"
            impact_text = f"{direction} of ${abs(delta):.2f}M ({clamped_pct:+.1f}%). {item.impact_per_10pct}"

        # Domain-specific policy guardrails
        if item.id == "housing" and simulated < 30.0 and baseline >= 30.0:
            warnings.append(
                f"Grant Cliff Risk: {item.plain_english_title} fell to ${simulated:.2f}M, "
                "below the $30.0M threshold needed to keep $4.5M in state matching funds."
            )
        if item.id == "education" and clamped_pct < -5.0:
            warnings.append(
                f"Maintenance-of-Effort Alert: Cutting {item.plain_english_title} by {clamped_pct:.1f}% "
                "may trigger state education funding penalties."
            )
        if item.id == "admin_debt" and clamped_pct < -10.0:
            warnings.append(
                f"Fixed Obligation Constraint: Over half of {item.plain_english_title} is legally "
                "obligated bond debt; deep cuts fall disproportionately on permitting & IT."
            )

        results.append(
            SimulatedLineResult(
                id=item.id,
                category=item.category,
                plain_english_title=item.plain_english_title,
                baseline_musd=baseline,
                simulated_musd=simulated,
                delta_musd=delta,
                delta_pct=round(clamped_pct, 1),
                projected_impact=impact_text,
            )
        )

    baseline_total = round(baseline_total, 2)
    simulated_total = round(simulated_total, 2)
    net_variance = round(simulated_total - baseline_total, 2)

    reserve_drawdown = 0.0
    tax_rate_impact_pct = 0.0
    household_annual_impact_usd = 0.0

    if net_variance > 0:
        if req.balance_mode == "reserve_buffer":
            reserve_drawdown = min(net_variance, RAINY_DAY_RESERVE_MUSD)
            uncovered = max(0.0, net_variance - reserve_drawdown)
            if reserve_drawdown > 0:
                warnings.append(
                    f"Reserve Drawdown: Uses ${reserve_drawdown:.2f}M of the ${RAINY_DAY_RESERVE_MUSD:.1f}M "
                    "rainy-day fund (one-time buffer; recurring deficit remains next year)."
                )
        else:
            uncovered = net_variance

        if uncovered > 0:
            tax_rate_impact_pct = round((uncovered / baseline_total) * 100.0, 2)
            household_annual_impact_usd = round(
                (uncovered * 1_000_000.0) / ESTIMATED_TAXABLE_HOUSEHOLDS, 2
            )
            warnings.append(
                f"Unfunded Deficit (+${uncovered:.2f}M): Requires ~{tax_rate_impact_pct:+.2f}% "
                f"local tax increase (~${household_annual_impact_usd:.0f}/yr per household) or offsetting cuts."
            )
    elif net_variance < 0:
        tax_rate_impact_pct = round((net_variance / baseline_total) * 100.0, 2)
        household_annual_impact_usd = round(
            (net_variance * 1_000_000.0) / ESTIMATED_TAXABLE_HOUSEHOLDS, 2
        )

    return SimulationResponse(
        document_id=doc.document_id,
        baseline_total_musd=baseline_total,
        simulated_total_musd=simulated_total,
        net_variance_musd=net_variance,
        tax_rate_impact_pct=tax_rate_impact_pct,
        household_annual_impact_usd=household_annual_impact_usd,
        reserve_drawdown_musd=round(reserve_drawdown, 2),
        tradeoff_warnings=warnings,
        results=results,
    )
