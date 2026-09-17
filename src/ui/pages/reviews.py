"""
Page: Supervisory Review Queue & Decision Workspace.
Enterprise Light Theme — Interactive audit workspace for manual verification, decision recording, and persistent status management.
"""

import json
import streamlit as st
import pandas as pd
from src.ui.styles import badge, attention_band, COLOR_HIGH, COLOR_MODERATE, COLOR_LOW, COLOR_TEAL_PRIMARY
from src.ui.nav import go_to
from src.ui.db_helper import (
    fetch_evidence_record, compute_ticket_signals,
    get_review_decisions, save_review_decision
)
from src.analytics.similarity import detect_repetitive_investigations


def render_reviews_page(conn, results):
    st.markdown('<div class="page-title">Supervisory Review Queue</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Recommended manual reviews for supervisory validation, false-positive elimination, and compliance governance.</div>',
        unsafe_allow_html=True,
    )

    if results is None:
        st.markdown(
            """
            <div class="satsa-card" style="text-align: center; padding: 30px;">
                <div style="font-weight: 600; color: #172326;">No Review Queue Data Available</div>
                <div class="card-note">Import data or run an assessment to populate the review queue.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Load recorded supervisory decisions from DuckDB
    decisions_df = get_review_decisions(conn)
    decision_map = {}
    if not decisions_df.empty:
        for _, d_row in decisions_df.iterrows():
            decision_map[d_row["ticket_id"]] = {
                "status": d_row["status"],
                "decision": d_row["decision"],
                "notes": d_row["supervisor_notes"],
                "updated_at": d_row["updated_at"],
            }

    # Tab selection
    current_tab = st.session_state.get("review_tab", "Priority Cases")
    tabs = st.tabs(["Priority Cases", "Analyst Pattern Deviation", "Investigation Quality"])

    with tabs[0]:
        render_priority_cases_tab(conn, results, decision_map)

    with tabs[1]:
        render_analyst_patterns_tab(conn, results)

    with tabs[2]:
        render_investigation_quality_tab(conn)


def render_priority_cases_tab(conn, results, decision_map):
    df_tickets = results["ticket_scores"]
    df_cses = results["cse_scores"]
    name_lookup = dict(zip(df_cses["entity_id"], df_cses["entity_name"])) if not df_cses.empty else {}

    if df_tickets.empty:
        st.caption("No cases require priority review.")
        return

    # High attention tickets (score >= 15)
    flagged = df_tickets[df_tickets["total_score"] >= 15].sort_values("total_score", ascending=False).copy()

    # Apply statuses from decision_map
    flagged["status"] = flagged["entity_id"].apply(
        lambda tid: decision_map.get(tid, {}).get("status", "OPEN")
    )

    # Status KPI summary strip
    total_queue = len(flagged)
    open_cnt = len(flagged[flagged["status"] == "OPEN"])
    in_rev_cnt = len(flagged[flagged["status"] == "IN REVIEW"])
    conf_cnt = len(flagged[flagged["status"] == "CONFIRMED"])
    dism_cnt = len(flagged[flagged["status"] == "DISMISSED"])
    esc_cnt = len(flagged[flagged["status"] == "ESCALATED"])

    s_cols = st.columns(6)
    s_cols[0].markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Review Queue Items</div><div class="satsa-kpi-value">{total_queue}</div><div class="satsa-kpi-sub">Priority cases flagged</div></div>',
        unsafe_allow_html=True,
    )
    s_cols[1].markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Open</div><div class="satsa-kpi-value" style="color:#C58A18;">{open_cnt}</div><div class="satsa-kpi-sub">Awaiting review</div></div>',
        unsafe_allow_html=True,
    )
    s_cols[2].markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">In Review</div><div class="satsa-kpi-value" style="color:#2B6CB0;">{in_rev_cnt}</div><div class="satsa-kpi-sub">Under inspection</div></div>',
        unsafe_allow_html=True,
    )
    s_cols[3].markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Confirmed</div><div class="satsa-kpi-value" style="color:#C93C3C;">{conf_cnt}</div><div class="satsa-kpi-sub">Finding verified</div></div>',
        unsafe_allow_html=True,
    )
    s_cols[4].markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Dismissed</div><div class="satsa-kpi-value" style="color:#667579;">{dism_cnt}</div><div class="satsa-kpi-sub">False positive</div></div>',
        unsafe_allow_html=True,
    )
    s_cols[5].markdown(
        f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Escalated</div><div class="satsa-kpi-value" style="color:#8B1E3F;">{esc_cnt}</div><div class="satsa-kpi-sub">Escalated to Tier-3</div></div>',
        unsafe_allow_html=True,
    )

    st.write("")

    # Filter controls for Review Queue
    rf1, rf2, rf3 = st.columns([2.5, 2.5, 3])
    status_filter = rf1.selectbox("Filter Status", ["All Statuses", "OPEN", "IN REVIEW", "CONFIRMED", "DISMISSED", "ESCALATED"], key="rev_f_status")
    entity_filter = rf2.selectbox("Filter Entity", ["All Entities"] + sorted(list(name_lookup.values())), key="rev_f_ent")
    search_ticket = rf3.text_input("Search Case ID", placeholder="TKT-…", key="rev_f_txt")

    filtered_cases = flagged.copy()
    if status_filter != "All Statuses":
        filtered_cases = filtered_cases[filtered_cases["status"] == status_filter]
    if entity_filter != "All Entities":
        matching_cids = [k for k, v in name_lookup.items() if v == entity_filter]
        filtered_cases = filtered_cases[filtered_cases["cse_id"].isin(matching_cids)]
    if search_ticket:
        filtered_cases = filtered_cases[filtered_cases["entity_id"].str.contains(search_ticket, case=False, na=False)]

    st.caption(f"Showing {len(filtered_cases)} priority case(s)")

    highlight = st.session_state.get("highlight_ticket")
    active_review_ticket = st.session_state.get("active_review_ticket", highlight)

    # If a ticket is actively being reviewed, display the full Review Workspace Drawer/Panel at the top
    if active_review_ticket:
        render_review_workspace(conn, active_review_ticket, decision_map)

    # Master Queue Table
    thead = st.columns([0.5, 1.4, 2.8, 1.2, 3.2, 1.0, 1.3, 1.2])
    for c, t in zip(thead, ["#", "Case ID", "Entity", "Priority", "Why Selected", "Score", "Status", "Action"]):
        c.markdown(f'<div class="tbl-head">{t}</div>', unsafe_allow_html=True)

    for rank, (_, row) in enumerate(filtered_cases.head(30).iterrows(), start=1):
        tid = row["entity_id"]
        c_name = name_lookup.get(row["cse_id"], row["cse_id"])
        t_reasons = json.loads(row["explanation_json"]) if row["explanation_json"] else []
        reason_summary = t_reasons[0] if t_reasons else "Operational pattern deviation"
        status_val = row["status"]

        is_selected = (active_review_ticket == tid)
        bg_style = "background-color: #F0F9F8;" if is_selected else ""

        r = st.columns([0.5, 1.4, 2.8, 1.2, 3.2, 1.0, 1.3, 1.2])
        r[0].markdown(f'<div class="tbl-row" style="{bg_style}">{rank}</div>', unsafe_allow_html=True)
        r[1].markdown(f'<div class="tbl-row" style="{bg_style}"><strong>`{tid}`</strong></div>', unsafe_allow_html=True)
        r[2].markdown(f'<div class="tbl-row" style="{bg_style}">{c_name}</div>', unsafe_allow_html=True)
        r[3].markdown(f'<div class="tbl-row" style="{bg_style}">{badge("HIGH", "High")}</div>', unsafe_allow_html=True)
        r[4].markdown(f'<div class="tbl-row card-note" style="{bg_style}">{reason_summary[:75]}…</div>', unsafe_allow_html=True)
        r[5].markdown(f'<div class="tbl-row" style="{bg_style}; font-weight:600;">{row["total_score"]:.0f}</div>', unsafe_allow_html=True)
        r[6].markdown(f'<div class="tbl-row" style="{bg_style}">{badge(status_val, status_val)}</div>', unsafe_allow_html=True)
        if r[7].button("Review →", key=f"btn_rev_case_{tid}", type="primary" if is_selected else "secondary", use_container_width=True):
            st.session_state.active_review_ticket = tid
            st.rerun()


def render_review_workspace(conn, ticket_id: str, decision_map: dict):
    """
    Renders the dedicated supervisory decision workspace for a selected case.
    Enables recording findings, false positive dismissal, and escalation.
    """
    rec = fetch_evidence_record(conn, "ticket", ticket_id)
    if not rec:
        return

    current_decision = decision_map.get(ticket_id, {})
    current_status = current_decision.get("status", "OPEN")
    current_notes = current_decision.get("notes", "")

    # Explainability signals
    signals = compute_ticket_signals(rec)

    with st.container():
        st.markdown(
            f"""
            <div class="satsa-card" style="border: 2px solid #087F73; background:#FFFFFF; margin-bottom: 20px;">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #E4E9E8; padding-bottom: 10px; margin-bottom: 12px;">
                    <div>
                        <span style="font-size: 18px; font-weight: 700; color: #172326;">
                            Supervisory Review Workspace: Case `{ticket_id}`
                        </span>
                        <span style="margin-left: 10px;">{badge(current_status, current_status)}</span>
                    </div>
                </div>
            """,
            unsafe_allow_html=True,
        )

        close_col1, close_col2 = st.columns([6, 1.2])
        if close_col2.button("Close Workspace", key="btn_close_rev_ws", type="secondary"):
            st.session_state.active_review_ticket = None
            st.rerun()

        w_col1, w_col2 = st.columns([1.5, 1.5])
        with w_col1:
            st.markdown(
                f"""
                <div style="font-size: 13.5px; color: #172326; line-height: 1.6;">
                    <strong>Entity:</strong> {rec.get('entity_name', '—')} (<code>{rec.get('cse_id', '—')}</code>)<br/>
                    <strong>Assigned Analyst:</strong> {rec.get('analyst_name', 'Unassigned')} (Tier {rec.get('analyst_tier', '—')})<br/>
                    <strong>Priority:</strong> {rec.get('priority', '—')} &nbsp;·&nbsp; <strong>Status:</strong> {rec.get('status', '—')}<br/>
                    <strong>Resolution:</strong> {rec.get('resolution_category', '—')} &nbsp;·&nbsp; <strong>Escalated to Tier-2:</strong> {'Yes' if rec.get('escalated_to_tier2') else 'NO'}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with w_col2:
            st.markdown(
                f"""
                <div style="font-size: 13px; color: #667579; line-height: 1.6;">
                    <strong>Created:</strong> {rec.get('created_at')}<br/>
                    <strong>Assigned:</strong> {rec.get('assigned_at')}<br/>
                    <strong>Closed:</strong> {rec.get('closed_at')}<br/>
                    <strong>Triggering Alert:</strong> {rec.get('rule_name', '—')} ({rec.get('alert_severity', '—')})
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<hr/>", unsafe_allow_html=True)

        # Why Was This Selected?
        st.markdown('<div class="section-title" style="font-size:14px;">Why Was This Flagged for Review?</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="explain-box">' +
            "".join([f'<div class="signal-check"><span class="signal-check-icon">✓</span><span>{sig}</span></div>' for sig in signals]) +
            '</div>',
            unsafe_allow_html=True,
        )

        # Investigation Note Content
        st.markdown("**Recorded Investigation Note:**")
        note_text = rec.get("note_text")
        if note_text and str(note_text).strip():
            st.markdown(f"> “{note_text}”")
            st.caption(f"Length: {int(rec.get('word_count') or 0)} words")
        else:
            st.caption("No investigation note was recorded for this case.")

        st.markdown("<hr/>", unsafe_allow_html=True)

        # Supervisory Decision Workflow Form
        st.markdown('<div class="section-title" style="font-size:14px;">Supervisor Decision & Audit Action</div>', unsafe_allow_html=True)

        dec_cols = st.columns([2, 3])
        status_options = ["CONFIRMED", "IN REVIEW", "DISMISSED", "ESCALATED", "OPEN"]
        def_idx = status_options.index(current_status) if current_status in status_options else 0
        new_status = dec_cols[0].selectbox("Supervisory Action Status", status_options, index=def_idx, key=f"sel_status_{ticket_id}")

        decision_reasons = {
            "CONFIRMED": "Confirm Finding (Valid operational gap/SLA breach)",
            "IN REVIEW": "Needs Further Investigation (Requires analyst interview)",
            "DISMISSED": "False Positive / Dismiss (Operational exception approved)",
            "ESCALATED": "Escalate to CSIRT / Senior Oversight",
            "OPEN": "Pending Assessment"
        }
        dec_label = decision_reasons.get(new_status, "Supervisory assessment")

        supervisor_notes = dec_cols[1].text_area(
            "Supervisor Governance Notes",
            value=current_notes,
            placeholder="Record audit reasoning, corrective instructions, or compliance remarks…",
            key=f"txt_notes_{ticket_id}",
            height=85,
        )

        btn_c1, btn_c2, btn_c3 = st.columns([4, 1.5, 1.5])
        if btn_c2.button("Save Decision", key=f"btn_save_dec_{ticket_id}", type="primary", use_container_width=True):
            success = save_review_decision(
                conn,
                ticket_id=ticket_id,
                cse_id=rec.get("cse_id", ""),
                status=new_status,
                decision=dec_label,
                supervisor_notes=supervisor_notes,
            )
            if success:
                st.success(f"✓ Supervisory decision recorded for {ticket_id}: {new_status}")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)


def render_analyst_patterns_tab(conn, results):
    st.markdown('<div class="section-title">Analyst Performance Patterns</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Supervisory identification of unusual operational patterns, repetitive notes, and workload deviations (Not an employee leaderboard).</div>',
        unsafe_allow_html=True,
    )

    df_analysts = results["analyst_scores"] if results else pd.DataFrame()
    if df_analysts.empty:
        st.caption("No analyst score telemetry available.")
        return

    df_sorted = df_analysts.sort_values("total_score", ascending=False)

    thead = st.columns([2.5, 1.2, 1.5, 1.4, 3.5])
    for c, t in zip(thead, ["Analyst Name", "Tier", "Shift Group", "Deviation Score", "Observed Pattern"]):
        c.markdown(f'<div class="tbl-head">{t}</div>', unsafe_allow_html=True)

    for _, row in df_sorted.iterrows():
        b_name = attention_band(row["total_score"])
        factors = json.loads(row["explanation_json"]) if row["explanation_json"] else []
        factor_summary = factors[0] if factors else "Standard operational performance within peer baseline"

        r = st.columns([2.5, 1.2, 1.5, 1.4, 3.5])
        r[0].markdown(f'<div class="tbl-row"><strong>{row["entity_name"]}</strong></div>', unsafe_allow_html=True)
        r[1].markdown(f'<div class="tbl-row">{row["tier"]}</div>', unsafe_allow_html=True)
        r[2].markdown(f'<div class="tbl-row">{row["shift_group"]} shift</div>', unsafe_allow_html=True)
        r[3].markdown(f'<div class="tbl-row" style="font-weight:600;">{row["total_score"]:.1f}</div>', unsafe_allow_html=True)
        r[4].markdown(f'<div class="tbl-row card-note">{factor_summary[:80]}</div>', unsafe_allow_html=True)

        with st.expander(f"View Analytical Breakdown for {row['entity_name']} (Score: {row['total_score']:.1f})"):
            sc = st.columns(5)
            sc[0].markdown(f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Execution Gaps</div><div class="satsa-kpi-value" style="font-size:18px;">{row["gap_score"]:.1f}</div></div>', unsafe_allow_html=True)
            sc[1].markdown(f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Monitoring Gaps</div><div class="satsa-kpi-value" style="font-size:18px;">{row["negative_space_score"]:.1f}</div></div>', unsafe_allow_html=True)
            sc[2].markdown(f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Peer Deviation</div><div class="satsa-kpi-value" style="font-size:18px;">{row["outlier_score"]:.1f}</div></div>', unsafe_allow_html=True)
            sc[3].markdown(f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Multivariate Anomaly</div><div class="satsa-kpi-value" style="font-size:18px;">{row["anomaly_score"]:.1f}</div></div>', unsafe_allow_html=True)
            sc[4].markdown(f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">Note Similarity</div><div class="satsa-kpi-value" style="font-size:18px;">{row["repetitive_text_score"]:.1f}</div></div>', unsafe_allow_html=True)
            if factors:
                st.markdown("**Empirical Contributing Factors:**")
                for f in factors:
                    st.markdown(f"- {f}")


def render_investigation_quality_tab(conn):
    st.markdown('<div class="section-title">Investigation Quality & Repetitive Note Detection</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Identifies identical or templated investigation notes across independent tickets via TF-IDF cosine similarity analysis.</div>',
        unsafe_allow_html=True,
    )

    sim = detect_repetitive_investigations(conn)
    pairs = sim["high_similarity_pairs"]

    if pairs.empty:
        st.caption("No repetitive or copy-pasted investigation notes detected.")
        return

    st.caption(f"Detected {len(pairs)} high-similarity ticket note pair(s) (>= 70% textual similarity).")

    thead = st.columns([1.5, 2.2, 1.5, 2.2, 1.4, 1.2])
    for c, t in zip(thead, ["Case A", "Analyst A", "Case B", "Analyst B", "Similarity", "Compare"]):
        c.markdown(f'<div class="tbl-head">{t}</div>', unsafe_allow_html=True)

    for idx, (_, row) in enumerate(pairs.head(20).iterrows()):
        r = st.columns([1.5, 2.2, 1.5, 2.2, 1.4, 1.2])
        r[0].markdown(f'<div class="tbl-row">`{row["ticket_id_1"]}`</div>', unsafe_allow_html=True)
        r[1].markdown(f'<div class="tbl-row">{row["analyst_name_1"]}</div>', unsafe_allow_html=True)
        r[2].markdown(f'<div class="tbl-row">`{row["ticket_id_2"]}`</div>', unsafe_allow_html=True)
        r[3].markdown(f'<div class="tbl-row">{row["analyst_name_2"]}</div>', unsafe_allow_html=True)
        sim_pct = row["similarity_score"] * 100.0
        r[4].markdown(f'<div class="tbl-row" style="font-weight:700; color:#C93C3C;">{sim_pct:.0f}% Match</div>', unsafe_allow_html=True)
        if r[5].button("Compare", key=f"btn_sim_cmp_{idx}", type="secondary", use_container_width=True):
            st.session_state[f"show_sim_{idx}"] = not st.session_state.get(f"show_sim_{idx}", False)

        if st.session_state.get(f"show_sim_{idx}"):
            with st.container():
                st.markdown(
                    f"""
                    <div class="satsa-card" style="background:#F8FAFA;">
                        <div style="display:flex; gap:20px;">
                            <div style="flex:1;">
                                <strong>Case `{row['ticket_id_1']}` Note ({row['analyst_name_1']}):</strong>
                                <div style="margin-top:4px; font-size:13px; color:#172326;">> “{row['note_preview_1']}”</div>
                            </div>
                            <div style="flex:1; border-left:1px solid #E4E9E8; padding-left:16px;">
                                <strong>Case `{row['ticket_id_2']}` Note ({row['analyst_name_2']}):</strong>
                                <div style="margin-top:4px; font-size:13px; color:#172326;">> “{row['note_preview_2']}”</div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
