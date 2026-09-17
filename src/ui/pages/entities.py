"""
Page: Entities Directory.
Enterprise Light Theme — Directory of Critical Sector Entities (CSEs) with multi-filtering and attention rankings.
"""

import streamlit as st
import pandas as pd
from src.ui.styles import badge, attention_band
from src.ui.nav import go_to


def render_entities_page(conn, results):
    st.markdown('<div class="page-title">Critical Sector Entities</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Supervisory register of all critical infrastructure SOC operations under oversight.</div>',
        unsafe_allow_html=True,
    )

    df_cses = results["cse_scores"] if results else pd.DataFrame()
    df_all = conn.execute("SELECT cse_id, entity_name, sector, peer_group, criticality, maturity_level FROM cses").df()

    if df_all.empty:
        st.markdown(
            """
            <div class="satsa-card" style="text-align: center; padding: 30px;">
                <div style="font-weight: 600; color: #172326;">No Critical Sector Entities Found</div>
                <div class="card-note">Import entity configuration or sample data in the Assessment tab.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Merge scores
    merged = df_all.merge(
        df_cses[["entity_id", "total_score", "finding_count"]] if not df_cses.empty else pd.DataFrame(columns=["entity_id", "total_score", "finding_count"]),
        left_on="cse_id", right_on="entity_id", how="left",
    )
    merged["total_score"] = merged["total_score"].fillna(0.0)
    merged["finding_count"] = merged["finding_count"].fillna(0).astype(int)
    merged["attention"] = merged["total_score"].apply(attention_band)

    # KPI strip for entities
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Total Entities</div><div class="satsa-kpi-value">{len(merged)}</div></div>',
        unsafe_allow_html=True,
    )
    high_cnt = len(merged[merged["attention"].isin(["Critical", "High"])])
    c2.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">High Attention</div><div class="satsa-kpi-value" style="color:#C93C3C;">{high_cnt}</div></div>',
        unsafe_allow_html=True,
    )
    mod_cnt = len(merged[merged["attention"] == "Moderate"])
    c3.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Moderate Attention</div><div class="satsa-kpi-value" style="color:#C58A18;">{mod_cnt}</div></div>',
        unsafe_allow_html=True,
    )
    total_findings = merged["finding_count"].sum()
    c4.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Total Findings Logged</div><div class="satsa-kpi-value" style="color:#087F73;">{total_findings}</div></div>',
        unsafe_allow_html=True,
    )

    st.write("")

    # Filter Bar
    f1, f2, f3, f4 = st.columns([2, 2, 2, 3])
    sectors = ["All Sectors"] + sorted(df_all["sector"].unique().tolist())
    sel_sec = f1.selectbox("Sector", sectors, key="ent_f_sec")
    sel_crit = f2.selectbox("Criticality", ["All Criticalities", "Critical", "High", "Medium", "Low"], key="ent_f_crit")
    sel_att = f3.selectbox("Attention Level", ["All Attention Levels", "Critical", "High", "Moderate", "Low"], key="ent_f_att")
    search_q = f4.text_input("Filter by entity or ID", placeholder="Type name or CSE ID…", key="ent_f_txt")

    filtered = merged.copy()
    if sel_sec != "All Sectors":
        filtered = filtered[filtered["sector"] == sel_sec]
    if sel_crit != "All Criticalities":
        filtered = filtered[filtered["criticality"].str.lower() == sel_crit.lower()]
    if sel_att != "All Attention Levels":
        filtered = filtered[filtered["attention"] == sel_att]
    if search_q:
        filtered = filtered[
            filtered["entity_name"].str.contains(search_q, case=False, na=False) |
            filtered["cse_id"].str.contains(search_q, case=False, na=False)
        ]

    filtered = filtered.sort_values("total_score", ascending=False)

    st.caption(f"Showing {len(filtered)} of {len(merged)} entities")

    if filtered.empty:
        st.markdown(
            """
            <div class="satsa-card" style="text-align: center; padding: 20px;">
                <div style="font-weight: 600; color: #667579;">No entities match the current filters.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Table
    header = st.columns([0.6, 3, 1.8, 1.4, 1.4, 1.2, 1.2, 1.4])
    for c, t in zip(header, ["#", "Entity Name", "Sector", "Criticality", "Attention", "Score", "Findings", ""]):
        c.markdown(f'<div class="tbl-head">{t}</div>', unsafe_allow_html=True)

    for rank, (_, row) in enumerate(filtered.iterrows(), start=1):
        band_name = row["attention"]
        r = st.columns([0.6, 3, 1.8, 1.4, 1.4, 1.2, 1.2, 1.4])
        r[0].markdown(f'<div class="tbl-row">{rank}</div>', unsafe_allow_html=True)
        r[1].markdown(f'<div class="tbl-row"><strong>{row["entity_name"]}</strong><br/><span style="font-size:11px; color:#667579;">{row["cse_id"]}</span></div>', unsafe_allow_html=True)
        r[2].markdown(f'<div class="tbl-row">{row["sector"]}</div>', unsafe_allow_html=True)
        r[3].markdown(f'<div class="tbl-row">{row["criticality"].title()}</div>', unsafe_allow_html=True)
        r[4].markdown(f'<div class="tbl-row">{badge(band_name.upper(), band_name)}</div>', unsafe_allow_html=True)
        r[5].markdown(f'<div class="tbl-row" style="font-weight:600;">{row["total_score"]:.1f}</div>', unsafe_allow_html=True)
        r[6].markdown(f'<div class="tbl-row">{row["finding_count"]}</div>', unsafe_allow_html=True)
        if r[7].button("Inspect Entity →", key=f"ent_detail_btn_{row['cse_id']}", type="secondary", use_container_width=True):
            go_to("entity_detail", selected_entity=row["cse_id"])
