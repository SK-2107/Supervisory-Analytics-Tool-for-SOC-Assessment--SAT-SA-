"""
Styles & Visual Design System for SAT-SA 2.0.
Enterprise Light Theme Only — NCIIPC / SIH26157 Government SOC Supervisory Standard.
"""

import streamlit as st

# ============================================================================
# DESIGN TOKENS
# ============================================================================

COLOR_BG = "#F8FAFA"
COLOR_SURFACE = "#FFFFFF"
COLOR_TEXT_PRIMARY = "#172326"
COLOR_TEXT_SECONDARY = "#667579"
COLOR_TEXT_MUTED = "#8C9B9E"
COLOR_BORDER = "#E4E9E8"
COLOR_BORDER_LIGHT = "#EEF2F1"

COLOR_TEAL_PRIMARY = "#087F73"
COLOR_TEAL_DARK = "#065F56"
COLOR_TEAL_LIGHT = "#E6F4F2"
COLOR_TEAL_BORDER = "#B2DDD7"

COLOR_HIGH = "#C93C3C"
COLOR_HIGH_BG = "#FDF2F2"
COLOR_HIGH_BORDER = "#FACDCD"

COLOR_MODERATE = "#C58A18"
COLOR_MODERATE_BG = "#FEF9EE"
COLOR_MODERATE_BORDER = "#FDE6BA"

COLOR_LOW = "#278A55"
COLOR_LOW_BG = "#F0F9F4"
COLOR_LOW_BORDER = "#C4ECD5"

COLOR_INFO = "#2B6CB0"
COLOR_INFO_BG = "#EBF8FF"
COLOR_INFO_BORDER = "#BEE3F8"

BAND_COLOR = {
    "Critical": COLOR_HIGH,
    "High": COLOR_HIGH,
    "Moderate": COLOR_MODERATE,
    "Medium": COLOR_MODERATE,
    "Low": COLOR_LOW,
    "Routine": COLOR_LOW,
    "Open": "#C58A18",
    "In Review": "#2B6CB0",
    "Confirmed": "#C93C3C",
    "Dismissed": "#667579",
    "Escalated": "#8B1E3F",
}

BAND_BG = {
    "Critical": COLOR_HIGH_BG,
    "High": COLOR_HIGH_BG,
    "Moderate": COLOR_MODERATE_BG,
    "Medium": COLOR_MODERATE_BG,
    "Low": COLOR_LOW_BG,
    "Routine": COLOR_LOW_BG,
    "Open": COLOR_MODERATE_BG,
    "In Review": COLOR_INFO_BG,
    "Confirmed": COLOR_HIGH_BG,
    "Dismissed": "#F1F5F9",
    "Escalated": "#FCE8EF",
}

BAND_BORDER = {
    "Critical": COLOR_HIGH_BORDER,
    "High": COLOR_HIGH_BORDER,
    "Moderate": COLOR_MODERATE_BORDER,
    "Medium": COLOR_MODERATE_BORDER,
    "Low": COLOR_LOW_BORDER,
    "Routine": COLOR_LOW_BORDER,
    "Open": COLOR_MODERATE_BORDER,
    "In Review": COLOR_INFO_BORDER,
    "Confirmed": COLOR_HIGH_BORDER,
    "Dismissed": "#CBD5E1",
    "Escalated": "#F7B8CC",
}

ATTENTION_BANDS = [(35, "Critical"), (20, "High"), (8, "Moderate"), (0, "Low")]
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
    color = BAND_COLOR.get(band, COLOR_TEXT_SECONDARY)
    bg = BAND_BG.get(band, "#F1F5F9")
    border = BAND_BORDER.get(band, "#E2E8F0")
    return (
        f'<span class="satsa-badge" style="color:{color}; background-color:{bg}; border: 1px solid {border};">'
        f'{text}</span>'
    )


def inject_custom_css():
    st.markdown(
        """
        <style>
        /* Base typography & layout */
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", "Helvetica Neue", Arial, sans-serif;
            color: #172326;
            background-color: #F8FAFA;
        }

        #MainMenu, header, footer { visibility: hidden !important; height: 0 !important; }
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }

        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 3.5rem !important;
            max-width: 1360px !important;
        }

        /* Top Brand Header */
        .satsa-header-wrapper {
            background-color: #FFFFFF;
            border: 1px solid #E4E9E8;
            border-radius: 8px;
            padding: 14px 20px;
            margin-bottom: 12px;
            box-shadow: 0 1px 2px rgba(23, 35, 38, 0.03);
        }

        .satsa-brand-title {
            font-size: 20px;
            font-weight: 700;
            color: #172326;
            letter-spacing: -0.02em;
            line-height: 1.2;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .satsa-brand-tagline {
            font-size: 11.5px;
            color: #667579;
            font-weight: 500;
            letter-spacing: 0.02em;
            text-transform: uppercase;
            margin-top: 2px;
        }

        .satsa-pill-badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 3px 9px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.02em;
        }

        .satsa-local-badge {
            background-color: #E6F4F2;
            color: #087F73;
            border: 1px solid #B2DDD7;
        }

        .satsa-status-complete {
            background-color: #F0F9F4;
            color: #278A55;
            border: 1px solid #C4ECD5;
        }

        /* Navigation Buttons */
        div[data-testid="stButton"] button {
            border-radius: 6px;
            font-weight: 500;
            font-size: 13.5px;
            padding: 0.4rem 0.9rem;
            transition: all 0.15s ease-in-out;
            white-space: nowrap !important;
            text-overflow: clip !important;
        }

        div[data-testid="stButton"] button[kind="secondary"] {
            border: 1px solid #E4E9E8;
            background-color: #FFFFFF;
            color: #485659;
        }

        div[data-testid="stButton"] button[kind="secondary"]:hover {
            background-color: #F1F6F5;
            color: #087F73;
            border-color: #B2DDD7;
        }

        div[data-testid="stButton"] button[kind="primary"] {
            background-color: #087F73 !important;
            border-color: #087F73 !important;
            color: #FFFFFF !important;
            box-shadow: 0 1px 3px rgba(8, 127, 115, 0.2);
        }

        div[data-testid="stButton"] button[kind="primary"]:hover {
            background-color: #065F56 !important;
            border-color: #065F56 !important;
        }

        /* Typography */
        .page-title {
            font-size: 24px;
            font-weight: 700;
            color: #172326;
            margin-bottom: 2px;
            letter-spacing: -0.015em;
        }

        .page-subtitle {
            font-size: 14px;
            color: #667579;
            margin-bottom: 14px;
        }

        .section-title {
            font-size: 16px;
            font-weight: 700;
            color: #172326;
            margin: 12px 0 10px 0;
            letter-spacing: -0.01em;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .section-desc {
            font-size: 13px;
            color: #667579;
            margin-top: -6px;
            margin-bottom: 12px;
        }

        .meta-line {
            font-size: 12px;
            color: #667579;
        }

        .card-note {
            font-size: 13px;
            color: #485659;
            line-height: 1.45;
        }

        /* Badges */
        .satsa-badge {
            display: inline-block;
            padding: 2px 9px;
            border-radius: 4px;
            font-size: 11.5px;
            font-weight: 600;
            letter-spacing: 0.02em;
            white-space: nowrap;
        }

        /* Cards & Containers */
        .satsa-card {
            background-color: #FFFFFF;
            border: 1px solid #E4E9E8;
            border-radius: 8px;
            padding: 16px 18px;
            margin-bottom: 14px;
            box-shadow: 0 1px 2px rgba(23, 35, 38, 0.02);
        }

        .satsa-card-interactive {
            transition: border-color 0.15s ease;
        }

        .satsa-card-interactive:hover {
            border-color: #B2DDD7;
        }

        .satsa-attention-banner {
            background-color: #FFFFFF;
            border: 1px solid #E4E9E8;
            border-left: 5px solid #C93C3C;
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 16px;
        }

        .satsa-attention-banner-warning {
            background-color: #FFFFFF;
            border: 1px solid #E4E9E8;
            border-left: 5px solid #C58A18;
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 16px;
        }

        /* Breadcrumbs */
        .satsa-breadcrumbs {
            font-size: 12.5px;
            color: #667579;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .satsa-breadcrumbs a, .satsa-breadcrumb-item {
            color: #087F73;
            text-decoration: none;
            font-weight: 500;
        }

        .satsa-breadcrumb-current {
            color: #172326;
            font-weight: 600;
        }

        /* KPI Metric Block */
        .satsa-kpi-block {
            background-color: #FFFFFF;
            border: 1px solid #E4E9E8;
            border-radius: 8px;
            padding: 12px 14px;
            text-align: left;
        }

        .satsa-kpi-label {
            font-size: 12px;
            font-weight: 500;
            color: #667579;
            margin-bottom: 4px;
        }

        .satsa-kpi-value {
            font-size: 24px;
            font-weight: 700;
            color: #172326;
            line-height: 1.1;
        }

        .satsa-kpi-sub {
            font-size: 11px;
            color: #8C9B9E;
            margin-top: 4px;
        }

        /* Table headers & rows */
        .tbl-head {
            font-size: 11.5px;
            font-weight: 600;
            color: #667579;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            border-bottom: 1px solid #E4E9E8;
            padding-bottom: 8px;
            margin-bottom: 6px;
        }

        .tbl-row {
            padding: 8px 0;
            border-bottom: 1px solid #F1F5F4;
            font-size: 13.5px;
            color: #172326;
            display: flex;
            align-items: center;
        }

        /* Capability progress bar */
        .cap-row { margin-bottom: 12px; }
        .cap-label-row {
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            color: #172326;
            margin-bottom: 4px;
        }
        .cap-track {
            background: #EEF2F1;
            border-radius: 4px;
            height: 8px;
            width: 100%;
            overflow: hidden;
        }
        .cap-fill {
            height: 8px;
            border-radius: 4px;
            transition: width 0.3s ease;
        }

        /* Explainability Checklist */
        .explain-box {
            background-color: #FFFFFF;
            border: 1px solid #E4E9E8;
            border-radius: 6px;
            padding: 12px 14px;
            margin: 8px 0;
        }

        .signal-check {
            display: flex;
            align-items: flex-start;
            gap: 8px;
            font-size: 13.5px;
            color: #172326;
            margin-bottom: 6px;
        }

        .signal-check-icon {
            color: #087F73;
            font-weight: 700;
            font-size: 14px;
        }

        /* Dividers */
        hr {
            margin: 0.8rem 0 1.2rem 0;
            border: 0;
            border-top: 1px solid #E4E9E8;
        }

        /* Inputs */
        div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div[data-baseweb="select"] {
            border-radius: 6px !important;
            border-color: #E4E9E8 !important;
            font-size: 13.5px !important;
        }

        div[data-testid="stTextInput"] input:focus {
            border-color: #087F73 !important;
            box-shadow: 0 0 0 1px #087F73 !important;
        }

        /* Streamlit Tabs */
        div[data-testid="stTabs"] button[role="tab"] {
            font-size: 13.5px !important;
            font-weight: 600 !important;
            color: #667579 !important;
            padding: 8px 16px !important;
        }

        div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            color: #087F73 !important;
            border-bottom-color: #087F73 !important;
            border-bottom-width: 2px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
