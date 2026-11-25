from fastapi.testclient import TestClient

from app.main import app
from app.pdf_parser import build_sample_budget_pdf_bytes

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_sample_and_simulate():
    sample_res = client.get("/api/sample")
    assert sample_res.status_code == 200
    doc = sample_res.json()
    assert doc["document_id"] == "sample-northbridge-fy27"
    assert len(doc["line_items"]) == 6

    sim_res = client.post(
        "/api/simulate",
        json={
            "document_id": doc["document_id"],
            "adjustments_pct": {"transit": 5.0, "housing": -10.0},
            "balance_mode": "strict_balanced",
        },
    )
    assert sim_res.status_code == 200
    sim = sim_res.json()
    assert sim["net_variance_musd"] < 0
    assert any("Grant Cliff Risk" in w for w in sim["tradeoff_warnings"])


def test_pdf_upload_and_qa_and_letter():
    pdf_bytes = build_sample_budget_pdf_bytes()
    upload_res = client.post(
        "/api/upload",
        files={"file": ("northbridge_budget.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload_res.status_code == 200
    doc = upload_res.json()
    assert doc["page_count"] == 3
    assert len(doc["line_items"]) >= 3

    qa_res = client.post(
        "/api/qa",
        json={"document_id": doc["document_id"], "question": "What does transit fund?"},
    )
    assert qa_res.status_code == 200
    assert len(qa_res.json()["citations"]) >= 1

    letter_res = client.post(
        "/api/letter",
        json={
            "document_id": doc["document_id"],
            "resident_name": "Alex Rivera",
            "neighborhood": "Eastside",
            "adjustments_pct": {doc["line_items"][0]["id"]: 5.0},
            "tone": "constructive",
        },
    )
    assert letter_res.status_code == 200
    assert "Alex Rivera" in letter_res.json()["letter_body"]
