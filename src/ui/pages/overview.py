"""
Page: Overview (Executive Dashboard).
SAT-SA — Supervisory Analytics Tool for SOC Assessment.
"""

import streamlit as st
import pandas as pd
from src.ui.styles import (
    badge, neutral_badge, attention_band, finding_severity_band,
    COLOR_TEAL_PRIMARY, COLOR_CRITICAL, COLOR_HIGH, COLOR_MODERATE, COLOR_LOW, COLOR_NEUTRAL
)
from src.ui.nav import go_to, fmt_dt, fmt_period
from src.ui.db_helper import get_assessment_period, get_last_assessment_time


def render_overview_page(conn, results):
    st.markdown('<div class="page-title">Supervisory Command Center</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Real-time operational overview — entity attention priorities, capability gap distribution, and supervisory review backlog.</div>',
        unsafe_allow_html=True,
    )

    if results is None:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-state-icon">📊</div>
                <div class="empty-state-title">No Assessment Data Available</div>
                <div class="empty-state-desc">Import operational logs or generate a dataset to populate the command center.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns([2, 1.5, 2])
        if c2.button("Go to Assessment Workflow", type="primary", use_container_width=True):
            go_to("assessment")
        return

    df_cses    = results["cse_scores"]
    df_findings = results["findings_df"]
    df_tickets  = results["ticket_scores"]

    # ── 1. KPI Strip ──────────────────────────────────────────────────────────
    kpi_counts = conn.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM cses)     AS total_entities,
            (SELECT COUNT(*) FROM alerts)   AS total_alerts,
            (SELECT COUNT(*) FROM tickets)  AS total_cases,
            (SELECT COUNT(*) FROM findings) AS total_findings
        """
    ).df().iloc[0]

    high_att_count = 0
    mod_att_count  = 0
    routine_count  = 0
    if not df_cses.empty:
        for s in df_cses["total_score"]:
            b = attention_band(s)
            if b in ("Critical", "High"):
                high_att_count += 1
            elif b == "Moderate":
                mod_att_count += 1
            else:
                routine_count += 1

    total_attention   = high_att_count + mod_att_count
    review_queue_count = len(df_tickets[df_tickets["total_score"] >= 15]) if not df_tickets.empty else 0

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    _kpi(k1, "Entities", int(kpi_counts["total_entities"]), "Critical sector SOCs")
    _kpi(k2, "Alerts Analyzed", f"{int(kpi_counts['total_alerts']):,}", "Raw telemetry events")
    _kpi(k3, "Incident Cases", f"{int(kpi_counts['total_cases']):,}", "Linked SOC tickets")
    _kpi(k4, "Findings", int(kpi_counts["total_findings"]), "Evidence-backed gaps")
    _kpi(k5, "Need Attention", total_attention,
         f"{high_att_count} high · {mod_att_count} moderate",
         value_color=COLOR_CRITICAL if high_att_count else COLOR_MODERATE)
    _kpi_hero(k6, "Review Queue", review_queue_count, "Cases pending manual review",
              value_color=COLOR_HIGH if review_queue_count else COLOR_LOW)

    st.write("")

    # ── 2. Priority Attention Entities ────────────────────────────────────────
    st.markdown('<div class="section-title">⚠ Entities Requiring Supervisory Attention</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Ranked by composite attention score. Entities above the threshold exhibit statistically significant operational anomalies or capability gaps compared to peer cohort.</div>',
        unsafe_allow_html=True,
    )

    if df_cses.empty or total_attention == 0:
        st.markdown(
            """
            <div class="satsa-card satsa-card-low" style="padding:16px 20px;">
                <span style="font-weight:700; color:#16A34A;">✓ All entities are operating within expected baseline.</span>
                <div class="card-note" style="margin-top:4px;">No Critical Sector Entity currently exceeds the supervisory attention threshold.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Summary banner
        st.markdown(
            f"""
            <div class="satsa-attention-banner">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                    <div>
                        <div style="font-size:15px; font-weight:700; color:#111827;">
                            {total_attention} Entities Flagged for Supervisory Review
                        </div>
                        <div class="card-note" style="margin-top:3px;">
                            Identified through multi-engine anomaly detection and capability dimension analysis.
                        </div>
                    </div>
                    <div style="display:flex; gap:8px; flex-wrap:wrap;">
                        <span class="satsa-badge" style="background:#FEF2F2;color:#DC2626;border:1px solid #FECACA;">HIGH: {high_att_count}</span>
                        <span class="satsa-badge" style="background:#FFFBEB;color:#D97706;border:1px solid #FDE68A;">MODERATE: {mod_att_count}</span>
                        <span class="satsa-badge" style="background:#F0FDF4;color:#16A34A;border:1px solid #BBF7D0;">ROUTINE: {routine_count}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        priority_ents = df_cses[df_cses["total_score"] > 0].sort_values("total_score", ascending=False)
        for _, row in priority_ents.iterrows():
            band_name     = attention_band(row["total_score"])
            ent_findings  = df_findings[df_findings["cse_id"] == row["entity_id"]]
            primary_title = ent_findings.iloc[0]["finding_title"] if not ent_findings.empty else "Operational pattern deviation detected"
            primary_reason = ent_findings.iloc[0]["reason"] if not ent_findings.empty else "Deviation from peer performance baseline"
            finding_cnt   = int(row["finding_count"])

            accent = COLOR_CRITICAL if band_name in ("Critical", "High") else COLOR_MODERATE
            score_color = COLOR_CRITICAL if band_name in ("Critical", "High") else (
                COLOR_MODERATE if band_name == "Moderate" else COLOR_LOW
            )

            with st.container():
                st.markdown(
                    f"""
                    <div class="satsa-card satsa-card-interactive" style="border-left:3px solid {accent};">
                        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom:6px;">
                            <div>
                                <span style="font-size:15px; font-weight:700; color:#111827;">{row['entity_name']}</span>
                                <span style="font-size:11.5px; color:#6B7280; margin-left:8px;">({row['entity_id']})</span>
                                <span style="margin-left:8px;">{neutral_badge(row['sector'])}</span>
                                <span style="margin-left:6px;">{neutral_badge(row['criticality'].title() + ' criticality')}</span>
                            </div>
                            <div style="display:flex; align-items:center; gap:10px; flex-shrink:0;">
                                {badge(band_name.upper() + ' ATTENTION', band_name)}
                                <span style="font-size:14px; font-weight:800; color:{score_color};">{row['total_score']:.1f}<span style="font-size:11px; font-weight:500; color:#9CA3AF;">/100</span></span>
                            </div>
                        </div>
                        <div style="font-size:13.5px; color:#111827; margin:4px 0;">
                            <strong>Primary concern:</strong> <span style="color:{accent}; font-weight:600;">{primary_title}</span>
                            — <span style="color:#4B5563;">{primary_reason}</span>
                        </div>
                        <div style="margin-top:8px;" class="meta-line">
                            <strong>{finding_cnt}</strong> structured evidence finding{'s' if finding_cnt != 1 else ''} recorded
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                act_c1, act_c2 = st.columns([6.5, 1.5])
                if act_c2.button("View Entity →", key=f"ov_ent_{row['entity_id']}", type="primary", use_container_width=True):
                    go_to("entity_detail", selected_entity=row["entity_id"])

    st.write("")

    # ── 3. Findings by Capability Dimension ───────────────────────────────────
    st.markdown('<div class="section-title">Findings Breakdown by Capability Dimension</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Distribution of supervisory gaps across capability dimensions from real assessment data.</div>',
        unsafe_allow_html=True,
    )
    st.caption("A score of 0 means no anomaly detected for that dimension — this is the expected baseline.")

    if not df_findings.empty:
        dim_counts  = df_findings["dimension"].value_counts().reset_index()
        dim_counts.columns = ["Dimension", "Count"]
        total_fnds  = len(df_findings)

        bc1, bc2 = st.columns([4, 3])
        with bc1:
            for _, r in dim_counts.iterrows():
                d_name = r["Dimension"]
                cnt    = int(r["Count"])
                pct    = int((cnt / total_fnds) * 100)
                bar_color = COLOR_CRITICAL if pct > 40 else (COLOR_MODERATE if pct > 20 else COLOR_TEAL_PRIMARY)
                st.markdown(
                    f"""
                    <div class="cap-row">
                        <div class="cap-label-row">
                            <span style="font-weight:600; color:#111827;">{d_name}</span>
                            <span style="font-weight:700; color:{bar_color}; font-size:13px;">{cnt} finding{'s' if cnt > 1 else ''} &nbsp;({pct}%)</span>
                        </div>
                        <div class="cap-track">
                            <div class="cap-fill" style="width:{max(pct, 4)}%; background:{bar_color};"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with bc2:
            st.markdown(
                """
                <div class="satsa-card" style="height:100%;">
                    <div style="font-size:14px; font-weight:700; color:#111827; margin-bottom:10px;">Capability Observations</div>
                    <ul style="font-size:13px; color:#374151; margin-left:-14px; line-height:1.65; margin-top:0;">
                        <li><strong>Escalation compliance</strong> is the highest-risk dimension — multiple entities closed critical tickets without Tier-2 CSIRT escalation.</li>
                        <li><strong>Investigation quality</strong> shows superficial documentation patterns (&lt;10 words) across closed tickets.</li>
                        <li><strong>Security operations</strong> detected triage speed anomalies (sub-30s closures) indicating possible metric gaming.</li>
                        <li><strong>Incident Response SLA</strong> breaches identified on high and critical priority tickets exceeding the 180-minute threshold.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")

    # ── 4. All Entities Master Table ──────────────────────────────────────────
    st.markdown('<div class="section-title">All Entities — Ranked Priority Register</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Complete supervisory register of all assessed critical infrastructure entities. Filter and sort to focus your review.</div>',
        unsafe_allow_html=True,
    )

    df_all_cses = conn.execute("SELECT cse_id, entity_name, sector, criticality, maturity_level FROM cses").df()
    merged = df_all_cses.merge(
        df_cses[["entity_id", "total_score", "finding_count"]] if not df_cses.empty
        else pd.DataFrame(columns=["entity_id", "total_score", "finding_count"]),
        left_on="cse_id", right_on="entity_id", how="left",
    )
    merged["total_score"]  = merged["total_score"].fillna(0.0)
    merged["finding_count"] = merged["finding_count"].fillna(0).astype(int)
    merged["attention"]    = merged["total_score"].apply(attention_band)

    fc1, fc2, fc3 = st.columns([2, 2, 3])
    sector_opts = ["All Sectors"] + sorted(merged["sector"].unique().tolist())
    sel_sec = fc1.selectbox("Sector", sector_opts, key="ov_sec", label_visibility="collapsed")
    sel_att = fc2.selectbox(
        "Attention",
        ["All Attention Levels", "Critical", "High", "Moderate", "Low"],
        key="ov_att",
        label_visibility="collapsed",
    )
    txt_q = fc3.text_input("", placeholder="Search entity name…", key="ov_txt", label_visibility="collapsed")

    filtered = merged.copy()
    if sel_sec != "All Sectors":
        filtered = filtered[filtered["sector"] == sel_sec]
    if sel_att != "All Attention Levels":
        filtered = filtered[filtered["attention"] == sel_att]
    if txt_q:
        filtered = filtered[filtered["entity_name"].str.contains(txt_q, case=False, na=False)]
    filtered = filtered.sort_values("total_score", ascending=False)

    st.caption(f"Showing {len(filtered)} of {len(merged)} entities")

    thead = st.columns([0.5, 3, 1.8, 1.5, 1.8, 1.4, 1.2, 1.5])
    for c, t in zip(thead, ["#", "Entity Name", "Sector", "Criticality", "Attention Level", "Score", "Findings", ""]):
        c.markdown(f'<div class="tbl-head">{t}</div>', unsafe_allow_html=True)

    for rank, (_, row) in enumerate(filtered.iterrows(), start=1):
        band = row["attention"]
        score_color = COLOR_CRITICAL if band in ("Critical", "High") else (
            COLOR_MODERATE if band == "Moderate" else COLOR_LOW
        )
        row_cls = "tbl-row-alt" if rank % 2 == 0 else "tbl-row"
        r = st.columns([0.5, 3, 1.8, 1.5, 1.8, 1.4, 1.2, 1.5])
        r[0].markdown(f'<div class="{row_cls}">{rank}</div>', unsafe_allow_html=True)
        r[1].markdown(f'<div class="{row_cls}"><strong>{row["entity_name"]}</strong><br/><span style="font-size:11px;color:#9CA3AF;">{row["cse_id"]}</span></div>', unsafe_allow_html=True)
        r[2].markdown(f'<div class="{row_cls}">{row["sector"]}</div>', unsafe_allow_html=True)
        r[3].markdown(f'<div class="{row_cls}">{row["criticality"].title()}</div>', unsafe_allow_html=True)
        r[4].markdown(f'<div class="{row_cls}">{badge(band, band)}</div>', unsafe_allow_html=True)
        r[5].markdown(f'<div class="{row_cls}" style="font-weight:700; color:{score_color};">{row["total_score"]:.1f}</div>', unsafe_allow_html=True)
        r[6].markdown(f'<div class="{row_cls}">{row["finding_count"]}</div>', unsafe_allow_html=True)
        if r[7].button("Inspect →", key=f"ov_tbl_{row['cse_id']}", type="secondary", use_container_width=True):
            go_to("entity_detail", selected_entity=row["cse_id"])


def _kpi(col, label, value, sub, value_color="#111827"):
    col.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">{label}</div><div class="satsa-kpi-value" style="color:{value_color};">{value}</div><div class="satsa-kpi-sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )


def _kpi_hero(col, label, value, sub, value_color="#111827"):
    col.markdown(
        f'<div class="satsa-kpi-hero"><div class="satsa-kpi-label">{label}</div><div class="satsa-kpi-value" style="color:{value_color};">{value}</div><div class="satsa-kpi-sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )
