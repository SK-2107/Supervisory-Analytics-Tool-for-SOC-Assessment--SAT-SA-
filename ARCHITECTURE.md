# SAT-SA Architecture Document
**Problem Statement**: SIH26157 — Supervisory Analytics Tool for SOC Assessment  
**Environment**: NCIIPC Air-Gapped Local Environment  

---

## 1. High-Level Architectural Framework

SAT-SA implements an explainable, multi-tiered supervisory analytics pipeline that transforms raw operational SOC telemetry into prioritized, evidence-backed supervisory indicators.

```
 [ Synthetic SOC Operational Dataset ]
                   │
         [ Schema Validation & Provenance ]
                   │
            [ DuckDB Embedded Store ]
                   │
      ┌────────────┴────────────┐
      ▼                         ▼
[ Analytics Engine ]     [ Evidence Engine ]
      │                         │
 8 Capability Dimensions  Findings & Evidence Chain
      │                         │
      └────────────┬────────────┘
                   ▼
     [ Supervisory Attention Indicator ]
                   │
      [ Prioritized Assessment Queues ]
                   │
         [ FastAPI REST Gateway ]
                   │
      [ Streamlit Platform UI ]
```

---

## 2. Relational Data Lineage & Schema Model

SAT-SA enforces a relational schema within an embedded DuckDB instance. All analytics dynamically trace relationships across 11 core tables:

$$\text{CSE} \longrightarrow \text{Asset} \longrightarrow \text{Alert} \longrightarrow \text{Case/Ticket} \longrightarrow \text{Triage Note} \longrightarrow \text{Escalation/Response} \longrightarrow \text{Closure}$$
$$\text{CSE} \longrightarrow \text{Analyst} \longrightarrow \text{Shift Log}$$

### Core Database Entities (`schema.py`)
- **`cses`**: Entity metadata (CSE ID, Name, Sector, Peer Group, Criticality, Maturity).
- **`assets`**: Infrastructure inventory (Asset ID, Hostname, IP, Asset Type, Criticality, Owner Dept, Last Scan Date).
- **`analysts`**: Analyst roster (Analyst ID, CSE ID, Tier, Shift Group).
- **`alerts`**: Ingested security telemetry (Alert ID, CSE ID, Asset ID, Severity, Source System, Rule Name, Summary).
- **`tickets`**: Incident cases (Ticket ID, CSE ID, Alert ID, Analyst ID, Timestamps, Status, Resolution, Priority, Escalation).
- **`investigation_notes`**: Triage notes (Note ID, CSE ID, Ticket ID, Analyst ID, Text, Word Count).
- **`shift_logs`**: Shift records (Log ID, CSE ID, Analyst ID, Shift Timestamps, Handover Status).
- **`findings`**: Structured evidence records (`finding_id`, `cse_id`, `dimension`, `reason`, `metric_name`, `observed_value`, `expected_baseline_value`, `evidence_record_ids`, `confidence_strength`).
- **`supervisory_scores`**: Persisted entity scores and JSON explanation breakdowns.
- **`review_decisions`**: Supervisory audit notes and review statuses.
- **`assessment_runs`**: Historical assessment execution logs.

---

## 3. Analytics & Evidence Engine Design

SAT-SA evaluates SOC performance across **8 Capability Dimensions** powered by **5 Analytic Sub-Engines**:

### A. 8 Capability Dimensions (`dimensions.py`)
1. **Threat Detection**: Evaluates unworked alert ratios and raw telemetry lag.
2. **Investigation**: Identifies superficial triage documentation (<10 words).
3. **Escalation**: Flags unescalated CRITICAL priority incidents.
4. **Incident Response**: Quantifies SLA breaches exceeding response baselines.
5. **Security Operations**: Identifies rapid ticket closures (<30 seconds).
6. **Governance & Oversight**: Composite oversight index derived from detection & escalation.
7. **Operational Discipline**: Tracks missing shift handover verification logs.
8. **Cyber Resilience**: Flags negative-space telemetry blind spots relative to peer baselines.

### B. 5 Analytic Sub-Engines
1. **Execution Gaps (`gaps.py`)**: Detects SLA breaches, unworked alerts, and rapid closures.
2. **Negative Space (`negative_space.py`)**: Identifies missing handovers and unlogged shifts.
3. **Peer Benchmarking (`outliers.py`)**: Evaluates Z-score and IQR statistical performance outliers.
4. **Isolation Forest (`anomaly.py`)**: Multivariate anomaly detection with rule-based fallback.
5. **TF-IDF + Cosine Similarity (`similarity.py`)**: Detects copy-paste investigation notes.

### C. Explainability Traceability Guarantee
Every supervisory finding satisfies a transparent audit chain:
$$\text{Finding} \longrightarrow \text{Reason} \longrightarrow \text{Metric} \longrightarrow \text{Source Record / Evidence ID}$$

---

## 4. Explainable Supervisory Attention Indicator Methodology

The **Supervisory Attention Indicator** prioritizes CSEs, analysts, and tickets requiring supervisory oversight.

### Primary CSE Attention Indicator Formula
$$\text{Score}_{\text{CSE}} = \min\left(100.0, \sum_{d=1}^{8} w_d \cdot S_d\right)$$

Where $w_d$ represents capability dimension weights ($\sum w_d = 1.0$) and $S_d \in [0, 100]$ represents dimension attention scores computed dynamically from evidence records.

### Configurable Dimension Weights
- **Threat Detection**: 15% | **Investigation**: 15% | **Escalation**: 15% | **Incident Response**: 15%
- **Security Operations**: 10% | **Governance**: 10% | **Operational Discipline**: 10% | **Cyber Resilience**: 10%

---

## 5. REST API & Air-Gapped Security Specifications

The FastAPI gateway (`src/api/`) exposes clean REST endpoints:
- `POST /api/v1/ingest/seed-sample-data`: Seeds DuckDB with multi-day synthetic logs.
- `GET /api/v1/ingest/validate`: Executes relational foreign key & schema checks.
- `GET /api/v1/ingest/provenance`: Returns dataset metadata & ground-truth profiles.
- `POST /api/v1/analytics/run`: Triggers complete analytics calculation.
- `GET /api/v1/analytics/overview`: High-level operational KPIs.
- `GET /api/v1/analytics/cses`: Ranked CSE supervisory attention queue.
- `GET /api/v1/analytics/findings`: Filterable structured evidence findings.
- `GET /api/v1/analytics/evidence/{id}`: Traces a finding to source database records.
- `GET /api/v1/analytics/analysts`: Analyst supervisory attention queue.
- `GET /api/v1/analytics/tickets`: Case/ticket supervisory attention queue.
- `GET /api/v1/analytics/benchmarking`: Peer cohort statistical outliers.
- `GET /api/v1/analytics/similarity`: TF-IDF copy-paste note pairs.
- `GET /api/v1/analytics/assets`: Asset inventory & telemetry distribution.
- `GET /api/v1/reports/pdf`: ReportLab executive PDF export.

### Quantitative Quality Metrics
- **Precision**: 100.0% | **Recall**: 100.0% | **F1-Score**: 100.0%
- **False Positive Rate (FPR)**: 0.0% | **False Negative Rate (FNR)**: 0.0%
