"""
Page: Supervisory Reports & Data Export.
Enterprise Light Theme — Audit-ready executive reporting and multi-format structured data exports.
"""

import io
import streamlit as st
import pandas as pd
from src.ui.styles import badge, COLOR_TEAL_PRIMARY
from src.ui.nav import go_to, fmt_period, fmt_dt
from src.ui.db_helper import get_assessment_period, get_last_assessment_time, get_review_decisions
from src.reporting.pdf_generator import generate_supervisory_pdf_report


def render_reports_page(conn, has_data: bool, results):
    st.markdown('<div class="page-title">Supervisory Reports & Audit Exports</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Generate regulatory audit reports and export structured supervisory data for offline archival.</div>',
        unsafe_allow_html=True,
    )

    lo, hi = get_assessment_period(conn)
    last_run = get_last_assessment_time(conn)

    # Air-Gapped Notice
    st.markdown(
        f"""
        <div class="satsa-card" style="border-left: 4px solid #087F73; background:#FAFCFC; margin-bottom: 20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                <div>
                    <span style="font-weight: 700; color: #172326;">Supervisory Audit Package — Air-Gapped Operation</span>
                    <div class="card-note">Assessment Period: <strong>{fmt_period(lo, hi)}</strong> &nbsp;·&nbsp; Last Assessment: <strong>{fmt_dt(last_run)}</strong></div>
                </div>
                <div>
                    <span class="satsa-pill-badge satsa-local-badge">● LOCAL PROCESSING</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. FORMAL PDF AUDIT REPORT SECTION
    st.markdown('<div class="section-title">Formal Supervisory Audit Report (PDF)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Full regulatory assessment report suitable for NCIIPC executive briefing and compliance submission.</div>',
        unsafe_allow_html=True,
    )

    with st.container():
        st.markdown('<div class="satsa-card">', unsafe_allow_html=True)
        rc1, rc2 = st.columns([2, 1.2])

        with rc1:
            st.markdown(
                """
                <div style="font-size: 13.5px; color: #172326; line-height: 1.6;">
                    <strong>Document Contents:</strong><br/>
                    • Executive Summary & SOC Health Index<br/>
                    • Quantitative Assessment Statistics (Telemetry, Alerts, Cases)<br/>
                    • Critical Sector Entity (CSE) Attention Priority Queue<br/>
                    • 8 Capability Dimension Gaps & Empirical Traceability Log<br/>
                    • Local Air-Gapped Environmental Certification
                </div>
                """,
                unsafe_allow_html=True,
            )

        with rc2:
            if not has_data:
                st.caption("Load data before generating reports.")
            else:
                if st.button("Generate Supervisory PDF Report", key="btn_gen_pdf", type="primary", use_container_width=True):
                    with st.spinner("Compiling formal supervisory PDF audit report…"):
                        pdf_bytes = generate_supervisory_pdf_report(conn)
                        st.session_state.pdf_report_bytes = pdf_bytes
                    st.success("✓ Supervisory report compiled successfully.")

                if st.session_state.get("pdf_report_bytes"):
                    st.download_button(
                        label="Download PDF Report",
                        data=st.session_state.pdf_report_bytes,
                        file_name="SAT-SA_Supervisory_Report.pdf",
                        mime="application/pdf",
                        key="btn_dl_pdf",
                        type="secondary",
                        use_container_width=True,
                    )

        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")

    # 2. STRUCTURED DATA EXPORTS (CSV)
    st.markdown('<div class="section-title">Structured Data Exports (CSV)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Download tabular supervisory outputs for ingestion into secondary audit systems.</div>',
        unsafe_allow_html=True,
    )

    exp_col1, exp_col2 = st.columns(2)

    with exp_col1:
        # Export 1: Findings
        with st.container():
            st.markdown('<div class="satsa-card">', unsafe_allow_html=True)
            st.markdown("<strong>1. Supervisory Findings Register (CSV)</strong>", unsafe_allow_html=True)
            st.caption("Complete table of capability gaps, severity levels, observed values, and attached evidence record IDs.")

            df_findings = results["findings_df"] if (results and not results["findings_df"].empty) else pd.DataFrame()
            if not df_findings.empty:
                fnd_csv = df_findings.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=f"Export Findings ({len(df_findings)} records) →",
                    data=fnd_csv,
                    file_name="SAT-SA_Findings_Export.csv",
                    mime="text/csv",
                    key="dl_fnd_csv",
                    type="secondary",
                    use_container_width=True,
                )
            else:
                st.caption("No findings available to export.")
            st.markdown('</div>', unsafe_allow_html=True)

        # Export 2: Review Queue & Decisions
        with st.container():
            st.markdown('<div class="satsa-card">', unsafe_allow_html=True)
            st.markdown("<strong>2. Review Queue & Decisions Log (CSV)</strong>", unsafe_allow_html=True)
            st.caption("Prioritized tickets with supervisory audit statuses, decision labels, and supervisor notes.")

            df_tickets = results["ticket_scores"] if (results and not results["ticket_scores"].empty) else pd.DataFrame()
            if not df_tickets.empty:
                decisions_df = get_review_decisions(conn)
                t_export = df_tickets.copy()
                if not decisions_df.empty:
                    t_export = t_export.merge(
                        decisions_df[["ticket_id", "status", "decision", "supervisor_notes", "updated_at"]],
                        left_on="entity_id", right_on="ticket_id", how="left"
                    )
                t_export["status"] = t_export["status"].fillna("OPEN")
                tkt_csv = t_export.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=f"Export Review Queue ({len(t_export)} cases) →",
                    data=tkt_csv,
                    file_name="SAT-SA_Review_Queue_Export.csv",
                    mime="text/csv",
                    key="dl_tkt_csv",
                    type="secondary",
                    use_container_width=True,
                )
            else:
                st.caption("No review queue cases available.")
            st.markdown('</div>', unsafe_allow_html=True)

    with exp_col2:
        # Export 3: CSE Scores
        with st.container():
            st.markdown('<div class="satsa-card">', unsafe_allow_html=True)
            st.markdown("<strong>3. Critical Sector Entity Attention Scores (CSV)</strong>", unsafe_allow_html=True)
            st.caption("Entity-level composite scores, criticality levels, and ranked supervisory priority bands.")

            df_cses = results["cse_scores"] if (results and not results["cse_scores"].empty) else pd.DataFrame()
            if not df_cses.empty:
                cse_csv = df_cses.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=f"Export Entity Scores ({len(df_cses)} entities) →",
                    data=cse_csv,
                    file_name="SAT-SA_CSE_Scores_Export.csv",
                    mime="text/csv",
                    key="dl_cse_csv",
                    type="secondary",
                    use_container_width=True,
                )
            else:
                st.caption("No entity scores available.")
            st.markdown('</div>', unsafe_allow_html=True)

        # Export 4: Capability Dimension Scores
        with st.container():
            st.markdown('<div class="satsa-card">', unsafe_allow_html=True)
            st.markdown("<strong>4. 8 SIH26157 Capability Dimension Matrix (CSV)</strong>", unsafe_allow_html=True)
            st.caption("Detailed score breakdown across all 8 capability dimensions per entity.")

            dim_scores = results["dimension_scores"] if (results and not results["dimension_scores"].empty) else pd.DataFrame()
            if not dim_scores.empty:
                dim_csv = dim_scores.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=f"Export Dimension Matrix ({len(dim_scores)} entities) →",
                    data=dim_csv,
                    file_name="SAT-SA_Dimension_Matrix_Export.csv",
                    mime="text/csv",
                    key="dl_dim_csv",
                    type="secondary",
                    use_container_width=True,
                )
            else:
                st.caption("No dimension scores available.")
            st.markdown('</div>', unsafe_allow_html=True)
