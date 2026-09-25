"""
Unit tests for the Public Dataset (NSL-KDD) Source Adapter.
Verifies authentic ingestion, schema population, zero-fabrication guarantees,
and clean analytics execution on real telemetry records.
"""

import pytest
from src.db.connection import get_db_connection
from src.generator.public_dataset_adapter import (
    ingest_public_dataset,
    get_public_dataset_provenance,
    get_public_compatibility_matrix,
)
from src.analytics.scoring import calculate_supervisory_attention_scores


@pytest.fixture
def public_conn():
    conn = get_db_connection(db_path=":memory:")
    res = ingest_public_dataset(conn)
    yield conn, res
    conn.close()


def test_public_dataset_ingestion_counts(public_conn):
    """
    Verifies that public NSL-KDD dataset ingests authentic alerts and assets
    while strictly keeping human operational tables empty (zero fabrication).
    """
    conn, res = public_conn
    assert res["status"] == "success"
    assert res["alerts_count"] == 1011
    assert res["cses_count"] == 6
    assert res["assets_count"] == 60
    assert res["attack_events"] == 495
    assert res["benign_events"] == 516

    # Verify zero fabrication on human/workflow tables
    for tbl in ["analysts", "tickets", "investigation_notes", "shift_logs"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        assert count == 0, f"Table {tbl} must be empty under authentic public data (zero fabrication)"


def test_public_dataset_provenance():
    """Verifies that dataset provenance citations and URLs are well-formed."""
    prov = get_public_dataset_provenance()
    assert prov["dataset_id"] == "NSL-KDD-2009-UNB"
    assert "Canadian Institute for Cybersecurity" in prov["publisher"]
    assert "Tavallaee" in prov["citation"]
    assert prov["download_url"].startswith("http")


def test_public_compatibility_matrix():
    """Verifies that the compatibility matrix clearly delineates supported vs unassessable capabilities."""
    matrix = get_public_compatibility_matrix()
    assert matrix["Threat Detection"]["status"] == "SUPPORTED"
    assert matrix["Cyber Resilience"]["status"] == "SUPPORTED"
    assert matrix["Security Operations"]["status"] == "SUPPORTED"
    assert matrix["Investigation Quality"]["status"] == "NOT ASSESSABLE (No Triage Notes in Source)"
    assert matrix["Escalation Compliance"]["status"] == "NOT ASSESSABLE (No Tickets in Source)"


def test_public_analytics_execution(public_conn):
    """
    Verifies that SAT-SA supervisory analytics executes cleanly on public network telemetry
    without crashing on empty operational tables.
    """
    conn, _ = public_conn
    results = calculate_supervisory_attention_scores(conn)
    assert "cse_scores" in results
    assert "findings_df" in results

    # CSE scores should be computed for the 6 network service asset groups
    assert len(results["cse_scores"]) == 6
    # Findings should be generated for detected attacks/negative space
    assert not results["findings_df"].empty
