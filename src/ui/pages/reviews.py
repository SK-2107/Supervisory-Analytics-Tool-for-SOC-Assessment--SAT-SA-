"""
Page: Supervisory Review Queue & Decision Workspace.
Enterprise Light Theme — Interactive audit workspace for manual verification, decision recording, and persistent status management.
Supports both Ticket Cases (Demo/Real data) and Priority Security Alert Telemetry (Public NSL-KDD data).
"""

import json
import streamlit as st
import pandas as pd
from src.ui.styles import badge, neutral_badge, attention_band, COLOR_CRITICAL, COLOR_HIGH, COLOR_MODERATE, COLOR_LOW, COLOR_TEAL_PRIMARY
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
    tabs = st.tabs(["Priority Cases & Telemetry", "Analyst & Asset Telemetry", "Investigation & Attack Signatures"])

    with tabs[0]:
        render_priority_cases_tab(conn, results, decision_map)

    with tabs[1]:
        render_analyst_patterns_tab(conn, results)

    with tabs[2]:
        render_investigation_quality_tab(conn)


def render_priority_cases_tab(conn, results, decision_map):
    df_tickets = results["ticket_scores"] if (results and "ticket_scores" in results) else pd.DataFrame()
    df_cses = results["cse_scores"] if (results and "cse_scores" in results) else pd.DataFrame()
    name_lookup = dict(zip(df_cses["entity_id"], df_cses["entity_name"])) if not df_cses.empty else {}

    # If tickets are not present, display empty state
    if df_tickets.empty:
        st.info("No tickets currently queued for supervisory review.")
        return

    # High attention tickets (score >= 15)
    flagged = df_tickets[df_tickets["total_score"] >= 15].sort_values("total_score", ascending=False).copy()

    # Map entity_name and apply statuses from decision_map
    flagged["entity_name"] = flagged["cse_id"].map(name_lookup).fillna(flagged["cse_id"])
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

    # Master Queue Table
    thead = st.columns([0.5, 1.4, 2.8, 1.2, 3.2, 1.0, 1.3, 1.2])
    for c, t in zip(thead, ["#", "Case ID", "Entity", "Priority", "Why Selected", "Score", "Status", "Action"]):
        c.markdown(f'<div class="tbl-head">{t}</div>', unsafe_allow_html=True)

    for idx, (_, row) in enumerate(filtered_cases.head(50).iterrows()):
        tid = row["entity_id"]
        c_name = row.get("entity_name") or name_lookup.get(row.get("cse_id"), row.get("cse_id", "—"))
        score = row["total_score"]
        curr_status = row["status"]

        reasons = json.loads(row["explanation_json"]) if row["explanation_json"] else []
        why_selected = reasons[0] if reasons else "Elevated operational risk score"
        status_color = "#C58A18" if curr_status == "OPEN" else ("#2B6CB0" if curr_status == "IN REVIEW" else ("#C93C3C" if curr_status == "CONFIRMED" else "#278A55"))

        row_cls = "tbl-row-alt" if idx % 2 == 0 else "tbl-row"
        r = st.columns([0.5, 1.4, 2.8, 1.2, 3.2, 1.0, 1.3, 1.2])
        r[0].markdown(f'<div class="{row_cls}">{idx + 1}</div>', unsafe_allow_html=True)
        r[1].markdown(f'<div class="{row_cls}"><strong>`{tid}`</strong></div>', unsafe_allow_html=True)
        r[2].markdown(f'<div class="{row_cls}">{c_name}</div>', unsafe_allow_html=True)
        r[3].markdown(f'<div class="{row_cls}">{badge("HIGH", "High")}</div>', unsafe_allow_html=True)
        r[4].markdown(f'<div class="{row_cls} card-note">{why_selected[:70]}</div>', unsafe_allow_html=True)
        r[5].markdown(f'<div class="{row_cls}" style="font-weight:600;">{score:.1f}</div>', unsafe_allow_html=True)
        r[6].markdown(f'<div class="{row_cls}"><span class="satsa-badge" style="background:#FAFCFC; color:{status_color}; border:1px solid {status_color}44;">{curr_status}</span></div>', unsafe_allow_html=True)

        if r[7].button("Inspect →", key=f"btn_insp_{tid}", type="secondary", use_container_width=True):
            st.session_state["active_review_ticket"] = tid
            st.rerun()

    # Detail Workspace
    if active_review_ticket:
        st.markdown("<hr/>", unsafe_allow_html=True)
        render_ticket_review_workspace(conn, active_review_ticket, decision_map)


def render_ticket_review_workspace(conn, ticket_id, decision_map):
    """Renders supervisory audit workspace for an operational ticket case."""
    rec = fetch_evidence_record(conn, "ticket", ticket_id)
    if not rec:
        st.warning(f"Could not load details for ticket `{ticket_id}`.")
        return

    curr_dec = decision_map.get(ticket_id, {})
    current_status = curr_dec.get("status", "OPEN")
    current_notes = curr_dec.get("notes", "")
    signals = compute_ticket_signals(rec)

    st.markdown(f'<div class="section-title">Case Review Workspace: `{ticket_id}`</div>', unsafe_allow_html=True)
    st.markdown('<div class="satsa-card" style="border: 1px solid #087F73; background:#FFFFFF; padding: 20px;">', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"**Entity:**<br/>{rec.get('entity_name', 'Unknown')}", unsafe_allow_html=True)
    c2.markdown(f"**Assigned Analyst:**<br/>{rec.get('analyst_name', 'Unassigned')} ({rec.get('analyst_tier', 'Tier-1')})", unsafe_allow_html=True)
    c3.markdown(f"**Priority / Status:**<br/>{badge(str(rec.get('priority', 'Medium')).title(), str(rec.get('priority', 'Medium')).title())} &nbsp;·&nbsp; {rec.get('status', 'CLOSED')}", unsafe_allow_html=True)
    c4.markdown(f"**Current Audit Status:**<br/><strong>{current_status}</strong>", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown('<div class="section-title" style="font-size:14px;">Why Was This Flagged for Review?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="explain-box">' +
        "".join([f'<div class="signal-check"><span class="signal-check-icon">✔</span><span>{sig}</span></div>' for sig in signals]) +
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("**Recorded Investigation Note:**")
    note_text = rec.get("note_text")
    if note_text and str(note_text).strip():
        st.markdown(f"> “{note_text}”")
        st.caption(f"Length: {int(rec.get('word_count') or 0)} words")
    else:
        st.caption("No investigation note was recorded for this case.")

    st.markdown("<hr/>", unsafe_allow_html=True)
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
    st.markdown('<div class="section-title">Analyst & Asset Telemetry Deviation</div>', unsafe_allow_html=True)

    df_analysts = results["analyst_scores"] if (results and "analyst_scores" in results) else pd.DataFrame()
    if df_analysts.empty:
        st.markdown(
            """
            <div class="satsa-card" style="border-left: 4px solid #667579; background:#FAFCFC; margin-bottom: 16px;">
                <div style="font-weight: 700; color: #172326; margin-bottom: 4px;">Analyst Personnel Roster: Not Present in Source Dataset</div>
                <div class="card-note">
                    The active dataset represents raw network security telemetry (NSL-KDD); zero fictional analyst identities were fabricated.
                    Below is the authentic <strong>Monitored Service Endpoints & Threat Ingestion Distribution</strong>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        df_assets = conn.execute(
            """
            SELECT ast.asset_id, c.entity_name, ast.hostname, ast.ip_address, ast.asset_type, ast.criticality,
                   COUNT(a.alert_id) AS total_events,
                   SUM(CASE WHEN a.rule_name != 'BASELINE_BENIGN_FLOW' THEN 1 ELSE 0 END) AS attack_events
            FROM assets ast
            LEFT JOIN cses c ON ast.cse_id = c.cse_id
            LEFT JOIN alerts a ON ast.asset_id = a.asset_id
            GROUP BY ast.asset_id, c.entity_name, ast.hostname, ast.ip_address, ast.asset_type, ast.criticality
            ORDER BY attack_events DESC, total_events DESC
            """
        ).df()

        if not df_assets.empty:
            thead = st.columns([1.8, 2.4, 1.8, 1.6, 1.2, 1.2, 1.2])
            for c, t in zip(thead, ["Asset ID", "Service Cohort", "Hostname", "Endpoint Type", "Criticality", "Flows", "Attacks"]):
                c.markdown(f'<div class="tbl-head">{t}</div>', unsafe_allow_html=True)

            for idx, (_, row) in enumerate(df_assets.head(30).iterrows()):
                row_cls = "tbl-row-alt" if idx % 2 == 0 else "tbl-row"
                r = st.columns([1.8, 2.4, 1.8, 1.6, 1.2, 1.2, 1.2])
                r[0].markdown(f'<div class="{row_cls}"><strong>`{row["asset_id"]}`</strong></div>', unsafe_allow_html=True)
                r[1].markdown(f'<div class="{row_cls}">{row["entity_name"]}</div>', unsafe_allow_html=True)
                r[2].markdown(f'<div class="{row_cls}">{row["hostname"]}</div>', unsafe_allow_html=True)
                r[3].markdown(f'<div class="{row_cls}">{row["asset_type"]}</div>', unsafe_allow_html=True)
                r[4].markdown(f'<div class="{row_cls}">{badge(row["criticality"], row["criticality"])}</div>', unsafe_allow_html=True)
                r[5].markdown(f'<div class="{row_cls}">{int(row["total_events"])}</div>', unsafe_allow_html=True)
                r[6].markdown(f'<div class="{row_cls}" style="font-weight:600; color:#C93C3C;">{int(row["attack_events"])}</div>', unsafe_allow_html=True)
        return

    st.markdown(
        '<div class="section-desc">Supervisory identification of unusual operational patterns, repetitive notes, and workload deviations (Not an employee leaderboard).</div>',
        unsafe_allow_html=True,
    )

    df_sorted = df_analysts.sort_values("total_score", ascending=False)
    thead = st.columns([2.5, 1.2, 1.5, 1.4, 3.5])
    for c, t in zip(thead, ["Analyst Name", "Tier", "Shift Group", "Deviation Score", "Observed Pattern"]):
        c.markdown(f'<div class="tbl-head">{t}</div>', unsafe_allow_html=True)

    for idx, (_, row) in enumerate(df_sorted.iterrows()):
        b_name = attention_band(row["total_score"])
        factors = json.loads(row["explanation_json"]) if row["explanation_json"] else []
        factor_summary = factors[0] if factors else "Standard operational performance within peer baseline"
        row_cls = "tbl-row-alt" if idx % 2 == 0 else "tbl-row"

        r = st.columns([2.5, 1.2, 1.5, 1.4, 3.5])
        r[0].markdown(f'<div class="{row_cls}"><strong>{row["entity_name"]}</strong></div>', unsafe_allow_html=True)
        r[1].markdown(f'<div class="{row_cls}">{row["tier"]}</div>', unsafe_allow_html=True)
        r[2].markdown(f'<div class="{row_cls}">{row["shift_group"]} shift</div>', unsafe_allow_html=True)
        r[3].markdown(f'<div class="{row_cls}" style="font-weight:600;">{row["total_score"]:.1f}</div>', unsafe_allow_html=True)
        r[4].markdown(f'<div class="{row_cls} card-note">{factor_summary[:80]}</div>', unsafe_allow_html=True)


def render_investigation_quality_tab(conn):
    st.markdown('<div class="section-title">Investigation Quality & Signature Telemetry</div>', unsafe_allow_html=True)

    notes_cnt = conn.execute("SELECT COUNT(*) FROM investigation_notes").fetchone()[0]
    if notes_cnt == 0:
        st.markdown(
            """
            <div class="satsa-card" style="border-left: 4px solid #667579; background:#FAFCFC; margin-bottom: 16px;">
                <div style="font-weight: 700; color: #172326; margin-bottom: 4px;">Investigation Notes: Not Present in Source Dataset</div>
                <div class="card-note">
                    The active dataset represents raw network security telemetry (NSL-KDD) without human triage notes; textual similarity is marked <strong>Not Assessable from Source Data</strong>.
                    Below is the authentic <strong>Observed Threat Signature Inventory & Detection Frequencies</strong> across sensors.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        df_sigs = conn.execute(
            """
            SELECT rule_name AS "Signature Rule", severity AS "Severity",
                   COUNT(*) AS "Observed Events",
                   COUNT(DISTINCT asset_id) AS "Impacted Assets",
                   COUNT(DISTINCT cse_id) AS "Impacted Entities"
            FROM alerts
            WHERE rule_name != 'BASELINE_BENIGN_FLOW'
            GROUP BY rule_name, severity
            ORDER BY "Observed Events" DESC
            """
        ).df()

        if not df_sigs.empty:
            thead = st.columns([3.0, 1.5, 1.8, 1.8, 1.8])
            for c, t in zip(thead, ["Signature Rule", "Severity", "Observed Events", "Impacted Endpoints", "Impacted Entities"]):
                c.markdown(f'<div class="tbl-head">{t}</div>', unsafe_allow_html=True)

            for idx, (_, row) in enumerate(df_sigs.iterrows()):
                row_cls = "tbl-row-alt" if idx % 2 == 0 else "tbl-row"
                r = st.columns([3.0, 1.5, 1.8, 1.8, 1.8])
                r[0].markdown(f'<div class="{row_cls}"><strong>`{row["Signature Rule"]}`</strong></div>', unsafe_allow_html=True)
                r[1].markdown(f'<div class="{row_cls}">{badge(row["Severity"], row["Severity"])}</div>', unsafe_allow_html=True)
                r[2].markdown(f'<div class="{row_cls}" style="font-weight:600;">{int(row["Observed Events"])}</div>', unsafe_allow_html=True)
                r[3].markdown(f'<div class="{row_cls}">{int(row["Impacted Assets"])}</div>', unsafe_allow_html=True)
                r[4].markdown(f'<div class="{row_cls}">{int(row["Impacted Entities"])}</div>', unsafe_allow_html=True)
        return

    st.markdown(
        '<div class="section-desc">Identifies identical or templated investigation notes across independent tickets via TF-IDF cosine similarity analysis.</div>',
        unsafe_allow_html=True,
    )

    sim = detect_repetitive_investigations(conn)
    pairs = sim["high_similarity_pairs"]

    if pairs.empty:
        st.caption("No repetitive or copy-pasted investigation notes detected.")
        return

    st.caption(f"Detected {len(pairs)} high-similarity ticket note pair(s) (>= 85% textual similarity).")

    thead = st.columns([1.5, 2.2, 1.5, 2.2, 1.4, 1.2])
    for c, t in zip(thead, ["Case A", "Analyst A", "Case B", "Analyst B", "Similarity", "Compare"]):
        c.markdown(f'<div class="tbl-head">{t}</div>', unsafe_allow_html=True)

    for idx, (_, row) in enumerate(pairs.head(20).iterrows()):
        row_cls = "tbl-row-alt" if idx % 2 == 0 else "tbl-row"
        r = st.columns([1.5, 2.2, 1.5, 2.2, 1.4, 1.2])
        r[0].markdown(f'<div class="{row_cls}">`{row["ticket_id_1"]}`</div>', unsafe_allow_html=True)
        r[1].markdown(f'<div class="{row_cls}">{row["analyst_name_1"]}</div>', unsafe_allow_html=True)
        r[2].markdown(f'<div class="{row_cls}">`{row["ticket_id_2"]}`</div>', unsafe_allow_html=True)
        r[3].markdown(f'<div class="{row_cls}">{row["analyst_name_2"]}</div>', unsafe_allow_html=True)
        sim_pct = row["similarity_score"] * 100.0
        r[4].markdown(f'<div class="{row_cls}" style="font-weight:700; color:#C93C3C;">{sim_pct:.0f}% Match</div>', unsafe_allow_html=True)
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
