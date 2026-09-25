"""
Global Navigation, Header & Routing for SAT-SA.
Top navigation only. No sidebar.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from src.ui.db_helper import get_assessment_period, get_last_assessment_time

NAV_ITEMS = [
    ("overview",     "Overview"),
    ("entities",     "Entities"),
    ("findings",     "Findings & Evidence"),
    ("reviews",      "Review Queue"),
    ("benchmarking", "Benchmarking"),
    ("assessment",   "Data & Reports"),
    ("reports",      "Export"),
]


def fmt_dt(value) -> str:
    if value is None:
        return "—"
    try:
        ts = pd.to_datetime(value)
        return ts.strftime("%d %b %Y, %H:%M")
    except Exception:
        return "—"


def fmt_period(start, end) -> str:
    if start is None or end is None:
        return "No period data"
    try:
        s = pd.to_datetime(start)
        e = pd.to_datetime(end)
        return f"{s.strftime('%d %b %Y')} — {e.strftime('%d %b %Y')}"
    except Exception:
        return "—"


def go_to(page: str, **kwargs):
    st.session_state.page = page
    for k, v in kwargs.items():
        st.session_state[k] = v
    st.rerun()


def render_breadcrumbs(crumbs: list):
    parts = ['<div class="satsa-breadcrumbs">']
    for idx, item in enumerate(crumbs):
        label = item[0]
        page  = item[1] if len(item) > 1 else None
        if idx > 0:
            parts.append('<span style="color:#D1D5DB; margin:0 5px;">›</span>')
        if page is not None:
            parts.append(f'<span class="satsa-breadcrumb-item">{label}</span>')
        else:
            parts.append(f'<span class="satsa-breadcrumb-current">{label}</span>')
    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)


def render_global_header(conn, has_data: bool, current_page: str = None, **kwargs):
    lo, hi    = get_assessment_period(conn)
    last_run  = get_last_assessment_time(conn)
    period    = fmt_period(lo, hi)
    last_str  = fmt_dt(last_run)
    status_html = (
        '<span class="satsa-status-pill satsa-pill-green">● Analysis complete</span>'
        if has_data else
        '<span class="satsa-status-pill" style="background:#FFF7ED;color:#EA580C;border:1px solid #FED7AA;">● Awaiting data</span>'
    )

    st.markdown(
        f"""
        <div style="background:#FFFFFF; border-bottom:1px solid #E5E7EB; padding:0 0 0 0; margin-bottom:0;">
          <!-- Brand row -->
          <div style="display:flex; justify-content:space-between; align-items:center; padding:12px 4px 10px 4px; flex-wrap:wrap; gap:10px;">
            <div style="display:flex; align-items:center; gap:12px;">
              <div style="width:34px; height:34px; background:linear-gradient(135deg,#0D9488,#0F766E); border-radius:8px; display:inline-flex; align-items:center; justify-content:center; color:white; font-size:14px; font-weight:800; letter-spacing:-1px; flex-shrink:0;">SA</div>
              <div>
                <div style="font-size:17px; font-weight:800; color:#111827; letter-spacing:-0.025em; line-height:1;">SAT‑SA</div>
                <div style="font-size:10.5px; font-weight:500; color:#6B7280; text-transform:uppercase; letter-spacing:0.06em; margin-top:1px;">Supervisory Analytics · SOC Assessment</div>
              </div>
            </div>
            <div style="display:flex; align-items:center; gap:14px; flex-wrap:wrap;">
              {status_html}
              <span class="satsa-status-pill satsa-pill-teal">⊙ Offline / Air-Gapped</span>
              <div style="border-left:1px solid #E5E7EB; padding-left:14px;">
                <div style="font-size:11.5px; color:#6B7280;">Period: <strong style="color:#111827;">{period}</strong></div>
                <div style="font-size:11.5px; color:#6B7280; margin-top:1px;">Last run: <strong style="color:#111827;">{last_str}</strong></div>
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Navigation strip — uses Streamlit columns for clickable buttons
    current = current_page or st.session_state.get("page", "overview")
    nav_cols = st.columns(len(NAV_ITEMS))
    for col, (key, label) in zip(nav_cols, NAV_ITEMS):
        is_active = (
            current == key
            or (key == "entities"  and current == "entity_detail")
            or (key == "findings"  and current == "finding_detail")
        )
        col.button(
            label,
            key=f"nav_{key}",
            type="primary" if is_active else "secondary",
            use_container_width=True,
            on_click=go_to,
            args=(key,),
        )

    # Global search
    with st.container():
        gs1, gs2 = st.columns([6, 1])
        query = gs1.text_input(
            "Global Search",
            value=st.session_state.get("search_query", ""),
            placeholder="🔍  Search entities, findings, tickets, analysts…",
            label_visibility="collapsed",
            key="global_search_input",
        )
        if gs2.button("Search", key="global_search_btn", use_container_width=True):
            st.session_state.search_query = query
            st.rerun()

    if st.session_state.get("search_query"):
        _render_search_results(conn, st.session_state.search_query)

    st.markdown('<hr style="margin:6px 0 14px 0;border:0;border-top:1px solid #E5E7EB;">', unsafe_allow_html=True)


def _render_search_results(conn, query: str):
    pat = f"%{query.strip()}%"
    with st.container():
        st.markdown(
            f"""
            <div class="satsa-card" style="border:1px solid #99F6E4; margin-bottom:12px;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <div style="font-weight:700; font-size:14px; color:#111827;">
                  Results for "<span style="color:#0D9488;">{query.strip()}</span>"
                </div>
              </div>
            """,
            unsafe_allow_html=True,
        )
        clr1, clr2 = st.columns([8, 1])
        if clr2.button("✕ Clear", key="btn_clear_search", type="secondary"):
            st.session_state.search_query = ""
            st.rerun()

        found = False

        ents = conn.execute(
            "SELECT cse_id, entity_name, sector, criticality FROM cses WHERE entity_name ILIKE ? OR cse_id ILIKE ? LIMIT 5",
            [pat, pat],
        ).df()
        if not ents.empty:
            found = True
            st.markdown('<div style="font-size:11px;font-weight:700;color:#6B7280;text-transform:uppercase;letter-spacing:.07em;margin:4px 0 6px;">Entities</div>', unsafe_allow_html=True)
            for _, r in ents.iterrows():
                c1, c2 = st.columns([6, 1.2])
                c1.markdown(f"**{r['entity_name']}** · `{r['cse_id']}` · {r['sector']} · {r['criticality'].title()}")
                if c2.button("Open →", key=f"sr_e_{r['cse_id']}", type="secondary"):
                    st.session_state.search_query = ""
                    go_to("entity_detail", selected_entity=r["cse_id"])

        fnds = conn.execute(
            "SELECT f.finding_id, f.cse_id, f.finding_title, f.dimension, c.entity_name FROM findings f LEFT JOIN cses c ON f.cse_id=c.cse_id WHERE f.finding_title ILIKE ? OR f.reason ILIKE ? LIMIT 5",
            [pat, pat],
        ).df()
        if not fnds.empty:
            found = True
            st.markdown('<div style="font-size:11px;font-weight:700;color:#6B7280;text-transform:uppercase;letter-spacing:.07em;margin:10px 0 6px;">Findings</div>', unsafe_allow_html=True)
            for _, r in fnds.iterrows():
                f1, f2 = st.columns([6, 1.2])
                f1.markdown(f"**{r['finding_title']}** · {r['dimension']} · {r.get('entity_name', r['cse_id'])}")
                if f2.button("Open →", key=f"sr_f_{r['finding_id']}", type="secondary"):
                    st.session_state.search_query = ""
                    go_to("finding_detail", selected_finding=r["finding_id"])

        tkts = conn.execute(
            "SELECT t.ticket_id, t.cse_id, c.entity_name, t.priority, t.status FROM tickets t LEFT JOIN cses c ON t.cse_id=c.cse_id WHERE t.ticket_id ILIKE ? LIMIT 5",
            [pat],
        ).df()
        if not tkts.empty:
            found = True
            st.markdown('<div style="font-size:11px;font-weight:700;color:#6B7280;text-transform:uppercase;letter-spacing:.07em;margin:10px 0 6px;">Cases / Tickets</div>', unsafe_allow_html=True)
            for _, r in tkts.iterrows():
                t1, t2 = st.columns([6, 1.2])
                t1.markdown(f"Case **`{r['ticket_id']}`** · {r.get('entity_name','—')} · {r['priority']} · {r['status']}")
                if t2.button("Review →", key=f"sr_t_{r['ticket_id']}", type="secondary"):
                    st.session_state.search_query = ""
                    go_to("reviews", highlight_ticket=r["ticket_id"])

        if not found:
            st.caption("No matching results found.")

        st.markdown("</div>", unsafe_allow_html=True)
