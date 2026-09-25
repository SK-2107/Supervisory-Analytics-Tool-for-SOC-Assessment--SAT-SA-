# SAT-SA Architecture Document
**Framework**: National Critical Sector SOC Operations Oversight Framework  
**Environment**: Sovereign Air-Gapped Local Environment  

---

## 1. High-Level Architectural Framework

SAT-SA implements an explainable, multi-tiered supervisory analytics pipeline that transforms raw operational SOC telemetry into prioritized, evidence-backed supervisory indicators.

```
                 ┌──────────────────────────────────────┐
                 │             DATA SOURCE              │
                 │                                      │
                 │  A. CALIBRATED BENCHMARK DATASET     │
                 │  B. AUTHORIZED ORGANIZATIONAL SOC    │
                 └──────────────────┬───────────────────┘
                                    ↓
                 ┌──────────────────────────────────────┐
                 │        RELATIONAL SCHEMA VALIDATOR   │
                 │   (Foreign keys, schema consistency, │
                 │    field-level integrity checks)     │
                 └──────────────────┬───────────────────┘
                                    ↓
                 ┌──────────────────────────────────────┐
                 │         EMBEDDED DUCKDB STORE        │
                 │   (11 normalized relational tables)  │
                 └──────────────────┬───────────────────┘
                                    ↓
              ┌────────────────────────────────────────────┐
              │              ANALYTICS ENGINE              │
              │                                            │
              │ Execution Gap Engine                       │
              │ Negative Space Engine                      │
              │ Statistical Outliers (Z-Score / IQR)       │
              │ Isolation Forest Anomaly Detection         │
              │ TF-IDF Note Similarity (Copy-Paste triage) │
              │ Peer Benchmarking Engine                   │
              │ 8 Capability Dimensions                    │
              └─────────────────────┬──────────────────────┘
                                    ↓
                 ┌──────────────────────────────────────┐
                 │         FINDINGS & EVIDENCE          │
                 │     (Traceable to Source Record IDs) │
                 └──────────────────┬───────────────────┘
                 │
                 │
                 ↓
                 ┌──────────────────────────────────────┐
                 │   SUPERVISORY ATTENTION INDICATOR    │
                 │     (Explainable Prioritization)     │
                 └──────────────────┬───────────────────┘
                                    ↓
                 ┌──────────────────────────────────────┐
                 │    ENTERPRISE STREAMLIT FRONTEND     │
                 │  (Top Nav, Glass-Box UX, Light Theme)│
                 └──────────────────┬───────────────────┘
                                    ↓
                 ┌──────────────────────────────────────┐
                 │           HUMAN SUPERVISOR           │
                 │     (Final Assessment Decision)      │
                 └──────────────────────────────────────┘
```

---

## 2. Relational Data Lineage & Schema Model

SAT-SA enforces a relational schema within an embedded DuckDB instance. All analytics dynamically trace relationships across 11 core tables:

$$\text{CSE} \longrightarrow \text{Asset} \longrightarrow \text{Alert} \longrightarrow \text{Case/Ticket} \longrightarrow \text{Triage Note} \longrightarrow \text{Escalation/Response} \longrightarrow \text{Closure}$$
$$\text{CSE} \longrightarrow \text{Analyst} \longrightarrow \text{Shift Log}$$

### Core Database Entities (`src/db/schema.py`)
- **`cses`**: Entity metadata (CSE ID, Name, Sector, Peer Group, Criticality, Maturity).
- **`assets`**: Infrastructure inventory (Asset ID, Hostname, IP, Asset Type, Criticality, Owner Dept, Last Scan Date).
- **`analysts`**: Analyst roster (Analyst ID, CSE ID, Tier, Shift Group).
- **`alerts`**: Ingested security telemetry (Alert ID, CSE ID, Asset ID, Severity, Source System, Rule Name, Summary).
- **`tickets`**: Incident cases (Ticket ID, CSE ID, Alert ID, Analyst ID, Timestamps, Status, Resolution, Priority, Escalation).
- **`investigation_notes`**: Triage notes (Note ID, CSE ID, Ticket ID, Analyst ID, Text, Word Count).
- **`shift_logs`**: Shift records (Log ID, CSE ID, Analyst ID, Shift Timestamps, Handover Status).
- **`findings`**: Structured evidence records (`finding_id`, `cse_id`, `dimension`, `reason`, `metric_name`, `observed_value`, `expected_baseline_value`, `evidence_record_ids`, `confidence_strength`).
- **`supervisory_scores`**: Persisted entity scores and JSON explanation breakdowns.
- **`review_decisions`**: Supervisory audit notes, status (`OPEN`, `IN REVIEW`, `CONFIRMED`, `DISMISSED`, `ESCALATED`), and timestamps.
- **`assessment_runs`**: Historical assessment execution logs and audit trail.

---

## 3. Analytics & Evidence Engine Design

SAT-SA evaluates SOC performance across **8 Capability Dimensions** powered by **5 Analytic Sub-Engines**:

### A. 8 Capability Dimensions (`src/analytics/dimensions.py`)
1. **Threat Detection**: Evaluates unworked alert ratios and raw telemetry lag.
2. **Investigation**: Identifies superficial triage documentation (<10 words).
3. **Escalation**: Flags unescalated CRITICAL priority incidents.
4. **Incident Response**: Quantifies SLA breaches exceeding response baselines.
5. **Security Operations**: Identifies rapid ticket closures (<30 seconds).
6. **Governance & Oversight**: Composite oversight index derived from detection & escalation.
7. **Operational Discipline**: Tracks missing shift handover verification logs.
8. **Cyber Resilience**: Flags negative-space telemetry blind spots relative to peer baselines.

### B. 5 Analytic Sub-Engines
1. **Execution Gaps (`src/analytics/gaps.py`)**: Detects SLA breaches, unworked alerts, and rapid closures.
2. **Negative Space (`src/analytics/negative_space.py`)**: Identifies missing handovers and unlogged shifts.
3. **Peer Benchmarking (`src/analytics/outliers.py`)**: Evaluates Z-score and IQR statistical performance outliers.
4. **Isolation Forest (`src/analytics/anomaly.py`)**: Multivariate anomaly detection with rule-based fallback.
5. **TF-IDF + Cosine Similarity (`src/analytics/similarity.py`)**: Detects copy-paste investigation notes.

### C. Explainability Traceability Guarantee
Every supervisory finding satisfies a transparent audit chain:
$$\text{Finding} \longrightarrow \text{Reason} \longrightarrow \text{Metric} \longrightarrow \text{Source Record / Evidence ID}$$

---

## 4. Explainable Supervisory Attention Indicator Methodology

The **Supervisory Attention Indicator** prioritizes CSEs, analysts, and tickets requiring supervisory oversight.

### Primary CSE Attention Indicator Formula
$$\text{Score}_{\text{CSE}} = \min\left(100.0, \sum_{d=1}^{8} w_d \cdot S_d\right)$$

Where $w_d$ represents capability dimension weights ($\sum w_d = 1.0$) and $S_d \in [0, 100]$ represents dimension attention scores computed dynamically from evidence records.

### Dimension Weights (Baseline Calibration)
- **Threat Detection**: 15% (Unworked alert ratios, raw telemetry lag)
- **Investigation**: 15% (Superficial documentation, minimal engagement)
- **Escalation**: 15% (Critical incidents unescalated to Tier-2 / CSIRT)
- **Incident Response**: 15% (SLA breaches exceeding response baselines)
- **Security Operations**: 10% (Rapid closures biologically implausible for investigation)
- **Governance & Oversight**: 10% (Cross-dimension systemic degradation)
- **Operational Discipline**: 10% (Missing shift handovers, unlogged shift rotations)
- **Cyber Resilience**: 10% (Sensor blindspots and anomalous volume divergence)

---

## 5. Frontend Architecture & Enterprise Design System

The frontend is implemented in Streamlit as a zero-sidebar, high-density enterprise dashboard structured across three layers:

```
┌──────────────────────────────────────────────────────────────┐
│                    GLOBAL BRAND & STATUS BAR                 │
│  Brand Mark · Entity Period · Last Run · Air-Gapped Status   │
├──────────────────────────────────────────────────────────────┤
│                   TOP-LEVEL NAVIGATION STRIP                 │
│  [Overview] [Entities] [Findings] [Reviews] [Bench] [Data]   │
├──────────────────────────────────────────────────────────────┤
│                   GLOBAL SEARCH CONTROLLER                   │
│  Live multi-table lookup: Entities, Findings, Cases, Staff   │
├──────────────────────────────────────────────────────────────┤
│                       ACTIVE VIEW LAYER                      │
│                                                              │
│  1. Overview: Executive KPI Strip + Priority Entity Cards    │
│  2. Entities: Filterable Registry + Attention Badges         │
│  3. Findings & Evidence: Traceable Gap Records               │
│  4. Review Queue: Human-in-the-Loop Decision Workspace      │
│  5. Benchmarking: Plotly Cohort Comparisons + Medians        │
│  6. Data & Reports: 5-Step Ingestion & Validation Pipeline   │
│  7. Export: ReportLab PDF Exporter + 4 Multi-Table CSVs      │
└──────────────────────────────────────────────────────────────┘
```

### A. Enterprise Design System (`src/ui/styles.py`)
- **Semantic Color Palette**:
  - Primary Brand: Teal `#0D9488` (Dark: `#0F766E`, Light: `#F0FDFA`)
  - Critical Severity: `#DC2626` (Red `#FEF2F2`)
  - High Severity: `#EA580C` (Orange `#FFF7ED`)
  - Moderate Severity: `#D97706` (Amber `#FFFBEB`)
  - Routine / Low: `#16A34A` (Green `#F0FDF4`)
  - Neutral / In Review: `#2563EB` / `#6B7280`
- **Component Classes**:
  - `satsa-card` & `satsa-card-elevated`: Standardized card containers with subtle drop-shadows.
  - `satsa-kpi-block` & `satsa-kpi-hero`: Metric display blocks with dominant typography.
  - `tbl-head`, `tbl-row`, `tbl-row-alt`: Enterprise data tables with alternating row shading.
  - `satsa-badge` & `satsa-status-pill`: Status badges with calibrated contrast ratios.
  - `workflow-steps`: 5-step numbered horizontal pipeline status indicator.

### B. Navigation & Session Router (`src/ui/nav.py`, `src/ui/app.py`)
- State-driven navigation via `st.session_state.page` and helper `go_to(page, **kwargs)`.
- Global search dropdown querying DuckDB across 4 entity types simultaneously.
- Breadcrumb trail tracking drill-downs (e.g. `Overview › Entities › Entity Detail`).

### C. Glass-Box Explainability & Audit Workspace
- **Explainability Checklist**: Every finding renders a 4-point verification panel detailing Priority Context, Workflow Condition, Observed Pattern, and Empirical Source Records.
- **Supervisory Decision Workspace**: Case review interface with human-in-the-loop decision recording (`CONFIRMED`, `IN REVIEW`, `DISMISSED`, `ESCALATED`) persisted directly into the `review_decisions` table in DuckDB.

---

## 6. REST API & Air-Gapped Security Specifications

The FastAPI gateway (`src/api/`) exposes clean REST endpoints:
- `POST /api/v1/ingest/seed-sample-data`: Seeds DuckDB with multi-day calibrated logs.
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

---

## 7. Verification & Ground-Truth Validation Results

```
==================================================
SAT-SA SYSTEM VERIFICATION & VALIDATION SUITE
==================================================
[1/7] Testing DuckDB Schema Initialization...      [PASS]
[2/7] Testing Dataset Generator & Validation...   [PASS]
[3/7] Testing 8 Capability Dimensions Engine...    [PASS]
[4/7] Testing Analytics Sub-Engines...             [PASS]
[5/7] Testing CSE Supervisory Attention Scoring... [PASS]
[6/7] Computing Ground-Truth Verification...       [PASS]
[7/7] Testing ReportLab PDF Audit Exporter...      [PASS]
==================================================
ALL SAT-SA VERIFICATION CHECKS PASSED (7/7)
==================================================
Pytest Suite: 12 passed, 0 failed (100% pass)
```

- **Synthetic Profile Detection Rate**: 100.0% (6/6 Injected CSE Profiles Correctly Evaluated)
- **Rule Detection Consistency**: 100.0%
- **Synthetic Ground-Truth F1-Score**: 100.0%
- **False Positive Rate (FPR)**: 0.0% | **False Negative Rate (FNR)**: 0.0%
