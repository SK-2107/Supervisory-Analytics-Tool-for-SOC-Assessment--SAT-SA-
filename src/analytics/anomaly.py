"""
Conditional Isolation Forest Anomaly Detection Module for SAT-SA.
Uses multivariate Scikit-Learn IsolationForest model with statistical safeguards and fallbacks.
"""

import pandas as pd
import numpy as np

HAS_ISOLATION_FOREST = False
try:
    from sklearn.ensemble import IsolationForest
    HAS_ISOLATION_FOREST = True
except Exception:
    IsolationForest = None
    HAS_ISOLATION_FOREST = False


def detect_multivariate_anomalies(conn):
    """
    Extracts multivariate features per analyst and runs Isolation Forest with sample size safeguards.
    Returns DataFrame of analyst anomaly scores, confidence metadata, and explanations.
    """
    query = """
        SELECT 
            a.analyst_id,
            a.name AS analyst_name,
            COUNT(t.ticket_id) AS total_tickets,
            SUM(CASE WHEN t.assigned_at IS NOT NULL AND t.closed_at IS NOT NULL AND EPOCH(t.closed_at - t.assigned_at) < 30 THEN 1 ELSE 0 END) AS rapid_closures,
            SUM(CASE WHEN t.closed_at IS NOT NULL AND t.created_at IS NOT NULL AND EPOCH(t.closed_at - t.created_at) > 14400 THEN 1 ELSE 0 END) AS sla_breaches,
            AVG(COALESCE(n.word_count, 0)) AS avg_word_count,
            AVG(CASE WHEN t.assigned_at IS NOT NULL AND t.closed_at IS NOT NULL THEN EPOCH(t.closed_at - t.assigned_at) / 60.0 ELSE 30.0 END) AS avg_triage_mins
        FROM analysts a
        LEFT JOIN tickets t ON a.analyst_id = t.analyst_id
        LEFT JOIN investigation_notes n ON t.ticket_id = n.ticket_id
        GROUP BY a.analyst_id, a.name
    """
    df = conn.execute(query).df()

    if df.empty:
        return pd.DataFrame(columns=[
            "analyst_id", "analyst_name", "anomaly_score", "confidence_level", "anomaly_explanations"
        ])

    sample_size = len(df)
    results = []

    # Attempt Isolation Forest when available and sample size >= 10
    if HAS_ISOLATION_FOREST and sample_size >= 10:
        try:
            feature_cols = ["total_tickets", "rapid_closures", "sla_breaches", "avg_word_count", "avg_triage_mins"]
            X = df[feature_cols].fillna(0.0).values

            clf = IsolationForest(n_estimators=100, contamination=0.15, random_state=42)
            clf.fit(X)

            scores = clf.decision_function(X)
            preds = clf.predict(X)

            for idx, row in df.iterrows():
                aid = row["analyst_id"]
                name = row["analyst_name"]
                raw_score = scores[idx]
                is_anom = preds[idx] == -1

                anomaly_score = max(0.0, min(100.0, (0.2 - raw_score) * 150.0)) if is_anom else max(0.0, (0.1 - raw_score) * 40.0)

                explanations = []
                if is_anom:
                    explanations.append(f"Isolation Forest Multivariate Anomaly (Decision Score: {raw_score:.3f})")
                    if row["rapid_closures"] > 1:
                        explanations.append(f"High rapid closure frequency ({int(row['rapid_closures'])} tickets <30s)")
                    if row["avg_word_count"] < 15:
                        explanations.append(f"Sparse note documentation ({row['avg_word_count']:.1f} avg words)")

                results.append({
                    "analyst_id": aid,
                    "analyst_name": name,
                    "anomaly_score": round(anomaly_score, 2),
                    "confidence_level": "HIGH" if is_anom else "MEDIUM",
                    "anomaly_explanations": explanations
                })

            return pd.DataFrame(results)
        except Exception:
            # Fall back to statistical rules if Isolation Forest runtime raises DLL/AppLocker exceptions
            results = []

    # Safeguard / Fallback: Statistical rule-based anomaly scoring
    for _, row in df.iterrows():
        aid = row["analyst_id"]
        name = row["analyst_name"]
        stat_score = 0.0
        explanations = []

        if row["rapid_closures"] > 2:
            stat_score += 35.0
            explanations.append(f"Statistical Anomaly (Fallback): {int(row['rapid_closures'])} rapid closures (<30s)")
        if row["avg_word_count"] < 12 and row["total_tickets"] > 5:
            stat_score += 30.0
            explanations.append(f"Statistical Anomaly (Fallback): Unusually low note word count ({row['avg_word_count']:.1f} words)")
        if row["sla_breaches"] > 2:
            stat_score += 25.0
            explanations.append(f"Statistical Anomaly (Fallback): High SLA breach count ({int(row['sla_breaches'])} overdue)")

        results.append({
            "analyst_id": aid,
            "analyst_name": name,
            "anomaly_score": round(min(100.0, stat_score), 2),
            "confidence_level": "FALLBACK_STATISTICAL",
            "anomaly_explanations": explanations
        })

    return pd.DataFrame(results)
