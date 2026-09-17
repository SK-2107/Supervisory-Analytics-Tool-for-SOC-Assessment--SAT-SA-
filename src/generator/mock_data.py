"""
Synthetic SOC Operational Dataset & Data Provenance Generator for SAT-SA (SIH26157).
Generates realistic SOC operational logs mapped to Critical Sector Entities (CSEs) and Asset Inventories
with deliberate ground-truth behavioral profiles for supervisory analytics validation.
"""

import random
from datetime import datetime, timedelta
import pandas as pd


def generate_mock_soc_data(num_days: int = 7, seed: int = 42):
    """
    Generates structured synthetic SOC operational dataset for prototype validation.
    Maintains relational integrity across CSEs -> Assets -> Analysts -> Alerts -> Tickets -> Notes -> Shift Logs.
    """
    random.seed(seed)
    base_time = datetime(2026, 9, 1, 8, 0, 0)

    cses_data = [
        {
            "cse_id": "CSE-101",
            "entity_name": "Northern Grid Transmission Corporation",
            "sector": "Energy & Power",
            "peer_group": "Power-Grid-Operators",
            "criticality": "CRITICAL",
            "maturity_level": "Advanced",
            "ground_truth_profile": "MATURE_NORMAL"
        },
        {
            "cse_id": "CSE-102",
            "entity_name": "National Clearing Bank SOC",
            "sector": "Banking & Finance",
            "peer_group": "Tier-1-Banks",
            "criticality": "CRITICAL",
            "maturity_level": "Intermediate",
            "ground_truth_profile": "ESCALATION_WEAKNESS"
        },
        {
            "cse_id": "CSE-103",
            "entity_name": "Bharat Telecom Backbone Ltd",
            "sector": "Telecommunications",
            "peer_group": "Telecom-Operators",
            "criticality": "HIGH",
            "maturity_level": "Basic",
            "ground_truth_profile": "RAPID_CLOSURE"
        },
        {
            "cse_id": "CSE-104",
            "entity_name": "National Defence Logistics Network",
            "sector": "Defense & Strategic",
            "peer_group": "Defense-Units",
            "criticality": "CRITICAL",
            "maturity_level": "Intermediate",
            "ground_truth_profile": "REPETITIVE_INVESTIGATION"
        },
        {
            "cse_id": "CSE-105",
            "entity_name": "Western State Hydro-Power Board",
            "sector": "Energy & Power",
            "peer_group": "Power-Grid-Operators",
            "criticality": "HIGH",
            "maturity_level": "Basic",
            "ground_truth_profile": "MONITORING_BLIND_SPOT"
        },
        {
            "cse_id": "CSE-106",
            "entity_name": "City Metro Rail Corporation",
            "sector": "Transportation",
            "peer_group": "Transit-Operators",
            "criticality": "MEDIUM",
            "maturity_level": "Basic",
            "ground_truth_profile": "METRIC_GAMING"
        },
    ]
    df_cses = pd.DataFrame(cses_data)

    # 1. Assets Inventory per CSE
    assets_data = []
    asset_templates = [
        ("Domain-Controller", "CRITICAL", "IT Infrastructure"),
        ("SCADA-Gateway", "CRITICAL", "OT Operations"),
        ("Perimeter-Firewall", "HIGH", "Network Security"),
        ("SIEM-Appliance", "CRITICAL", "SOC Operations"),
        ("EDR-Management-Node", "HIGH", "Endpoint Security"),
        ("WAF-Cluster", "MEDIUM", "Web Services")
    ]
    for cse in cses_data:
        cid = cse["cse_id"]
        for idx, (atype, crit, dept) in enumerate(asset_templates, start=1):
            assets_data.append({
                "asset_id": f"AST-{cid}-{idx}",
                "cse_id": cid,
                "hostname": f"{cid.lower()}-{atype.lower()}-0{idx}.internal",
                "ip_address": f"10.{int(cid.split('-')[1]) % 255}.{idx}.10",
                "asset_type": atype,
                "criticality": crit,
                "owner_dept": dept,
                "last_scanned_at": base_time - timedelta(days=random.randint(1, 5))
            })
    df_assets = pd.DataFrame(assets_data)

    # 2. Analysts per CSE
    analyst_name_pool = [
        "Ananya Sharma", "Rohan Mehta", "Priya Nair", "Arjun Reddy", "Kavya Iyer",
        "Vikram Singh", "Sneha Kulkarni", "Aditya Rao", "Neha Gupta", "Karan Malhotra",
        "Divya Menon", "Rajesh Patil", "Meera Krishnan", "Suresh Yadav", "Pooja Verma",
        "Nikhil Joshi", "Anjali Desai", "Manish Chatterjee",
    ]

    analysts_data = []
    name_idx = 0
    for cse in cses_data:
        cid = cse["cse_id"]
        analysts_data.extend([
            {"analyst_id": f"AN-{cid}-1", "cse_id": cid, "name": analyst_name_pool[name_idx % len(analyst_name_pool)], "tier": "Tier-2", "shift_group": "Morning"},
            {"analyst_id": f"AN-{cid}-2", "cse_id": cid, "name": analyst_name_pool[(name_idx + 1) % len(analyst_name_pool)], "tier": "Tier-1", "shift_group": "Morning"},
            {"analyst_id": f"AN-{cid}-3", "cse_id": cid, "name": analyst_name_pool[(name_idx + 2) % len(analyst_name_pool)], "tier": "Tier-1", "shift_group": "Night"},
        ])
        name_idx += 3
    df_analysts = pd.DataFrame(analysts_data)

    legit_notes = [
        "Analyzed firewall logs for host {host}. Source IP {ip} flagged as malicious in threat intel feeds. Blocked IP on perimeter firewall and notified endpoint team.",
        "Verified user authentication attempt. Password reset initiated following 5 consecutive failed attempts. User confirmed legitimate activity via phone verification. Marked as False Positive.",
        "Inspected process execution tree for process {proc}. Executable signed by trusted vendor. No outbound connection detected. Alert closed as Benign.",
        "Investigated suspected phishing email. Email contained suspicious link to credential harvesting domain. Link neutralised, recipient mailbox purged.",
        "High CPU utilization alert triggered on domain controller. Correlated with scheduled backup process. No unauthorized privilege escalation found.",
    ]

    copy_paste_template = (
        "Standard triage completed per SOP-SOC-104. Checked Virustotal IP reputation and internal SIEM database. "
        "No malicious IOC observed in local firewall logs. Closing alert per routine checklist."
    )

    rules = [
        ("BRUTE_FORCE", "HIGH", "SIEM-WAF"),
        ("MALWARE_EXECUTION", "CRITICAL", "EDR-CROWDSTRIKE"),
        ("UNUSUAL_POWERSHELL", "MEDIUM", "WINDOWS-EVENT"),
        ("DATA_EXFIL_ATTEMPT", "CRITICAL", "DLP-FORCEPOINT"),
        ("PORT_SCAN", "LOW", "NIDS-SURICATA"),
        ("SUSPICIOUS_LOGIN", "HIGH", "IAM-OKTA"),
    ]

    alerts = []
    tickets = []
    notes = []
    shift_logs = []

    alert_counter = 1000
    ticket_counter = 5000
    note_counter = 8000

    for day in range(num_days):
        day_date = (base_time + timedelta(days=day)).date()

        for a in analysts_data:
            aid = a["analyst_id"]
            cid = a["cse_id"]
            shift = a["shift_group"]
            s_start = datetime.combine(day_date, datetime.min.time()).replace(hour=8 if shift == "Morning" else 20)
            s_end = datetime.combine(day_date if shift == "Morning" else day_date + timedelta(days=1), datetime.min.time()).replace(hour=16 if shift == "Morning" else 4)

            handover = False if cid == "CSE-105" and day % 2 == 0 else True

            shift_logs.append({
                "log_id": f"LOG-{day}-{aid}",
                "cse_id": cid,
                "analyst_id": aid,
                "shift_date": str(day_date),
                "shift_name": shift,
                "shift_start": s_start,
                "shift_end": s_end,
                "handover_completed": handover,
                "notes_logged": 0,
            })

        for cse in cses_data:
            cid = cse["cse_id"]
            profile = cse["ground_truth_profile"]
            cse_asset_list = [ast for ast in assets_data if ast["cse_id"] == cid]

            for hour in range(24):
                is_night = (hour >= 20 or hour < 4)
                if profile == "MONITORING_BLIND_SPOT" and is_night:
                    continue  # Silent shift gap injected

                curr_time = base_time + timedelta(days=day, hours=hour)
                num_alerts = random.randint(1, 3)

                for _ in range(num_alerts):
                    alert_counter += 1
                    alt_id = f"ALT-{alert_counter}"
                    rule_name, severity, source = random.choice(rules)
                    target_asset = random.choice(cse_asset_list) if cse_asset_list else assets_data[0]

                    alerts.append({
                        "alert_id": alt_id,
                        "cse_id": cid,
                        "asset_id": target_asset["asset_id"],
                        "timestamp": curr_time,
                        "severity": severity,
                        "source_system": source,
                        "rule_name": rule_name,
                        "raw_summary": f"{rule_name} triggered from {source} on asset {target_asset['hostname']} at {cid}"
                    })

                    valid_analysts = [a for a in analysts_data if a["cse_id"] == cid and (a["shift_group"] == "Night" if is_night else a["shift_group"] == "Morning")]
                    analyst = random.choice(valid_analysts) if valid_analysts else analysts_data[0]

                    ticket_counter += 1
                    tkt_id = f"TKT-{ticket_counter}"
                    assigned_at = curr_time + timedelta(minutes=random.randint(2, 15))

                    is_unworked = False
                    is_sla_breach = False
                    is_rapid_close = False
                    is_copy_pasted = False
                    escalated = False

                    if profile == "ESCALATION_WEAKNESS":
                        if severity == "CRITICAL":
                            escalated = False
                            closed_at = assigned_at + timedelta(minutes=45)
                        else:
                            closed_at = assigned_at + timedelta(minutes=30)
                    elif profile == "RAPID_CLOSURE":
                        is_rapid_close = True
                        closed_at = assigned_at + timedelta(seconds=15)
                    elif profile == "REPETITIVE_INVESTIGATION":
                        is_copy_pasted = True
                        closed_at = assigned_at + timedelta(minutes=25)
                    elif profile == "METRIC_GAMING":
                        if random.random() < 0.4:
                            is_sla_breach = True
                            closed_at = assigned_at + timedelta(hours=8)
                        else:
                            closed_at = assigned_at + timedelta(minutes=10)
                    elif profile == "MATURE_NORMAL":
                        closed_at = assigned_at + timedelta(minutes=25)
                        if severity == "CRITICAL":
                            escalated = True
                    else:
                        closed_at = assigned_at + timedelta(minutes=30)

                    status = "CLOSED"
                    tickets.append({
                        "ticket_id": tkt_id,
                        "cse_id": cid,
                        "alert_id": alt_id,
                        "analyst_id": analyst["analyst_id"],
                        "created_at": curr_time,
                        "assigned_at": assigned_at,
                        "closed_at": closed_at,
                        "status": status,
                        "resolution_category": "BENIGN",
                        "priority": severity,
                        "escalated_to_tier2": escalated
                    })

                    note_counter += 1
                    note_id = f"NOTE-{note_counter}"
                    if is_copy_pasted:
                        note_text = copy_paste_template
                    elif is_rapid_close:
                        note_text = "Closed."
                    else:
                        note_text = random.choice(legit_notes).format(
                            host=target_asset["hostname"],
                            ip=target_asset["ip_address"],
                            proc="powershell.exe"
                        )

                    notes.append({
                        "note_id": note_id,
                        "cse_id": cid,
                        "ticket_id": tkt_id,
                        "analyst_id": analyst["analyst_id"],
                        "created_at": assigned_at + timedelta(minutes=1),
                        "note_text": note_text,
                        "char_count": len(note_text),
                        "word_count": len(note_text.split())
                    })

    df_alerts = pd.DataFrame(alerts)
    df_tickets = pd.DataFrame(tickets)
    df_notes = pd.DataFrame(notes)
    df_shift_logs = pd.DataFrame(shift_logs)

    ground_truth = {
        "CSE-101": "MATURE_NORMAL",
        "CSE-102": "ESCALATION_WEAKNESS",
        "CSE-103": "RAPID_CLOSURE",
        "CSE-104": "REPETITIVE_INVESTIGATION",
        "CSE-105": "MONITORING_BLIND_SPOT",
        "CSE-106": "METRIC_GAMING"
    }

    return {
        "cses": df_cses,
        "assets": df_assets,
        "analysts": df_analysts,
        "alerts": df_alerts,
        "tickets": df_tickets,
        "investigation_notes": df_notes,
        "shift_logs": df_shift_logs,
        "ground_truth": ground_truth
    }


def validate_soc_dataset(data: dict) -> dict:
    """
    Validates schema structure, null constraints, and relational foreign-key integrity.
    Returns dictionary containing validation status, error list, and record counts.
    """
    required_tables = ["cses", "assets", "analysts", "alerts", "tickets", "investigation_notes", "shift_logs"]
    errors = []
    warnings = []

    for tbl in required_tables:
        if tbl not in data or data[tbl] is None or (isinstance(data[tbl], pd.DataFrame) and data[tbl].empty):
            errors.append(f"Missing or empty required table: '{tbl}'")

    if errors:
        return {
            "valid": False,
            "error_count": len(errors),
            "errors": errors,
            "warning_count": len(warnings),
            "warnings": warnings,
            "record_counts": {}
        }

    df_cses = data["cses"]
    df_assets = data["assets"]
    df_analysts = data["analysts"]
    df_alerts = data["alerts"]
    df_tickets = data["tickets"]
    df_notes = data["investigation_notes"]
    df_shift_logs = data["shift_logs"]

    # Check relational foreign key integrity
    valid_cse_ids = set(df_cses["cse_id"])
    valid_asset_ids = set(df_assets["asset_id"])
    valid_analyst_ids = set(df_analysts["analyst_id"])
    valid_alert_ids = set(df_alerts["alert_id"])
    valid_ticket_ids = set(df_tickets["ticket_id"])

    invalid_asset_cses = set(df_assets["cse_id"]) - valid_cse_ids
    if invalid_asset_cses:
        errors.append(f"Assets table contains orphan cse_ids: {invalid_asset_cses}")

    invalid_alert_cses = set(df_alerts["cse_id"]) - valid_cse_ids
    if invalid_alert_cses:
        errors.append(f"Alerts table contains orphan cse_ids: {invalid_alert_cses}")

    invalid_alert_assets = set(df_alerts["asset_id"].dropna()) - valid_asset_ids
    if invalid_alert_assets:
        warnings.append(f"Alerts table contains orphan asset_ids: {invalid_alert_assets}")

    invalid_ticket_alerts = set(df_tickets["alert_id"].dropna()) - valid_alert_ids
    if invalid_ticket_alerts:
        errors.append(f"Tickets table contains orphan alert_ids: {invalid_ticket_alerts}")

    invalid_note_tickets = set(df_notes["ticket_id"].dropna()) - valid_ticket_ids
    if invalid_note_tickets:
        errors.append(f"Notes table contains orphan ticket_ids: {invalid_note_tickets}")

    counts = {tbl: len(data[tbl]) for tbl in required_tables}
    is_valid = len(errors) == 0

    return {
        "valid": is_valid,
        "error_count": len(errors),
        "errors": errors,
        "warning_count": len(warnings),
        "warnings": warnings,
        "record_counts": counts
    }


def get_dataset_provenance() -> dict:
    """
    Returns dataset metadata and provenance documentation for prototype validation defensibility.
    """
    return {
        "dataset_name": "Synthetic SOC Operational Dataset for Prototype Validation",
        "version": "1.0.0",
        "description": (
            "Realistic, structured synthetic SOC operational dataset designed strictly according to the SAT-SA schema "
            "for SIH26157 supervisory analytics validation. Contains complete relational integrity linking CSEs, "
            "Asset Inventories, Analysts, Shift Logs, Alerts, Cases/Tickets, and Triage Notes."
        ),
        "environment": "NCIIPC Air-Gapped Prototype Evaluation",
        "data_provenance": "Synthetic generation based on SOC operational workflows and ground-truth behavioral profiles",
        "ground_truth_profiles": {
            "CSE-101": "MATURE_NORMAL (Standard SOC operational compliance)",
            "CSE-102": "ESCALATION_WEAKNESS (Critical alerts unescalated to Tier-2)",
            "CSE-103": "RAPID_CLOSURE (Superficial ticket closures <30s)",
            "CSE-104": "REPETITIVE_INVESTIGATION (High TF-IDF copy-paste triage notes)",
            "CSE-105": "MONITORING_BLIND_SPOT (Unlogged night shifts & telemetry gaps)",
            "CSE-106": "METRIC_GAMING (SLA compliance gaming & delayed resolution)"
        },
        "disclaimer": "Synthetic dataset created for prototype validation — does not contain actual confidential NCIIPC/CSE operational data."
    }


from src.db.schema import init_db


def seed_database(conn, num_days: int = 7):
    """Generates synthetic SOC data and populates DuckDB tables."""
    data = generate_mock_soc_data(num_days=num_days)

    init_db(conn)

    try:
        conn.execute("DELETE FROM supervisory_scores")
        conn.execute("DELETE FROM findings")
        conn.execute("DELETE FROM shift_logs")
        conn.execute("DELETE FROM investigation_notes")
        conn.execute("DELETE FROM tickets")
        conn.execute("DELETE FROM alerts")
        conn.execute("DELETE FROM analysts")
        conn.execute("DELETE FROM assets")
        conn.execute("DELETE FROM cses")
    except Exception:
        pass



    df_cses_db = data["cses"].drop(columns=["ground_truth_profile"], errors="ignore")
    conn.register("df_cses", df_cses_db)
    conn.execute("INSERT INTO cses SELECT * FROM df_cses")

    conn.register("df_assets", data["assets"])
    conn.execute("INSERT INTO assets SELECT * FROM df_assets")

    conn.register("df_analysts", data["analysts"])
    conn.execute("INSERT INTO analysts SELECT * FROM df_analysts")

    conn.register("df_alerts", data["alerts"])
    conn.execute("INSERT INTO alerts SELECT * FROM df_alerts")

    conn.register("df_tickets", data["tickets"])
    conn.execute("INSERT INTO tickets SELECT * FROM df_tickets")

    conn.register("df_notes", data["investigation_notes"])
    conn.execute("INSERT INTO investigation_notes SELECT * FROM df_notes")

    conn.register("df_shift_logs", data["shift_logs"])
    conn.execute("INSERT INTO shift_logs SELECT * FROM df_shift_logs")

    return {
        "cses_count": len(data["cses"]),
        "assets_count": len(data["assets"]),
        "analysts_count": len(data["analysts"]),
        "alerts_count": len(data["alerts"]),
        "tickets_count": len(data["tickets"]),
        "notes_count": len(data["investigation_notes"]),
        "shift_logs_count": len(data["shift_logs"])
    }

