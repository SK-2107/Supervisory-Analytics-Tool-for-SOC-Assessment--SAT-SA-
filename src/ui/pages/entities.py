"""
Page: Entities — Entity Directory.
SAT-SA — Supervisory Analytics Tool for SOC Assessment.
"""

import streamlit as st
import pandas as pd
from src.ui.styles import badge, neutral_badge, attention_band, COLOR_CRITICAL, COLOR_MODERATE, COLOR_LOW, COLOR_TEAL_PRIMARY
from src.ui.nav import go_to


def render_entities_page(conn, results):
    st.markdown('<div class="page-title">Entities</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Supervisory register of all Critical Sector Entities under oversight — scored, ranked, and filtered by operational priority.</div>',
        unsafe_allow_html=True,
    )

    df_cses = results["cse_scores"] if results else pd.DataFrame()
    df_all  = conn.execute("SELECT cse_id, entity_name, sector, peer_group, criticality, maturity_level FROM cses").df()

    if df_all.empty:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-state-icon">🏢</div>
                <div class="empty-state-title">No Entities Found</div>
                <div class="empty-state-desc">Import entity configuration data in the Assessment tab to populate this register.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    merged = df_all.merge(
        df_cses[["entity_id", "total_score", "finding_count"]] if not df_cses.empty
        else pd.DataFrame(columns=["entity_id", "total_score", "finding_count"]),
        left_on="cse_id", right_on="entity_id", how="left",
    )
    merged["total_score"]   = merged["total_score"].fillna(0.0)
    merged["finding_count"] = merged["finding_count"].fillna(0).astype(int)
    merged["attention"]     = merged["total_score"].apply(attention_band)

    # KPI Strip
    high_cnt   = len(merged[merged["attention"].isin(["Critical", "High"])])
    mod_cnt    = len(merged[merged["attention"] == "Moderate"])
    low_cnt    = len(merged[merged["attention"] == "Low"])
    total_fnds = merged["finding_count"].sum()

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Total Entities</div><div class="satsa-kpi-value">{len(merged)}</div><div class="satsa-kpi-sub">Under assessment</div></div>',
        unsafe_allow_html=True,
    )
    k2.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">High Attention</div><div class="satsa-kpi-value" style="color:{COLOR_CRITICAL};">{high_cnt}</div><div class="satsa-kpi-sub">Exceeds threshold</div></div>',
        unsafe_allow_html=True,
    )
    k3.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Moderate Attention</div><div class="satsa-kpi-value" style="color:{COLOR_MODERATE};">{mod_cnt}</div><div class="satsa-kpi-sub">Warrants monitoring</div></div>',
        unsafe_allow_html=True,
    )
    k4.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Routine Oversight</div><div class="satsa-kpi-value" style="color:{COLOR_LOW};">{low_cnt}</div><div class="satsa-kpi-sub">Within baseline</div></div>',
        unsafe_allow_html=True,
    )
    k5.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Total Findings</div><div class="satsa-kpi-value" style="color:{COLOR_TEAL_PRIMARY};">{total_fnds}</div><div class="satsa-kpi-sub">Across all entities</div></div>',
        unsafe_allow_html=True,
    )

    st.write("")

    # Filter Bar
    f1, f2, f3, f4 = st.columns([2, 2, 2, 3])
    sectors  = ["All Sectors"]         + sorted(df_all["sector"].unique().tolist())
    crits    = ["All Criticalities",    "Critical", "High", "Medium", "Low"]
    att_opts = ["All Attention Levels", "Critical", "High", "Moderate", "Low"]

    sel_sec  = f1.selectbox("Sector",       sectors,  key="ent_sec")
    sel_crit = f2.selectbox("Criticality",  crits,    key="ent_crit")
    sel_att  = f3.selectbox("Attention",    att_opts, key="ent_att")
    txt_q    = f4.text_input("Filter Entities", placeholder="Search by name or CSE ID…", key="ent_txt", label_visibility="collapsed")

    filtered = merged.copy()
    if sel_sec  != "All Sectors":         filtered = filtered[filtered["sector"] == sel_sec]
    if sel_crit != "All Criticalities":   filtered = filtered[filtered["criticality"].str.lower() == sel_crit.lower()]
    if sel_att  != "All Attention Levels": filtered = filtered[filtered["attention"] == sel_att]
    if txt_q:
        filtered = filtered[
            filtered["entity_name"].str.contains(txt_q, case=False, na=False) |
            filtered["cse_id"].str.contains(txt_q, case=False, na=False)
        ]
    filtered = filtered.sort_values("total_score", ascending=False)

    sc1, _ = st.columns([6, 1.5])
    sc1.caption(f"Showing {len(filtered)} of {len(merged)} entities · sorted by attention score (highest first)")

    if filtered.empty:
        st.markdown(
            '<div class="satsa-card" style="text-align:center; padding:24px;"><div style="color:#6B7280; font-weight:600;">No entities match the current filters.</div></div>',
            unsafe_allow_html=True,
        )
        return

    # Table
    thead = st.columns([0.5, 3, 1.8, 1.4, 1.8, 1.4, 1.2, 1.6])
    for c, t in zip(thead, ["#", "Entity Name / ID", "Sector", "Criticality", "Attention Level", "Score", "Findings", ""]):
        c.markdown(f'<div class="tbl-head">{t}</div>', unsafe_allow_html=True)

    for rank, (_, row) in enumerate(filtered.iterrows(), start=1):
        band        = row["attention"]
        score_color = COLOR_CRITICAL if band in ("Critical", "High") else (
            COLOR_MODERATE if band == "Moderate" else COLOR_LOW
        )
        row_cls = "tbl-row-alt" if rank % 2 == 0 else "tbl-row"
        r = st.columns([0.5, 3, 1.8, 1.4, 1.8, 1.4, 1.2, 1.6])
        r[0].markdown(f'<div class="{row_cls}">{rank}</div>', unsafe_allow_html=True)
        r[1].markdown(
            f'<div class="{row_cls}"><strong>{row["entity_name"]}</strong><br/><span style="font-size:11px;color:#9CA3AF;font-family:monospace;">{row["cse_id"]}</span></div>',
            unsafe_allow_html=True,
        )
        r[2].markdown(f'<div class="{row_cls}">{row["sector"]}</div>', unsafe_allow_html=True)
        r[3].markdown(f'<div class="{row_cls}">{row["criticality"].title()}</div>', unsafe_allow_html=True)
        r[4].markdown(f'<div class="{row_cls}">{badge(band, band)}</div>', unsafe_allow_html=True)
        r[5].markdown(f'<div class="{row_cls}" style="font-weight:800; font-size:15px; color:{score_color};">{row["total_score"]:.1f}</div>', unsafe_allow_html=True)
        r[6].markdown(f'<div class="{row_cls}">{row["finding_count"]}</div>', unsafe_allow_html=True)
        if r[7].button("Inspect →", key=f"ent_btn_{row['cse_id']}", type="secondary", use_container_width=True):
            go_to("entity_detail", selected_entity=row["cse_id"])
