"""
Page: Dedicated Finding Detail View.
Enterprise Light Theme — Explainable, traceable supervisory drill-down for an analytical finding.
Follows: FINDING -> REASON -> EVIDENCE -> EXPLAINABILITY -> REVIEW ACTION.
"""

import streamlit as st
import pandas as pd
from src.ui.styles import badge, finding_severity_band, COLOR_HIGH, COLOR_MODERATE, COLOR_TEAL_PRIMARY
from src.ui.nav import go_to, render_breadcrumbs
from src.ui.db_helper import fetch_evidence_record
from src.ui.pages.entity_detail import render_evidence_card

DIMENSION_EXPLAINABILITY = {
    "Escalation": {
        "priority_context": "Mandatory escalation procedures dictate that CRITICAL severity incidents cannot be resolved without CSIRT/Tier-2 senior analyst intervention.",
        "workflow_condition": "Incident closure was finalized in the ticketing database without recording an escalated_to_tier2 flag or dispatch reference.",
        "repeated_pattern": "Multiple instances occurred within the assessment window, indicating a systematic procedural breakdown rather than an isolated anomaly.",
        "supervisory_action": "Audit the listed closed tickets with Tier-1 personnel and confirm whether incidents required active mitigation or containment."
    },
    "Investigation": {
        "priority_context": "Investigation notes constitute the legal and regulatory audit trail of incident triage under NCIIPC supervisory standards.",
        "workflow_condition": "Closed incident records contain superficial triage summaries with fewer than 10 words, lacking diagnostic evidence.",
        "repeated_pattern": "Observed across numerous closed cases, suggesting copy-pasting or minimal engagement during alert validation.",
        "supervisory_action": "Mandate investigation note re-audits for the identified analysts and review Shift Handover protocols."
    },
    "Security Operations": {
        "priority_context": "Effective triage requires adequate dwell time to investigate log artifacts, correlate telemetry, and eliminate false positives.",
        "workflow_condition": "Tickets were transitioned from assigned to closed in under 30 seconds, which is biologically and technically implausible for genuine investigation.",
        "repeated_pattern": "Repeated sub-30-second closures indicate potential SLA gaming or automated mass-closing of uninvestigated events.",
        "supervisory_action": "Conduct an unannounced sampling of rapidly closed cases and interview the assigned analysts regarding triage procedures."
    },
    "Operational Discipline": {
        "priority_context": "Shift handovers ensure seamless continuity of critical infrastructure surveillance across 24x7 SOC rotations.",
        "workflow_condition": "Completed operational shifts were concluded without recording mandatory handover checklists or unverified shift logs.",
        "repeated_pattern": "Absence of handover logs during critical shift boundaries creates blind spots during incident transition windows.",
        "supervisory_action": "Enforce verified dual-sign-off for shift lead handovers and inspect pending unresolved alerts."
    },
    "Incident Response": {
        "priority_context": "Critical Sector Entities operate under strict NCIIPC Mean-Time-To-Respond (MTTR) and Mean-Time-To-Contain (MTTC) benchmarks.",
        "workflow_condition": "High and Critical severity incidents experienced closure delays far exceeding the 180-minute (or 60-minute for Critical) SLA threshold.",
        "repeated_pattern": "Systematic queuing and investigation delays leading to prolonged threat dwell times.",
        "supervisory_action": "Review bottleneck causes in the SOC tier escalation chain and assess staffing levels during peak volume periods."
    },
    "Threat Detection": {
        "priority_context": "All high-severity detections originating from SIEM/EDR must be accounted for via a tracked incident case.",
        "workflow_condition": "High-severity alerts were ingested into the telemetry pool but were never promoted to an active ticket.",
        "repeated_pattern": "Silent alert drops or unassigned telemetry streams without documented suppression rules.",
        "supervisory_action": "Review alert ingest pipelines and correlation rules to ensure automated ticket creation for all high-fidelity alerts."
    },
    "Governance & Oversight": {
        "priority_context": "Comprehensive compliance with SOC operational frameworks mandates end-to-end accountability.",
        "workflow_condition": "Compound gaps across detection, escalation, and response capabilities exceeded acceptable supervisory tolerances.",
        "repeated_pattern": "Multi-dimensional operational degradation impacting overall SOC resilience.",
        "supervisory_action": "Initiate a formal supervisory review with SOC management and request a remediation roadmap."
    },
    "Cyber Resilience": {
        "priority_context": "Operational volume and investigation depth must remain proportionate to peer entities within the same critical sector.",
        "workflow_condition": "Telemetry volumes or closure rates diverge significantly (> 2 standard deviations) from the sector peer median.",
        "repeated_pattern": "Chronic under-reporting or excessive alert fatigue relative to peer infrastructure.",
        "supervisory_action": "Review log ingestion baselines and sensor coverage across critical operational assets."
    }
}


def _dim_score_for(dim_scores_df, cse_id, dimension) -> float:
    if dim_scores_df is None or dim_scores_df.empty or cse_id not in dim_scores_df["cse_id"].values:
        return 0.0
    row = dim_scores_df[dim_scores_df["cse_id"] == cse_id].iloc[0]
    return float(row.get(dimension, 0.0))


def render_finding_detail_page(conn, results):
    finding_id = st.session_state.get("selected_finding")
    df_findings = results["findings_df"] if results else pd.DataFrame()
    match = df_findings[df_findings["finding_id"] == finding_id] if not df_findings.empty else pd.DataFrame()

    if match.empty:
        st.warning("Selected finding is not found or has been cleared.")
        if st.button("← Back to Findings"):
            go_to("findings")
        return

    f = match.iloc[0]
    dim_scores = results["dimension_scores"] if results else pd.DataFrame()
    dim_score = _dim_score_for(dim_scores, f["cse_id"], f["dimension"])
    sev_band = finding_severity_band(dim_score)

    entity_row = conn.execute("SELECT entity_name, sector, criticality FROM cses WHERE cse_id = ?", [f["cse_id"]]).df()
    entity_name = entity_row.iloc[0]["entity_name"] if not entity_row.empty else f["cse_id"]
    sector_name = entity_row.iloc[0]["sector"] if not entity_row.empty else "Unknown"

    # Breadcrumbs
    render_breadcrumbs([
        ("Overview", "overview"),
        ("Findings", "findings"),
        (f["finding_title"], None),
    ])

    # Top action bar
    top_c1, top_c2 = st.columns([6, 1.5])
    with top_c2:
        if st.button("← Back to Findings", key="back_fnd_top", type="secondary", use_container_width=True):
            go_to("findings")

    # Finding Title & Badges
    with st.container():
        st.markdown(
            f"""
            <div class="satsa-card" style="border-left: 5px solid {COLOR_HIGH if sev_band=='High' else COLOR_MODERATE}; margin-bottom: 18px;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
                    <div>
                        <div style="font-size: 22px; font-weight: 700; color: #172326; letter-spacing: -0.015em;">
                            {f['finding_title']}
                        </div>
                        <div style="font-size: 13.5px; color: #667579; margin-top: 4px;">
                            Finding ID: <strong>`{f['finding_id']}`</strong> &nbsp;·&nbsp;
                            Dimension: <strong>{f['dimension']}</strong> &nbsp;·&nbsp;
                            Source Type: <strong>{f['source_record_type'].title()}</strong>
                        </div>
                    </div>
                    <div>
                        {badge(sev_band.upper() + ' SEVERITY', sev_band)}
                        <span style="margin-left: 6px;">{badge(f['confidence_strength'].title() + ' Confidence', 'Routine')}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Associated Entity Quick Bar
    with st.container():
        ec1, ec2 = st.columns([5.5, 1.5])
        ec1.markdown(
            f"""
            <div style="font-size: 14px; color: #172326;">
                Associated Entity: <strong>{entity_name}</strong> &nbsp;·&nbsp; Sector: <strong>{sector_name}</strong> &nbsp;·&nbsp; CSE ID: <code>{f['cse_id']}</code>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if ec2.button("Open Entity Detail →", key="btn_open_ent_from_fnd", type="secondary", use_container_width=True):
            go_to("entity_detail", selected_entity=f["cse_id"])

    st.write("")

    # Section 1: WHAT SAT-SA DETECTED
    st.markdown('<div class="section-title">What SAT-SA Detected</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="satsa-card" style="font-size: 15px; color: #172326; background: #FFFFFF; border-left: 4px solid #087F73;">
            <strong>Analytical Output:</strong> {f['reason']}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    # Section 2: DETECTION SIGNALS
    st.markdown('<div class="section-title">Detection Signals & Parameters</div>', unsafe_allow_html=True)
    evidence_ids = [e.strip() for e in str(f["evidence_record_ids"]).split(",") if e.strip()]

    sig_cols = st.columns(4)
    sig_cols[0].markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Observed Value</div><div class="satsa-kpi-value" style="font-size:18px; color:#C93C3C;">{f["observed_value"]}</div><div class="satsa-kpi-sub">Flagged operational metric</div></div>',
        unsafe_allow_html=True,
    )
    sig_cols[1].markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Expected Baseline</div><div class="satsa-kpi-value" style="font-size:18px; color:#278A55;">{f["expected_baseline_value"]}</div><div class="satsa-kpi-sub">Standard compliance rule</div></div>',
        unsafe_allow_html=True,
    )
    sig_cols[2].markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Evidence Records</div><div class="satsa-kpi-value" style="font-size:18px; color:#087F73;">{len(evidence_ids)} records</div><div class="satsa-kpi-sub">Extracted log artifacts</div></div>',
        unsafe_allow_html=True,
    )
    sig_cols[3].markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Detection Confidence</div><div class="satsa-kpi-value" style="font-size:18px; color:#172326;">{f["confidence_strength"].title()}</div><div class="satsa-kpi-sub">Statistical certainty</div></div>',
        unsafe_allow_html=True,
    )

    st.write("")

    # Section 3: WHY WAS THIS FLAGGED?
    st.markdown('<div class="section-title">Why Was This Flagged? (Explainability Architecture)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">SAT-SA employs glass-box explainability to eliminate black-box uncertainty for SOC supervisors.</div>',
        unsafe_allow_html=True,
    )

    exp_info = DIMENSION_EXPLAINABILITY.get(f["dimension"], DIMENSION_EXPLAINABILITY["Escalation"])

    with st.container():
        st.markdown(
            f"""
            <div class="satsa-card">
                <div class="explain-box">
                    <div class="signal-check">
                        <span class="signal-check-icon">✓</span>
                        <div>
                            <strong>1. Priority Context:</strong> {exp_info['priority_context']}
                        </div>
                    </div>
                    <div class="signal-check">
                        <span class="signal-check-icon">✓</span>
                        <div>
                            <strong>2. Workflow Condition:</strong> {exp_info['workflow_condition']}
                        </div>
                    </div>
                    <div class="signal-check">
                        <span class="signal-check-icon">✓</span>
                        <div>
                            <strong>3. Repeated Pattern:</strong> {exp_info['repeated_pattern']}
                        </div>
                    </div>
                    <div class="signal-check">
                        <span class="signal-check-icon">✓</span>
                        <div>
                            <strong>4. Empirical Traceability:</strong> Flagged directly from {len(evidence_ids)} verified operational record(s) in DuckDB.
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    # Section 4: SUPPORTING EVIDENCE TRACEABILITY
    st.markdown(f'<div class="section-title">Supporting Evidence Records Traceability ({len(evidence_ids)})</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Direct drill-down into source records supporting this finding. Every finding maps to verifiable telemetry.</div>',
        unsafe_allow_html=True,
    )

    if not evidence_ids:
        st.caption("No specific individual records attached.")
    else:
        sample_limit = min(len(evidence_ids), 8)
        tabs = st.tabs([f"Evidence: {eid}" for eid in evidence_ids[:sample_limit]])
        for tab, eid in zip(tabs, evidence_ids[:sample_limit]):
            with tab:
                render_evidence_card(conn, f["source_record_type"], eid)

        if len(evidence_ids) > sample_limit:
            st.caption(f"+ {len(evidence_ids) - sample_limit} additional evidence records logged in DuckDB.")

    st.write("")

    # Section 5: SUPERVISORY RECOMMENDATION & AUDIT ACTION
    st.markdown('<div class="section-title">Recommended Supervisory Review Action</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown(
            f"""
            <div class="satsa-card" style="background:#F8FAFA;">
                <div style="font-weight: 700; color: #172326; margin-bottom: 6px;">Supervisory Protocol:</div>
                <div style="font-size: 13.5px; color: #485659; margin-bottom: 12px;">{exp_info['supervisory_action']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        act_cols = st.columns([3.5, 2, 2])
        if act_cols[1].button("Open Review Queue", key="fnd_go_review", type="primary", use_container_width=True):
            go_to("reviews", review_tab="Priority Cases", highlight_ticket=evidence_ids[0] if evidence_ids else None)
        if act_cols[2].button("Generate Assessment Report", key="fnd_go_report", type="secondary", use_container_width=True):
            go_to("reports")
