from __future__ import annotations

from dataclasses import dataclass
import fitz  # PyMuPDF


@dataclass
class PageText:
    page_number: int
    text: str


def extract_pdf_pages(pdf_bytes: bytes) -> list[PageText]:
    """Extract text page-by-page from a PDF byte stream using PyMuPDF."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages: list[PageText] = []
    try:
        for idx in range(len(doc)):
            page = doc[idx]
            text = page.get_text("text").strip()
            pages.append(PageText(page_number=idx + 1, text=text))
    finally:
        doc.close()
    return pages


def build_sample_budget_pdf_bytes() -> bytes:
    """Generate a realistic multi-page municipal budget PDF for testing PDF upload."""
    doc = fitz.open()
    pages_content = [
        (
            "CITY OF NORTHBRIDGE - FY 2026-2027 PROPOSED MUNICIPAL BUDGET\n\n"
            "EXECUTIVE OVERVIEW\n"
            "Total Proposed General Fund: $248.50 Million\n"
            "Prepared by the Office of Management and Budget for City Council Review.\n\n"
            "SECTION 1: PUBLIC TRANSIT & MOBILITY INFRASTRUCTURE\n"
            "Allocation: $42.00 Million (16.9% of General Fund)\n"
            "Official Description: Funds MetroBus fixed-route operations, paratransit fleet\n"
            "electrification, arterial bus-only lane striping, and signal priority upgrades.\n"
            "Trade-off Note: A 5% increase (+$2.10M) restores 15-minute evening headways on\n"
            "Routes 4 and 9 but requires offsetting cuts or reserve drawdown.\n"
        ),
        (
            "SECTION 2: AFFORDABLE HOUSING & HOMELESSNESS PREVENTION\n"
            "Allocation: $31.50 Million (12.7% of General Fund)\n"
            "Official Description: Capitalizes the Municipal Housing Trust Fund, emergency\n"
            "rental assistance grants, and permanent supportive housing vouchers.\n"
            "Trade-off Note: Reducing below $30.00M risks losing $4.5M in state matching grants.\n\n"
            "SECTION 3: PUBLIC SAFETY & COMMUNITY RESPONSE\n"
            "Allocation: $68.00 Million (27.4% of General Fund)\n"
            "Official Description: Police patrol operations, fire suppression, EMS dispatch,\n"
            "and unarmed behavioral-health crisis response teams.\n"
        ),
        (
            "SECTION 4: K-12 PUBLIC SCHOOLS & YOUTH PROGRAMS\n"
            "Allocation: $64.00 Million (25.8% of General Fund)\n"
            "Official Description: Local school district operating transfer, STEM lab\n"
            "modernization, after-school care, and universal school meals.\n\n"
            "SECTION 5: PARKS, CLIMATE RESILIENCE & URBAN FORESTRY\n"
            "Allocation: $21.00 Million (8.5% of General Fund)\n"
            "Official Description: Stormwater green infrastructure, urban tree canopy\n"
            "expansion in heat-island neighborhoods, and community rec centers.\n\n"
            "SECTION 6: MUNICIPAL ADMINISTRATION & DEBT SERVICE\n"
            "Allocation: $22.00 Million (8.9% of General Fund)\n"
            "Official Description: IT modernization, permitting portal upgrades, and\n"
            "general obligation bond debt service.\n"
        ),
    ]
    for content in pages_content:
        page = doc.new_page(width=612, height=792)
        page.insert_text((54, 64), content, fontsize=11, fontname="helv")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes
