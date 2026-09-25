"""
SAT-SA Visual Design System — Enterprise Light Theme.
Supervisory Analytics Tool for SOC Assessment.
Clean, professional, minimal. No dark themes. No gimmicks.
"""

import streamlit as st

# ============================================================================
# DESIGN TOKENS
# ============================================================================

COLOR_BG              = "#F4F6F8"
COLOR_SURFACE         = "#FFFFFF"
COLOR_SURFACE_SUBTLE  = "#F9FAFB"
COLOR_TEXT_PRIMARY    = "#111827"
COLOR_TEXT_SECONDARY  = "#6B7280"
COLOR_TEXT_MUTED      = "#9CA3AF"
COLOR_BORDER          = "#E5E7EB"
COLOR_BORDER_LIGHT    = "#F3F4F6"

COLOR_TEAL_PRIMARY    = "#0D9488"
COLOR_TEAL_DARK       = "#0F766E"
COLOR_TEAL_LIGHT      = "#F0FDFA"
COLOR_TEAL_BORDER     = "#99F6E4"
COLOR_TEAL_MID        = "#CCFBF1"

# Semantic status colours
COLOR_CRITICAL        = "#DC2626"   # Red
COLOR_HIGH            = "#EA580C"   # Orange
COLOR_MODERATE        = "#D97706"   # Amber
COLOR_LOW             = "#16A34A"   # Green
COLOR_INFO            = "#2563EB"   # Blue
COLOR_NEUTRAL         = "#6B7280"   # Slate

COLOR_CRITICAL_BG     = "#FEF2F2"
COLOR_CRITICAL_BORDER = "#FECACA"
COLOR_HIGH_BG         = "#FFF7ED"
COLOR_HIGH_BORDER     = "#FED7AA"
COLOR_MODERATE_BG     = "#FFFBEB"
COLOR_MODERATE_BORDER = "#FDE68A"
COLOR_LOW_BG          = "#F0FDF4"
COLOR_LOW_BORDER      = "#BBF7D0"
COLOR_INFO_BG         = "#EFF6FF"
COLOR_INFO_BORDER     = "#BFDBFE"

# Alias kept for backward compat
COLOR_HIGH_BG_COMPAT  = COLOR_CRITICAL_BG

BAND_COLOR = {
    "Critical":   COLOR_CRITICAL,
    "High":       COLOR_HIGH,
    "Moderate":   COLOR_MODERATE,
    "Medium":     COLOR_MODERATE,
    "Low":        COLOR_LOW,
    "Routine":    COLOR_LOW,
    "Open":       COLOR_MODERATE,
    "In Review":  COLOR_INFO,
    "Confirmed":  COLOR_CRITICAL,
    "Dismissed":  COLOR_NEUTRAL,
    "Escalated":  "#7C3AED",
}

BAND_BG = {
    "Critical":   COLOR_CRITICAL_BG,
    "High":       COLOR_HIGH_BG,
    "Moderate":   COLOR_MODERATE_BG,
    "Medium":     COLOR_MODERATE_BG,
    "Low":        COLOR_LOW_BG,
    "Routine":    COLOR_LOW_BG,
    "Open":       COLOR_MODERATE_BG,
    "In Review":  COLOR_INFO_BG,
    "Confirmed":  COLOR_CRITICAL_BG,
    "Dismissed":  "#F9FAFB",
    "Escalated":  "#F5F3FF",
}

BAND_BORDER = {
    "Critical":   COLOR_CRITICAL_BORDER,
    "High":       COLOR_HIGH_BORDER,
    "Moderate":   COLOR_MODERATE_BORDER,
    "Medium":     COLOR_MODERATE_BORDER,
    "Low":        COLOR_LOW_BORDER,
    "Routine":    COLOR_LOW_BORDER,
    "Open":       COLOR_MODERATE_BORDER,
    "In Review":  COLOR_INFO_BORDER,
    "Confirmed":  COLOR_CRITICAL_BORDER,
    "Dismissed":  "#E5E7EB",
    "Escalated":  "#DDD6FE",
}

ATTENTION_BANDS        = [(35, "Critical"), (20, "High"), (8, "Moderate"), (0, "Low")]
FINDING_SEVERITY_BANDS = [(50, "High"), (20, "Medium"), (0, "Low")]


def attention_band(score: float) -> str:
    for threshold, label in ATTENTION_BANDS:
        if score >= threshold:
            return label
    return "Low"


def finding_severity_band(dim_score: float) -> str:
    for threshold, label in FINDING_SEVERITY_BANDS:
        if dim_score >= threshold:
            return label
    return "Low"


def badge(text: str, band: str) -> str:
    color  = BAND_COLOR.get(band, COLOR_TEXT_SECONDARY)
    bg     = BAND_BG.get(band, "#F9FAFB")
    border = BAND_BORDER.get(band, COLOR_BORDER)
    return (
        f'<span class="satsa-badge" style="color:{color};background:{bg};border:1px solid {border};">'
        f'{text}</span>'
    )


def neutral_badge(text: str) -> str:
    return (
        f'<span class="satsa-badge" style="color:{COLOR_NEUTRAL};background:#F3F4F6;border:1px solid {COLOR_BORDER};">'
        f'{text}</span>'
    )


def fmt_timestamp(value) -> str:
    import pandas as pd
    if value is None:
        return "—"
    try:
        ts = pd.to_datetime(value)
        return ts.strftime("%d %b %Y, %H:%M")
    except Exception:
        return str(value)


def priority_dot(band: str) -> str:
    """Tiny colored dot for inline status indication."""
    color = BAND_COLOR.get(band, COLOR_NEUTRAL)
    return f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{color};margin-right:5px;vertical-align:middle;"></span>'


def inject_custom_css():
    st.markdown(
        """
        <style>
        /* ================================================================
           RESET & BASE
        ================================================================ */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            color: #111827;
            background-color: #F4F6F8;
        }

        #MainMenu, header, footer { visibility: hidden !important; height: 0 !important; }
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }

        .block-container {
            padding-top: 0.75rem !important;
            padding-bottom: 4rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 1400px !important;
        }

        /* ================================================================
           HEADER & NAVIGATION
        ================================================================ */
        .satsa-topbar {
            background: #FFFFFF;
            border-bottom: 1px solid #E5E7EB;
            padding: 0 0 0 0;
            margin-bottom: 0;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .satsa-brand-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 0 10px 0;
            flex-wrap: wrap;
            gap: 10px;
        }

        .satsa-logo-mark {
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }

        .satsa-logo-icon {
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, #0D9488 0%, #0F766E 100%);
            border-radius: 8px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 15px;
            font-weight: 800;
            letter-spacing: -1px;
            flex-shrink: 0;
        }

        .satsa-brand-name {
            font-size: 18px;
            font-weight: 800;
            color: #111827;
            letter-spacing: -0.03em;
            line-height: 1;
        }

        .satsa-brand-sub {
            font-size: 11px;
            font-weight: 500;
            color: #6B7280;
            letter-spacing: 0.02em;
            text-transform: uppercase;
            margin-top: 1px;
        }

        .satsa-header-meta {
            display: flex;
            align-items: center;
            gap: 16px;
            flex-wrap: wrap;
        }

        .satsa-status-pill {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            white-space: nowrap;
        }

        .satsa-pill-green {
            background: #F0FDF4;
            color: #16A34A;
            border: 1px solid #BBF7D0;
        }

        .satsa-pill-teal {
            background: #F0FDFA;
            color: #0D9488;
            border: 1px solid #99F6E4;
        }

        .satsa-meta-text {
            font-size: 12px;
            color: #6B7280;
        }

        .satsa-meta-text strong {
            color: #111827;
            font-weight: 600;
        }

        /* Nav strip */
        .satsa-nav-strip {
            border-top: 1px solid #F3F4F6;
            padding: 0;
            display: flex;
            gap: 0;
            overflow-x: auto;
        }

        .satsa-nav-item {
            padding: 10px 16px;
            font-size: 13px;
            font-weight: 500;
            color: #6B7280;
            cursor: pointer;
            white-space: nowrap;
            border-bottom: 2px solid transparent;
            transition: color 0.15s, border-color 0.15s;
            text-decoration: none;
        }

        .satsa-nav-item:hover {
            color: #0D9488;
            border-bottom-color: #CCFBF1;
        }

        .satsa-nav-item.active {
            color: #0D9488;
            font-weight: 600;
            border-bottom-color: #0D9488;
        }

        /* Streamlit button overrides for nav */
        div[data-testid="stButton"] button {
            border-radius: 6px;
            font-size: 13px;
            font-weight: 500;
            padding: 0.35rem 0.75rem;
            transition: all 0.15s ease;
            white-space: nowrap !important;
            letter-spacing: 0;
        }

        div[data-testid="stButton"] button[kind="secondary"] {
            border: 1px solid #E5E7EB;
            background: #FFFFFF;
            color: #374151;
        }

        div[data-testid="stButton"] button[kind="secondary"]:hover {
            background: #F9FAFB;
            border-color: #99F6E4;
            color: #0D9488;
        }

        div[data-testid="stButton"] button[kind="primary"] {
            background: #0D9488 !important;
            border-color: #0D9488 !important;
            color: #FFFFFF !important;
            box-shadow: 0 1px 2px rgba(13, 148, 136, 0.25);
        }

        div[data-testid="stButton"] button[kind="primary"]:hover {
            background: #0F766E !important;
            border-color: #0F766E !important;
        }

        /* ================================================================
           TYPOGRAPHY
        ================================================================ */
        .page-title {
            font-size: 22px;
            font-weight: 800;
            color: #111827;
            letter-spacing: -0.025em;
            line-height: 1.2;
            margin-bottom: 3px;
        }

        .page-subtitle {
            font-size: 14px;
            color: #6B7280;
            font-weight: 400;
            margin-bottom: 20px;
            line-height: 1.5;
        }

        .section-title {
            font-size: 15px;
            font-weight: 700;
            color: #111827;
            letter-spacing: -0.015em;
            margin-top: 24px;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 7px;
        }

        .section-desc {
            font-size: 13px;
            color: #6B7280;
            margin-bottom: 14px;
            line-height: 1.5;
        }

        .meta-line {
            font-size: 12px;
            color: #6B7280;
            line-height: 1.5;
        }

        .card-note {
            font-size: 13px;
            color: #374151;
            line-height: 1.55;
        }

        /* ================================================================
           CARDS
        ================================================================ */
        .satsa-card {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 10px;
            padding: 16px 20px;
            margin-bottom: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03);
        }

        .satsa-card-flat {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 10px;
            padding: 16px 20px;
            margin-bottom: 12px;
        }

        .satsa-card-elevated {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 10px;
            padding: 20px 24px;
            margin-bottom: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05), 0 1px 3px rgba(0,0,0,0.04);
        }

        .satsa-card-interactive {
            cursor: default;
            transition: border-color 0.15s, box-shadow 0.15s;
        }

        .satsa-card-interactive:hover {
            border-color: #99F6E4;
            box-shadow: 0 2px 8px rgba(13,148,136,0.08);
        }

        /* Accent left border variants */
        .satsa-card-critical { border-left: 3px solid #DC2626 !important; }
        .satsa-card-high     { border-left: 3px solid #EA580C !important; }
        .satsa-card-moderate { border-left: 3px solid #D97706 !important; }
        .satsa-card-low      { border-left: 3px solid #16A34A !important; }
        .satsa-card-teal     { border-left: 3px solid #0D9488 !important; }

        /* Attention banners */
        .satsa-attention-banner {
            background: #FFFFFF;
            border: 1px solid #FECACA;
            border-left: 4px solid #DC2626;
            border-radius: 8px;
            padding: 14px 18px;
            margin-bottom: 14px;
        }

        .satsa-attention-banner-warning {
            background: #FFFBEB;
            border: 1px solid #FDE68A;
            border-left: 4px solid #D97706;
            border-radius: 8px;
            padding: 14px 18px;
            margin-bottom: 14px;
        }

        .satsa-info-banner {
            background: #EFF6FF;
            border: 1px solid #BFDBFE;
            border-left: 4px solid #2563EB;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 14px;
        }

        /* ================================================================
           KPI METRIC BLOCKS
        ================================================================ */
        .satsa-kpi-block {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 10px;
            padding: 14px 16px;
            text-align: left;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }

        .satsa-kpi-hero {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 10px;
            padding: 14px 16px;
            text-align: left;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
            border-top: 3px solid #0D9488;
        }

        .satsa-kpi-label {
            font-size: 11.5px;
            font-weight: 600;
            color: #6B7280;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 5px;
        }

        .satsa-kpi-value {
            font-size: 26px;
            font-weight: 800;
            color: #111827;
            letter-spacing: -0.03em;
            line-height: 1.1;
        }

        .satsa-kpi-sub {
            font-size: 11px;
            color: #9CA3AF;
            margin-top: 4px;
            font-weight: 400;
        }

        .satsa-kpi-trend {
            font-size: 11px;
            font-weight: 600;
            margin-top: 4px;
        }

        /* ================================================================
           TABLES
        ================================================================ */
        .tbl-head {
            font-size: 11px;
            font-weight: 700;
            color: #6B7280;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            border-bottom: 2px solid #E5E7EB;
            padding: 0 0 8px 0;
            margin-bottom: 4px;
        }

        .tbl-row {
            padding: 9px 0;
            border-bottom: 1px solid #F3F4F6;
            font-size: 13.5px;
            color: #111827;
            display: flex;
            align-items: center;
            min-height: 38px;
        }

        .tbl-row-alt {
            padding: 9px 0;
            border-bottom: 1px solid #F3F4F6;
            font-size: 13.5px;
            color: #111827;
            display: flex;
            align-items: center;
            background: #FAFAFA;
            min-height: 38px;
        }

        /* ================================================================
           BADGES
        ================================================================ */
        .satsa-badge {
            display: inline-flex;
            align-items: center;
            padding: 2px 8px;
            border-radius: 5px;
            font-size: 11.5px;
            font-weight: 600;
            letter-spacing: 0.02em;
            white-space: nowrap;
            line-height: 1.5;
        }

        /* ================================================================
           BREADCRUMBS
        ================================================================ */
        .satsa-breadcrumbs {
            font-size: 12.5px;
            color: #6B7280;
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            gap: 6px;
            flex-wrap: wrap;
        }

        .satsa-breadcrumb-item {
            color: #0D9488;
            font-weight: 500;
            cursor: pointer;
        }

        .satsa-breadcrumb-current {
            color: #111827;
            font-weight: 600;
        }

        /* ================================================================
           CAPABILITY PROGRESS BARS
        ================================================================ */
        .cap-row { margin-bottom: 14px; }

        .cap-label-row {
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            color: #111827;
            margin-bottom: 5px;
            align-items: center;
        }

        .cap-track {
            background: #F3F4F6;
            border-radius: 4px;
            height: 7px;
            width: 100%;
            overflow: hidden;
        }

        .cap-fill {
            height: 7px;
            border-radius: 4px;
            transition: width 0.4s ease;
        }

        /* ================================================================
           EXPLAINABILITY / SIGNAL BOXES
        ================================================================ */
        .explain-box {
            background: #F9FAFB;
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            padding: 12px 16px;
            margin: 8px 0;
        }

        .signal-check {
            display: flex;
            align-items: flex-start;
            gap: 8px;
            font-size: 13px;
            color: #111827;
            margin-bottom: 7px;
            line-height: 1.5;
        }

        .signal-check-icon {
            color: #0D9488;
            font-weight: 700;
            font-size: 14px;
            flex-shrink: 0;
            margin-top: 1px;
        }

        /* ================================================================
           DIVIDERS & SPACING
        ================================================================ */
        hr {
            margin: 1rem 0 1.4rem 0 !important;
            border: 0 !important;
            border-top: 1px solid #E5E7EB !important;
        }

        /* ================================================================
           INPUTS & CONTROLS
        ================================================================ */
        div[data-testid="stTextInput"] input {
            border-radius: 7px !important;
            border-color: #E5E7EB !important;
            font-size: 13.5px !important;
            background: #FFFFFF !important;
        }

        div[data-testid="stTextInput"] input:focus {
            border-color: #0D9488 !important;
            box-shadow: 0 0 0 2px rgba(13, 148, 136, 0.12) !important;
        }

        div[data-baseweb="select"] {
            border-radius: 7px !important;
        }

        div[data-testid="stSelectbox"] div[data-baseweb="select"] {
            font-size: 13.5px !important;
        }

        /* ================================================================
           TABS
        ================================================================ */
        div[data-testid="stTabs"] button[role="tab"] {
            font-size: 13.5px !important;
            font-weight: 600 !important;
            color: #6B7280 !important;
            padding: 9px 18px !important;
        }

        div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            color: #0D9488 !important;
            border-bottom-color: #0D9488 !important;
            border-bottom-width: 2px !important;
        }

        div[data-testid="stTabs"] [role="tabpanel"] {
            padding-top: 16px;
        }

        /* ================================================================
           EXPANDER
        ================================================================ */
        div[data-testid="stExpander"] details {
            border: 1px solid #E5E7EB !important;
            border-radius: 8px !important;
            background: #FFFFFF !important;
            margin-bottom: 8px;
        }

        div[data-testid="stExpander"] summary {
            font-size: 13.5px !important;
            font-weight: 600 !important;
            color: #111827 !important;
            padding: 10px 14px !important;
        }

        /* ================================================================
           ALERTS / NOTIFICATIONS
        ================================================================ */
        div[data-testid="stAlert"] {
            border-radius: 8px !important;
            font-size: 13.5px !important;
        }

        /* ================================================================
           DOWNLOAD BUTTON
        ================================================================ */
        div[data-testid="stDownloadButton"] button {
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
        }

        /* ================================================================
           METRIC DELTA
        ================================================================ */
        div[data-testid="stMetricDelta"] {
            font-size: 12px !important;
        }

        /* ================================================================
           WORKFLOW STEPS
        ================================================================ */
        .workflow-steps {
            display: flex;
            align-items: center;
            gap: 0;
            overflow-x: auto;
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 10px;
            padding: 14px 20px;
            margin-bottom: 20px;
        }

        .workflow-step {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 0 12px;
            white-space: nowrap;
        }

        .workflow-step:first-child { padding-left: 0; }
        .workflow-step:last-child  { padding-right: 0; }

        .workflow-step-num {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 700;
            flex-shrink: 0;
        }

        .workflow-step-active   .workflow-step-num { background: #0D9488; color: #FFFFFF; }
        .workflow-step-done     .workflow-step-num { background: #CCFBF1; color: #0D9488; }
        .workflow-step-inactive .workflow-step-num { background: #F3F4F6; color: #9CA3AF; }

        .workflow-step-label {
            font-size: 13px;
            font-weight: 600;
        }

        .workflow-step-active   .workflow-step-label { color: #0D9488; }
        .workflow-step-done     .workflow-step-label { color: #0D9488; }
        .workflow-step-inactive .workflow-step-label { color: #9CA3AF; }

        .workflow-arrow {
            color: #D1D5DB;
            font-size: 16px;
            flex-shrink: 0;
        }

        /* ================================================================
           EMPTY STATES
        ================================================================ */
        .empty-state {
            text-align: center;
            padding: 48px 24px;
            background: #FFFFFF;
            border: 1px dashed #D1D5DB;
            border-radius: 12px;
            margin: 16px 0;
        }

        .empty-state-icon {
            font-size: 36px;
            margin-bottom: 12px;
        }

        .empty-state-title {
            font-size: 16px;
            font-weight: 700;
            color: #374151;
            margin-bottom: 6px;
        }

        .empty-state-desc {
            font-size: 13px;
            color: #6B7280;
            max-width: 400px;
            margin: 0 auto;
            line-height: 1.55;
        }

        /* ================================================================
           FINDING CARDS
        ================================================================ */
        .finding-card {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 10px;
            padding: 16px 20px;
            margin-bottom: 10px;
            transition: border-color 0.15s;
        }

        .finding-card:hover {
            border-color: #99F6E4;
        }

        .finding-card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 8px;
            gap: 12px;
        }

        .finding-title {
            font-size: 14px;
            font-weight: 700;
            color: #111827;
            line-height: 1.3;
        }

        .finding-why {
            font-size: 13px;
            color: #4B5563;
            line-height: 1.5;
            margin-top: 4px;
        }

        .finding-evidence {
            font-size: 11.5px;
            color: #6B7280;
            margin-top: 8px;
            font-family: "SF Mono", "Fira Mono", monospace;
            background: #F9FAFB;
            border: 1px solid #E5E7EB;
            border-radius: 4px;
            padding: 4px 8px;
            word-break: break-all;
        }

        /* ================================================================
           STREAMLIT SPECIFIC FIXES
        ================================================================ */
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
            gap: 0.5rem;
        }

        div[data-testid="column"] {
            padding: 0 6px !important;
        }

        div[data-testid="column"]:first-child { padding-left: 0 !important; }
        div[data-testid="column"]:last-child  { padding-right: 0 !important; }

        /* Plotly chart container */
        div[data-testid="stPlotlyChart"] {
            border-radius: 8px;
            overflow: hidden;
        }

        /* Spinner */
        div[data-testid="stSpinner"] p {
            font-size: 13px;
            color: #6B7280;
        }

        /* File uploader */
        div[data-testid="stFileUploader"] {
            border-radius: 8px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )
