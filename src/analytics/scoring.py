"""
Explainable Supervisory Attention Indicator Scoring Engine for SAT-SA.
Primary Hierarchy: CSE Assessment -> 8 Capability Dimensions -> Findings -> CSE Attention Indicator.
Disclaimer: Prototype Supervisory Attention Indicator — not an official NCIIPC risk score.
"""

import json
import uuid
from datetime import datetime
import pandas as pd

from src.analytics.dimensions import evaluate_cse_capability_dimensions, DIMENSIONS
from src.analytics.gaps import detect_execution_gaps
from src.analytics.negative_space import detect_negative_space
from src.analytics.outliers import detect_statistical_outliers
from src.analytics.anomaly import detect_multivariate_anomalies
from src.analytics.similarity import detect_repetitive_investigations


# Prototype-configured baseline weights for operational demonstration.
# Note: These weights are configurable prototype defaults and not officially prescribed by NCIIPC.
DEFAULT_DIMENSION_WEIGHTS = {
    "Threat Detection": 0.15,
    "Investigation": 0.15,
    "Escalation": 0.15,
    "Incident Response": 0.15,
    "Security Operations": 0.10,
    "Governance & Oversight": 0.10,
    "Operational Discipline": 0.10,
    "Cyber Resilience": 0.10,
}


def calculate_supervisory_attention_scores(conn):
    """
    Computes primary CSE-level Supervisory Attention Indicators across 8 capability dimensions
    and supporting analyst/ticket scores.
    Returns:
        dict containing:
            - 'cse_scores': DataFrame of CSE attention indicators, rank, priority, and findings.
            - 'analyst_scores': Supporting analyst attention scores.
            - 'ticket_scores': Supporting ticket attention scores.
            - 'findings_df': Full list of structured evidence findings.
            - 'high_similarity_pairs': Detected TF-IDF copy-paste note pairs.
    """
    # 1. Run 8 Capability Dimensions & Findings Engine
    dim_res = evaluate_cse_capability_dimensions(conn)
    df_findings = dim_res["findings_df"]
    df_dim_scores = dim_res["dimension_scores"]

    # 2. Run sub-analytic engines for supporting analyst/ticket evidence
    gaps_res = detect_execution_gaps(conn)
    neg_res = detect_negative_space(conn)
    outliers_df = detect_statistical_outliers(conn)
    anomalies_df = detect_multivariate_anomalies(conn)
    similarity_res = detect_repetitive_investigations(conn)

    ticket_gaps_df = gaps_res["ticket_gaps"]
    analyst_gaps_df = gaps_res["analyst_gap_summary"]

    analyst_neg_df = neg_res["analyst_negative_space"]
    ticket_neg_df = neg_res["ticket_negative_space"]

    ticket_sim_df = similarity_res["ticket_similarity_scores"]
    analyst_sim_df = similarity_res["analyst_similarity_scores"]
    high_sim_pairs = similarity_res["high_similarity_pairs"]

    now_str = datetime.now().isoformat()

    # -------------------------------------------------------------
    # A. PRIMARY CSE SUPERVISORY ATTENTION INDICATORS
    # -------------------------------------------------------------
    df_cses = conn.execute("SELECT cse_id, entity_name, sector, peer_group, criticality, maturity_level FROM cses").df()

    cse_final_list = []

    if not df_cses.empty:
        for _, cse in df_cses.iterrows():
            cid = cse["cse_id"]
            cname = cse["entity_name"]

            # Get dimension scores
            dim_row = df_dim_scores[df_dim_scores["cse_id"] == cid].iloc[0] if not df_dim_scores.empty and cid in df_dim_scores["cse_id"].values else {}

            total_attention_score = 0.0
            dim_breakdown = {}
            for d in DIMENSIONS:
                d_score = float(dim_row.get(d, 0.0))
                weight = DEFAULT_DIMENSION_WEIGHTS.get(d, 0.125)
                total_attention_score += d_score * weight
                dim_breakdown[d] = d_score

            total_attention_score = min(100.0, total_attention_score)

            # Get Findings for this CSE
            cse_findings = df_findings[df_findings["cse_id"] == cid] if not df_findings.empty else pd.DataFrame()
            finding_titles = cse_findings["finding_title"].tolist() if not cse_findings.empty else []

            # Priority level recommendation
            if total_attention_score >= 45.0 or cse["criticality"] == "CRITICAL" and total_attention_score >= 30.0:
                priority_level = "HIGH SUPERVISORY PRIORITY"
            elif total_attention_score >= 20.0:
                priority_level = "MEDIUM SUPERVISORY PRIORITY"
            else:
                priority_level = "ROUTINE OVERSIGHT"

            cse_final_list.append({
                "entity_type": "cse",
                "entity_id": cid,
                "entity_name": cname,
                "sector": cse["sector"],
                "peer_group": cse["peer_group"],
                "criticality": cse["criticality"],
                "maturity_level": cse["maturity_level"],
                "total_score": round(total_attention_score, 2),
                "priority_level": priority_level,
                "dimension_scores_json": json.dumps(dim_breakdown),
                "finding_count": len(finding_titles),
                "explanation_json": json.dumps(finding_titles)
            })

    df_cse_final = pd.DataFrame(cse_final_list).sort_values(by="total_score", ascending=False) if cse_final_list else pd.DataFrame()

    # -------------------------------------------------------------
    # B. SUPPORTING ANALYST ATTENTION SCORES
    # -------------------------------------------------------------
    df_analysts = conn.execute("SELECT analyst_id, cse_id, name, tier, shift_group FROM analysts").df()
    analyst_final_list = []

    if not df_analysts.empty:
        for _, row in df_analysts.iterrows():
            aid = row["analyst_id"]
            name = row["name"]

            gap_score = float(analyst_gaps_df.loc[analyst_gaps_df["analyst_id"] == aid, "avg_gap_score"].values[0]) if not analyst_gaps_df.empty and aid in analyst_gaps_df["analyst_id"].values else 0.0
            neg_score = float(analyst_neg_df.loc[analyst_neg_df["analyst_id"] == aid, "negative_space_score"].values[0]) if not analyst_neg_df.empty and aid in analyst_neg_df["analyst_id"].values else 0.0
            out_score = float(outliers_df.loc[outliers_df["analyst_id"] == aid, "outlier_score"].values[0]) if not outliers_df.empty and aid in outliers_df["analyst_id"].values else 0.0
            anom_score = float(anomalies_df.loc[anomalies_df["analyst_id"] == aid, "anomaly_score"].values[0]) if not anomalies_df.empty and aid in anomalies_df["analyst_id"].values else 0.0
            sim_score = float(analyst_sim_df.loc[analyst_sim_df["analyst_id"] == aid, "repetitive_text_score"].values[0]) if not analyst_sim_df.empty and aid in analyst_sim_df["analyst_id"].values else 0.0

            total_score = min(100.0, (0.25 * gap_score + 0.20 * neg_score + 0.20 * out_score + 0.20 * anom_score + 0.15 * sim_score))

            analyst_final_list.append({
                "entity_type": "analyst",
                "entity_id": aid,
                "cse_id": row["cse_id"],
                "entity_name": name,
                "tier": row["tier"],
                "shift_group": row["shift_group"],
                "total_score": round(total_score, 2),
                "gap_score": round(gap_score, 2),
                "negative_space_score": round(neg_score, 2),
                "outlier_score": round(out_score, 2),
                "anomaly_score": round(anom_score, 2),
                "repetitive_text_score": round(sim_score, 2),
                "explanation_json": json.dumps([f"Analyst Supervisory Attention Score: {total_score:.1f}/100"])
            })

    df_analyst_final = pd.DataFrame(analyst_final_list).sort_values(by="total_score", ascending=False) if analyst_final_list else pd.DataFrame()

    # -------------------------------------------------------------
    # C. SUPPORTING TICKET ATTENTION SCORES
    # -------------------------------------------------------------
    df_tickets = conn.execute("""
        SELECT t.ticket_id, t.cse_id, t.analyst_id, a.name AS analyst_name, t.priority, t.status 
        FROM tickets t
        LEFT JOIN analysts a ON t.analyst_id = a.analyst_id
    """).df()

    ticket_final_list = []
    if not df_tickets.empty:
        for _, row in df_tickets.iterrows():
            t_id = row["ticket_id"]

            gap_s = float(ticket_gaps_df.loc[ticket_gaps_df["ticket_id"] == t_id, "gap_score"].values[0]) if not ticket_gaps_df.empty and t_id in ticket_gaps_df["ticket_id"].values else 0.0
            gap_expl = ticket_gaps_df.loc[ticket_gaps_df["ticket_id"] == t_id, "gap_explanations"].values[0] if not ticket_gaps_df.empty and t_id in ticket_gaps_df["ticket_id"].values else []

            neg_s = float(ticket_neg_df.loc[ticket_neg_df["ticket_id"] == t_id, "negative_space_score"].values[0]) if not ticket_neg_df.empty and t_id in ticket_neg_df["ticket_id"].values else 0.0
            neg_expl = ticket_neg_df.loc[ticket_neg_df["ticket_id"] == t_id, "explanations"].values[0] if not ticket_neg_df.empty and t_id in ticket_neg_df["ticket_id"].values else []

            sim_s = float(ticket_sim_df.loc[ticket_sim_df["ticket_id"] == t_id, "repetitive_text_score"].values[0]) if not ticket_sim_df.empty and t_id in ticket_sim_df["ticket_id"].values else 0.0
            sim_expl = ticket_sim_df.loc[ticket_sim_df["ticket_id"] == t_id, "similarity_explanations"].values[0] if not ticket_sim_df.empty and t_id in ticket_sim_df["ticket_id"].values else []

            tkt_total = min(100.0, (0.45 * gap_s + 0.25 * neg_s + 0.30 * sim_s))
            tkt_factors = gap_expl + neg_expl + sim_expl

            ticket_final_list.append({
                "entity_type": "ticket",
                "entity_id": t_id,
                "cse_id": row["cse_id"],
                "analyst_id": row["analyst_id"],
                "analyst_name": row["analyst_name"],
                "priority": row["priority"],
                "status": row["status"],
                "total_score": round(tkt_total, 2),
                "gap_score": round(gap_s, 2),
                "negative_space_score": round(neg_s, 2),
                "outlier_score": 0.0,
                "anomaly_score": 0.0,
                "repetitive_text_score": round(sim_s, 2),
                "explanation_json": json.dumps(tkt_factors)
            })

    df_ticket_final = pd.DataFrame(ticket_final_list).sort_values(by="total_score", ascending=False) if ticket_final_list else pd.DataFrame()

    # -------------------------------------------------------------
    # D. PERSIST TO DUCKDB
    # -------------------------------------------------------------
    conn.execute("DELETE FROM supervisory_scores")

    db_records = []
    for d in cse_final_list:
        db_records.append({
            "score_id": f"SCR-{uuid.uuid4().hex[:8]}",
            "entity_type": "cse",
            "entity_id": d["entity_id"],
            "calculated_at": now_str,
            "total_score": d["total_score"],
            "gap_score": 0.0,
            "negative_space_score": 0.0,
            "outlier_score": 0.0,
            "anomaly_score": 0.0,
            "repetitive_text_score": 0.0,
            "explanation_json": d["explanation_json"]
        })

    for d in analyst_final_list + ticket_final_list:
        db_records.append({
            "score_id": f"SCR-{uuid.uuid4().hex[:8]}",
            "entity_type": d["entity_type"],
            "entity_id": d["entity_id"],
            "calculated_at": now_str,
            "total_score": d["total_score"],
            "gap_score": d["gap_score"],
            "negative_space_score": d["negative_space_score"],
            "outlier_score": d.get("outlier_score", 0.0),
            "anomaly_score": d.get("anomaly_score", 0.0),
            "repetitive_text_score": d["repetitive_text_score"],
            "explanation_json": d["explanation_json"]
        })

    if db_records:
        df_scores_db = pd.DataFrame(db_records)
        conn.register("df_scores_db", df_scores_db)
        conn.execute("INSERT INTO supervisory_scores SELECT * FROM df_scores_db")

    return {
        "cse_scores": df_cse_final,
        "analyst_scores": df_analyst_final,
        "ticket_scores": df_ticket_final,
        "findings_df": df_findings,
        "dimension_scores": df_dim_scores,
        "high_similarity_pairs": high_sim_pairs
    }
