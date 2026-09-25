"""
Page: Data & Reports Workflow.
SAT-SA — Supervisory Analytics Tool for SOC Assessment.
End-to-end 5-step supervisory assessment pipeline.
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
    st.markdown('<div class="page-title">Data & Assessment Workflow</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">End-to-end pipeline for importing, validating, and analyzing SOC operational telemetry against capability benchmarks.</div>',
        unsafe_allow_html=True,
    )

    # 5-step pipeline strip
    step_colors = ["#0D9488"] * 5 if has_data else ["#0D9488", "#0D9488", "#D1D5DB", "#D1D5DB", "#D1D5DB"]
    st.markdown(
        f"""
        <div class="workflow-steps">
            <div class="workflow-step">
                <div class="workflow-step-num" style="background:{step_colors[0]};color:white;">1</div>
                <div class="workflow-step-label" style="color:{step_colors[0]};">Data Import</div>
            </div>
            <div class="workflow-arrow">→</div>
            <div class="workflow-step">
                <div class="workflow-step-num" style="background:{step_colors[1]};color:{'white' if step_colors[1]=='#0D9488' else '#9CA3AF'};">2</div>
                <div class="workflow-step-label" style="color:{step_colors[1]};">Validation</div>
            </div>
            <div class="workflow-arrow">→</div>
            <div class="workflow-step">
                <div class="workflow-step-num" style="background:{step_colors[2]};color:{'white' if step_colors[2]=='#0D9488' else '#9CA3AF'};">3</div>
                <div class="workflow-step-label" style="color:{step_colors[2]};">Run Assessment</div>
            </div>
            <div class="workflow-arrow">→</div>
            <div class="workflow-step">
                <div class="workflow-step-num" style="background:{step_colors[3]};color:{'white' if step_colors[3]=='#0D9488' else '#9CA3AF'};">4</div>
                <div class="workflow-step-label" style="color:{step_colors[3]};">Results</div>
            </div>
            <div class="workflow-arrow">→</div>
            <div class="workflow-step">
                <div class="workflow-step-num" style="background:{step_colors[4]};color:{'white' if step_colors[4]=='#0D9488' else '#9CA3AF'};">5</div>
                <div class="workflow-step-label" style="color:{step_colors[4]};">Audit Log</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- STEP 1 & 2: IMPORT & VALIDATE
    st.markdown('<div class="section-title">Step 1 &amp; 2: Import &amp; Validate Operational Data</div>', unsafe_allow_html=True)

    st.markdown('<div class="satsa-card">', unsafe_allow_html=True)
    imp_col1, imp_col2 = st.columns([1.5, 1.5])

    with imp_col1:
        st.markdown("<strong>Option A: Upload Data File (CSV / JSON)</strong>", unsafe_allow_html=True)
        st.caption("Import a CSV or JSON file into one of the target database tables.")
        target_table   = st.selectbox("Target Table", VALID_IMPORT_TABLES, key="asmt_tbl")
        uploaded_file  = st.file_uploader("Select file", type=["csv", "json"], key="asmt_upld")

        if uploaded_file is not None and st.button("Import & Validate", type="primary", key="btn_import"):
            try:
                new_df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_json(uploaded_file)
                conn.register("df_import_tmp", new_df)
                conn.execute(f"INSERT INTO {target_table} SELECT * FROM df_import_tmp")
                st.success(f"✓ Imported {len(new_df)} records into `{target_table}`.")
                st.session_state.results_cache = None
                st.rerun()
            except Exception as e:
                st.error(f"Import failed: {e}")

    with imp_col2:
        st.markdown("<strong>Option B: Generate Standard Audit Dataset</strong>", unsafe_allow_html=True)
        st.caption("Seed a multi-entity synthetic dataset calibrated to ground-truth operational profiles for demonstration.")
        num_days = st.slider("Assessment period (days)", 1, 30, 7, key="asmt_days")
        if st.button("Generate & Seed Dataset", type="secondary", key="btn_seed", use_container_width=True):
            with st.spinner("Seeding database…"):
                counts = seed_database(conn, num_days=num_days)
                st.session_state.results_cache = None
            st.success(f"✓ Seeded {counts.get('alerts_count',0)} alerts, {counts.get('tickets_count',0)} tickets, {counts.get('cses_count',0)} entities.")
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # ---- DATABASE STATUS
    st.markdown('<div class="section-title">Database Integrity Summary</div>', unsafe_allow_html=True)
    table_counts = conn.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM cses)                  AS cses,
            (SELECT COUNT(*) FROM alerts)                AS alerts,
            (SELECT COUNT(*) FROM tickets)               AS tickets,
            (SELECT COUNT(*) FROM analysts)              AS analysts,
            (SELECT COUNT(*) FROM investigation_notes)   AS notes,
            (SELECT COUNT(*) FROM shift_logs)            AS shifts
        """
    ).df().iloc[0]

    def _validity(count):
        if int(count) > 0:
            return '<span style="color:#16A34A; font-weight:600;">✓ Valid</span>'
        return '<span style="color:#9CA3AF;">— Empty</span>'

    ic1, ic2, ic3, ic4, ic5, ic6 = st.columns(6)
    ic1.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Entities</div><div class="satsa-kpi-value">{int(table_counts["cses"])}</div><div class="satsa-kpi-sub">{_validity(table_counts["cses"])}</div></div>',
        unsafe_allow_html=True,
    )
    ic2.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Alerts</div><div class="satsa-kpi-value">{int(table_counts["alerts"]):,}</div><div class="satsa-kpi-sub">{_validity(table_counts["alerts"])}</div></div>',
        unsafe_allow_html=True,
    )
    ic3.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Tickets</div><div class="satsa-kpi-value">{int(table_counts["tickets"]):,}</div><div class="satsa-kpi-sub">{_validity(table_counts["tickets"])}</div></div>',
        unsafe_allow_html=True,
    )
    ic4.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Analysts</div><div class="satsa-kpi-value">{int(table_counts["analysts"])}</div><div class="satsa-kpi-sub">{_validity(table_counts["analysts"])}</div></div>',
        unsafe_allow_html=True,
    )
    ic5.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Inv. Notes</div><div class="satsa-kpi-value">{int(table_counts["notes"]):,}</div><div class="satsa-kpi-sub">{_validity(table_counts["notes"])}</div></div>',
        unsafe_allow_html=True,
    )
    ic6.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Shift Logs</div><div class="satsa-kpi-value">{int(table_counts["shifts"])}</div><div class="satsa-kpi-sub">{_validity(table_counts["shifts"])}</div></div>',
        unsafe_allow_html=True,
    )

    st.write("")

    # ---- STEP 3: RUN ASSESSMENT
    st.markdown('<div class="section-title">Step 3: Run Supervisory Assessment</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Executes all capability dimension evaluations, anomaly detection engines, and supervisory attention scoring across loaded data.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="satsa-card">', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="font-size:13.5px; color:#374151; margin-bottom:14px;">
            <strong>What will happen:</strong> SAT-SA will re-evaluate all loaded telemetry across Escalation, Investigation Quality,
            Security Operations, Incident Response, and Handover dimensions — then regenerate ranked attention scores and findings.
        </div>
        """,
        unsafe_allow_html=True,
    )
    conf_col1, conf_col2, conf_col3 = st.columns([3, 2, 2])
    if conf_col2.button("Run Assessment", key="btn_run_asmt", type="primary", use_container_width=True, disabled=not has_data):
        st.session_state.confirm_run_asmt = True

    if not has_data:
        st.caption("Import data (Steps 1 & 2) before running an assessment.")

    if st.session_state.get("confirm_run_asmt"):
        st.markdown(
            '<div class="satsa-attention-banner-warning"><strong>Confirm Assessment Execution?</strong><div class="card-note" style="margin-top:4px;">SAT-SA will analyze all loaded data and regenerate findings, scores, and review priorities.</div></div>',
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

            high_cnt = sum(1 for s in results["cse_scores"]["total_score"] if attention_band(s) in ("Critical", "High", "Moderate")) if not results["cse_scores"].empty else 0
            run_id = f"ASMT-{datetime.now().strftime('%Y%m%d-%H%M')}"
            record_assessment_run(
                conn=conn, run_id=run_id,
                entities_count=int(table_counts["cses"]),
                alerts_count=int(table_counts["alerts"]),
                tickets_count=int(table_counts["tickets"]),
                findings_count=len(results["findings_df"]),
                high_attention_count=high_cnt,
                duration_seconds=dur,
            )
            st.success(f"✓ Assessment completed in {dur}s — {len(results['findings_df'])} findings across {len(results['cse_scores'])} entities.")
            st.rerun()

        if cc2.button("Cancel", type="secondary", key="btn_confirm_no"):
            st.session_state.confirm_run_asmt = False
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.write("")

    # ---- STEP 4: ASSESSMENT RUNS LOG
    st.markdown('<div class="section-title">Step 4: Assessment Runs Log & Audit Trail</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Verifiable record of all completed assessment executions stored locally in DuckDB.</div>',
        unsafe_allow_html=True,
    )

    runs_df = get_assessment_runs(conn)
    if runs_df.empty:
        st.caption("No historical assessment runs logged yet.")
    else:
        thead = st.columns([2.2, 2.8, 1.4, 1.4, 1.4, 1.4, 1.4])
        for c, t in zip(thead, ["Run ID", "Execution Date/Time", "Status", "Entities", "Alerts", "Findings", "Duration"]):
            c.markdown(f'<div class="tbl-head">{t}</div>', unsafe_allow_html=True)

        for idx, (_, r) in enumerate(runs_df.iterrows()):
            row_cls = "tbl-row-alt" if idx % 2 == 0 else "tbl-row"
            rc = st.columns([2.2, 2.8, 1.4, 1.4, 1.4, 1.4, 1.4])
            rc[0].markdown(f'<div class="{row_cls}"><strong>{r["run_id"]}</strong></div>', unsafe_allow_html=True)
            dt_str = pd.to_datetime(r["run_date"]).strftime("%d %b %Y, %H:%M")
            rc[1].markdown(f'<div class="{row_cls}">{dt_str}</div>', unsafe_allow_html=True)
            rc[2].markdown(f'<div class="{row_cls}">{badge("Complete", "Low")}</div>', unsafe_allow_html=True)
            rc[3].markdown(f'<div class="{row_cls}">{r["entities_count"]}</div>', unsafe_allow_html=True)
            rc[4].markdown(f'<div class="{row_cls}">{r["alerts_count"]:,}</div>', unsafe_allow_html=True)
            rc[5].markdown(f'<div class="{row_cls}" style="font-weight:700; color:#0D9488;">{r["findings_count"]}</div>', unsafe_allow_html=True)
            dur_val = float(r.get("duration_seconds", 0.0) or 0.0)
            rc[6].markdown(f'<div class="{row_cls}">{dur_val:.2f}s</div>', unsafe_allow_html=True)

    st.write("")

    # ---- STEP 5: TREND ANALYSIS
    st.markdown('<div class="section-title">Step 5: Longitudinal Trends Analysis</div>', unsafe_allow_html=True)
    if runs_df.empty or len(runs_df) < 2:
        st.markdown(
            """
            <div class="satsa-card" style="background:#F9FAFB;">
                <div style="font-weight:600; color:#6B7280;">Trend analysis requires at least 2 completed assessment runs.</div>
                <div class="card-note" style="margin-top:4px;">Once multiple assessments are recorded, this section will automatically display longitudinal gap trajectories from real data.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.caption(f"Historical trend across {len(runs_df)} assessment executions:")
        trend_data = runs_df.sort_values("run_date")
        st.line_chart(trend_data.set_index("run_id")[["findings_count", "high_attention_count"]])
