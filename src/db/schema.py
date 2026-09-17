"""
DuckDB Database Schema Definition for SAT-SA.
Supports Critical Sector Entity (CSE) assessment, asset inventory, 8 capability dimensions, evidence findings, review decisions, and assessment runs.
"""

CREATE_CSES_TABLE = """
CREATE TABLE IF NOT EXISTS cses (
    cse_id VARCHAR PRIMARY KEY,
    entity_name VARCHAR NOT NULL,
    sector VARCHAR NOT NULL,
    peer_group VARCHAR NOT NULL,
    criticality VARCHAR NOT NULL,
    maturity_level VARCHAR NOT NULL
);
"""

CREATE_ASSETS_TABLE = """
CREATE TABLE IF NOT EXISTS assets (
    asset_id VARCHAR PRIMARY KEY,
    cse_id VARCHAR REFERENCES cses(cse_id),
    hostname VARCHAR NOT NULL,
    ip_address VARCHAR NOT NULL,
    asset_type VARCHAR NOT NULL,
    criticality VARCHAR NOT NULL,
    owner_dept VARCHAR NOT NULL,
    last_scanned_at TIMESTAMP
);
"""

CREATE_ANALYSTS_TABLE = """
CREATE TABLE IF NOT EXISTS analysts (
    analyst_id VARCHAR PRIMARY KEY,
    cse_id VARCHAR REFERENCES cses(cse_id),
    name VARCHAR NOT NULL,
    tier VARCHAR NOT NULL,
    shift_group VARCHAR NOT NULL
);
"""

CREATE_ALERTS_TABLE = """
CREATE TABLE IF NOT EXISTS alerts (
    alert_id VARCHAR PRIMARY KEY,
    cse_id VARCHAR REFERENCES cses(cse_id),
    asset_id VARCHAR REFERENCES assets(asset_id),
    timestamp TIMESTAMP NOT NULL,
    severity VARCHAR NOT NULL,
    source_system VARCHAR NOT NULL,
    rule_name VARCHAR NOT NULL,
    raw_summary TEXT
);
"""

CREATE_TICKETS_TABLE = """
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id VARCHAR PRIMARY KEY,
    cse_id VARCHAR REFERENCES cses(cse_id),
    alert_id VARCHAR REFERENCES alerts(alert_id),
    analyst_id VARCHAR REFERENCES analysts(analyst_id),
    created_at TIMESTAMP NOT NULL,
    assigned_at TIMESTAMP,
    closed_at TIMESTAMP,
    status VARCHAR NOT NULL,
    resolution_category VARCHAR,
    priority VARCHAR NOT NULL,
    escalated_to_tier2 BOOLEAN DEFAULT FALSE
);
"""

CREATE_INVESTIGATION_NOTES_TABLE = """
CREATE TABLE IF NOT EXISTS investigation_notes (
    note_id VARCHAR PRIMARY KEY,
    cse_id VARCHAR REFERENCES cses(cse_id),
    ticket_id VARCHAR REFERENCES tickets(ticket_id),
    analyst_id VARCHAR REFERENCES analysts(analyst_id),
    created_at TIMESTAMP NOT NULL,
    note_text TEXT NOT NULL,
    char_count INTEGER,
    word_count INTEGER
);
"""

CREATE_SHIFT_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS shift_logs (
    log_id VARCHAR PRIMARY KEY,
    cse_id VARCHAR REFERENCES cses(cse_id),
    analyst_id VARCHAR REFERENCES analysts(analyst_id),
    shift_date DATE NOT NULL,
    shift_name VARCHAR NOT NULL,
    shift_start TIMESTAMP NOT NULL,
    shift_end TIMESTAMP NOT NULL,
    handover_completed BOOLEAN NOT NULL DEFAULT FALSE,
    notes_logged INTEGER DEFAULT 0
);
"""

CREATE_FINDINGS_TABLE = """
CREATE TABLE IF NOT EXISTS findings (
    finding_id VARCHAR PRIMARY KEY,
    cse_id VARCHAR REFERENCES cses(cse_id),
    dimension VARCHAR NOT NULL,
    finding_title VARCHAR NOT NULL,
    reason TEXT NOT NULL,
    metric_name VARCHAR NOT NULL,
    observed_value VARCHAR NOT NULL,
    expected_baseline_value VARCHAR NOT NULL,
    evidence_record_ids TEXT NOT NULL,
    source_record_type VARCHAR NOT NULL,
    confidence_strength VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL
);
"""

CREATE_SUPERVISORY_SCORES_TABLE = """
CREATE TABLE IF NOT EXISTS supervisory_scores (
    score_id VARCHAR PRIMARY KEY,
    entity_type VARCHAR NOT NULL, -- 'cse', 'analyst', or 'ticket'
    entity_id VARCHAR NOT NULL,
    calculated_at TIMESTAMP NOT NULL,
    total_score DOUBLE NOT NULL,
    gap_score DOUBLE NOT NULL,
    negative_space_score DOUBLE NOT NULL,
    outlier_score DOUBLE NOT NULL,
    anomaly_score DOUBLE NOT NULL,
    repetitive_text_score DOUBLE NOT NULL,
    explanation_json TEXT NOT NULL
);
"""

CREATE_REVIEW_DECISIONS_TABLE = """
CREATE TABLE IF NOT EXISTS review_decisions (
    review_id VARCHAR PRIMARY KEY,
    ticket_id VARCHAR NOT NULL,
    cse_id VARCHAR,
    status VARCHAR NOT NULL DEFAULT 'OPEN',
    decision VARCHAR,
    supervisor_notes TEXT,
    updated_at TIMESTAMP NOT NULL,
    updated_by VARCHAR DEFAULT 'SOC Supervisor'
);
"""

CREATE_ASSESSMENT_RUNS_TABLE = """
CREATE TABLE IF NOT EXISTS assessment_runs (
    run_id VARCHAR PRIMARY KEY,
    run_date TIMESTAMP NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'Completed',
    entities_count INTEGER NOT NULL,
    alerts_count INTEGER NOT NULL,
    tickets_count INTEGER NOT NULL,
    findings_count INTEGER NOT NULL,
    high_attention_count INTEGER NOT NULL,
    duration_seconds DOUBLE DEFAULT 0.0
);
"""

ALL_SCHEMAS = [
    CREATE_CSES_TABLE,
    CREATE_ASSETS_TABLE,
    CREATE_ANALYSTS_TABLE,
    CREATE_ALERTS_TABLE,
    CREATE_TICKETS_TABLE,
    CREATE_INVESTIGATION_NOTES_TABLE,
    CREATE_SHIFT_LOGS_TABLE,
    CREATE_FINDINGS_TABLE,
    CREATE_SUPERVISORY_SCORES_TABLE,
    CREATE_REVIEW_DECISIONS_TABLE,
    CREATE_ASSESSMENT_RUNS_TABLE,
]


def init_db(conn):
    """Initializes all database tables in DuckDB connection."""
    for schema_sql in ALL_SCHEMAS:
        conn.execute(schema_sql)
    try:
        conn.execute("ALTER TABLE alerts ADD COLUMN asset_id VARCHAR")
    except Exception:
        pass

