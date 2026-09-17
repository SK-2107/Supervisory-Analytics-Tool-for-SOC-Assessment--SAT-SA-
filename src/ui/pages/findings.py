"""
Page: Supervisory Findings Directory.
Enterprise Light Theme — Comprehensive register of all structured capability dimension findings.
"""

import streamlit as st
import pandas as pd
from src.ui.styles import badge, finding_severity_band
from src.ui.nav import go_to
from src.analytics.dimensions import DIMENSIONS


def _dim_score_for(dim_scores_df, cse_id, dimension) -> float:
    if dim_scores_df is None or dim_scores_df.empty or cse_id not in dim_scores_df["cse_id"].values:
        return 0.0
    row = dim_scores_df[dim_scores_df["cse_id"] == cse_id].iloc[0]
    return float(row.get(dimension, 0.0))


def render_findings_page(conn, results):
    st.markdown('<div class="page-title">Supervisory Findings Directory</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Evidence-backed capability gaps, operational anomalies, and policy non-compliance issues.</div>',
        unsafe_allow_html=True,
    )

    df_findings = results["findings_df"] if results else pd.DataFrame()
    if df_findings.empty:
        st.markdown(
            """
            <div class="satsa-card" style="text-align: center; padding: 30px;">
                <div style="font-weight: 600; color: #172326;">No Findings Generated</div>
                <div class="card-note">Run an assessment in the Assessment tab to evaluate operational logs.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    dim_scores = results["dimension_scores"]
    df_cses = results["cse_scores"]
    name_lookup = dict(zip(df_cses["entity_id"], df_cses["entity_name"])) if not df_cses.empty else {}
    sector_lookup = dict(zip(df_cses["entity_id"], df_cses["sector"])) if not df_cses.empty else {}

    df = df_findings.copy()
    df["entity_name"] = df["cse_id"].map(name_lookup).fillna(df["cse_id"])
    df["sector"] = df["cse_id"].map(sector_lookup).fillna("Unknown")
    df["dim_score"] = df.apply(lambda r: _dim_score_for(dim_scores, r["cse_id"], r["dimension"]), axis=1)
    df["severity"] = df["dim_score"].apply(finding_severity_band)
    df["evidence_count"] = df["evidence_record_ids"].apply(lambda s: len([e for e in str(s).split(",") if e.strip()]))

    # Summary Section Above Table
    high_cnt = len(df[df["severity"] == "High"])
    med_cnt = len(df[df["severity"] == "Medium"])
    low_cnt = len(df[df["severity"] == "Low"])

    s_cols = st.columns([1.2, 2.5, 3.3])
    with s_cols[0]:
        st.markdown(
            f"""
            <div class="satsa-kpi-block">
                <div class="satsa-kpi-label">Total Findings</div>
                <div class="satsa-kpi-value">{len(df)}</div>
                <div class="satsa-kpi-sub">Across 8 Dimensions</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s_cols[1]:
        st.markdown(
            f"""
            <div class="satsa-kpi-block">
                <div class="satsa-kpi-label">Severity Breakdown</div>
                <div style="display:flex; gap: 8px; margin-top: 6px;">
                    <span class="satsa-badge" style="background:#FDF2F2; color:#C93C3C; border:1px solid #FACDCD;">HIGH: {high_cnt}</span>
                    <span class="satsa-badge" style="background:#FEF9EE; color:#C58A18; border:1px solid #FDE6BA;">MEDIUM: {med_cnt}</span>
                    <span class="satsa-badge" style="background:#F0F9F4; color:#278A55; border:1px solid #C4ECD5;">LOW: {low_cnt}</span>
                </div>
                <div class="satsa-kpi-sub" style="margin-top:6px;">Calibrated against baseline thresholds</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s_cols[2]:
        dim_summary = df["dimension"].value_counts().to_dict()
        badges_html = " ".join([f"<span class='satsa-badge' style='background:#F1F5F4; color:#172326; margin:2px;'>{k}: {v}</span>" for k, v in dim_summary.items()])
        st.markdown(
            f"""
            <div class="satsa-kpi-block">
                <div class="satsa-kpi-label">Findings by Capability</div>
                <div style="margin-top: 4px; display:flex; flex-wrap:wrap; gap:4px;">
                    {badges_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    # Filter Bar
    f1, f2, f3, f4, f5 = st.columns(5)
    entity_opts = ["All Entities"] + sorted(df["entity_name"].dropna().unique().tolist())
    sector_opts = ["All Sectors"] + sorted(df["sector"].dropna().unique().tolist())
    sev_opts = ["All Severities", "High", "Medium", "Low"]
    cap_opts = ["All Capabilities"] + sorted(df["dimension"].dropna().unique().tolist())

    # Pre-select entity filter if navigated from command center
    default_ent = st.session_state.get("entity_filter", "All Entities")
    if default_ent not in entity_opts:
        default_ent = "All Entities"

    sel_ent = f1.selectbox("Filter Entity", entity_opts, index=entity_opts.index(default_ent), key="fnd_sel_ent")
    sel_sec = f2.selectbox("Filter Sector", sector_opts, key="fnd_sel_sec")
    sel_sev = f3.selectbox("Filter Severity", sev_opts, key="fnd_sel_sev")
    sel_cap = f4.selectbox("Filter Capability", cap_opts, key="fnd_sel_cap")
    search_txt = f5.text_input("Search Keyword", placeholder="Title or reason…", key="fnd_txt_search")

    filtered = df.copy()
    if sel_ent != "All Entities":
        filtered = filtered[filtered["entity_name"] == sel_ent]
    if sel_sec != "All Sectors":
        filtered = filtered[filtered["sector"] == sel_sec]
    if sel_sev != "All Severities":
        filtered = filtered[filtered["severity"] == sel_sev]
    if sel_cap != "All Capabilities":
        filtered = filtered[filtered["dimension"] == sel_cap]
    if search_txt:
        filtered = filtered[
            filtered["finding_title"].str.contains(search_txt, case=False, na=False) |
            filtered["reason"].str.contains(search_txt, case=False, na=False)
        ]

    filtered = filtered.sort_values("dim_score", ascending=False)

    sub_c1, sub_c2 = st.columns([5, 2])
    sub_c1.caption(f"Showing {len(filtered)} of {len(df)} finding(s)")
    if sub_c2.button("Clear All Filters", key="btn_clear_fnd_filters", type="secondary"):
        st.session_state.entity_filter = "All Entities"
        st.rerun()

    if filtered.empty:
        st.markdown(
            """
            <div class="satsa-card" style="text-align: center; padding: 24px;">
                <div style="font-weight: 600; color: #667579;">No findings match the selected filters.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Table
    thead = st.columns([2.8, 2.2, 1.8, 1.2, 1.3, 1.1, 1.4])
    for c, t in zip(thead, ["Finding Title", "Entity Name", "Capability Dimension", "Severity", "Confidence", "Evidence", "Action"]):
        c.markdown(f'<div class="tbl-head">{t}</div>', unsafe_allow_html=True)

    for _, row in filtered.iterrows():
        sev_name = row["severity"]
        r = st.columns([2.8, 2.2, 1.8, 1.2, 1.3, 1.1, 1.4])
        r[0].markdown(f'<div class="tbl-row"><strong>{row["finding_title"]}</strong></div>', unsafe_allow_html=True)
        r[1].markdown(f'<div class="tbl-row">{row["entity_name"]}</div>', unsafe_allow_html=True)
        r[2].markdown(f'<div class="tbl-row">{row["dimension"]}</div>', unsafe_allow_html=True)
        r[3].markdown(f'<div class="tbl-row">{badge(sev_name.upper(), sev_name)}</div>', unsafe_allow_html=True)
        r[4].markdown(f'<div class="tbl-row">{badge(row["confidence_strength"].title(), "Routine")}</div>', unsafe_allow_html=True)
        r[5].markdown(f'<div class="tbl-row" style="color:#087F73; font-weight:600;">{row["evidence_count"]} recs</div>', unsafe_allow_html=True)
        if r[6].button("Inspect →", key=f"fnd_inspect_{row['finding_id']}", type="secondary", use_container_width=True):
            go_to("finding_detail", selected_finding=row["finding_id"])
