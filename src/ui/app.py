"""
SAT-SA 2.0 — Supervisory Analytics Tool for SOC Assessment.
Smart India Hackathon 2026 | Problem Statement SIH26157 | TOP 50 Stage.

Light Enterprise Theme Only. No dark mode. No external network dependencies.
Strictly offline, air-gapped, explainable supervisory analytics.
"""

import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st
import pandas as pd

from src.db.connection import get_db_connection
from src.analytics.scoring import calculate_supervisory_attention_scores
from src.ui.styles import inject_custom_css
from src.ui.nav import render_global_header
from src.ui.db_helper import has_any_data
from src.ui.pages.overview import render_overview_page
from src.ui.pages.entities import render_entities_page
from src.ui.pages.entity_detail import render_entity_detail_page
from src.ui.pages.findings import render_findings_page
from src.ui.pages.finding_detail import render_finding_detail_page
from src.ui.pages.reviews import render_reviews_page
from src.ui.pages.benchmarking import render_benchmarking_page
from src.ui.pages.assessment import render_assessment_page
from src.ui.pages.reports import render_reports_page


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="SAT-SA | Supervisory Analytics for SOC Assessment",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    defaults = {
        "page": "overview",
        "selected_entity": None,
        "selected_finding": None,
        "highlight_ticket": None,
        "active_review_ticket": None,
        "search_query": "",
        "entity_filter": "All Entities",
        "results_cache": None,
        "confirm_run_asmt": False,
        "pdf_report_bytes": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def get_results(conn, has_data: bool):
    if not has_data:
        st.session_state.results_cache = None
        return None
    if st.session_state.get("results_cache") is None:
        st.session_state.results_cache = calculate_supervisory_attention_scores(conn)
    return st.session_state.results_cache


# ============================================================================
# APPLICATION ENTRYPOINT
# ============================================================================

def main():
    init_session_state()
    inject_custom_css()

    conn = get_db_connection()
    data_loaded = has_any_data(conn)

    # Global Top Navigation & Enterprise Brand Header
    render_global_header(conn, data_loaded)

    # Core Analytical Calculations (Real Data Only)
    results = get_results(conn, data_loaded)

    # Routing
    page = st.session_state.page
    if page == "overview":
        render_overview_page(conn, results)
    elif page == "entities":
        render_entities_page(conn, results)
    elif page == "entity_detail":
        render_entity_detail_page(conn, results)
    elif page == "findings":
        render_findings_page(conn, results)
    elif page == "finding_detail":
        render_finding_detail_page(conn, results)
    elif page == "reviews":
        render_reviews_page(conn, results)
    elif page == "benchmarking":
        render_benchmarking_page(conn, results)
    elif page == "assessment":
        render_assessment_page(conn, data_loaded)
    elif page == "reports":
        render_reports_page(conn, data_loaded, results)
    else:
        render_overview_page(conn, results)


if __name__ == "__main__":
    main()
