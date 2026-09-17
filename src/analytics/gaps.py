"""
Execution-Gap Detection Module for SAT-SA.
Detects SLA breaches, unworked high-severity alerts, and rapid/superficial closures.
Eliminates false positives by filtering out compliant operational records.
"""

import pandas as pd

SLA_THRESHOLD_MINUTES = {
    "CRITICAL": 60,   # 1 hour
    "HIGH": 180,      # 3 hours
    "MEDIUM": 480,    # 8 hours
    "LOW": 1440,      # 24 hours
}


def detect_execution_gaps(conn):
    """
    Queries tickets, alerts, and notes from DuckDB to detect execution gaps.
    Returns:
        dict containing:
            - 'ticket_gaps': DataFrame of ticket-level gaps with explanation strings and sub-scores.
            - 'analyst_gap_summary': DataFrame summarizing gap scores per analyst.
    """
    query = """
        SELECT 
            t.ticket_id,
            t.cse_id,
            t.alert_id,
            t.analyst_id,
            a.name AS analyst_name,
            t.created_at,
            t.assigned_at,
            t.closed_at,
            t.status,
            t.priority,
            al.severity,
            al.rule_name,
            n.note_text,
            n.word_count
        FROM tickets t
        LEFT JOIN alerts al ON t.alert_id = al.alert_id
        LEFT JOIN analysts a ON t.analyst_id = a.analyst_id
        LEFT JOIN investigation_notes n ON t.ticket_id = n.ticket_id
    """
    df = conn.execute(query).df()

    if df.empty:
        return {
            "ticket_gaps": pd.DataFrame(),
            "analyst_gap_summary": pd.DataFrame()
        }

    results = []

    for _, row in df.iterrows():
        tkt_id = row["ticket_id"]
        cid = row["cse_id"]
        aid = row["analyst_id"]
        priority = str(row["priority"]).upper()
        status = str(row["status"]).upper()
        created_at = pd.to_datetime(row["created_at"])
        assigned_at = pd.to_datetime(row["assigned_at"]) if pd.notnull(row["assigned_at"]) else None
        closed_at = pd.to_datetime(row["closed_at"]) if pd.notnull(row["closed_at"]) else None
        word_count = row["word_count"] if pd.notnull(row["word_count"]) else 0

        gap_score = 0.0
        explanations = []

        # 1. Unworked High/Critical alert
        if status == "OPEN" or assigned_at is None:
            if priority in ["CRITICAL", "HIGH"]:
                gap_score += 50.0
                explanations.append(f"Unworked {priority} priority alert (unassigned or unclosed)")

        # 2. SLA Breach (with 20% margin to prevent false positives)
        if closed_at and created_at:
            triage_duration_mins = (closed_at - created_at).total_seconds() / 60.0
            allowed_sla = SLA_THRESHOLD_MINUTES.get(priority, 480)
            if triage_duration_mins > (allowed_sla * 1.20):  # 20% SLA breach margin
                overdue_mins = triage_duration_mins - allowed_sla
                penalty = min(50.0, 20.0 + (overdue_mins / 60.0) * 5.0)
                gap_score += penalty
                explanations.append(f"SLA Breach: Closed in {int(triage_duration_mins)}m vs allowed {allowed_sla}m ({int(overdue_mins)}m overdue)")

        # 3. Rapid/Superficial Triage (<30 seconds duration AND word count < 10)
        if assigned_at and closed_at:
            duration_sec = (closed_at - assigned_at).total_seconds()
            if duration_sec < 30 and word_count < 10:
                gap_score += 40.0
                explanations.append(f"Rapid Triage Anomaly: Closed in {int(duration_sec)}s with only {int(word_count)} words")

        # ONLY flag tickets where a genuine gap exists (gap_score > 0)
        if gap_score > 0:
            results.append({
                "ticket_id": tkt_id,
                "cse_id": cid,
                "analyst_id": aid,
                "analyst_name": row["analyst_name"],
                "gap_score": min(100.0, gap_score),
                "gap_explanations": explanations
            })

    df_ticket_gaps = pd.DataFrame(results)

    # Summarize by Analyst
    if not df_ticket_gaps.empty and "analyst_id" in df_ticket_gaps.columns:
        df_analyst_gaps = df_ticket_gaps.groupby("analyst_id").agg(
            avg_gap_score=("gap_score", "mean"),
            max_gap_score=("gap_score", "max"),
            total_flagged_tickets=("gap_score", lambda x: (x > 0).sum())
        ).reset_index()
    else:
        df_analyst_gaps = pd.DataFrame(columns=["analyst_id", "avg_gap_score", "max_gap_score", "total_flagged_tickets"])

    return {
        "ticket_gaps": df_ticket_gaps,
        "analyst_gap_summary": df_analyst_gaps
    }
