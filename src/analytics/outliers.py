"""
Peer Benchmarking & Statistical Outlier Detection Module for SAT-SA.
Uses Z-Score and IQR to detect extreme performance anomalies relative to peer cohorts.
"""

import pandas as pd
import numpy as np


def detect_statistical_outliers(conn):
    """
    Evaluates analyst performance metrics against peer cohorts (tier + shift_group).
    Returns DataFrame of analyst outlier scores and explanations.
    """
    query = """
        SELECT 
            a.analyst_id,
            a.name AS analyst_name,
            a.tier,
            a.shift_group,
            COUNT(t.ticket_id) AS total_tickets,
            AVG(CASE WHEN t.assigned_at IS NOT NULL AND t.closed_at IS NOT NULL 
                     THEN EPOCH(t.closed_at - t.assigned_at) / 60.0 ELSE NULL END) AS avg_triage_mins,
            AVG(COALESCE(n.word_count, 0)) AS avg_word_count
        FROM analysts a
        LEFT JOIN tickets t ON a.analyst_id = t.analyst_id
        LEFT JOIN investigation_notes n ON t.ticket_id = n.ticket_id
        GROUP BY a.analyst_id, a.name, a.tier, a.shift_group
    """
    df = conn.execute(query).df()

    if df.empty or len(df) < 2:
        return pd.DataFrame(columns=[
            "analyst_id", "analyst_name", "tier", "shift_group",
            "outlier_score", "outlier_explanations"
        ])

    df["avg_triage_mins"] = df["avg_triage_mins"].fillna(df["avg_triage_mins"].median() or 30.0)
    df["avg_word_count"] = df["avg_word_count"].fillna(df["avg_word_count"].median() or 20.0)

    outlier_records = []

    # Group by peer cohorts
    for (tier, shift_group), cohort_df in df.groupby(["tier", "shift_group"]):
        if len(cohort_df) < 2:
            # Fallback to global stats if cohort is too small
            cohort_df = df

        # Metrics for comparison
        for _, row in cohort_df.iterrows():
            aid = row["analyst_id"]
            name = row["analyst_name"]
            score = 0.0
            explanations = []

            # 1. Triage Duration Z-score & IQR
            triage_val = row["avg_triage_mins"]
            triage_mean = cohort_df["avg_triage_mins"].mean()
            triage_std = cohort_df["avg_triage_mins"].std()
            triage_q1 = cohort_df["avg_triage_mins"].quantile(0.25)
            triage_q3 = cohort_df["avg_triage_mins"].quantile(0.75)
            triage_iqr = triage_q3 - triage_q1

            if triage_std and triage_std > 0:
                z_triage = (triage_val - triage_mean) / triage_std
                if abs(z_triage) > 2.0:
                    penalty = min(40.0, abs(z_triage) * 15.0)
                    score += penalty
                    direction = "slower" if z_triage > 0 else "faster"
                    explanations.append(f"Triage duration Z-score = {z_triage:+.2f} ({direction} than peer avg of {triage_mean:.1f}m)")

            if triage_iqr > 0 and (triage_val > triage_q3 + 1.5 * triage_iqr or triage_val < triage_q1 - 1.5 * triage_iqr):
                score += 20.0
                explanations.append(f"Triage duration IQR outlier ({triage_val:.1f}m outside peer normal range [{triage_q1:.1f}m - {triage_q3:.1f}m])")

            # 2. Word Count Z-score (Superficial notes outlier)
            wc_val = row["avg_word_count"]
            wc_mean = cohort_df["avg_word_count"].mean()
            wc_std = cohort_df["avg_word_count"].std()
            wc_q1 = cohort_df["avg_word_count"].quantile(0.25)
            wc_q3 = cohort_df["avg_word_count"].quantile(0.75)
            wc_iqr = wc_q3 - wc_q1

            if wc_std and wc_std > 0:
                z_wc = (wc_val - wc_mean) / wc_std
                if z_wc < -1.8:  # significantly fewer words
                    score += 35.0
                    explanations.append(f"Superficial Note Z-score = {z_wc:+.2f} (Avg {wc_val:.1f} words vs peer mean {wc_mean:.1f})")

            outlier_records.append({
                "analyst_id": aid,
                "analyst_name": name,
                "tier": tier,
                "shift_group": shift_group,
                "outlier_score": min(100.0, score),
                "outlier_explanations": explanations
            })

    return pd.DataFrame(outlier_records).drop_duplicates(subset=["analyst_id"])
