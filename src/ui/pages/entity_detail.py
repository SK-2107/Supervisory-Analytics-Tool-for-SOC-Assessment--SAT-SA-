"""
Page: Dedicated Entity Detail View.
Enterprise Light Theme — Deep supervisory analytical inspection of a single Critical Sector Entity (CSE).
"""

import streamlit as st
import pandas as pd
from src.ui.styles import badge, attention_band, finding_severity_band, COLOR_HIGH, COLOR_MODERATE, COLOR_TEAL_PRIMARY
from src.ui.nav import go_to, render_breadcrumbs
from src.ui.db_helper import fetch_evidence_record, compute_ticket_signals
from src.analytics.dimensions import DIMENSIONS


def render_entity_detail_page(conn, results):
    cse_id = st.session_state.get("selected_entity")
    if not cse_id:
        st.warning("No entity selected. Returning to entities directory.")
        if st.button("← Go to Entities"):
            go_to("entities")
        return

    # Fetch entity record
    info_df = conn.execute(
        "SELECT cse_id, entity_name, sector, peer_group, criticality, maturity_level FROM cses WHERE cse_id = ?",
        [cse_id],
    ).df()

    if info_df.empty:
        st.error("Entity not found in database.")
        if st.button("← Back to Entities"):
            go_to("entities")
        return

    info = info_df.iloc[0]

    # Breadcrumbs
    render_breadcrumbs([
        ("Overview", "overview"),
        ("Entities", "entities"),
        (info["entity_name"], None),
    ])

    # Top action bar
    top_c1, top_c2 = st.columns([6, 1.5])
    with top_c2:
        if st.button("← Back to Entities", key="back_ent_top", type="secondary", use_container_width=True):
            go_to("entities")

    # Score & attention level
    df_cses = results["cse_scores"] if results else pd.DataFrame()
    score_row = df_cses[df_cses["entity_id"] == cse_id] if not df_cses.empty else pd.DataFrame()
    total_score = float(score_row.iloc[0]["total_score"]) if not score_row.empty else 0.0
    finding_count = int(score_row.iloc[0]["finding_count"]) if not score_row.empty else 0
    band_name = attention_band(total_score)

    accent_color = COLOR_HIGH if band_name in ("Critical", "High") else (COLOR_MODERATE if band_name == "Moderate" else COLOR_TEAL_PRIMARY)

    # Entity Header Banner
    with st.container():
        st.markdown(
            f"""
            <div class="satsa-card" style="border-left: 5px solid {accent_color}; margin-bottom: 18px;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
                    <div>
                        <div style="font-size: 24px; font-weight: 700; color: #172326; letter-spacing: -0.02em;">
                            {info['entity_name']}
                        </div>
                        <div style="font-size: 13.5px; color: #667579; margin-top: 4px;">
                            CSE ID: <strong>`{info['cse_id']}`</strong> &nbsp;·&nbsp;
                            Sector: <strong>{info['sector']}</strong> &nbsp;·&nbsp;
                            Criticality: <strong>{info['criticality'].title()}</strong> &nbsp;·&nbsp;
                            Maturity: <strong>{info['maturity_level']}</strong> &nbsp;·&nbsp;
                            Peer Group: <strong>{info['peer_group']}</strong>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div>{badge(band_name.upper() + ' ATTENTION', band_name)}</div>
                        <div style="font-size: 18px; font-weight: 700; color: {accent_color}; margin-top: 4px;">
                            Score: {total_score:.1f} / 100
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Operational Snapshot Metrics
    counts = conn.execute(
        """
        SELECT 
            (SELECT COUNT(*) FROM alerts WHERE cse_id=?) AS alerts_cnt,
            (SELECT COUNT(*) FROM tickets WHERE cse_id=?) AS tickets_cnt,
            (SELECT COUNT(*) FROM analysts WHERE cse_id=?) AS analysts_cnt,
            (SELECT COUNT(*) FROM findings WHERE cse_id=?) AS findings_cnt
        """,
        [cse_id, cse_id, cse_id, cse_id],
    ).df().iloc[0]

    df_tickets = results["ticket_scores"] if results else pd.DataFrame()
    ent_tickets = df_tickets[(df_tickets["cse_id"] == cse_id) & (df_tickets["total_score"] >= 15)] if not df_tickets.empty else pd.DataFrame()
    review_queue_items = len(ent_tickets)

    snap_cols = st.columns(5)
    snap_metrics = [
        ("Alerts Ingested", f"{int(counts['alerts_cnt']):,}", "Source telemetry"),
        ("Cases On Record", f"{int(counts['tickets_cnt']):,}", "Incident tickets"),
        ("Findings Identified", int(counts["findings_cnt"]), "Capability gaps"),
        ("Review Queue Items", review_queue_items, "Flagged for supervisor review"),
        ("SOC Analysts Assigned", int(counts["analysts_cnt"]), "Monitored personnel"),
    ]
    for col, (lbl, val, sub) in zip(snap_cols, snap_metrics):
        col.markdown(
            f'<div class="satsa-kpi-block"><div class="satsa-kpi-label">{lbl}</div><div class="satsa-kpi-value">{val}</div><div class="satsa-kpi-sub">{sub}</div></div>',
            unsafe_allow_html=True,
        )

    st.write("")

    # Supervisory Summary
    st.markdown('<div class="section-title">Supervisory Assessment Summary</div>', unsafe_allow_html=True)
    df_findings_all = results["findings_df"] if results else pd.DataFrame()
    entity_findings = df_findings_all[df_findings_all["cse_id"] == cse_id] if not df_findings_all.empty else pd.DataFrame()

    if entity_findings.empty:
        summary_text = (
            f"No capability dimension findings were identified for {info['entity_name']}. "
            "All analyzed incident triage, escalation, and shift logs conform to expected baseline thresholds."
        )
    else:
        finding_titles = ", ".join([f"“{t}”" for t in entity_findings["finding_title"].unique()])
        summary_text = (
            f"Supervisory assessment identified {len(entity_findings)} finding(s) requiring management review: {finding_titles}. "
            f"The entity exhibits an attention score of {total_score:.1f}/100, warranting active operational scrutiny."
        )

    st.markdown(
        f"""
        <div class="satsa-card" style="background-color: #FFFFFF; font-size: 14px; color: #172326; line-height: 1.55;">
            {summary_text}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    # Layout: Left column = 8 Capability Dimensions, Right column = Findings list
    grid_cols = st.columns([1.1, 1.9])

    dim_scores = results["dimension_scores"] if results else pd.DataFrame()

    with grid_cols[0]:
        st.markdown('<div class="section-title">8 Capability Dimensions</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-desc">Quantitative dimension scores calibrated across SOC operational logs.</div>',
            unsafe_allow_html=True,
        )
        with st.container():
            st.markdown('<div class="satsa-card">', unsafe_allow_html=True)
            for d in DIMENSIONS:
                s = 0.0
                if not dim_scores.empty and cse_id in dim_scores["cse_id"].values:
                    row = dim_scores[dim_scores["cse_id"] == cse_id].iloc[0]
                    s = float(row.get(d, 0.0))
                b = finding_severity_band(s)
                fill_color = COLOR_HIGH if b == "High" else (COLOR_MODERATE if b == "Medium" else COLOR_TEAL_PRIMARY)
                pct = max(3, min(100, s))
                st.markdown(
                    f"""
                    <div class="cap-row">
                        <div class="cap-label-row">
                            <span style="font-size: 12.5px; font-weight: 600;">{d}</span>
                            <span style="font-size: 12px; font-weight: 700; color:{fill_color};">{s:.1f} / 100</span>
                        </div>
                        <div class="cap-track"><div class="cap-fill" style="width:{pct}%; background:{fill_color};"></div></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown('</div>', unsafe_allow_html=True)

    with grid_cols[1]:
        st.markdown(f'<div class="section-title">Structured Findings for this Entity ({len(entity_findings)})</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-desc">Gaps identified with empirical evidence and confidence ratings.</div>',
            unsafe_allow_html=True,
        )

        if entity_findings.empty:
            st.markdown(
                """
                <div class="satsa-card" style="text-align: center; padding: 24px;">
                    <div style="font-weight: 600; color: #278A55;">No Findings Detected</div>
                    <div class="card-note">This entity operates within standard compliance and operational expectations.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for _, fnd in entity_findings.iterrows():
                # Severity
                dim_s = 0.0
                if not dim_scores.empty and cse_id in dim_scores["cse_id"].values:
                    r_dim = dim_scores[dim_scores["cse_id"] == cse_id].iloc[0]
                    dim_s = float(r_dim.get(fnd["dimension"], 0.0))
                sev = finding_severity_band(dim_s)
                evidence_ids = [e.strip() for e in str(fnd["evidence_record_ids"]).split(",") if e.strip()]

                with st.container():
                    st.markdown(
                        f"""
                        <div class="satsa-card satsa-card-interactive">
                            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                                <div>
                                    <span style="font-size: 15px; font-weight: 700; color: #172326;">{fnd['finding_title']}</span>
                                    <span style="margin-left: 8px;">{badge(sev.upper(), sev)}</span>
                                    <span style="margin-left: 6px;">{badge(fnd['confidence_strength'].title() + ' Confidence', 'Routine')}</span>
                                </div>
                                <span style="font-size: 12px; color: #667579;">{fnd['dimension']}</span>
                            </div>
                            <div class="card-note" style="margin: 6px 0 8px 0;">
                                {fnd['reason']}
                            </div>
                            <div style="font-size: 12px; color: #667579; background: #F8FAFA; padding: 6px 10px; border-radius: 4px; margin-bottom: 8px;">
                                <strong>Observed:</strong> {fnd['observed_value']} &nbsp;·&nbsp; <strong>Expected:</strong> {fnd['expected_baseline_value']}
                            </div>
                            <div style="font-size: 12px; color: #087F73;">
                                <strong>{len(evidence_ids)}</strong> supporting evidence record{'s' if len(evidence_ids) != 1 else ''} attached
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    btn_c1, btn_c2 = st.columns([5, 1.5])
                    if btn_c2.button("Inspect Finding →", key=f"ent_open_fnd_{fnd['finding_id']}", type="primary", use_container_width=True):
                        go_to("finding_detail", selected_finding=fnd["finding_id"])

    st.write("")

    # Supporting Evidence Drill-Down for this Entity
    st.markdown('<div class="section-title">Supporting Evidence Records Drill-Down</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Sample audit records associated with supervisory findings for this entity.</div>',
        unsafe_allow_html=True,
    )

    all_evidence_ids = []
    if not entity_findings.empty:
        for _, f in entity_findings.iterrows():
            e_list = [e.strip() for e in str(f["evidence_record_ids"]).split(",") if e.strip()]
            for eid in e_list:
                if eid not in [x[0] for x in all_evidence_ids]:
                    all_evidence_ids.append((eid, f["source_record_type"], f["finding_title"]))

    if not all_evidence_ids:
        st.caption("No specific evidence records logged for this entity.")
    else:
        ev_sample = all_evidence_ids[:6]
        tabs = st.tabs([f"{rec_id} ({rec_type})" for rec_id, rec_type, _ in ev_sample])
        for tab, (rec_id, rec_type, finding_title) in zip(tabs, ev_sample):
            with tab:
                st.caption(f"Evidence for finding: **{finding_title}**")
                render_evidence_card(conn, rec_type, rec_id)

    st.write("")

    # Review Items for this Entity
    st.markdown(f'<div class="section-title">High Priority Review Items for {info["entity_name"]}</div>', unsafe_allow_html=True)
    if ent_tickets.empty:
        st.caption("No high priority tickets currently queued for this entity.")
    else:
        st.caption(f"{len(ent_tickets)} tickets flagged for manual supervisory review.")
        thead = st.columns([1.5, 1.5, 3.5, 1.2, 1.3])
        for c, t in zip(thead, ["Case ID", "Priority", "Flagged Reason", "Score", "Action"]):
            c.markdown(f'<div class="tbl-head">{t}</div>', unsafe_allow_html=True)

        for _, trow in ent_tickets.head(5).iterrows():
            t_signals = compute_ticket_signals(
                fetch_evidence_record(conn, "ticket", trow["entity_id"]) or {}
            )
            r = st.columns([1.5, 1.5, 3.5, 1.2, 1.3])
            r[0].markdown(f'<div class="tbl-row"><strong>`{trow["entity_id"]}`</strong></div>', unsafe_allow_html=True)
            r[1].markdown(f'<div class="tbl-row">{badge("HIGH", "High")}</div>', unsafe_allow_html=True)
            r[2].markdown(f'<div class="tbl-row card-note">{t_signals[0] if t_signals else "Pattern deviation"}</div>', unsafe_allow_html=True)
            r[3].markdown(f'<div class="tbl-row" style="font-weight:600;">{trow["total_score"]:.0f}</div>', unsafe_allow_html=True)
            if r[4].button("Review →", key=f"ent_rev_tkt_{trow['entity_id']}", type="secondary", use_container_width=True):
                go_to("reviews", review_tab="Priority Cases", highlight_ticket=trow["entity_id"])


def render_evidence_card(conn, source_type: str, record_id: str):
    """Renders a comprehensive evidence record inside an entity or finding view."""
    rec = fetch_evidence_record(conn, source_type, record_id)
    if not rec:
        st.caption(f"Record `{record_id}` is an entity-level aggregate indicator.")
        return

    with st.container():
        st.markdown('<div class="satsa-card" style="margin-top: 6px;">', unsafe_allow_html=True)
        if source_type == "ticket":
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Ticket ID:** `{rec['ticket_id']}`")
            c1.caption(f"Entity: {rec.get('entity_name', '—')}")
            c2.markdown(f"**Priority:** {rec.get('priority', '—')}")
            c2.markdown(f"**Status:** {rec.get('status', '—')}")
            c3.markdown(f"**Analyst:** {rec.get('analyst_name') or 'Unassigned'} ({rec.get('analyst_tier', '—')})")
            esc = rec.get("escalated_to_tier2")
            esc_color = "#278A55" if esc else "#C93C3C"
            c3.markdown(f"**Tier-2 Escalation:** <span style='color:{esc_color}; font-weight:600;'>{'Recorded' if esc else 'NOT RECORDED'}</span>", unsafe_allow_html=True)

            d1, d2, d3 = st.columns(3)
            d1.caption(f"Opened: {rec.get('created_at')}")
            d2.caption(f"Assigned: {rec.get('assigned_at')}")
            d3.caption(f"Closed: {rec.get('closed_at')}")

            if rec.get("rule_name"):
                st.markdown(f"**Triggering Alert:** {rec['rule_name']} (Severity: {rec.get('alert_severity', '—')})")

            st.markdown("**Investigation Note Recorded:**")
            note = rec.get("note_text")
            if note and str(note).strip():
                st.markdown(f"> “{note}”")
                st.caption(f"Word count: {int(rec.get('word_count') or 0)} words")
            else:
                st.caption("No investigation note logged.")

        elif source_type == "alert":
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Alert ID:** `{rec['alert_id']}`")
            c1.caption(f"Entity: {rec.get('entity_name', '—')}")
            c2.markdown(f"**Severity:** {rec.get('severity', '—')}")
            c2.markdown(f"**Source System:** {rec.get('source_system', '—')}")
            c3.markdown(f"**Rule:** {rec.get('rule_name', '—')}")
            c3.caption(f"Timestamp: {rec.get('timestamp')}")
            if rec.get("raw_summary"):
                st.markdown(f"> “{rec['raw_summary']}”")

        elif source_type == "note":
            c1, c2 = st.columns(2)
            c1.markdown(f"**Note ID:** `{rec['note_id']}` (Case `{rec.get('ticket_id', '—')}`)")
            c1.caption(f"Entity: {rec.get('entity_name', '—')}")
            c2.markdown(f"**Analyst:** {rec.get('analyst_name', '—')}")
            c2.caption(f"Logged at: {rec.get('created_at')}")
            st.markdown(f"> “{rec.get('note_text', '—')}”")
            st.caption(f"Word count: {int(rec.get('word_count') or 0)} words")

        elif source_type == "shift":
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Shift Log ID:** `{rec['log_id']}`")
            c1.caption(f"Entity: {rec.get('entity_name', '—')}")
            c2.markdown(f"**Shift:** {rec.get('shift_name', '—')} on {rec.get('shift_date', '—')}")
            c2.caption(f"Analyst: {rec.get('analyst_name', '—')}")
            handover = rec.get("handover_completed")
            h_color = "#278A55" if handover else "#C93C3C"
            c3.markdown(f"**Handover Status:** <span style='color:{h_color}; font-weight:600;'>{'Completed' if handover else 'MISSING / UNVERIFIED'}</span>", unsafe_allow_html=True)
            c3.caption(f"Notes logged: {int(rec.get('notes_logged') or 0)}")

        st.markdown('</div>', unsafe_allow_html=True)
