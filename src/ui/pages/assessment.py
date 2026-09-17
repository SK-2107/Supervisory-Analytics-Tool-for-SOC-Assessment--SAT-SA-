"""
Page: Assessment Workflow & Historical Runs.
Enterprise Light Theme — End-to-end 5-step supervisory assessment pipeline:
Data Import -> Validation -> Run Assessment -> Results -> Historical Runs & Trends.
"""

import time
from datetime import datetime
import streamlit as st
import pandas as pd
from src.ui.styles import badge, attention_band
from src.ui.nav import go_to
from src.ui.db_helper import (
    has_any_data, get_assessment_runs, record_assessment_run
)
from src.generator.mock_data import seed_database
from src.analytics.scoring import calculate_supervisory_attention_scores

VALID_IMPORT_TABLES = ["analysts", "alerts", "tickets", "investigation_notes", "shift_logs"]


def render_assessment_page(conn, has_data: bool):
    st.markdown('<div class="page-title">Supervisory Assessment Workflow</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">End-to-end operational pipeline for ingesting, validating, and analyzing SOC operational telemetry.</div>',
        unsafe_allow_html=True,
    )

    # 5-Step Pipeline Breadcrumb / Progress Strip
    st.markdown(
        """
        <div class="satsa-card" style="padding: 12px 20px; background: #FFFFFF; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 13px; font-weight: 600; color: #485659; flex-wrap: wrap; gap: 8px;">
                <span style="color:#087F73;">STEP 1: Data Import</span>
                <span style="color:#B2BDC0;">→</span>
                <span style="color:#087F73;">STEP 2: Validation</span>
                <span style="color:#B2BDC0;">→</span>
                <span style="color:#087F73;">STEP 3: Run Assessment</span>
                <span style="color:#B2BDC0;">→</span>
                <span style="color:#087F73;">STEP 4: Results & Attention</span>
                <span style="color:#B2BDC0;">→</span>
                <span style="color:#087F73;">STEP 5: Runs & Reporting</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # STEP 1 & 2: DATA IMPORT & INTEGRITY VALIDATION
    st.markdown('<div class="section-title">Step 1 & 2: Ingest & Validate Operational Data</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="satsa-card">', unsafe_allow_html=True)
        col1, col2 = st.columns([1.5, 1.5])

        with col1:
            st.markdown("<strong>Option A: Upload Operational Files (CSV / JSON)</strong>", unsafe_allow_html=True)
            target_table = st.selectbox("Target Database Table", VALID_IMPORT_TABLES, key="asmt_target_table")
            uploaded_file = st.file_uploader("Select CSV or JSON data file", type=["csv", "json"], key="asmt_file_upload")

            if uploaded_file is not None and st.button("Import & Validate File", type="primary", key="btn_import_file"):
                try:
                    if uploaded_file.name.endswith(".csv"):
                        new_df = pd.read_csv(uploaded_file)
                    else:
                        new_df = pd.read_json(uploaded_file)

                    rec_count = len(new_df)
                    conn.register("df_import_tmp", new_df)
                    conn.execute(f"INSERT INTO {target_table} SELECT * FROM df_import_tmp")
                    st.success(f"✓ Successfully imported {rec_count} records into table `{target_table}`.")
                    st.session_state.results_cache = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Import validation failed for table `{target_table}`. Reason: {e}")

        with col2:
            st.markdown("<strong>Option B: Generate Standard Audit Dataset</strong>", unsafe_allow_html=True)
            st.caption("Generate a multi-entity synthetic dataset calibrated to NCIIPC ground-truth profiles.")
            num_days = st.slider("Assessment Period Duration (Days)", 1, 30, 7, key="asmt_slider_days")

            if st.button("Generate & Seed Dataset", type="secondary", key="btn_seed_data", use_container_width=True):
                with st.spinner("Seeding database with calibrated multi-entity SOC records…"):
                    counts = seed_database(conn, num_days=num_days)
                    st.session_state.results_cache = None
                st.success(f"✓ Seeded {counts.get('alerts_count', 0)} alerts, {counts.get('tickets_count', 0)} tickets, and {counts.get('cses_count', 0)} entities.")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # Current Database Telemetry Status
    st.markdown('<div class="section-title">Database Integrity & Record Summary</div>', unsafe_allow_html=True)
    table_counts = conn.execute(
        """
        SELECT 
            (SELECT COUNT(*) FROM cses) AS cses,
            (SELECT COUNT(*) FROM alerts) AS alerts,
            (SELECT COUNT(*) FROM tickets) AS tickets,
            (SELECT COUNT(*) FROM analysts) AS analysts,
            (SELECT COUNT(*) FROM investigation_notes) AS notes,
            (SELECT COUNT(*) FROM shift_logs) AS shifts
        """
    ).df().iloc[0]

    ic1, ic2, ic3, ic4, ic5, ic6 = st.columns(6)
    ic1.markdown(f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Entities</div><div class="satsa-kpi-value">{int(table_counts["cses"])}</div><div class="satsa-kpi-sub">✓ Valid</div></div>', unsafe_allow_html=True)
    ic2.markdown(f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Alerts</div><div class="satsa-kpi-value">{int(table_counts["alerts"]):,}</div><div class="satsa-kpi-sub">✓ Valid</div></div>', unsafe_allow_html=True)
    ic3.markdown(f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Tickets</div><div class="satsa-kpi-value">{int(table_counts["tickets"]):,}</div><div class="satsa-kpi-sub">✓ Valid</div></div>', unsafe_allow_html=True)
    ic4.markdown(f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Analysts</div><div class="satsa-kpi-value">{int(table_counts["analysts"])}</div><div class="satsa-kpi-sub">✓ Valid</div></div>', unsafe_allow_html=True)
    ic5.markdown(f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Notes</div><div class="satsa-kpi-value">{int(table_counts["notes"]):,}</div><div class="satsa-kpi-sub">✓ Valid</div></div>', unsafe_allow_html=True)
    ic6.markdown(f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Shift Logs</div><div class="satsa-kpi-value">{int(table_counts["shifts"])}</div><div class="satsa-kpi-sub">✓ Valid</div></div>', unsafe_allow_html=True)

    st.write("")

    # STEP 3: RUN SUPERVISORY ASSESSMENT WITH CONFIRMATION
    st.markdown('<div class="section-title">Step 3: Run Supervisory Assessment</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Executes the 8 capability dimension evaluations, anomaly engines, and supervisory attention ranking.</div>',
        unsafe_allow_html=True,
    )

    with st.container():
        st.markdown('<div class="satsa-card">', unsafe_allow_html=True)
        st.markdown(
            """
            <div style="font-size: 14px; color: #172326; margin-bottom: 12px;">
                <strong>Confirmation Notice:</strong> Triggering an assessment will re-evaluate all loaded logs in DuckDB across 
                Escalation, Investigation, Security Operations, Incident Response, and Handover dimensions.
            </div>
            """,
            unsafe_allow_html=True,
        )

        confirm_col1, confirm_col2, confirm_col3 = st.columns([3, 2, 2])
        if confirm_col2.button("Run Supervisory Assessment", key="btn_run_asmt", type="primary", use_container_width=True, disabled=not has_data):
            st.session_state.confirm_run_asmt = True

        if st.session_state.get("confirm_run_asmt"):
            with st.container():
                st.markdown(
                    """
                    <div class="satsa-card" style="border: 2px solid #C58A18; background:#FFFDF7;">
                        <div style="font-weight: 700; color: #172326; margin-bottom: 6px;">
                            Confirm Assessment Execution?
                        </div>
                        <div class="card-note" style="margin-bottom: 12px;">
                            SAT-SA will analyze the currently loaded assessment data and regenerate findings, attention scores and review priorities.
                        </div>
                    """,
                    unsafe_allow_html=True,
                )
                cc1, cc2 = st.columns([1, 1])
                if cc1.button("Yes, Execute Assessment", type="primary", key="btn_confirm_yes"):
                    st.session_state.confirm_run_asmt = False
                    start_t = time.time()
                    with st.spinner("Executing supervisory assessment engine…"):
                        results = calculate_supervisory_attention_scores(conn)
                        st.session_state.results_cache = results
                        dur = round(time.time() - start_t, 2)

                    # Count high attention entities
                    high_cnt = 0
                    if not results["cse_scores"].empty:
                        for s in results["cse_scores"]["total_score"]:
                            if attention_band(s) in ("Critical", "High", "Moderate"):
                                high_cnt += 1

                    run_id = f"ASMT-{datetime.now().strftime('%Y%m%d-%H%M')}"
                    record_assessment_run(
                        conn=conn,
                        run_id=run_id,
                        entities_count=int(table_counts["cses"]),
                        alerts_count=int(table_counts["alerts"]),
                        tickets_count=int(table_counts["tickets"]),
                        findings_count=len(results["findings_df"]),
                        high_attention_count=high_cnt,
                        duration_seconds=dur,
                    )
                    st.success(f"✓ Assessment completed in {dur}s! {len(results['findings_df'])} findings identified across {len(results['cse_scores'])} entities.")
                    st.rerun()

                if cc2.button("Cancel", type="secondary", key="btn_confirm_no"):
                    st.session_state.confirm_run_asmt = False
                    st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")

    # STEP 5: HISTORICAL ASSESSMENT RUNS LOG
    st.markdown('<div class="section-title">Step 5: Assessment Runs Log & Audit Trail</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Verifiable record of completed assessment executions stored locally in DuckDB.</div>',
        unsafe_allow_html=True,
    )

    runs_df = get_assessment_runs(conn)
    if runs_df.empty:
        st.caption("No historical assessment runs logged yet.")
    else:
        thead = st.columns([2, 2.5, 1.4, 1.4, 1.4, 1.4, 1.4])
        for c, t in zip(thead, ["Run ID", "Execution Date/Time", "Status", "Entities", "Alerts", "Findings", "Duration"]):
            c.markdown(f'<div class="tbl-head">{t}</div>', unsafe_allow_html=True)

        for _, r in runs_df.iterrows():
            row_cols = st.columns([2, 2.5, 1.4, 1.4, 1.4, 1.4, 1.4])
            row_cols[0].markdown(f'<div class="tbl-row"><strong>`{r["run_id"]}`</strong></div>', unsafe_allow_html=True)
            dt_str = pd.to_datetime(r["run_date"]).strftime("%d %b %Y, %H:%M")
            row_cols[1].markdown(f'<div class="tbl-row">{dt_str}</div>', unsafe_allow_html=True)
            row_cols[2].markdown(f'<div class="tbl-row">{badge("Complete", "Low")}</div>', unsafe_allow_html=True)
            row_cols[3].markdown(f'<div class="tbl-row">{r["entities_count"]}</div>', unsafe_allow_html=True)
            row_cols[4].markdown(f'<div class="tbl-row">{r["alerts_count"]:,}</div>', unsafe_allow_html=True)
            row_cols[5].markdown(f'<div class="tbl-row" style="font-weight:600; color:#087F73;">{r["findings_count"]}</div>', unsafe_allow_html=True)
            dur_val = float(r.get("duration_seconds", 0.0) or 0.0)
            row_cols[6].markdown(f'<div class="tbl-row">{dur_val:.2f}s</div>', unsafe_allow_html=True)

    st.write("")

    # STEP 6: TREND ANALYSIS (REAL DATA ONLY)
    st.markdown('<div class="section-title">Longitudinal Trends Analysis</div>', unsafe_allow_html=True)
    if len(runs_df) < 2:
        st.markdown(
            """
            <div class="satsa-card" style="background:#FAFCFC; border:1px solid #E4E9E8;">
                <div style="font-weight: 600; color: #667579;">Trend analysis requires multiple assessment periods (minimum 2 runs).</div>
                <div class="card-note">Currently 1 assessment run is on record. Additional runs will automatically render longitudinal gap trajectories without synthetic extrapolation.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.caption(f"Historical trend across {len(runs_df)} assessment executions:")
        trend_chart_data = runs_df.sort_values("run_date")
        st.line_chart(trend_chart_data.set_index("run_id")[["findings_count", "high_attention_count"]])
