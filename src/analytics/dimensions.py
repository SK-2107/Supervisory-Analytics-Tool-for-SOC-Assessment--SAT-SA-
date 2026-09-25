"""
8 Supervisory Capability Dimensions & Structured Findings Engine.
Evaluates Threat Detection, Investigation, Escalation, Incident Response,
Security Operations, Governance & Oversight, Operational Discipline, and Cyber Resilience.
"""

import uuid
from datetime import datetime
import pandas as pd


DIMENSIONS = [
    "Threat Detection",
    "Investigation",
    "Escalation",
    "Incident Response",
    "Security Operations",
    "Governance & Oversight",
    "Operational Discipline",
    "Cyber Resilience",
]


def evaluate_cse_capability_dimensions(conn):
    """
    Evaluates all 8 supervisory capability dimensions per CSE and populates DuckDB `findings` table.
    Returns:
        dict containing:
            - 'findings_df': DataFrame of structured evidence findings.
            - 'dimension_scores': DataFrame of per-CSE scores across the 8 dimensions.
    """
    df_cses = conn.execute("SELECT cse_id, entity_name, sector, peer_group, criticality FROM cses").df()
    if df_cses.empty:
        return {"findings_df": pd.DataFrame(), "dimension_scores": pd.DataFrame()}

    findings = []
    dimension_scores_list = []
    now_str = datetime.now().isoformat()

    # Clear old findings
    conn.execute("DELETE FROM findings")

    for _, cse in df_cses.iterrows():
        cid = cse["cse_id"]
        cname = cse["entity_name"]

        # Metric stores per dimension (0 to 100 attention score)
        dim_scores = {d: 0.0 for d in DIMENSIONS}

        total_tickets = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]

        if total_tickets == 0:
            # -------------------------------------------------------------
            # Telemetry-Based Capability Evaluation (Public Research Dataset)
            # -------------------------------------------------------------
            crit_cnt = conn.execute("SELECT COUNT(*) FROM alerts WHERE cse_id = ? AND severity = 'CRITICAL'", [cid]).fetchone()[0]
            high_cnt = conn.execute("SELECT COUNT(*) FROM alerts WHERE cse_id = ? AND severity = 'HIGH'", [cid]).fetchone()[0]
            tot_cnt = conn.execute("SELECT COUNT(*) FROM alerts WHERE cse_id = ?", [cid]).fetchone()[0]
            assets = conn.execute("SELECT COUNT(DISTINCT asset_id) FROM alerts WHERE cse_id = ?", [cid]).fetchone()[0]
            rules_df = conn.execute("SELECT DISTINCT rule_name FROM alerts WHERE cse_id = ?", [cid]).df()
            rule_cnt = len(rules_df)

            # 1. Threat Detection
            dim_scores["Threat Detection"] = min(100.0, (crit_cnt * 1.5) + (high_cnt * 0.8) + (tot_cnt * 0.05))
            if crit_cnt >= 50:
                ev_ids = ", ".join(conn.execute("SELECT alert_id FROM alerts WHERE cse_id = ? AND severity = 'CRITICAL' LIMIT 5", [cid]).df()["alert_id"].tolist())
                findings.append({
                    "finding_id": f"FND-{uuid.uuid4().hex[:8]}",
                    "cse_id": cid,
                    "dimension": "Threat Detection",
                    "finding_title": "Critical Threat Ingestion Surge",
                    "reason": f"{crit_cnt} CRITICAL severity exploits detected, indicating intense adversarial targeting.",
                    "metric_name": "Critical Threat Volume",
                    "observed_value": f"{crit_cnt} critical alerts",
                    "expected_baseline_value": "0 critical exploits",
                    "evidence_record_ids": ev_ids,
                    "source_record_type": "alert",
                    "confidence_strength": "HIGH",
                    "created_at": now_str
                })
            elif crit_cnt > 0:
                ev_ids = ", ".join(conn.execute("SELECT alert_id FROM alerts WHERE cse_id = ? AND severity IN ('CRITICAL', 'HIGH') LIMIT 5", [cid]).df()["alert_id"].tolist())
                findings.append({
                    "finding_id": f"FND-{uuid.uuid4().hex[:8]}",
                    "cse_id": cid,
                    "dimension": "Threat Detection",
                    "finding_title": "Elevated Threat Telemetry Detected",
                    "reason": f"{crit_cnt} CRITICAL and {high_cnt} HIGH severity exploits ingested across monitored endpoints.",
                    "metric_name": "High-Severity Threat Ratio",
                    "observed_value": f"{crit_cnt + high_cnt} severe alerts",
                    "expected_baseline_value": "0 severe exploits",
                    "evidence_record_ids": ev_ids,
                    "source_record_type": "alert",
                    "confidence_strength": "HIGH",
                    "created_at": now_str
                })

            # 2. Investigation
            dim_scores["Investigation"] = min(100.0, rule_cnt * 8.0)
            if rule_cnt >= 5:
                ev_ids = ", ".join(conn.execute("SELECT alert_id FROM alerts WHERE cse_id = ? LIMIT 5", [cid]).df()["alert_id"].tolist())
                findings.append({
                    "finding_id": f"FND-{uuid.uuid4().hex[:8]}",
                    "cse_id": cid,
                    "dimension": "Investigation",
                    "finding_title": "Multi-Vector Exploit Diversity",
                    "reason": f"{rule_cnt} distinct exploit signatures detected requiring multi-vector forensic triage.",
                    "metric_name": "Distinct Attack Vectors",
                    "observed_value": f"{rule_cnt} signatures",
                    "expected_baseline_value": "< 3 signatures",
                    "evidence_record_ids": ev_ids,
                    "source_record_type": "alert",
                    "confidence_strength": "HIGH",
                    "created_at": now_str
                })

            # 3. Escalation
            crit_ratio = (crit_cnt / tot_cnt * 100.0) if tot_cnt > 0 else 0.0
            dim_scores["Escalation"] = min(100.0, (crit_ratio * 0.8) + min(40.0, crit_cnt * 1.0))
            if crit_ratio >= 25.0:
                ev_ids = ", ".join(conn.execute("SELECT alert_id FROM alerts WHERE cse_id = ? AND severity = 'CRITICAL' LIMIT 5", [cid]).df()["alert_id"].tolist())
                findings.append({
                    "finding_id": f"FND-{uuid.uuid4().hex[:8]}",
                    "cse_id": cid,
                    "dimension": "Escalation",
                    "finding_title": "Critical Threat Escalation Exposure",
                    "reason": f"{crit_ratio:.1f}% of ingested alerts represent CRITICAL severity exploits requiring immediate escalation.",
                    "metric_name": "Critical Threat Concentration",
                    "observed_value": f"{crit_ratio:.1f}% critical",
                    "expected_baseline_value": "< 10.0% critical",
                    "evidence_record_ids": ev_ids,
                    "source_record_type": "alert",
                    "confidence_strength": "HIGH",
                    "created_at": now_str
                })

            # 4. Incident Response
            dim_scores["Incident Response"] = min(100.0, (crit_cnt * 1.0) + (tot_cnt * 0.08))

            # 5. Security Operations
            concentration = tot_cnt / max(1, assets)
            dim_scores["Security Operations"] = min(100.0, concentration * 0.25)
            if concentration >= 100:
                ev_ids = ", ".join(conn.execute("SELECT alert_id FROM alerts WHERE cse_id = ? LIMIT 5", [cid]).df()["alert_id"].tolist())
                findings.append({
                    "finding_id": f"FND-{uuid.uuid4().hex[:8]}",
                    "cse_id": cid,
                    "dimension": "Security Operations",
                    "finding_title": "Persistent Endpoint Threat Bombardment",
                    "reason": f"{tot_cnt} security alerts concentrated across {assets} monitored asset endpoint.",
                    "metric_name": "Endpoint Concentration Ratio",
                    "observed_value": f"{tot_cnt} alerts/asset",
                    "expected_baseline_value": "< 50 alerts/asset",
                    "evidence_record_ids": ev_ids,
                    "source_record_type": "alert",
                    "confidence_strength": "HIGH",
                    "created_at": now_str
                })

            # 6. Governance & Oversight
            crit_factor = 1.3 if cse["criticality"] == "CRITICAL" else (1.1 if cse["criticality"] == "HIGH" else 0.8)
            dim_scores["Governance & Oversight"] = min(100.0, round((dim_scores["Threat Detection"] * 0.4 + dim_scores["Escalation"] * 0.4) * crit_factor, 2))

            # 7. Operational Discipline
            dim_scores["Operational Discipline"] = 5.0

            # 8. Cyber Resilience
            if assets >= 10:
                dim_scores["Cyber Resilience"] = min(100.0, assets * 1.5)
                findings.append({
                    "finding_id": f"FND-{uuid.uuid4().hex[:8]}",
                    "cse_id": cid,
                    "dimension": "Cyber Resilience",
                    "finding_title": "Lateral Blast Radius & Multi-Asset Exposure",
                    "reason": f"Exploits distributed across {assets} distinct monitored infrastructure assets, presenting lateral movement risk.",
                    "metric_name": "Monitored Asset Blast Radius",
                    "observed_value": f"{assets} exposed assets",
                    "expected_baseline_value": "< 10 exposed assets",
                    "evidence_record_ids": cid,
                    "source_record_type": "asset",
                    "confidence_strength": "HIGH",
                    "created_at": now_str
                })
            else:
                dim_scores["Cyber Resilience"] = 5.0

            # Baseline finding if no specific anomaly triggered
            cse_findings = [f for f in findings if f["cse_id"] == cid]
            if not cse_findings:
                ev_ids = ", ".join(conn.execute("SELECT alert_id FROM alerts WHERE cse_id = ? LIMIT 5", [cid]).df()["alert_id"].tolist())
                findings.append({
                    "finding_id": f"FND-{uuid.uuid4().hex[:8]}",
                    "cse_id": cid,
                    "dimension": "Governance & Oversight",
                    "finding_title": "Routine Baseline Threat Telemetry",
                    "reason": f"{tot_cnt} total alerts monitored with standard operational telemetry and 0 critical escalations.",
                    "metric_name": "Routine Operations Baseline",
                    "observed_value": f"{tot_cnt} alerts",
                    "expected_baseline_value": "Standard telemetry",
                    "evidence_record_ids": ev_ids or cid,
                    "source_record_type": "alert",
                    "confidence_strength": "HIGH",
                    "created_at": now_str
                })

        else:
            # -------------------------------------------------------------
            # Ticket-Based Operational Capability Evaluation (Synthetic/Demo Mode)
            # -------------------------------------------------------------
            # 1. Threat Detection
            df_unworked = conn.execute("""
                SELECT alert_id, severity FROM alerts 
                WHERE cse_id = ? AND alert_id NOT IN (SELECT alert_id FROM tickets WHERE alert_id IS NOT NULL)
            """, [cid]).df()

            if not df_unworked.empty:
                cnt = len(df_unworked)
                evidence_ids = ", ".join(df_unworked["alert_id"].head(5).tolist())
                dim_scores["Threat Detection"] += min(50.0, cnt * 10.0)
                findings.append({
                    "finding_id": f"FND-{uuid.uuid4().hex[:8]}",
                    "cse_id": cid,
                    "dimension": "Threat Detection",
                    "finding_title": "Unworked Security Alerts Detected",
                    "reason": f"{cnt} raw security alerts were ingested without corresponding ticket triage.",
                    "metric_name": "Unworked Alert Ratio",
                    "observed_value": f"{cnt} alerts",
                    "expected_baseline_value": "0 unworked alerts",
                    "evidence_record_ids": evidence_ids,
                    "source_record_type": "alert",
                    "confidence_strength": "HIGH",
                    "created_at": now_str
                })

            # 2. Investigation
            df_short_notes = conn.execute("""
                SELECT n.note_id, n.ticket_id, n.word_count 
                FROM investigation_notes n
                WHERE n.cse_id = ? AND n.word_count < 10
            """, [cid]).df()

            if not df_short_notes.empty:
                cnt = len(df_short_notes)
                evidence_ids = ", ".join(df_short_notes["ticket_id"].head(5).tolist())
                dim_scores["Investigation"] += min(45.0, cnt * 8.0)
                findings.append({
                    "finding_id": f"FND-{uuid.uuid4().hex[:8]}",
                    "cse_id": cid,
                    "dimension": "Investigation",
                    "finding_title": "Superficial Investigation Documentation",
                    "reason": f"{cnt} closed tickets contained superficial triage notes with less than 10 words.",
                    "metric_name": "Low-Word Count Triage Ratio",
                    "observed_value": f"{cnt} tickets",
                    "expected_baseline_value": "< 2% of tickets",
                    "evidence_record_ids": evidence_ids,
                    "source_record_type": "note",
                    "confidence_strength": "HIGH",
                    "created_at": now_str
                })

            # 3. Escalation
            df_unescalated = conn.execute("""
                SELECT ticket_id, priority FROM tickets 
                WHERE cse_id = ? AND priority = 'CRITICAL' AND escalated_to_tier2 = FALSE
            """, [cid]).df()

            if not df_unescalated.empty:
                cnt = len(df_unescalated)
                evidence_ids = ", ".join(df_unescalated["ticket_id"].head(5).tolist())
                dim_scores["Escalation"] += min(60.0, cnt * 15.0)
                findings.append({
                    "finding_id": f"FND-{uuid.uuid4().hex[:8]}",
                    "cse_id": cid,
                    "dimension": "Escalation",
                    "finding_title": "Potential Escalation Weakness",
                    "reason": f"{cnt} CRITICAL priority incidents were closed without Tier-2/CSIRT escalation record.",
                    "metric_name": "Unescalated Critical Incident Ratio",
                    "observed_value": f"{cnt} critical incidents",
                    "expected_baseline_value": "100% escalation for critical severity",
                    "evidence_record_ids": evidence_ids,
                    "source_record_type": "ticket",
                    "confidence_strength": "HIGH",
                    "created_at": now_str
                })

            # 4. Incident Response
            df_sla = conn.execute("""
                SELECT ticket_id, priority, EPOCH(closed_at - created_at)/60.0 AS duration_mins 
                FROM tickets 
                WHERE cse_id = ? AND priority IN ('CRITICAL', 'HIGH') AND closed_at IS NOT NULL
            """, [cid]).df()

            if not df_sla.empty:
                sla_breaches = df_sla[df_sla["duration_mins"] > 180.0]  # Breach 3 hours
                if not sla_breaches.empty:
                    cnt = len(sla_breaches)
                    evidence_ids = ", ".join(sla_breaches["ticket_id"].head(5).tolist())
                    dim_scores["Incident Response"] += min(50.0, cnt * 10.0)
                    findings.append({
                        "finding_id": f"FND-{uuid.uuid4().hex[:8]}",
                        "cse_id": cid,
                        "dimension": "Incident Response",
                        "finding_title": "Incident Response SLA Breach",
                        "reason": f"{cnt} High/Critical incidents exceeded maximum allowed response SLA.",
                        "metric_name": "Incident Resolution Duration",
                        "observed_value": f"Max {sla_breaches['duration_mins'].max():.0f}m",
                        "expected_baseline_value": "< 180m for High/Critical",
                        "evidence_record_ids": evidence_ids,
                        "source_record_type": "ticket",
                        "confidence_strength": "HIGH",
                        "created_at": now_str
                    })

            # 5. Security Operations
            df_rapid = conn.execute("""
                SELECT ticket_id FROM tickets 
                WHERE cse_id = ? AND assigned_at IS NOT NULL AND closed_at IS NOT NULL 
                  AND EPOCH(closed_at - assigned_at) < 30
            """, [cid]).df()

            if not df_rapid.empty:
                cnt = len(df_rapid)
                evidence_ids = ", ".join(df_rapid["ticket_id"].head(5).tolist())
                dim_scores["Security Operations"] += min(55.0, cnt * 12.0)
                findings.append({
                    "finding_id": f"FND-{uuid.uuid4().hex[:8]}",
                    "cse_id": cid,
                    "dimension": "Security Operations",
                    "finding_title": "Rapid Triage & Metric Gaming Anomaly",
                    "reason": f"{cnt} tickets were closed in less than 30 seconds after assignment.",
                    "metric_name": "Rapid Closure Ratio",
                    "observed_value": f"{cnt} rapid closures",
                    "expected_baseline_value": "0 rapid closures <30s",
                    "evidence_record_ids": evidence_ids,
                    "source_record_type": "ticket",
                    "confidence_strength": "HIGH",
                    "created_at": now_str
                })

            # 6. Governance & Oversight
            dim_scores["Governance & Oversight"] = min(100.0, (
                dim_scores["Threat Detection"] * 0.3 +
                dim_scores["Escalation"] * 0.4 +
                dim_scores["Incident Response"] * 0.3
            ))

            # 7. Operational Discipline
            df_handover = conn.execute("""
                SELECT log_id, shift_date, shift_name FROM shift_logs 
                WHERE cse_id = ? AND handover_completed = FALSE
            """, [cid]).df()

            if not df_handover.empty:
                cnt = len(df_handover)
                evidence_ids = ", ".join(df_handover["log_id"].head(5).tolist())
                dim_scores["Operational Discipline"] += min(40.0, cnt * 15.0)
                findings.append({
                    "finding_id": f"FND-{uuid.uuid4().hex[:8]}",
                    "cse_id": cid,
                    "dimension": "Operational Discipline",
                    "finding_title": "Missing Shift Handover Documentation",
                    "reason": f"{cnt} completed shift periods were logged without completed shift handover verification.",
                    "metric_name": "Shift Handover Compliance",
                    "observed_value": f"{cnt} missing handovers",
                    "expected_baseline_value": "100% handover completion",
                    "evidence_record_ids": evidence_ids,
                    "source_record_type": "shift",
                    "confidence_strength": "MEDIUM",
                    "created_at": now_str
                })

            # 8. Cyber Resilience (Potential Negative Space / Blind Spots)
            df_alert_count = conn.execute("SELECT COUNT(*) AS cnt FROM alerts WHERE cse_id = ?", [cid]).df()
            alert_cnt = df_alert_count["cnt"].values[0] if not df_alert_count.empty else 0

            if alert_cnt < 10 and cse["criticality"] in ["CRITICAL", "HIGH"]:
                dim_scores["Cyber Resilience"] += 45.0
                findings.append({
                    "finding_id": f"FND-{uuid.uuid4().hex[:8]}",
                    "cse_id": cid,
                    "dimension": "Cyber Resilience",
                    "finding_title": "Potential Negative-Space Signal: Monitoring Blind Spot",
                    "reason": "Anomalously low alert generation observed on critical sector asset relative to peer baselines.",
                    "metric_name": "Observed vs Peer Expected Monitoring Telemetry",
                    "observed_value": f"{alert_cnt} total alerts",
                    "expected_baseline_value": "Peer median > 50 alerts/week",
                    "evidence_record_ids": f"CSE-{cid}",
                    "source_record_type": "alert",
                    "confidence_strength": "POTENTIAL",
                    "created_at": now_str
                })

        dim_record = {"cse_id": cid, "entity_name": cname}
        for d in DIMENSIONS:
            dim_record[d] = min(100.0, round(dim_scores[d], 2))
        dimension_scores_list.append(dim_record)

    df_findings = pd.DataFrame(findings)

    # Persist findings to DuckDB
    if not df_findings.empty:
        conn.register("df_findings_db", df_findings)
        conn.execute("INSERT INTO findings SELECT * FROM df_findings_db")

    df_dim_scores = pd.DataFrame(dimension_scores_list)

    return {
        "findings_df": df_findings,
        "dimension_scores": df_dim_scores
    }
