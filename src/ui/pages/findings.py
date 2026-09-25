"""
Page: Findings & Evidence.
SAT-SA — Supervisory Analytics Tool for SOC Assessment.
"""

import streamlit as st
import pandas as pd
from src.ui.styles import badge, neutral_badge, finding_severity_band, COLOR_CRITICAL, COLOR_MODERATE, COLOR_LOW, COLOR_TEAL_PRIMARY
from src.ui.nav import go_to
from src.analytics.dimensions import DIMENSIONS


def _dim_score_for(dim_scores_df, cse_id, dimension) -> float:
    if dim_scores_df is None or dim_scores_df.empty or cse_id not in dim_scores_df["cse_id"].values:
        return 0.0
    row = dim_scores_df[dim_scores_df["cse_id"] == cse_id].iloc[0]
    return float(row.get(dimension, 0.0))


def render_findings_page(conn, results):
    st.markdown('<div class="page-title">Findings & Evidence</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Evidence-backed capability gaps, operational anomalies, and policy non-compliance issues — each finding is traceable to raw data records.</div>',
        unsafe_allow_html=True,
    )

    df_findings = results["findings_df"] if results else pd.DataFrame()
    if df_findings.empty:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <div class="empty-state-title">No Findings Generated</div>
                <div class="empty-state-desc">Run an assessment in the Assessment tab to evaluate operational logs and generate structured findings.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    dim_scores    = results["dimension_scores"]
    df_cses       = results["cse_scores"]
    name_lookup   = dict(zip(df_cses["entity_id"], df_cses["entity_name"])) if not df_cses.empty else {}
    sector_lookup = dict(zip(df_cses["entity_id"], df_cses["sector"]))      if not df_cses.empty else {}

    df = df_findings.copy()
    df["entity_name"]    = df["cse_id"].map(name_lookup).fillna(df["cse_id"])
    df["sector"]         = df["cse_id"].map(sector_lookup).fillna("Unknown")
    df["dim_score"]      = df.apply(lambda r: _dim_score_for(dim_scores, r["cse_id"], r["dimension"]), axis=1)
    df["severity"]       = df["dim_score"].apply(finding_severity_band)
    df["evidence_count"] = df["evidence_record_ids"].apply(
        lambda s: len([e for e in str(s).split(",") if e.strip()])
    )

    high_cnt = len(df[df["severity"] == "High"])
    med_cnt  = len(df[df["severity"] == "Medium"])
    low_cnt  = len(df[df["severity"] == "Low"])

    # Summary strip
    s1, s2, s3 = st.columns([1.2, 2.8, 3])
    with s1:
        st.markdown(
            f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Total Findings</div><div class="satsa-kpi-value">{len(df)}</div><div class="satsa-kpi-sub">Across all dimensions</div></div>',
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            f"""
            <div class="satsa-kpi-block">
                <div class="satsa-kpi-label">Severity Breakdown</div>
                <div style="display:flex; gap:8px; margin-top:8px; flex-wrap:wrap;">
                    <span class="satsa-badge" style="background:#FEF2F2;color:#DC2626;border:1px solid #FECACA;">HIGH: {high_cnt}</span>
                    <span class="satsa-badge" style="background:#FFFBEB;color:#D97706;border:1px solid #FDE68A;">MEDIUM: {med_cnt}</span>
                    <span class="satsa-badge" style="background:#F0FDF4;color:#16A34A;border:1px solid #BBF7D0;">LOW: {low_cnt}</span>
                </div>
                <div class="satsa-kpi-sub" style="margin-top:6px;">Calibrated against baseline thresholds</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s3:
        dim_summary  = df["dimension"].value_counts().to_dict()
        badges_html  = " ".join([
            f"<span class='satsa-badge' style='background:#F3F4F6;color:#111827;border:1px solid #E5E7EB;margin:2px;'>{k}: {v}</span>"
            for k, v in dim_summary.items()
        ])
        st.markdown(
            f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">By Capability</div><div style="margin-top:6px; display:flex; flex-wrap:wrap; gap:3px;">{badges_html}</div></div>',
            unsafe_allow_html=True,
        )

    st.write("")

    # Filters
    f1, f2, f3, f4, f5 = st.columns(5)
    ent_opts = ["All Entities"]    + sorted(df["entity_name"].dropna().unique().tolist())
    sec_opts = ["All Sectors"]     + sorted(df["sector"].dropna().unique().tolist())
    sev_opts = ["All Severities",   "High", "Medium", "Low"]
    cap_opts = ["All Capabilities"] + sorted(df["dimension"].dropna().unique().tolist())

    default_ent = st.session_state.get("entity_filter", "All Entities")
    if default_ent not in ent_opts:
        default_ent = "All Entities"

    sel_ent = f1.selectbox("Entity",     ent_opts, index=ent_opts.index(default_ent), key="fnd_ent")
    sel_sec = f2.selectbox("Sector",     sec_opts, key="fnd_sec")
    sel_sev = f3.selectbox("Severity",   sev_opts, key="fnd_sev")
    sel_cap = f4.selectbox("Capability", cap_opts, key="fnd_cap")
    txt_q   = f5.text_input("", placeholder="Search title or reason…", key="fnd_txt", label_visibility="collapsed")

    filtered = df.copy()
    if sel_ent != "All Entities":     filtered = filtered[filtered["entity_name"] == sel_ent]
    if sel_sec != "All Sectors":      filtered = filtered[filtered["sector"] == sel_sec]
    if sel_sev != "All Severities":   filtered = filtered[filtered["severity"] == sel_sev]
    if sel_cap != "All Capabilities": filtered = filtered[filtered["dimension"] == sel_cap]
    if txt_q:
        filtered = filtered[
            filtered["finding_title"].str.contains(txt_q, case=False, na=False) |
            filtered["reason"].str.contains(txt_q, case=False, na=False)
        ]
    filtered = filtered.sort_values("dim_score", ascending=False)

    cap1, cap2 = st.columns([6, 1.5])
    cap1.caption(f"Showing {len(filtered)} of {len(df)} findings")
    if cap2.button("Clear Filters", key="fnd_clr", type="secondary"):
        st.session_state.entity_filter = "All Entities"
        st.rerun()

    if filtered.empty:
        st.markdown(
            '<div class="satsa-card" style="text-align:center; padding:24px;"><div style="color:#6B7280; font-weight:600;">No findings match the selected filters.</div></div>',
            unsafe_allow_html=True,
        )
        return

    # Table
    thead = st.columns([2.8, 2.2, 1.8, 1.2, 1.3, 1.0, 1.5])
    for c, t in zip(thead, ["Finding Title", "Entity Name", "Capability", "Severity", "Confidence", "Evidence", "Action"]):
        c.markdown(f'<div class="tbl-head">{t}</div>', unsafe_allow_html=True)

    for idx, (_, row) in enumerate(filtered.iterrows()):
        sev     = row["severity"]
        row_cls = "tbl-row-alt" if idx % 2 == 0 else "tbl-row"
        r = st.columns([2.8, 2.2, 1.8, 1.2, 1.3, 1.0, 1.5])
        r[0].markdown(f'<div class="{row_cls}"><strong>{row["finding_title"]}</strong></div>', unsafe_allow_html=True)
        r[1].markdown(f'<div class="{row_cls}">{row["entity_name"]}</div>', unsafe_allow_html=True)
        r[2].markdown(f'<div class="{row_cls}">{row["dimension"]}</div>', unsafe_allow_html=True)
        r[3].markdown(f'<div class="{row_cls}">{badge(sev.upper(), sev)}</div>', unsafe_allow_html=True)
        r[4].markdown(f'<div class="{row_cls}">{neutral_badge(row["confidence_strength"].title())}</div>', unsafe_allow_html=True)
        r[5].markdown(f'<div class="{row_cls}" style="font-weight:700; color:{COLOR_TEAL_PRIMARY};">{row["evidence_count"]}</div>', unsafe_allow_html=True)
        if r[6].button("Details →", key=f"fnd_{row['finding_id']}", type="secondary", use_container_width=True):
            go_to("finding_detail", selected_finding=row["finding_id"])
