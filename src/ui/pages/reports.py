"""
Page: Export & Reports.
SAT-SA — Supervisory Analytics Tool for SOC Assessment.
"""

import io
import streamlit as st
import pandas as pd
from src.ui.styles import badge, neutral_badge, COLOR_TEAL_PRIMARY
from src.ui.nav import go_to, fmt_period, fmt_dt
from src.ui.db_helper import get_assessment_period, get_last_assessment_time, get_review_decisions
from src.reporting.pdf_generator import generate_supervisory_pdf_report


def render_reports_page(conn, has_data: bool, results):
    st.markdown('<div class="page-title">Export & Reports</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Download the formal supervisory audit report and export structured data for external review, compliance submission, or further analysis.</div>',
        unsafe_allow_html=True,
    )

    lo, hi   = get_assessment_period(conn)
    last_run = get_last_assessment_time(conn)

    # Status banner
    st.markdown(
        f"""
        <div class="satsa-card satsa-card-teal" style="margin-bottom:20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                <div>
                    <div style="font-weight:700; font-size:14px; color:#111827;">Supervisory Audit Package — Offline / Air-Gapped</div>
                    <div class="card-note" style="margin-top:3px;">
                        Assessment Period: <strong>{fmt_period(lo, hi)}</strong> &nbsp;·&nbsp; Last Assessment: <strong>{fmt_dt(last_run)}</strong>
                    </div>
                </div>
                <span class="satsa-status-pill satsa-pill-teal">⊙ Local Processing Only</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ----------------------------------------------------------------
    # 1. PDF AUDIT REPORT
    # ----------------------------------------------------------------
    st.markdown(
        '<div class="satsa-card-elevated"><div class="section-title" style="margin-top:0;">Supervisory Assessment Report (PDF)</div><div class="section-desc" style="margin-top:0;">The primary formal audit document — suitable for executive briefing, NCIIPC compliance submission, and stakeholder review. All data is locally computed; no network dependency.</div>',
        unsafe_allow_html=True,
    )

    doc_col, btn_col = st.columns([2.5, 1.2])
    with doc_col:
        st.markdown(
            """
            <div style="font-size:13.5px; color:#374151; line-height:1.7;">
                <strong>Report includes:</strong><br/>
                &bull; Executive Summary &amp; SOC Health Index<br/>
                &bull; Quantitative Statistics (Telemetry, Alerts, Cases)<br/>
                &bull; Critical Sector Entity Attention Priority Queue<br/>
                &bull; 8 Capability Dimension Gaps &amp; Evidence Traceability Log<br/>
                &bull; Air-Gapped Environmental Certification
            </div>
            """,
            unsafe_allow_html=True,
        )

    with btn_col:
        if not has_data:
            st.markdown(
                '<div class="satsa-info-banner">Load assessment data before generating reports.</div>',
                unsafe_allow_html=True,
            )
        else:
            if st.button("📄  Generate PDF Report", key="btn_gen_pdf", type="primary", use_container_width=True):
                with st.spinner("Compiling supervisory audit report…"):
                    pdf_bytes = generate_supervisory_pdf_report(conn)
                    st.session_state.pdf_report_bytes = pdf_bytes
                st.success("✓ Report compiled successfully.")

            if st.session_state.get("pdf_report_bytes"):
                st.download_button(
                    label="⬇  Download PDF Report",
                    data=st.session_state.pdf_report_bytes,
                    file_name="SAT-SA_Supervisory_Report.pdf",
                    mime="application/pdf",
                    key="btn_dl_pdf",
                    type="secondary",
                    use_container_width=True,
                )

    st.markdown('</div>', unsafe_allow_html=True)
    st.write("")

    # ----------------------------------------------------------------
    # 2. CSV DATA EXPORTS
    # ----------------------------------------------------------------
    st.markdown('<div class="section-title">Supporting Data Exports (CSV)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Export raw analytical outputs for further offline analysis, integration with GRC tools, or record-keeping.</div>',
        unsafe_allow_html=True,
    )

    e1, e2 = st.columns(2)

    # -- Findings
    with e1:
        st.markdown('<div class="satsa-card">', unsafe_allow_html=True)
        st.markdown("<strong>1. Supervisory Findings Register</strong>", unsafe_allow_html=True)
        st.caption("All capability gaps with severity, evidence IDs, dimension scores, and raw reasons.")
        df_findings = results["findings_df"] if (results and not results["findings_df"].empty) else pd.DataFrame()
        if not df_findings.empty:
            st.download_button(
                label=f"⬇  Export Findings ({len(df_findings)} records)",
                data=df_findings.to_csv(index=False).encode("utf-8"),
                file_name="SAT-SA_Findings_Export.csv",
                mime="text/csv",
                key="dl_fnd",
                type="secondary",
                use_container_width=True,
            )
        else:
            st.caption("No findings to export.")
        st.markdown('</div>', unsafe_allow_html=True)

    # -- Review Queue
    with e2:
        st.markdown('<div class="satsa-card">', unsafe_allow_html=True)
        st.markdown("<strong>2. Review Queue &amp; Decisions Log</strong>", unsafe_allow_html=True)
        st.caption("Priority cases with supervisory decisions, audit statuses, and governance notes.")
        df_tickets = results["ticket_scores"] if (results and not results["ticket_scores"].empty) else pd.DataFrame()
        if not df_tickets.empty:
            decisions_df = get_review_decisions(conn)
            t_export = df_tickets.copy()
            if not decisions_df.empty:
                t_export = t_export.merge(
                    decisions_df[["ticket_id", "status", "decision", "supervisor_notes", "updated_at"]],
                    left_on="entity_id", right_on="ticket_id", how="left",
                )
            t_export["status"] = t_export["status"].fillna("OPEN")
            st.download_button(
                label=f"⬇  Export Review Queue ({len(t_export)} cases)",
                data=t_export.to_csv(index=False).encode("utf-8"),
                file_name="SAT-SA_Review_Queue_Export.csv",
                mime="text/csv",
                key="dl_tkt",
                type="secondary",
                use_container_width=True,
            )
        else:
            st.caption("No review queue data to export.")
        st.markdown('</div>', unsafe_allow_html=True)

    e3, e4 = st.columns(2)

    # -- CSE Scores
    with e3:
        st.markdown('<div class="satsa-card">', unsafe_allow_html=True)
        st.markdown("<strong>3. Entity Attention Scores</strong>", unsafe_allow_html=True)
        st.caption("Per-entity composite scores, attention bands, finding counts, and criticality classifications.")
        df_cses = results["cse_scores"] if (results and not results["cse_scores"].empty) else pd.DataFrame()
        if not df_cses.empty:
            st.download_button(
                label=f"⬇  Export Entity Scores ({len(df_cses)} entities)",
                data=df_cses.to_csv(index=False).encode("utf-8"),
                file_name="SAT-SA_Entity_Scores.csv",
                mime="text/csv",
                key="dl_cse",
                type="secondary",
                use_container_width=True,
            )
        else:
            st.caption("No entity scores to export.")
        st.markdown('</div>', unsafe_allow_html=True)

    # -- Dimension Matrix
    with e4:
        st.markdown('<div class="satsa-card">', unsafe_allow_html=True)
        st.markdown("<strong>4. Capability Dimension Score Matrix</strong>", unsafe_allow_html=True)
        st.caption("Detailed per-entity score breakdown across all 8 capability dimensions.")
        dim_scores = results["dimension_scores"] if (results and not results["dimension_scores"].empty) else pd.DataFrame()
        if not dim_scores.empty:
            st.download_button(
                label=f"⬇  Export Dimension Matrix ({len(dim_scores)} entities)",
                data=dim_scores.to_csv(index=False).encode("utf-8"),
                file_name="SAT-SA_Dimension_Matrix.csv",
                mime="text/csv",
                key="dl_dim",
                type="secondary",
                use_container_width=True,
            )
        else:
            st.caption("No dimension score data to export.")
        st.markdown('</div>', unsafe_allow_html=True)
