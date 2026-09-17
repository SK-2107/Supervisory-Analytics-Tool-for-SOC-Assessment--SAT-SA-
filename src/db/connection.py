"""
DuckDB Database Connection Management for SAT-SA.
"""

import os
import threading
import duckdb
from src.db.schema import init_db

_lock = threading.Lock()
DEFAULT_DB_PATH = os.path.join("data", "sat_sa.duckdb")


def get_db_connection(db_path: str = None):
    """
    Returns a DuckDB connection. Initializes database schemas if needed.
    Pass db_path=":memory:" for in-memory DB or a file path for persistent DB.
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH

    if db_path != ":memory:":
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    with _lock:
        try:
            conn = duckdb.connect(db_path)
            init_db(conn)
            return conn
        except Exception:
            # If disk database file has an outdated/incompatible catalog, reset file & re-initialize
            if db_path != ":memory:" and os.path.exists(db_path):
                try:
                    conn.close()
                except Exception:
                    pass
                try:
                    os.remove(db_path)
                except Exception:
                    pass
                conn = duckdb.connect(db_path)
                init_db(conn)
                return conn
            raise


def get_pandas_df(conn, query: str, params=None):
    """Utility helper to query DuckDB and return a Pandas DataFrame."""
    if params:
        return conn.execute(query, params).df()
    return conn.execute(query).df()

