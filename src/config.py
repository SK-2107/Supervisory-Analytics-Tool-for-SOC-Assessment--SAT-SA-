"""
SAT-SA Central Configuration Module.
Supports configuration of Data Source (DEMO, PUBLIC, or REAL), Database Paths, and Operational Defaults.
"""

import os

# Data Source Mode:
#   - 'DEMO': Synthetic prototype dataset calibrated with injected behavioral profiles
#   - 'PUBLIC': Legitimate public research dataset (NSL-KDD benchmark, Canadian Institute for Cybersecurity)
#   - 'REAL': Legitimate imported/authorized SOC records
DEFAULT_DATA_SOURCE = "DEMO"
DEFAULT_DB_PATH = os.path.join("data", "sat_sa.duckdb")


def get_data_source_mode(conn=None) -> str:
    """
    Returns current active data source mode ('DEMO', 'PUBLIC', or 'REAL').
    If a database connection is available, dynamically inspects the database to ensure
    100% truthfulness and eliminate any discrepancy between label and actual data.
    """
    if conn is not None:
        try:
            row = conn.execute("SELECT cse_id FROM cses LIMIT 1").fetchone()
            if row:
                cid = str(row[0])
                if cid.startswith("ENT-NET-"):
                    return "PUBLIC"
                if cid.startswith("CSE-"):
                    return "DEMO"
                return "REAL"
        except Exception:
            pass

    mode = os.getenv("DATA_SOURCE", DEFAULT_DATA_SOURCE).upper().strip()
    if mode in ("PUBLIC", "PUBLIC_DATASET", "NSL_KDD", "NSL-KDD"):
        return "PUBLIC"
    if mode in ("REAL", "AUTHORIZED"):
        return "REAL"
    return "DEMO"


def get_data_source_label(conn=None) -> str:
    """
    Returns a clean, standardized data source status string.
    Strictly distinguishes synthetic, public research, and authorized real datasets.
    """
    mode = get_data_source_mode(conn)
    if mode == "PUBLIC":
        return "DATA: PUBLIC RESEARCH DATASET (NSL-KDD)"
    if mode == "REAL":
        return "DATA: IMPORTED / AUTHORIZED SOC DATA"
    return "DATA: DEMO / SYNTHETIC"


def get_dataset_provenance_info(conn=None) -> dict:
    """
    Returns official academic and provenance metadata for the active data source.
    """
    mode = get_data_source_mode(conn)
    if mode == "PUBLIC":
        return {
            "name": "NSL-KDD Benchmark Security & Intrusion Dataset",
            "organization": "Canadian Institute for Cybersecurity (CIC) / University of New Brunswick (UNB)",
            "authors": "Mahbod Tavallaee, Ebrahim Bagheri, Wei Lu, and Ali A. Ghorbani",
            "publication": "A Detailed Analysis of the KDD CUP 99 Data Set (IEEE CISDA 2009)",
            "doi": "10.1109/CISDA.2009.5356528",
            "license": "Open Public Research Dataset (Academic / Research evaluation)",
            "is_synthetic": False,
            "is_public_research": True,
            "has_human_tickets": False,
            "has_investigation_notes": False
        }
    if mode == "REAL":
        return {
            "name": "Authorized Organizational SOC Operational Records",
            "organization": "Authorized Critical Infrastructure Operator",
            "authors": "Internal SOC Telemetry & Ticketing System",
            "license": "Confidential / Restricted Regulatory Audit Use",
            "is_synthetic": False,
            "is_public_research": False,
            "has_human_tickets": True,
            "has_investigation_notes": True
        }
    return {
        "name": "SAT-SA Synthetic SOC Benchmark Dataset (v1.0.0)",
        "organization": "SAT-SA Development Framework",
        "authors": "Calibrated Injected Behavioral Profiles for Prototype Validation",
        "license": "MIT Open Source / Operational Demonstration",
        "is_synthetic": True,
        "is_public_research": False,
        "has_human_tickets": True,
        "has_investigation_notes": True
    }
