"""
Unit tests for DuckDB database initialization and schema queries.
"""

import pytest
from src.db.connection import get_db_connection


def test_in_memory_db_init():
    conn = get_db_connection(db_path=":memory:")
    tables_df = conn.execute("SHOW TABLES").df()
    tables = list(tables_df["name"].values) if not tables_df.empty else []

    expected_tables = ["analysts", "alerts", "tickets", "investigation_notes", "shift_logs", "supervisory_scores"]
    for t in expected_tables:
        assert t in tables
    conn.close()
