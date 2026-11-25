from __future__ import annotations

from app.models import BudgetLineItem, DocumentAnalysis


def get_sample_municipal_budget() -> DocumentAnalysis:
    """Return a rich, realistic municipal budget dataset for instant exploration."""
    items = [
        BudgetLineItem(
            id="transit",
            category="Transportation",
            official_title="Transit Authority Operating Subsidy & BRT Capital Match",
            plain_english_title="Public Transit & Bus Rapid Transit",
            plain_english_summary=(
                "Pays for daily city bus routes, ADA paratransit rides for seniors, "
                "and bus-only lanes on Main & Oak corridors."
            ),
            current_amount_musd=42.0,
            min_pct_change=-25.0,
            max_pct_change=35.0,
            page_number=1,
            source_excerpt=(
                "Section 1: Public Transit & Mobility Infrastructure — $42.00M. "
                "Funds MetroBus fixed-route operations, paratransit fleet electrification, "
                "and signal priority upgrades."
            ),
            impact_metric_name="Evening & Weekend Frequency",
            impact_per_10pct="Cuts or adds ~180,000 annual bus service hours (~4 min headway shift).",
            tradeoff_note="Each +5% (+$2.1M) restores 15-minute evening service on high-ridership corridors.",
        ),
        BudgetLineItem(
            id="housing",
            category="Housing",
            official_title="Municipal Housing Trust & Eviction Diversion Program",
            plain_english_title="Affordable Housing & Rent Relief",
            plain_english_summary=(
                "Builds below-market apartments, funds emergency rent assistance to prevent "
                "evictions, and supports shelters."
            ),
            current_amount_musd=31.5,
            min_pct_change=-25.0,
            max_pct_change=40.0,
            page_number=2,
            source_excerpt=(
                "Section 2: Affordable Housing & Homelessness Prevention — $31.50M. "
                "Reducing below $30.00M risks forfeiting $4.5M in state matching grants."
            ),
            impact_metric_name="Supported Households",
            impact_per_10pct="Affects ~420 rental assistance vouchers or ~65 affordable units.",
            tradeoff_note="Cutting more than 5% drops below the $30M threshold for state matching funds.",
        ),
        BudgetLineItem(
            id="public_safety",
            category="Public Safety",
            official_title="Police, Fire Suppression, EMS & Crisis Response",
            plain_english_title="Police, Fire, EMS & Crisis Teams",
            plain_english_summary=(
                "Covers 911 dispatch, firefighters, paramedics, police patrols, and unarmed "
                "mental-health crisis response teams."
            ),
            current_amount_musd=68.0,
            min_pct_change=-20.0,
            max_pct_change=25.0,
            page_number=2,
            source_excerpt=(
                "Section 3: Public Safety & Community Response — $68.00M. "
                "Includes police patrol operations, fire suppression, EMS dispatch, and crisis teams."
            ),
            impact_metric_name="Emergency Response Time",
            impact_per_10pct="Shifts staffing by ~38 FTEs; ~30–45 sec impact on non-critical response.",
            tradeoff_note="Largest single budget line (27.4%); small percentage shifts free up significant capital.",
        ),
        BudgetLineItem(
            id="education",
            category="Education",
            official_title="Unified School District Local Operating Transfer",
            plain_english_title="Public Schools & After-School Care",
            plain_english_summary=(
                "City contribution to K-12 classrooms, STEM labs, free school lunches, "
                "and subsidized after-school programs."
            ),
            current_amount_musd=64.0,
            min_pct_change=-15.0,
            max_pct_change=25.0,
            page_number=3,
            source_excerpt=(
                "Section 4: K-12 Public Schools & Youth Programs — $64.00M. "
                "Local school district operating transfer, STEM lab modernization, and universal meals."
            ),
            impact_metric_name="Classroom & Program Support",
            impact_per_10pct="Impacts ~60 instructional aides or 1,400 after-school seats.",
            tradeoff_note="State maintenance-of-effort rules penalize cuts exceeding 5% year-over-year.",
        ),
        BudgetLineItem(
            id="climate_parks",
            category="Climate & Parks",
            official_title="Stormwater Green Infrastructure & Urban Forestry",
            plain_english_title="Parks, Flood Prevention & Street Trees",
            plain_english_summary=(
                "Upgrades neighborhood parks, plants shade trees in heat-prone blocks, "
                "and builds rain gardens to stop street flooding."
            ),
            current_amount_musd=21.0,
            min_pct_change=-30.0,
            max_pct_change=40.0,
            page_number=3,
            source_excerpt=(
                "Section 5: Parks, Climate Resilience & Urban Forestry — $21.00M. "
                "Stormwater green infrastructure and urban tree canopy expansion."
            ),
            impact_metric_name="Flood-Prone Blocks Protected",
            impact_per_10pct="Adds or defers ~14 blocks of green stormwater upgrades and 1,200 trees.",
            tradeoff_note="Deferring stormwater projects increases emergency flood repair costs later.",
        ),
        BudgetLineItem(
            id="admin_debt",
            category="Operations",
            official_title="General Administration, Permitting IT & Debt Service",
            plain_english_title="City Hall Operations & Bond Payments",
            plain_english_summary=(
                "Pays for online building permits, cybersecurity, city clerk services, "
                "and interest on past infrastructure bonds."
            ),
            current_amount_musd=22.0,
            min_pct_change=-15.0,
            max_pct_change=15.0,
            page_number=3,
            source_excerpt=(
                "Section 6: Municipal Administration & Debt Service — $22.00M. "
                "IT modernization, permitting portal upgrades, and general obligation bond debt service."
            ),
            impact_metric_name="Permit Turnaround Speed",
            impact_per_10pct="Bond debt ($12M) is fixed; cuts hit permitting IT and clerk staffing.",
            tradeoff_note="Roughly 55% of this line is legally obligated bond debt and cannot be cut.",
        ),
    ]

    return DocumentAnalysis(
        document_id="sample-northbridge-fy27",
        title="FY 2026–2027 Proposed Municipal Budget",
        jurisdiction="City of Northbridge",
        fiscal_year="FY 2026–2027",
        total_budget_musd=248.5,
        executive_summary=(
            "Northbridge's $248.5M proposed budget prioritizes public safety (27.4%) and "
            "K-12 schools (25.8%), while holding transit and climate resilience flat. "
            "Rising housing costs and evening bus service cuts are the central debates ahead "
            "of next month's City Council vote."
        ),
        page_count=3,
        line_items=items,
        key_tensions=[
            "Public Safety + Schools account for 53.2% of total spending, leaving tight headroom for Transit & Housing.",
            "Cutting Affordable Housing below $30.0M (-4.8%) forfeits $4.5M in state matching grants.",
            "Increasing spending without offsetting cuts requires either a property tax hike or drawing down the $18M rainy-day reserve.",
        ],
        extraction_mode="sample",
    )
