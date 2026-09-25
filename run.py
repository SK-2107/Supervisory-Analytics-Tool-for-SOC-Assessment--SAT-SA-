"""
SAT-SA Unified One-Step Startup Launcher.
National Critical Sector SOC Operations Oversight | NCIIPC Context

Performs environment verification, directory validation, database safety checks,
and launches both FastAPI REST API and Streamlit Dashboard UI under managed supervision.

Usage:
    python run.py
    python run.py --reset-demo   (To explicitly force reset & reseed synthetic demo data)
"""

import os
import sys
import time
import socket
import signal
import argparse
import subprocess

# Ensure project root directory is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

REQUIRED_PACKAGES = [
    ("duckdb", "duckdb"),
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("scipy", "scipy"),
    ("sklearn", "scikit-learn"),
    ("reportlab", "reportlab"),
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("streamlit", "streamlit"),
]

FASTAPI_HOST = "127.0.0.1"
FASTAPI_PORT = 8000
STREAMLIT_PORT = 8501


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Checks if a TCP port is already open/bound on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            return s.connect_ex((host, port)) == 0
        except Exception:
            return False


def check_environment():
    """Validates Python version and essential dependencies quickly without heavy loading."""
    if sys.version_info < (3, 10):
        print(f"[FAIL] Python 3.10+ required. Current version: {sys.version.split()[0]}")
        sys.exit(1)

    import importlib.util
    missing = []
    for mod_name, pip_name in REQUIRED_PACKAGES:
        try:
            spec = importlib.util.find_spec(mod_name)
            if spec is None:
                missing.append(pip_name)
        except Exception:
            missing.append(pip_name)

    if missing:
        print("\n" + "=" * 60)
        print(" [ERROR] Missing Required Dependencies")
        print("=" * 60)
        print(f" The following package(s) are not installed:\n   -> {', '.join(missing)}\n")
        print(" To install all dependencies at once, run:")
        print("   pip install -r requirements.txt")
        print("=" * 60 + "\n")
        sys.exit(1)


def ensure_directories():
    """Ensures required local runtime directories exist."""
    dirs = [
        os.path.join(PROJECT_ROOT, "data"),
        os.path.join(PROJECT_ROOT, "src", "reporting", "exports")
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def check_and_prep_database(force_reset: bool = False, use_public: bool = False):
    """
    Ensures DuckDB schema is ready and handles data safely:
    - Never overwrites existing imported or previously evaluated data on normal runs.
    - Seeds default dataset only if the database is completely empty or --reset-demo/--public is passed.
    """
    from src.db.connection import get_db_connection
    from src.ui.db_helper import has_any_data
    from src.generator.mock_data import seed_database
    from src.generator.public_dataset_adapter import ingest_public_dataset
    from src.config import get_data_source_mode

    if use_public:
        os.environ["DATA_SOURCE"] = "PUBLIC"

    mode = get_data_source_mode()
    conn = get_db_connection(read_only=False)

    try:
        data_exists = has_any_data(conn)

        from src.analytics.scoring import calculate_supervisory_attention_scores
        from src.ui.db_helper import record_assessment_run
        from datetime import datetime

        if use_public:
            print(f"[*] Ingesting authentic public research dataset (NSL-KDD)...")
            p_stats = ingest_public_dataset(conn)
            res = calculate_supervisory_attention_scores(conn)
            f_count = len(res.get("findings_df", []))
            record_assessment_run(
                conn,
                run_id=f"RUN-PUB-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                entities_count=p_stats["entities_count"],
                alerts_count=p_stats["alerts_count"],
                tickets_count=0,
                findings_count=f_count,
                high_attention_count=0
            )
            print(f"[OK] Ingested {p_stats['alerts_count']} authentic connection events across {p_stats['entities_count']} service groups.")
            print(f"[OK] Supervisory capability assessment calculated ({f_count} findings on record).")
            return

        if force_reset:
            print(f"[*] --reset-demo requested: Re-seeding database with calibrated {mode} dataset...")
            c_stats = seed_database(conn, num_days=7)
            res = calculate_supervisory_attention_scores(conn)
            f_count = len(res.get("findings_df", []))
            record_assessment_run(
                conn,
                run_id=f"RUN-DEMO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                entities_count=c_stats["cses_count"],
                alerts_count=c_stats["alerts_count"],
                tickets_count=c_stats["tickets_count"],
                findings_count=f_count,
                high_attention_count=int((res["cse_scores"]["total_score"] >= 45).sum()) if "total_score" in res["cse_scores"] else 0
            )
            print("[OK] Database reset, seeded, and assessed successfully.")
            return

        if not data_exists:
            if mode == "PUBLIC":
                print(f"[*] Empty database detected: Initializing with authentic public research dataset (NSL-KDD)...")
                p_stats = ingest_public_dataset(conn)
                res = calculate_supervisory_attention_scores(conn)
                print(f"[OK] Ingested {p_stats['alerts_count']} authentic connection events across {p_stats['entities_count']} service groups.")
            else:
                print(f"[*] Empty database detected: Initializing with default {mode} dataset (7 days)...")
                c_stats = seed_database(conn, num_days=7)
                res = calculate_supervisory_attention_scores(conn)
                print("[OK] Database initialized, seeded, and assessed successfully.")
        else:
            # Preserving existing data (whether previously seeded demo, public research, or imported real data)
            cnt = conn.execute("SELECT COUNT(*) FROM cses").fetchone()[0]
            print(f"[OK] Database ready: Reusing existing database ({cnt} entities on record, no data wiped)")
    finally:
        conn.close()


def print_startup_banner(api_url: str, ui_url: str):
    """Displays a clear, clean executive startup banner."""
    from src.config import get_data_source_label

    print("\n" + "-" * 50)
    print(" SAT-SA")
    print(" Supervisory Analytics Tool for SOC Assessment")
    print(" National Critical Sector SOC Operations Oversight | NCIIPC Context")
    print("-" * 50)
    print(f" [OK] Environment ready (Python {sys.version.split()[0]})")
    print(f" [OK] Database ready (DuckDB Embedded)")
    print(f" [OK] {get_data_source_label()}")
    print(" [OK] FastAPI REST server started")
    print(" [OK] Streamlit Platform UI started")
    print("-" * 50)
    print(" SAT-SA is running (100% Local / Air-Gapped):\n")
    print(f"   Platform Dashboard:  {ui_url}")
    print(f"   FastAPI REST Docs:   {api_url}/docs")
    print(f"   API Base Endpoint:   {api_url}/")
    print("-" * 50)
    print(" Press Ctrl+C to stop SAT-SA.")
    print("-" * 50 + "\n")


def launch_services():
    """Launches FastAPI and Streamlit, supervising their lifecycles cleanly."""
    parser = argparse.ArgumentParser(description="SAT-SA Unified Platform Launcher")
    parser.add_argument("--reset-demo", action="store_true", help="Explicitly reseed database with default demo dataset")
    parser.add_argument("--public", action="store_true", help="Load legitimate public research dataset (NSL-KDD Benchmark)")
    args = parser.parse_args()

    # 1. Validation & Setup
    print("\n" + "=" * 60)
    print(" SAT-SA — Supervisory Analytics Tool for SOC Assessment")
    print(" National Critical Sector SOC Operations Oversight | NCIIPC Context")
    print("=" * 60)
    print("[*] Validating environment and dependencies...")
    check_environment()
    print("[OK] Dependencies verified.")
    ensure_directories()
    check_and_prep_database(force_reset=args.reset_demo, use_public=args.public)

    # 2. Port Collision Guard
    if is_port_in_use(FASTAPI_PORT, FASTAPI_HOST):
        print(f"\n[ERROR] Port {FASTAPI_PORT} is already in use by another service.")
        print("Please terminate any running uvicorn/FastAPI process before starting SAT-SA.\n")
        sys.exit(1)

    if is_port_in_use(STREAMLIT_PORT):
        print(f"\n[WARNING] Port {STREAMLIT_PORT} is currently in use.")
        print(f"Streamlit will automatically attempt to bind to the next available port (e.g. 8502).\n")

    api_process = None
    ui_process = None

    def cleanup(signum=None, frame=None):
        print("\n[*] Shutting down SAT-SA platform...")
        for name, proc in [("Streamlit UI", ui_process), ("FastAPI API", api_process)]:
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=3)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                print(f"[OK] {name} stopped.")
        sys.exit(0)

    # Register OS signal handlers for clean teardown
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    api_url = f"http://{FASTAPI_HOST}:{FASTAPI_PORT}"
    ui_url = f"http://localhost:{STREAMLIT_PORT}"

    try:
        # Start FastAPI as background service
        api_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "src.api.main:app", "--host", FASTAPI_HOST, "--port", str(FASTAPI_PORT)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            cwd=PROJECT_ROOT
        )

        # Brief pause to verify API didn't crash immediately on boot
        time.sleep(1.2)
        if api_process.poll() is not None:
            _, err = api_process.communicate()
            print(f"\n[ERROR] Failed to start FastAPI service:\n{err.decode('utf-8', errors='ignore')}")
            cleanup()

        print_startup_banner(api_url, ui_url)

        # Start Streamlit in foreground
        ui_cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            os.path.join("src", "ui", "app.py"),
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
            "--server.port", str(STREAMLIT_PORT)
        ]

        ui_process = subprocess.Popen(ui_cmd, cwd=PROJECT_ROOT)

        # Supervise child processes
        while True:
            if ui_process.poll() is not None:
                break
            if api_process.poll() is not None:
                print("\n[ALERT] FastAPI process unexpectedly terminated.")
                break
            time.sleep(1)

    except KeyboardInterrupt:
        pass
    finally:
        cleanup()


if __name__ == "__main__":
    launch_services()
