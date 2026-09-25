"""
DuckDB Database Connection Management for SAT-SA.
Thread-safe connection handling with read_only support for safe concurrent reads
between FastAPI REST server and Streamlit dashboard.
"""

import os
import threading
import time
import duckdb
from src.db.schema import init_db
from src.config import DEFAULT_DB_PATH

_lock = threading.Lock()


def get_db_connection(db_path: str = None, read_only: bool = False, max_retries: int = 5):
    """
    Returns a DuckDB connection with concurrency and retry protection.
    - read_only=True allows concurrent reads without locking conflicts.
    - read_only=False handles table creation and data modifications safely with retry backoff.
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH

    if db_path != ":memory:":
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # If file does not exist yet and read_only was requested, initialize it first in write mode
        if read_only and not os.path.exists(db_path):
            with _lock:
                if not os.path.exists(db_path):
                    temp_conn = duckdb.connect(db_path, read_only=False)
                    init_db(temp_conn)
                    temp_conn.close()

    # Read-only connection mode
    if read_only and db_path != ":memory:":
        last_err = None
        for attempt in range(max_retries):
            try:
                conn = duckdb.connect(db_path, read_only=True)
                return conn
            except Exception as e:
                last_err = e
                time.sleep(0.15 * (attempt + 1))
        raise last_err

    # Read-write connection mode with mutex protection
    with _lock:
        last_err = None
        for attempt in range(max_retries):
            try:
                conn = duckdb.connect(db_path, read_only=False)
                init_db(conn)
                return conn
            except Exception as e:
                last_err = e
                # If disk database file has an incompatible or corrupted catalog, reset & re-init
                if attempt == max_retries - 1 and db_path != ":memory:" and os.path.exists(db_path):
                    try:
                        conn.close()
                    except Exception:
                        pass
                    try:
                        os.remove(db_path)
                    except Exception:
                        pass
                    conn = duckdb.connect(db_path, read_only=False)
                    init_db(conn)
                    return conn
                time.sleep(0.2 * (attempt + 1))
        raise last_err


def get_pandas_df(conn, query: str, params=None):
    """Utility helper to query DuckDB and return a Pandas DataFrame."""
    if params:
        return conn.execute(query, params).df()
    return conn.execute(query).df()
