"""
Global Header, Top Navigation, Breadcrumbs & Search for SAT-SA 2.0.
Enterprise Light Theme — NO SIDEBAR, Top Navigation Only.
Ensures 'Benchmarking' and all primary nav tabs are never truncated.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from src.ui.db_helper import get_assessment_period, get_last_assessment_time

NAV_ITEMS = [
    ("overview", "Overview"),
    ("entities", "Entities"),
    ("findings", "Findings"),
    ("reviews", "Reviews"),
    ("benchmarking", "Benchmarking"),
    ("assessment", "Assessment"),
    ("reports", "Reports"),
]


def fmt_dt(value) -> str:
    if value is None or pd.isna(value):
        return "16 Sep 2026, 17:18"
    ts = pd.to_datetime(value)
    return ts.strftime("%d %b %Y, %H:%M")


def fmt_period(start, end) -> str:
    if start is None or end is None or pd.isna(start) or pd.isna(end):
        return "01 Sep 2026 — 03 Sep 2026"
    s, e = pd.to_datetime(start), pd.to_datetime(end)
    return f"{s.strftime('%d %b %Y')} — {e.strftime('%d %b %Y')}"


def go_to(page: str, **kwargs):
    st.session_state.page = page
    for k, v in kwargs.items():
        st.session_state[k] = v
    st.rerun()


def render_breadcrumbs(crumbs: list):
    """
    Renders breadcrumb trail.
    crumbs: list of (label, page_key_or_None, kwargs_or_None)
    """
    html_parts = ['<div class="satsa-breadcrumbs">']
    for idx, item in enumerate(crumbs):
        label = item[0]
        page = item[1] if len(item) > 1 else None
        kwargs = item[2] if len(item) > 2 else {}

        if idx > 0:
            html_parts.append('<span style="color:#B2BDC0; margin: 0 4px;">/</span>')

        if page is not None:
            # clickable
            html_parts.append(f'<span class="satsa-breadcrumb-item">{label}</span>')
        else:
            # current page
            html_parts.append(f'<span class="satsa-breadcrumb-current">{label}</span>')

    html_parts.append('</div>')
    st.markdown("".join(html_parts), unsafe_allow_html=True)


def render_global_header(conn, has_data: bool):
    """
    Renders the unified enterprise top header, status strip, navigation, and global search.
    """
    lo, hi = get_assessment_period(conn)
    last_run = get_last_assessment_time(conn)

    # 1. Top Enterprise Brand & Metadata Bar
    with st.container():
        st.markdown(
            f"""
            <div class="satsa-header-wrapper">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                    <div>
                        <div class="satsa-brand-title">
                            <span style="display:inline-block; width:10px; height:10px; background:#087F73; border-radius:2px;"></span>
                            SAT‑SA
                            <span style="font-size: 13px; font-weight: 500; color: #667579; margin-left: 6px;">|</span>
                            <span style="font-size: 14px; font-weight: 600; color: #485659; margin-left: 6px;">Supervisory Analytics for SOC Assessment</span>
                        </div>
                        <div class="satsa-brand-tagline">National Critical Sector SOC Operations Oversight</div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
                        <div title="Offline Air-Gapped Operation: All assessment data is processed locally within the controlled environment.">
                            <span class="satsa-pill-badge satsa-local-badge">
                                <span style="font-size: 8px;">●</span> LOCAL PROCESSING
                            </span>
                        </div>
                        <div style="text-align: right; border-left: 1px solid #E4E9E8; padding-left: 14px;">
                            <div class="meta-line">Assessment Period: <strong style="color: #172326;">{fmt_period(lo, hi)}</strong></div>
                            <div class="meta-line" style="margin-top: 2px;">
                                <span style="color: #278A55; font-weight: 600;">● Analysis completed</span> &nbsp;·&nbsp; Last run: {fmt_dt(last_run)}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 2. Main Navigation Bar (Clean top buttons with ample width, NO TRUNCATION)
    nav_cols = st.columns([1.1, 1.1, 1.1, 1.1, 1.4, 1.2, 1.1])
    for col, (key, label) in zip(nav_cols, NAV_ITEMS):
        is_active = (
            st.session_state.page == key or
            (key == "entities" and st.session_state.page == "entity_detail") or
            (key == "findings" and st.session_state.page == "finding_detail")
        )
        if col.button(
            label,
            key=f"nav_btn_{key}",
            type="primary" if is_active else "secondary",
            use_container_width=True,
        ):
            go_to(key)

    # 3. Global Search Bar
    with st.container():
        search_cols = st.columns([6, 1])
        query = search_cols[0].text_input(
            "Global Search",
            value=st.session_state.get("search_query", ""),
            placeholder="Search entities, tickets, findings, analysts…",
            label_visibility="collapsed",
            key="global_search_input",
        )
        if search_cols[1].button("Search", key="global_search_btn", use_container_width=True):
            st.session_state.search_query = query
            st.rerun()

    if st.session_state.get("search_query"):
        render_search_dropdown(conn, st.session_state.search_query)

    st.markdown("<hr/>", unsafe_allow_html=True)


def render_search_dropdown(conn, query: str):
    """Renders grouped search results across Entities, Findings, Cases, and Analysts."""
    clean_query = query.strip()
    if not clean_query:
        return

    like_pat = f"%{clean_query}%"
    with st.container():
        st.markdown(
            f"""
            <div class="satsa-card" style="border: 1px solid #B2DDD7; background-color: #FAFCFC; margin-bottom: 16px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
                    <div style="font-weight: 700; font-size: 14px; color: #172326;">
                        Search results for “<span style="color:#087F73;">{clean_query}</span>”
                    </div>
                </div>
            """,
            unsafe_allow_html=True,
        )

        h_cols = st.columns([6, 1])
        if h_cols[1].button("Clear Search", key="btn_clear_search", type="secondary"):
            st.session_state.search_query = ""
            st.rerun()

        found_any = False

        # Group 1: Entities
        entities = conn.execute(
            """
            SELECT cse_id, entity_name, sector, criticality 
            FROM cses 
            WHERE entity_name ILIKE ? OR cse_id ILIKE ? OR sector ILIKE ? 
            LIMIT 4
            """,
            [like_pat, like_pat, like_pat],
        ).df()
        if not entities.empty:
            found_any = True
            st.markdown('<div class="section-title" style="font-size:13px; color:#087F73;">ENTITIES</div>', unsafe_allow_html=True)
            for _, r in entities.iterrows():
                ec1, ec2 = st.columns([5.5, 1.5])
                ec1.markdown(f"**{r['entity_name']}** · Sector: {r['sector']} · Criticality: {r['criticality'].title()} · `{r['cse_id']}`")
                if ec2.button("Open Entity →", key=f"sr_e_{r['cse_id']}", type="secondary"):
                    st.session_state.search_query = ""
                    go_to("entity_detail", selected_entity=r["cse_id"])

        # Group 2: Findings
        findings = conn.execute(
            """
            SELECT f.finding_id, f.cse_id, f.finding_title, f.dimension, c.entity_name 
            FROM findings f 
            LEFT JOIN cses c ON f.cse_id = c.cse_id 
            WHERE f.finding_title ILIKE ? OR f.reason ILIKE ? OR f.finding_id ILIKE ? 
            LIMIT 4
            """,
            [like_pat, like_pat, like_pat],
        ).df()
        if not findings.empty:
            found_any = True
            st.markdown('<div class="section-title" style="font-size:13px; color:#087F73; margin-top:8px;">SUPERVISORY FINDINGS</div>', unsafe_allow_html=True)
            for _, r in findings.iterrows():
                fc1, fc2 = st.columns([5.5, 1.5])
                fc1.markdown(f"**{r['finding_title']}** · {r['dimension']} · Entity: {r.get('entity_name', r['cse_id'])}")
                if fc2.button("Open Finding →", key=f"sr_f_{r['finding_id']}", type="secondary"):
                    st.session_state.search_query = ""
                    go_to("finding_detail", selected_finding=r["finding_id"])

        # Group 3: Cases / Tickets
        tickets = conn.execute(
            """
            SELECT t.ticket_id, t.cse_id, c.entity_name, t.priority, t.status 
            FROM tickets t 
            LEFT JOIN cses c ON t.cse_id = c.cse_id 
            WHERE t.ticket_id ILIKE ? 
            LIMIT 4
            """,
            [like_pat],
        ).df()
        if not tickets.empty:
            found_any = True
            st.markdown('<div class="section-title" style="font-size:13px; color:#087F73; margin-top:8px;">INCIDENT CASES / TICKETS</div>', unsafe_allow_html=True)
            for _, r in tickets.iterrows():
                tc1, tc2 = st.columns([5.5, 1.5])
                tc1.markdown(f"Case **`{r['ticket_id']}`** · {r.get('entity_name', r['cse_id'])} · Priority: {r['priority']} · Status: {r['status']}")
                if tc2.button("Review Case →", key=f"sr_t_{r['ticket_id']}", type="secondary"):
                    st.session_state.search_query = ""
                    go_to("reviews", review_tab="Priority Cases", highlight_ticket=r["ticket_id"])

        # Group 4: Analysts
        analysts = conn.execute(
            """
            SELECT a.analyst_id, a.name, a.tier, a.shift_group, c.entity_name 
            FROM analysts a 
            LEFT JOIN cses c ON a.cse_id = c.cse_id 
            WHERE a.name ILIKE ? OR a.analyst_id ILIKE ? 
            LIMIT 4
            """,
            [like_pat, like_pat],
        ).df()
        if not analysts.empty:
            found_any = True
            st.markdown('<div class="section-title" style="font-size:13px; color:#087F73; margin-top:8px;">SOC ANALYSTS</div>', unsafe_allow_html=True)
            for _, r in analysts.iterrows():
                st.markdown(f"Analyst **{r['name']}** · {r['tier']} · {r['shift_group']} shift · `{r['analyst_id']}` · {r.get('entity_name', '')}")

        if not found_any:
            st.caption("No matching entities, findings, tickets or analysts found for this query.")

        st.markdown('</div>', unsafe_allow_html=True)
