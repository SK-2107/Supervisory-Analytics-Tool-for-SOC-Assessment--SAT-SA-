"""
ReportLab PDF Generator for SAT-SA.
Produces audit-ready supervisory assessment reports for Critical Sector Entities (CSEs) and SOC management.
Includes data-source identification, 8 capability dimension breakdown, evidence references, and supervisory disclaimers.
"""

import io
import json
from datetime import datetime
import pandas as pd

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from src.config import get_data_source_label


def generate_supervisory_pdf_report(conn) -> bytes:
    """
    Generates a PDF audit report using ReportLab focused on CSE Supervisory Assessment.
    Returns:
        bytes: The binary PDF data.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#1E293B'), spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'], fontSize=8.5, textColor=colors.HexColor('#64748B'), spaceAfter=8
    )
    disclaimer_style = ParagraphStyle(
        'Disclaimer', parent=styles['Italic'], fontSize=7.5, leading=10, textColor=colors.HexColor('#9A3412'), spaceAfter=10
    )
    h2_style = ParagraphStyle(
        'SectionHeading', parent=styles['Heading2'], fontSize=11, leading=14, textColor=colors.HexColor('#0F172A'), spaceBefore=8, spaceAfter=4
    )
    body_style = ParagraphStyle(
        'TableBody', parent=styles['Normal'], fontSize=7.5, leading=9.5, textColor=colors.HexColor('#334155')
    )
    header_cell_style = ParagraphStyle(
        'TableHeader', parent=styles['Normal'], fontSize=7.5, leading=9.5, fontName='Helvetica-Bold', textColor=colors.white
    )

    story = []

    # Title & Metadata
    data_label = get_data_source_label(conn)
    story.append(Paragraph("SAT-SA: Critical Sector Entity Supervisory Assessment Report", title_style))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Environment: NCIIPC Air-Gapped Prototype | {data_label}",
        subtitle_style
    ))
    story.append(Paragraph(
        "<b>Notice:</b> This report provides analytical indicators for supervisory review. "
        "It does not replace human assessment or constitute a definitive security determination. "
        "All supervisory attention scores indicate prioritized areas for focused manual review by authorized supervisors.",
        disclaimer_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=8))

    # 1. Summary Metrics
    df_metrics = conn.execute("""
        SELECT 
            (SELECT COUNT(*) FROM cses) AS total_cses,
            (SELECT COUNT(*) FROM alerts) AS total_alerts,
            (SELECT COUNT(*) FROM tickets) AS total_tickets,
            (SELECT COUNT(*) FROM findings) AS total_findings
    """).df()

    t_cses = df_metrics["total_cses"].values[0] if not df_metrics.empty else 0
    t_alerts = df_metrics["total_alerts"].values[0] if not df_metrics.empty else 0
    t_tickets = df_metrics["total_tickets"].values[0] if not df_metrics.empty else 0
    t_findings = df_metrics["total_findings"].values[0] if not df_metrics.empty else 0

    summary_data = [
        [
            Paragraph("<b>Total CSEs Assessed</b>", body_style), Paragraph(str(t_cses), body_style),
            Paragraph("<b>Total Findings</b>", body_style), Paragraph(str(t_findings), body_style),
        ],
        [
            Paragraph("<b>Total Alerts Ingested</b>", body_style), Paragraph(str(t_alerts), body_style),
            Paragraph("<b>Total Incident Tickets</b>", body_style), Paragraph(str(t_tickets), body_style),
        ]
    ]

    t_summary = Table(summary_data, colWidths=[130, 120, 130, 140])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 8))

    # 2. CSE Supervisory Attention Queue Table
    story.append(Paragraph("Critical Sector Entity (CSE) Supervisory Assessment Queue", h2_style))

    df_cse_scores = conn.execute("""
        SELECT 
            s.entity_id AS cse_id,
            c.entity_name,
            c.sector,
            c.criticality,
            s.total_score
        FROM supervisory_scores s
        JOIN cses c ON s.entity_id = c.cse_id
        WHERE s.entity_type = 'cse'
        ORDER BY s.total_score DESC
    """).df()

    if df_cse_scores.empty:
        try:
            from src.analytics.scoring import calculate_supervisory_attention_scores
            calculate_supervisory_attention_scores(conn)
            df_cse_scores = conn.execute("""
                SELECT 
                    s.entity_id AS cse_id,
                    c.entity_name,
                    c.sector,
                    c.criticality,
                    s.total_score
                FROM supervisory_scores s
                JOIN cses c ON s.entity_id = c.cse_id
                WHERE s.entity_type = 'cse'
                ORDER BY s.total_score DESC
            """).df()
        except Exception:
            pass

    if not df_cse_scores.empty:
        t_data = [[
            Paragraph("CSE ID", header_cell_style),
            Paragraph("Entity Name", header_cell_style),
            Paragraph("Sector", header_cell_style),
            Paragraph("Criticality", header_cell_style),
            Paragraph("Attention Score", header_cell_style),
            Paragraph("Priority Level", header_cell_style),
        ]]

        for _, row in df_cse_scores.iterrows():
            score_val = row['total_score']
            if score_val >= 45:
                score_color = "#DC2626"
                p_level = "HIGH SUPERVISORY PRIORITY"
            elif score_val >= 20:
                score_color = "#D97706"
                p_level = "MEDIUM SUPERVISORY PRIORITY"
            else:
                score_color = "#16A34A"
                p_level = "ROUTINE OVERSIGHT"

            score_p = Paragraph(f"<font color='{score_color}'><b>{score_val:.1f}/100</b></font>", body_style)

            t_data.append([
                Paragraph(str(row['cse_id']), body_style),
                Paragraph(str(row['entity_name']), body_style),
                Paragraph(str(row['sector']), body_style),
                Paragraph(str(row['criticality']), body_style),
                score_p,
                Paragraph(p_level, body_style),
            ])

        t_cses_table = Table(t_data, colWidths=[72, 148, 110, 60, 75, 75])
        t_cses_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E293B")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ]))
        story.append(t_cses_table)

    story.append(Spacer(1, 8))

    # 3. Major Findings & Evidence Traceability
    story.append(Paragraph("Major Evidence Findings & Traceability Log", h2_style))

    df_fnd = conn.execute("""
        SELECT cse_id, dimension, finding_title, reason, observed_value, evidence_record_ids
        FROM findings
        LIMIT 8
    """).df()

    if not df_fnd.empty:
        f_data = [[
            Paragraph("CSE ID", header_cell_style),
            Paragraph("Dimension", header_cell_style),
            Paragraph("Finding & Reason", header_cell_style),
            Paragraph("Evidence Record IDs", header_cell_style),
        ]]

        for _, row in df_fnd.iterrows():
            title_reason = f"<b>{row['finding_title']}</b><br/>{row['reason']}"

            f_data.append([
                Paragraph(str(row['cse_id']), body_style),
                Paragraph(str(row['dimension']), body_style),
                Paragraph(title_reason, body_style),
                Paragraph(str(row['evidence_record_ids']), body_style),
            ])

        t_fnd_table = Table(f_data, colWidths=[72, 90, 238, 140])
        t_fnd_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F172A")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ]))
        story.append(t_fnd_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
