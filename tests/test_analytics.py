"""
Unit tests for core analytics modules and supervisory attention scoring.
"""

import pytest
from src.db.connection import get_db_connection
from src.generator.mock_data import seed_database
from src.analytics.gaps import detect_execution_gaps
from src.analytics.negative_space import detect_negative_space
from src.analytics.outliers import detect_statistical_outliers
from src.analytics.anomaly import detect_multivariate_anomalies
from src.analytics.similarity import detect_repetitive_investigations
from src.analytics.scoring import calculate_supervisory_attention_scores


@pytest.fixture
def seeded_conn():
    conn = get_db_connection(db_path=":memory:")
    seed_database(conn, num_days=3)
    yield conn
    conn.close()


def test_execution_gaps(seeded_conn):
    res = detect_execution_gaps(seeded_conn)
    assert "ticket_gaps" in res
    assert "analyst_gap_summary" in res
    assert not res["ticket_gaps"].empty


def test_negative_space(seeded_conn):
    res = detect_negative_space(seeded_conn)
    assert "analyst_negative_space" in res
    assert "ticket_negative_space" in res
    assert not res["analyst_negative_space"].empty


def test_statistical_outliers(seeded_conn):
    df_outliers = detect_statistical_outliers(seeded_conn)
    assert not df_outliers.empty
    assert "outlier_score" in df_outliers.columns


def test_isolation_forest_anomalies(seeded_conn):
    df_anom = detect_multivariate_anomalies(seeded_conn)
    assert not df_anom.empty
    assert "anomaly_score" in df_anom.columns


def test_tf_idf_similarity(seeded_conn):
    res = detect_repetitive_investigations(seeded_conn, similarity_threshold=0.70)
    assert "high_similarity_pairs" in res
    assert "ticket_similarity_scores" in res


def test_composite_supervisory_scoring(seeded_conn):
    res = calculate_supervisory_attention_scores(seeded_conn)
    df_analysts = res["analyst_scores"]
    df_tickets = res["ticket_scores"]

    assert not df_analysts.empty
    assert not df_tickets.empty
    assert (df_analysts["total_score"] >= 0.0).all() and (df_analysts["total_score"] <= 100.0).all()
    assert (df_tickets["total_score"] >= 0.0).all() and (df_tickets["total_score"] <= 100.0).all()
