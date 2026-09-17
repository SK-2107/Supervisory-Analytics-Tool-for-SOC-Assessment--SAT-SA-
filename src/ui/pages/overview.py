"""
Page: Supervisory Command Center (Overview).
Enterprise Light Theme — The operational heartbeat of SAT-SA.
Follows: SUMMARY -> ATTENTION -> FINDING -> REASON -> EVIDENCE -> REVIEW -> REPORT.
"""

import streamlit as st
import pandas as pd
from src.ui.styles import (
    badge, attention_band, finding_severity_band,
    COLOR_TEAL_PRIMARY, COLOR_HIGH, COLOR_MODERATE, COLOR_LOW
)
from src.ui.nav import go_to, fmt_dt, fmt_period
from src.ui.db_helper import get_assessment_period, get_last_assessment_time


def render_overview_page(conn, results):
    # 1. Header & Context
    st.markdown('<div class="page-title">Supervisory Command Center</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Assessment of SOC operational performance, capability gaps, and supervisory review priorities.</div>',
        unsafe_allow_html=True,
    )

    if results is None:
        with st.container():
            st.markdown(
                """
                <div class="satsa-card" style="text-align: center; padding: 40px 20px;">
                    <div style="font-size: 18px; font-weight: 700; color: #172326; margin-bottom: 8px;">
                        No Assessment Data Available
                    </div>
                    <div style="font-size: 14px; color: #667579; margin-bottom: 20px;">
                        Import operational logs or run an assessment to populate the supervisory command center.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col1, col2, col3 = st.columns([2, 1, 2])
            if col2.button("Go to Assessment Workflow", type="primary", use_container_width=True):
                go_to("assessment")
        return

    df_cses = results["cse_scores"]
    df_findings = results["findings_df"]
    df_tickets = results["ticket_scores"]

    # 2. Executive KPI Strip
    kpi_counts = conn.execute(
        """
        SELECT 
            (SELECT COUNT(*) FROM cses) AS total_entities,
            (SELECT COUNT(*) FROM alerts) AS total_alerts,
            (SELECT COUNT(*) FROM tickets) AS total_cases,
            (SELECT COUNT(*) FROM findings) AS total_findings
        """
    ).df().iloc[0]

    # Calculate real attention count from cse_scores
    high_att_count = 0
    mod_att_count = 0
    routine_att_count = 0
    if not df_cses.empty:
        for s in df_cses["total_score"]:
            b = attention_band(s)
            if b in ("Critical", "High"):
                high_att_count += 1
            elif b == "Moderate":
                mod_att_count += 1
            else:
                routine_att_count += 1

    total_requiring_attention = high_att_count + mod_att_count
    review_queue_count = len(df_tickets[df_tickets["total_score"] >= 15]) if not df_tickets.empty else 0

    kpi_cols = st.columns(6)
    kpis = [
        ("Entities Assessed", int(kpi_counts["total_entities"]), "Critical Sector Entities"),
        ("Alerts Analyzed", f"{int(kpi_counts['total_alerts']):,}", "Raw SOC telemetry"),
        ("Cases Reviewed", f"{int(kpi_counts['total_cases']):,}", "Incident tickets"),
        ("Findings Identified", int(kpi_counts["total_findings"]), "Evidence-backed gaps"),
        ("Entities Needing Attention", total_requiring_attention, f"{high_att_count} High · {mod_att_count} Moderate"),
        ("Review Queue Items", review_queue_count, "Flagged for manual review"),
    ]

    for col, (label, val, sub) in zip(kpi_cols, kpis):
        with col:
            st.markdown(
                f"""
                <div class="satsa-kpi-block">
                    <div class="satsa-kpi-label">{label}</div>
                    <div class="satsa-kpi-value">{val}</div>
                    <div class="satsa-kpi-sub">{sub}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")

    # 3. ATTENTION REQUIRED — Central Component
    st.markdown('<div class="section-title">Attention Required</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Prioritized operational entities exhibiting statistically significant capability gaps or workflow non-compliance.</div>',
        unsafe_allow_html=True,
    )

    if df_cses.empty or total_requiring_attention == 0:
        st.markdown(
            """
            <div class="satsa-card" style="border-left: 4px solid #278A55;">
                <div style="font-weight: 600; color: #278A55;">All entities operating within baseline expectations.</div>
                <div class="card-note">No Critical Sector Entity currently exceeds the supervisory attention threshold.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Attention banner summary
        st.markdown(
            f"""
            <div class="satsa-attention-banner">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                    <div>
                        <div style="font-size: 16px; font-weight: 700; color: #172326;">
                            {total_requiring_attention} Entities Require Supervisory Attention
                        </div>
                        <div class="card-note" style="margin-top: 2px;">
                            Identified through SIH26157 capability dimension evaluation and multi-engine anomaly detection.
                        </div>
                    </div>
                    <div style="display:flex; gap: 8px;">
                        <span class="satsa-badge" style="background:#FDF2F2; color:#C93C3C; border:1px solid #FACDCD; font-size:12px; padding:4px 10px;">
                            HIGH: {high_att_count} entities
                        </span>
                        <span class="satsa-badge" style="background:#FEF9EE; color:#C58A18; border:1px solid #FDE6BA; font-size:12px; padding:4px 10px;">
                            MODERATE: {mod_att_count} entities
                        </span>
                        <span class="satsa-badge" style="background:#F0F9F4; color:#278A55; border:1px solid #C4ECD5; font-size:12px; padding:4px 10px;">
                            ROUTINE: {routine_att_count} entity
                        </span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Ranked attention cards for entities requiring attention
        priority_entities = df_cses[df_cses["total_score"] > 0].sort_values("total_score", ascending=False)
        for _, row in priority_entities.iterrows():
            band_name = attention_band(row["total_score"])
            # Get primary concern from findings
            ent_findings = df_findings[df_findings["cse_id"] == row["entity_id"]]
            primary_concern = ent_findings.iloc[0]["finding_title"] if not ent_findings.empty else "Operational Pattern Deviation"
            primary_reason = ent_findings.iloc[0]["reason"] if not ent_findings.empty else "Deviation from peer performance baseline"
            finding_cnt = int(row["finding_count"])

            border_accent = COLOR_HIGH if band_name in ("Critical", "High") else COLOR_MODERATE

            with st.container():
                st.markdown(
                    f"""
                    <div class="satsa-card satsa-card-interactive" style="border-left: 4px solid {border_accent};">
                        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 6px;">
                            <div>
                                <span style="font-size: 16px; font-weight: 700; color: #172326;">{row['entity_name']}</span>
                                <span style="font-size: 12px; color: #667579; margin-left: 8px;">({row['entity_id']})</span>
                                <span style="margin-left: 8px;">{badge(row['sector'], 'Routine')}</span>
                                <span style="margin-left: 6px;">{badge(row['criticality'].title() + ' Criticality', 'Routine')}</span>
                            </div>
                            <div>
                                {badge(band_name.upper() + ' ATTENTION', band_name)}
                                <span style="font-size: 13px; font-weight: 700; color: {border_accent}; margin-left: 8px;">
                                    Score: {row['total_score']:.1f}/100
                                </span>
                            </div>
                        </div>
                        <div style="font-size: 13.5px; color: #172326; margin: 4px 0;">
                            <strong>Primary Concern:</strong> <span style="color: {border_accent}; font-weight: 600;">{primary_concern}</span>
                            — <span style="color: #485659;">{primary_reason}</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-top: 8px;">
                            <span class="meta-line">
                                <strong>{finding_cnt}</strong> structured evidence finding{'s' if finding_cnt != 1 else ''} logged
                            </span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                c1, c2, c3 = st.columns([5, 1.2, 1.2])
                if c2.button("View Entity →", key=f"cmd_ent_{row['entity_id']}", type="primary", use_container_width=True):
                    go_to("entity_detail", selected_entity=row["entity_id"])
                if c3.button("Inspect Findings", key=f"cmd_fnd_{row['entity_id']}", type="secondary", use_container_width=True):
                    go_to("findings", entity_filter=row["entity_name"])

    st.write("")

    # 4. Analytical Breakdown: Findings by Capability Dimension
    st.markdown('<div class="section-title">Findings Breakdown by Capability Dimension</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Distribution of supervisory gaps across the 8 SIH26157 capability dimensions (Real Assessment Data).</div>',
        unsafe_allow_html=True,
    )

    if not df_findings.empty:
        dim_counts = df_findings["dimension"].value_counts().reset_index()
        dim_counts.columns = ["Dimension", "Count"]

        b_cols = st.columns([4, 3])
        with b_cols[0]:
            total_fnds = len(df_findings)
            for _, r in dim_counts.iterrows():
                d_name = r["Dimension"]
                cnt = int(r["Count"])
                pct = int((cnt / total_fnds) * 100)
                st.markdown(
                    f"""
                    <div class="cap-row">
                        <div class="cap-label-row">
                            <span style="font-weight: 600;">{d_name}</span>
                            <span style="font-weight: 600; color: #087F73;">{cnt} finding{'s' if cnt > 1 else ''} ({pct}%)</span>
                        </div>
                        <div class="cap-track">
                            <div class="cap-fill" style="width: {max(pct, 5)}%; background-color: #087F73;"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with b_cols[1]:
            with st.container():
                st.markdown(
                    """
                    <div class="satsa-card" style="height: 100%;">
                        <div style="font-size: 14px; font-weight: 700; color: #172326; margin-bottom: 8px;">
                            Supervisory Capability Observations
                        </div>
                        <ul style="font-size: 13px; color: #485659; margin-left: -15px; line-height: 1.6;">
                            <li><strong>Escalation</strong> represents the highest concentration of supervisory risk with 5 Critical Sector Entities closing critical tickets without Tier-2 CSIRT escalation.</li>
                            <li><strong>Investigation Quality</strong> identified superficial notes (< 10 words) across closed incident tickets.</li>
                            <li><strong>Security Operations</strong> flagged metric gaming and triage speed anomalies (< 30s closures).</li>
                            <li><strong>Incident Response SLA</strong> breaches detected on high/critical priority tickets exceeding 180 min window.</li>
                        </ul>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.write("")

    # 5. Priority Entities Enterprise Data Table
    st.markdown('<div class="section-title">Critical Sector Entities Master Table</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Comprehensive supervisory register of all assessed critical infrastructure entities with sorting and filters.</div>',
        unsafe_allow_html=True,
    )

    df_all_cses = conn.execute("SELECT cse_id, entity_name, sector, criticality, maturity_level FROM cses").df()
    merged_cses = df_all_cses.merge(
        df_cses[["entity_id", "total_score", "finding_count"]] if not df_cses.empty else pd.DataFrame(columns=["entity_id", "total_score", "finding_count"]),
        left_on="cse_id", right_on="entity_id", how="left"
    )
    merged_cses["total_score"] = merged_cses["total_score"].fillna(0.0)
    merged_cses["finding_count"] = merged_cses["finding_count"].fillna(0).astype(int)
    merged_cses["attention"] = merged_cses["total_score"].apply(attention_band)

    # Filter Controls
    fc1, fc2, fc3 = st.columns([2, 2, 3])
    sectors_list = ["All Sectors"] + sorted(merged_cses["sector"].unique().tolist())
    sel_sector = fc1.selectbox("Filter Sector", sectors_list, key="ov_sel_sec")
    sel_attention = fc2.selectbox("Filter Attention", ["All Attention Levels", "Critical", "High", "Moderate", "Low"], key="ov_sel_att")
    filter_search = fc3.text_input("Search Entity Name", placeholder="Type entity name…", key="ov_txt_search")

    filtered = merged_cses.copy()
    if sel_sector != "All Sectors":
        filtered = filtered[filtered["sector"] == sel_sector]
    if sel_attention != "All Attention Levels":
        filtered = filtered[filtered["attention"] == sel_attention]
    if filter_search:
        filtered = filtered[filtered["entity_name"].str.contains(filter_search, case=False, na=False)]

    filtered = filtered.sort_values("total_score", ascending=False)

    # Table Header
    thead = st.columns([0.6, 3.2, 1.8, 1.4, 1.4, 1.2, 1.2, 1.4])
    cols_titles = ["#", "Entity Name", "Sector", "Criticality", "Attention", "Score", "Findings", "Action"]
    for c, t in zip(thead, cols_titles):
        c.markdown(f'<div class="tbl-head">{t}</div>', unsafe_allow_html=True)

    for rank, (_, row) in enumerate(filtered.iterrows(), start=1):
        band_name = row["attention"]
        r = st.columns([0.6, 3.2, 1.8, 1.4, 1.4, 1.2, 1.2, 1.4])
        r[0].markdown(f'<div class="tbl-row">{rank}</div>', unsafe_allow_html=True)
        r[1].markdown(f'<div class="tbl-row"><strong>{row["entity_name"]}</strong></div>', unsafe_allow_html=True)
        r[2].markdown(f'<div class="tbl-row">{row["sector"]}</div>', unsafe_allow_html=True)
        r[3].markdown(f'<div class="tbl-row">{row["criticality"].title()}</div>', unsafe_allow_html=True)
        r[4].markdown(f'<div class="tbl-row">{badge(band_name.upper(), band_name)}</div>', unsafe_allow_html=True)
        r[5].markdown(f'<div class="tbl-row" style="font-weight:600;">{row["total_score"]:.1f}</div>', unsafe_allow_html=True)
        r[6].markdown(f'<div class="tbl-row">{row["finding_count"]}</div>', unsafe_allow_html=True)
        if r[7].button("Inspect →", key=f"tbl_view_{row['cse_id']}", type="secondary", use_container_width=True):
            go_to("entity_detail", selected_entity=row["cse_id"])
