"""
Page: Peer Benchmarking.
SAT-SA — Supervisory Analytics Tool for SOC Assessment.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.ui.styles import neutral_badge, COLOR_TEAL_PRIMARY, COLOR_CRITICAL, COLOR_MODERATE, COLOR_LOW


def render_benchmarking_page(conn, results):
    st.markdown('<div class="page-title">Peer Benchmarking</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Compare how each entity performs against similar organisations in its sector cohort. Significant deviations may indicate areas warranting supervisory attention.</div>',
        unsafe_allow_html=True,
    )

    df_cses = conn.execute("SELECT cse_id, entity_name, peer_group, sector FROM cses").df()
    if df_cses.empty:
        st.markdown(
            '<div class="empty-state"><div class="empty-state-icon">📊</div><div class="empty-state-title">No Entities Available</div><div class="empty-state-desc">Import entity data to enable peer benchmarking.</div></div>',
            unsafe_allow_html=True,
        )
        return

    # Entity selector
    st.markdown('<div class="section-title">Select Entity for Comparison</div>', unsafe_allow_html=True)
    entity_id = st.selectbox(
        "Entity",
        df_cses["cse_id"].tolist(),
        format_func=lambda cid: df_cses.loc[df_cses["cse_id"] == cid, "entity_name"].values[0],
        key="bench_ent",
        label_visibility="collapsed",
    )
    ent_row    = df_cses.loc[df_cses["cse_id"] == entity_id].iloc[0]
    peer_group = ent_row["peer_group"]
    sector_name = ent_row["sector"]

    # Compute telemetry metrics
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
        # Telemetry-based fallback using alerts
        metrics_df = conn.execute(
            """
            SELECT c.cse_id, c.entity_name, c.peer_group, c.sector,
                   NULL AS avg_investigation_mins,
                   NULL AS avg_note_words,
                   0    AS critical_cases,
                   0    AS critical_escalated,
                   0    AS total_cases
            FROM cses c
            """
        ).df()
        st.markdown(
            '<div class="satsa-info-banner" style="font-size:13px;">No incident ticket data available. Displaying alert-based metrics only.</div>',
            unsafe_allow_html=True,
        )

    metrics_df["escalation_rate"] = metrics_df.apply(
        lambda r: (r["critical_escalated"] / r["critical_cases"] * 100.0) if r["critical_cases"] > 0 else 0.0,
        axis=1,
    )

    if entity_id not in metrics_df["cse_id"].values:
        st.caption("No metrics available for the selected entity.")
        return

    selected = metrics_df[metrics_df["cse_id"] == entity_id].iloc[0]
    peers    = metrics_df[(metrics_df["peer_group"] == peer_group) & (metrics_df["cse_id"] != entity_id)]
    pool     = peers if not peers.empty else metrics_df[metrics_df["cse_id"] != entity_id]

    def peer_median(col):
        return float(pool[col].median()) if not pool.empty and pool[col].notna().any() else float(selected[col] or 0)

    # Context card
    st.markdown(
        f"""
        <div class="satsa-card" style="margin-bottom:16px;">
            <div style="font-size:14px; color:#111827; line-height:1.6;">
                Selected entity: <strong>{selected['entity_name']}</strong> &nbsp;·&nbsp;
                Sector: <strong>{sector_name}</strong> &nbsp;·&nbsp;
                Peer cohort: <strong>{peer_group}</strong>
                <span style="color:#6B7280;"> ({len(pool)} comparable {'entity' if len(pool)==1 else 'entities'})</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Metric picker
    st.markdown('<div class="section-title">Select Operational Metric</div>', unsafe_allow_html=True)
    metric_choices = {
        "Investigation Time (minutes)": (
            "avg_investigation_mins",
            "Average time elapsed between incident ticket assignment and closure. Unusually fast closure may indicate insufficient investigation."
        ),
        "Investigation Note Length (words)": (
            "avg_note_words",
            "Mean word count of recorded triage investigation notes. Very short notes may indicate superficial documentation."
        ),
        "Critical Escalation Rate (%)": (
            "escalation_rate",
            "Percentage of CRITICAL priority incidents formally escalated to Tier-2 / CSIRT. Low rates for critical cases may signal governance gaps."
        ),
    }
    sel_metric_label = st.selectbox("Select Operational Metric", list(metric_choices.keys()), key="bench_metric", label_visibility="collapsed")
    col_name, metric_desc = metric_choices[sel_metric_label]

    sel_val  = float(selected[col_name]) if pd.notna(selected[col_name]) else 0.0
    peer_val = peer_median(col_name)
    diff_pct = ((sel_val - peer_val) / peer_val * 100.0) if peer_val != 0 else 0.0

    # KPI cards
    c1, c2, c3 = st.columns(3)
    c1.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Selected Entity</div><div class="satsa-kpi-value" style="color:{COLOR_TEAL_PRIMARY};">{sel_val:,.1f}</div><div class="satsa-kpi-sub">{selected["entity_name"]}</div></div>',
        unsafe_allow_html=True,
    )
    c2.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Peer Cohort Median</div><div class="satsa-kpi-value" style="color:#6B7280;">{peer_val:,.1f}</div><div class="satsa-kpi-sub">Sector baseline</div></div>',
        unsafe_allow_html=True,
    )
    diff_color = COLOR_CRITICAL if abs(diff_pct) > 30 else (COLOR_MODERATE if abs(diff_pct) > 15 else COLOR_LOW)
    c3.markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Variance from Peer</div><div class="satsa-kpi-value" style="color:{diff_color};">{diff_pct:+.1f}%</div><div class="satsa-kpi-sub">Relative deviation</div></div>',
        unsafe_allow_html=True,
    )

    st.write("")

    # Chart
    all_labels = [metrics_df.loc[metrics_df["cse_id"] == cid, "entity_name"].values[0] for cid in metrics_df["cse_id"]]
    all_vals   = [float(metrics_df.loc[metrics_df["cse_id"] == cid, col_name].values[0] or 0) for cid in metrics_df["cse_id"]]
    all_colors = [COLOR_TEAL_PRIMARY if cid == entity_id else "#D1D5DB" for cid in metrics_df["cse_id"]]

    fig = go.Figure(go.Bar(
        y=all_labels,
        x=all_vals,
        orientation="h",
        marker=dict(color=all_colors, line=dict(width=0)),
        text=[f"{v:.1f}" for v in all_vals],
        textposition="outside",
        hovertemplate="%{y}: %{x:.1f}<extra></extra>",
    ))
    fig.update_layout(
        height=max(200, len(all_labels) * 45),
        margin=dict(l=0, r=60, t=10, b=10),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="Inter, -apple-system, sans-serif", size=12, color="#374151"),
        xaxis=dict(
            title=sel_metric_label,
            gridcolor="#F3F4F6",
            zeroline=False,
            showline=True,
            linecolor="#E5E7EB",
        ),
        yaxis=dict(autorange="reversed", tickfont=dict(size=12)),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Context explanation
    st.markdown(
        f"""
        <div class="satsa-card" style="background:#F9FAFB;">
            <div style="font-weight:700; color:#111827; margin-bottom:5px;">What does this metric mean for supervisors?</div>
            <div style="font-size:13.5px; color:#374151; line-height:1.6;">
                {metric_desc}<br/><br/>
                <strong>{selected['entity_name']}</strong> records <strong>{sel_val:.1f}</strong> compared to the peer cohort median of <strong>{peer_val:.1f}</strong> (a variance of <strong>{diff_pct:+.1f}%</strong>).
                Significant deviations highlight operational divergence that may warrant supervisory sampling
                without pre-judging individual analyst intent.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    # Full peer group table
    st.markdown(f'<div class="section-title">Full Peer Group: {peer_group}</div>', unsafe_allow_html=True)
    cohort_df = metrics_df[metrics_df["peer_group"] == peer_group][[
        "entity_name", "sector", "avg_investigation_mins", "avg_note_words", "escalation_rate", "total_cases"
    ]].copy()
    cohort_df["avg_investigation_mins"] = cohort_df["avg_investigation_mins"].round(1)
    cohort_df["avg_note_words"]         = cohort_df["avg_note_words"].round(1)
    cohort_df["escalation_rate"]        = cohort_df["escalation_rate"].round(1)

    thead = st.columns([3, 1.8, 2, 2.2, 2, 1.5])
    for c, t in zip(thead, ["Entity Name", "Sector", "Avg Inv. Time (min)", "Avg Note (words)", "Escalation Rate (%)", "Total Cases"]):
        c.markdown(f'<div class="tbl-head">{t}</div>', unsafe_allow_html=True)

    for idx, (_, r) in enumerate(cohort_df.iterrows()):
        row_cls = "tbl-row-alt" if idx % 2 == 0 else "tbl-row"
        rc = st.columns([3, 1.8, 2, 2.2, 2, 1.5])
        rc[0].markdown(f'<div class="{row_cls}"><strong>{r["entity_name"]}</strong></div>', unsafe_allow_html=True)
        rc[1].markdown(f'<div class="{row_cls}">{r["sector"]}</div>', unsafe_allow_html=True)
        rc[2].markdown(f'<div class="{row_cls}">{r["avg_investigation_mins"]}</div>', unsafe_allow_html=True)
        rc[3].markdown(f'<div class="{row_cls}">{r["avg_note_words"]}</div>', unsafe_allow_html=True)
        rc[4].markdown(f'<div class="{row_cls}">{r["escalation_rate"]}</div>', unsafe_allow_html=True)
        rc[5].markdown(f'<div class="{row_cls}">{r["total_cases"]}</div>', unsafe_allow_html=True)
