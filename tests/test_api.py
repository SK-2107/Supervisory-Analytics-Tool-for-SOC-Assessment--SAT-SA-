"""
Integration tests for FastAPI REST endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["problem_statement"] == "SIH26157"


def test_seed_and_analytics_flow():
    # 1. Seed data
    seed_res = client.post("/api/v1/ingest/seed-sample-data?num_days=2")
    if seed_res.status_code != 200:
        print("SEED ERROR RESPONSE:", seed_res.json())
    assert seed_res.status_code == 200
    assert seed_res.json()["status"] == "success"

    # 2. Validate dataset schema
    val_res = client.get("/api/v1/ingest/validate")
    assert val_res.status_code == 200
    assert val_res.json()["validation"]["valid"] is True

    # 3. Provenance metadata
    prov_res = client.get("/api/v1/ingest/provenance")
    assert prov_res.status_code == 200
    assert "provenance" in prov_res.json()

    # 4. Run analytics
    analytics_res = client.post("/api/v1/analytics/run")
    assert analytics_res.status_code == 200
    assert analytics_res.json()["status"] == "success"

    # 5. Fetch CSE assessment queue
    queue_res = client.get("/api/v1/analytics/cses")
    assert queue_res.status_code == 200
    assert "cses" in queue_res.json()

    # 6. Fetch structured findings
    findings_res = client.get("/api/v1/analytics/findings")
    assert findings_res.status_code == 200
    findings_data = findings_res.json()
    assert "findings" in findings_data
    assert len(findings_data["findings"]) > 0

    # 7. Trace first finding to evidence records
    finding_id = findings_data["findings"][0]["finding_id"]
    evidence_res = client.get(f"/api/v1/analytics/evidence/{finding_id}")
    assert evidence_res.status_code == 200
    assert evidence_res.json()["status"] == "success"

    # 8. Fetch supporting analyst and ticket queues
    analysts_res = client.get("/api/v1/analytics/analysts")
    assert analysts_res.status_code == 200
    assert "analysts" in analysts_res.json()

    tickets_res = client.get("/api/v1/analytics/tickets")
    assert tickets_res.status_code == 200
    assert "tickets" in tickets_res.json()

    # 9. Fetch peer benchmarking and assets
    bench_res = client.get("/api/v1/analytics/benchmarking")
    assert bench_res.status_code == 200

    assets_res = client.get("/api/v1/analytics/assets")
    assert assets_res.status_code == 200
    assert assets_res.json()["count"] > 0

    # 10. Fetch PDF report
    pdf_res = client.get("/api/v1/reports/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"

