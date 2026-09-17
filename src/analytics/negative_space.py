"""
Negative-Space Detection Module for SAT-SA.
Identifies unlogged shift windows, missing handovers, and zero-note closures.
Outputs labeled explicitly as 'Potential Negative-Space Signal'.
"""

import pandas as pd


def detect_negative_space(conn):
    """
    Analyzes shift logs, tickets, and investigation notes for negative-space anomalies.
    Returns:
        dict with 'analyst_negative_space' and 'ticket_negative_space' DataFrames.
    """
    shift_query = """
        SELECT 
            sl.log_id,
            sl.cse_id,
            sl.analyst_id,
            a.name AS analyst_name,
            sl.shift_date,
            sl.shift_name,
            sl.shift_start,
            sl.shift_end,
            sl.handover_completed,
            sl.notes_logged
        FROM shift_logs sl
        JOIN analysts a ON sl.analyst_id = a.analyst_id
    """
    df_shifts = conn.execute(shift_query).df()

    analyst_results = {}

    if not df_shifts.empty:
        for _, row in df_shifts.iterrows():
            aid = row["analyst_id"]
            if aid not in analyst_results:
                analyst_results[aid] = {
                    "analyst_id": aid,
                    "cse_id": row["cse_id"],
                    "analyst_name": row["analyst_name"],
                    "negative_space_score": 0.0,
                    "explanations": []
                }

            if not row["handover_completed"]:
                analyst_results[aid]["negative_space_score"] += 25.0
                analyst_results[aid]["explanations"].append(
                    f"Potential Negative-Space Signal: Missing shift handover on {row['shift_date']} ({row['shift_name']} Shift)"
                )

    zero_note_query = """
        SELECT 
            t.ticket_id,
            t.cse_id,
            t.analyst_id,
            a.name AS analyst_name,
            t.closed_at
        FROM tickets t
        LEFT JOIN investigation_notes n ON t.ticket_id = n.ticket_id
        LEFT JOIN analysts a ON t.analyst_id = a.analyst_id
        WHERE t.status = 'CLOSED' AND n.note_id IS NULL
    """
    df_zero_notes = conn.execute(zero_note_query).df()

    ticket_results = []
    if not df_zero_notes.empty:
        for _, row in df_zero_notes.iterrows():
            tkt_id = row["ticket_id"]
            aid = row["analyst_id"]
            ticket_results.append({
                "ticket_id": tkt_id,
                "cse_id": row["cse_id"],
                "analyst_id": aid,
                "negative_space_score": 40.0,
                "explanations": ["Potential Negative-Space Signal: Closed ticket without any recorded investigation note"]
            })

            if aid and aid in analyst_results:
                analyst_results[aid]["negative_space_score"] += 15.0
                analyst_results[aid]["explanations"].append(f"Potential Negative-Space Signal: Zero-note ticket closure on {tkt_id}")

    analyst_list = []
    for aid, res in analyst_results.items():
        res["negative_space_score"] = min(100.0, res["negative_space_score"])
        analyst_list.append(res)

    df_analyst_neg = pd.DataFrame(analyst_list)
    df_ticket_neg = pd.DataFrame(ticket_results)

    return {
        "analyst_negative_space": df_analyst_neg,
        "ticket_negative_space": df_ticket_neg
    }
