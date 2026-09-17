"""
Page: Peer Benchmarking.
Enterprise Light Theme — Objective comparative operational analysis against peer sector entities.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.ui.styles import COLOR_TEAL_PRIMARY, COLOR_BORDER


def render_benchmarking_page(conn, results):
    st.markdown('<div class="page-title">Peer Benchmarking</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Compare operational patterns with similar critical sector entities to detect cohort-level anomalies.</div>',
        unsafe_allow_html=True,
    )

    df_cses = conn.execute("SELECT cse_id, entity_name, peer_group, sector FROM cses").df()
    if df_cses.empty:
        st.markdown(
            """
            <div class="satsa-card" style="text-align: center; padding: 24px;">
                <div style="font-weight: 600; color: #172326;">No Entities Available for Benchmarking</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Entity selection
    entity_id = st.selectbox(
        "Select Entity for Peer Comparison",
        df_cses["cse_id"].tolist(),
        format_func=lambda cid: df_cses.loc[df_cses["cse_id"] == cid, "entity_name"].values[0],
        key="bench_sel_entity",
    )
    ent_row = df_cses.loc[df_cses["cse_id"] == entity_id].iloc[0]
    peer_group = ent_row["peer_group"]
    sector_name = ent_row["sector"]

    # Compute operational metrics across entities
    metrics_df = conn.execute(
        """
        SELECT c.cse_id, c.entity_name, c.peer_group, c.sector,
               AVG(CASE WHEN t.assigned_at IS NOT NULL AND t.closed_at IS NOT NULL
                        THEN EPOCH(t.closed_at - t.assigned_at) / 60.0 END) AS avg_investigation_mins,
               AVG(COALESCE(n.word_count, 0)) AS avg_note_words,
               SUM(CASE WHEN t.priority = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_cases,
               SUM(CASE WHEN t.priority = 'CRITICAL' AND t.escalated_to_tier2 THEN 1 ELSE 0 END) AS critical_escalated,
               COUNT(t.ticket_id) AS total_cases
        FROM cses c
        LEFT JOIN tickets t ON c.cse_id = t.cse_id
        LEFT JOIN investigation_notes n ON t.ticket_id = n.ticket_id
        GROUP BY c.cse_id, c.entity_name, c.peer_group, c.sector
        """
    ).df()

    if metrics_df.empty:
        st.caption("No operational ticket data available for peer comparison.")
        return

    metrics_df["escalation_rate"] = metrics_df.apply(
        lambda r: (r["critical_escalated"] / r["critical_cases"] * 100.0) if r["critical_cases"] else 0.0,
        axis=1,
    )

    selected = metrics_df[metrics_df["cse_id"] == entity_id].iloc[0]
    peers = metrics_df[(metrics_df["peer_group"] == peer_group) & (metrics_df["cse_id"] != entity_id)]
    compare_pool = peers if not peers.empty else metrics_df[metrics_df["cse_id"] != entity_id]

    def peer_median(col_name):
        return float(compare_pool[col_name].median()) if not compare_pool.empty else float(selected[col_name])

    st.markdown(
        f"""
        <div class="satsa-card" style="margin-bottom: 16px;">
            <div style="font-size: 14px; color: #172326;">
                Selected Entity: <strong>{selected['entity_name']}</strong> &nbsp;·&nbsp;
                Sector: <strong>{sector_name}</strong> &nbsp;·&nbsp;
                Assigned Peer Cohort: <strong>{peer_group}</strong> ({len(compare_pool)} comparable peer entit{'y' if len(compare_pool)==1 else 'ies'})
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Metric selection
    metric_choices = {
        "Investigation Time (Minutes)": ("avg_investigation_mins", "Average minutes elapsed between ticket assignment and ticket closure."),
        "Average Investigation Note Length (Words)": ("avg_note_words", "Mean word count per recorded triage investigation note."),
        "Critical Incident Escalation Rate (%)": ("escalation_rate", "Percentage of CRITICAL priority incidents formally escalated to Tier-2 / CSIRT."),
    }

    sel_metric_label = st.selectbox("Select Operational Metric", list(metric_choices.keys()), key="bench_sel_metric")
    col_name, metric_desc = metric_choices[sel_metric_label]

    sel_val = float(selected[col_name]) if pd.notna(selected[col_name]) else 0.0
    peer_val = peer_median(col_name)
    diff_pct = ((sel_val - peer_val) / peer_val * 100.0) if peer_val != 0 else 0.0

    # Metric Cards
    c1, c2, c3 = st.columns(3)
    c1.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Selected Entity</div><div class="satsa-kpi-value" style="color:#087F73;">{sel_val:,.1f}</div><div class="satsa-kpi-sub">{selected["entity_name"]}</div></div>',
        unsafe_allow_html=True,
    )
    c2.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Peer Cohort Median</div><div class="satsa-kpi-value" style="color:#667579;">{peer_val:,.1f}</div><div class="satsa-kpi-sub">Sector baseline</div></div>',
        unsafe_allow_html=True,
    )
    diff_color = "#C93C3C" if (abs(diff_pct) > 25) else "#278A55"
    c3.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Variance from Peer Median</div><div class="satsa-kpi-value" style="color:{diff_color};">{diff_pct:+.1f}%</div><div class="satsa-kpi-sub">Relative deviation</div></div>',
        unsafe_allow_html=True,
    )

    st.write("")

    # Comparative Horizontal Bar Visualization
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=[selected["entity_name"], f"Peer Median ({peer_group})"],
        x=[sel_val, peer_val],
        orientation="h",
        marker=dict(color=["#087F73", "#8C9B9E"]),
        text=[f"{sel_val:.1f}", f"{peer_val:.1f}"],
        textposition="outside",
    ))
    fig.update_layout(
        height=200,
        margin=dict(l=10, r=40, t=10, b=10),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        xaxis=dict(title=sel_metric_label, gridcolor="#EEF2F1", zeroline=False),
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Contextual Explanation
    st.markdown(
        f"""
        <div class="satsa-card" style="background:#FAFCFC; border:1px solid #E4E9E8;">
            <div style="font-weight: 700; color: #172326; margin-bottom: 4px;">Metric Context & Supervisory Meaning:</div>
            <div style="font-size: 13.5px; color: #485659; line-height: 1.55;">
                {metric_desc} In this comparison, {selected['entity_name']} records <strong>{sel_val:.1f}</strong> compared to the peer cohort median of <strong>{peer_val:.1f}</strong> (a variance of <strong>{diff_pct:+.1f}%</strong>). 
                Significant deviations highlight operational divergence that may warrant supervisory sampling without pre-judging intent.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    # Full Peer Group Comparison Table
    st.markdown(f'<div class="section-title">Full Peer Group Metrics: {peer_group}</div>', unsafe_allow_html=True)
    cohort_df = metrics_df[metrics_df["peer_group"] == peer_group][["entity_name", "sector", "avg_investigation_mins", "avg_note_words", "escalation_rate", "total_cases"]].copy()
    cohort_df = cohort_df.rename(columns={
        "entity_name": "Entity Name",
        "sector": "Sector",
        "avg_investigation_mins": "Avg Investigation (min)",
        "avg_note_words": "Avg Note Length (words)",
        "escalation_rate": "Escalation Rate (%)",
        "total_cases": "Total Cases",
    })
    cohort_df["Avg Investigation (min)"] = cohort_df["Avg Investigation (min)"].round(1)
    cohort_df["Avg Note Length (words)"] = cohort_df["Avg Note Length (words)"].round(1)
    cohort_df["Escalation Rate (%)"] = cohort_df["Escalation Rate (%)"].round(1)

    st.dataframe(cohort_df, use_container_width=True, hide_index=True)
