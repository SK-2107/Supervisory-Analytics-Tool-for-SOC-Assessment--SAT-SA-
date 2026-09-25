# SAT-SA — Supervisory Analytics Tool for SOC Assessment
**Framework**: National Critical Sector Entity (CSE) SOC Capability Assessment  
**Organization / Context**: Sovereign Air-Gapped Local Prototype Environment  

---

## 📋 Project Overview & Purpose

**SAT-SA** (Supervisory Analytics Tool for SOC Assessment) is an explainable supervisory analytics platform designed to evaluate and monitor Security Operations Centers (SOCs) across Critical Sector Entities (CSEs). 

It replaces superficial, self-reported compliance checklists with **evidence-backed behavioral analytics** derived from structured operational records across 8 capability dimensions:
1. **Threat Detection**: Evaluates unworked alert ratios and raw telemetry lag.
2. **Investigation**: Identifies superficial triage documentation (<10 words).
3. **Escalation**: Flags unescalated CRITICAL priority incidents.
4. **Incident Response**: Quantifies SLA breaches exceeding response baselines.
5. **Security Operations**: Identifies rapid ticket closures (<30 seconds).
6. **Governance & Oversight**: Composite oversight index derived from detection & escalation.
7. **Operational Discipline**: Tracks missing shift handover verification logs.
8. **Cyber Resilience**: Flags negative-space telemetry blind spots relative to peer baselines.

---

## 🚫 What SAT-SA IS NOT

To maintain clarity during evaluation and deployment, SAT-SA is strictly scoped:
- ❌ **NOT a SIEM**: Does not ingest high-volume raw packet streams or real-time event logs.
- ❌ **NOT a SOC**: Does not perform real-time perimeter defense or active endpoint blocking.
- ❌ **NOT a Real-Time Monitoring Platform**: Performs supervisory periodic and batch assessments on structured operational records.
- ❌ **NOT a Centralized National Monitoring System**: Designed for sovereign, local operational review.
- ❌ **NOT a Live Log Collector**: Operates on structured, normalized incident and operational records.
- ❌ **NOT a Replacement for Human Supervisors**: SAT-SA computes **Supervisory Attention Indicators** to prioritize focused manual reviews; final supervisory assessment decisions remain strictly human-in-the-loop.

---

## 🔒 Air-Gapped & 100% Offline Operation

SAT-SA strictly complies with sovereign, air-gapped environment requirements:
- ❌ **No Internet Connection Required**
- ❌ **No Cloud Dependencies (AWS, Azure, GCP)**
- ❌ **No External SaaS Applications**
- ❌ **No External AI APIs (OpenAI, Anthropic, Gemini, LangChain)**
- ❌ **No Remote Database Connections**
- ❌ **No External Web CDN Scripts**
- ✅ **100% Local Execution** using Python 3.10+, DuckDB (embedded), Scikit-Learn, ReportLab, FastAPI, and Streamlit.

---

## 🖥️ Modernized UI/UX Experience

The SAT-SA user interface has been built for high-density, mission-critical oversight:
- **Enterprise Light Theme**: Clean, distraction-free aesthetic with high-contrast typography, crisp borders, and zero dark-mode/glassmorphism gimmicks.
- **Top-Level Horizontal Navigation**: Replaces heavy sidebars with an un-truncated top navigation strip:
  1. **Overview**: Executive dashboard with dominant Review Queue hero KPI, priority attention entity cards, and capability distribution bars.
  2. **Entities**: Comprehensive entity registry with multi-criteria filters (Sector, Criticality, Attention Level), attention scores, and deep inspection links.
  3. **Findings & Evidence**: Traceable capability gaps, confidence ratings, and direct links to supporting evidence.
  4. **Review Queue**: Operational case review workspace with supervisor decision forms (Confirm, In Review, Dismiss, Escalate) saved locally to DuckDB.
  5. **Benchmarking**: Interactive Plotly bar visualizer displaying peer cohort medians, relative variance, and plain-English operational guidance.
  6. **Data & Reports**: 5-step end-to-end assessment pipeline with dataset integrity indicators, assessment confirmation modal, run logs, and longitudinal trend charts.
  7. **Export**: High-fidelity PDF audit report generation (ReportLab) and 4 structured CSV exports (Findings, Review Queue, Entity Scores, Dimension Matrix).
- **Glass-Box Explainability**: Every flagged item includes a 4-point rationale checklist explaining *why* it was flagged, with exact source record IDs.

---

## ⚙️ Prerequisites & Installation

### Requirements
- **OS**: Windows 10/11, Linux, or macOS
- **Python**: Python 3.10+ (Verified on Python 3.10, 3.11, 3.12, 3.14)
- **Database**: DuckDB (Embedded, zero external configuration required)

### Step 1: Install Dependencies
```powershell
pip install -r requirements.txt
```

---

## 🚀 Quick Start (One-Step Execution)

### Launch FastAPI Backend + Streamlit UI
```powershell
python run.py
```

`run.py` automatically orchestrates:
- Checking Python environment & essential dependencies
- Initializing the local embedded DuckDB database safely with the calibrated benchmark dataset
- Launching the **FastAPI REST API** at `http://127.0.0.1:8000` (Swagger UI at `/docs`)
- Launching the **Streamlit Dashboard** at `http://localhost:8501`
- Handling clean, coordinated teardown on `Ctrl+C`

> **Data Reset**: To explicitly reset and re-seed the benchmark dataset:
> ```powershell
> python run.py --reset-demo
> ```

---

## 🧪 Testing & Quantitative Verification

### 1. System Verification Suite (7-Step End-to-End Validation)
```powershell
python run_tests.py
```
Validates DuckDB schema initialization, synthetic dataset generator, 8 capability dimensions, analytics sub-engines, CSE supervisory attention scoring, ground-truth profile verification, and ReportLab PDF generation.

### 2. Full Pytest Integration Suite (12 Automated Tests)
```powershell
pytest
```
Executes complete test suite including analytics algorithms, relational validation rules, and FastAPI REST endpoints.

---

## 📊 Dataset Architecture & Behavioral Calibration

SAT-SA operates on a calibrated operational dataset designed for reproducible evaluation of full-stack supervisory workflows:

### A. Calibrated Demonstration Dataset (Injected Behavioral Profiles)
- **Purpose**: Evaluates all 8 capability dimensions including human ticketing, SLA compliance, shift handovers, and text similarity.
- Calibrated with injected behavioral profiles across 6 Critical Sector Entities (CSEs) to verify detection rule coverage:
  - **CSE-101**: `MATURE_NORMAL` (Standard compliance baseline — zero attention findings)
  - **CSE-102**: `ESCALATION_WEAKNESS` (Critical alerts unescalated to Tier-2 / CSIRT)
  - **CSE-103**: `RAPID_CLOSURE` (Superficial ticket closures <30 seconds)
  - **CSE-104**: `REPETITIVE_INVESTIGATION` (High TF-IDF copy-paste triage notes)
  - **CSE-105**: `MONITORING_BLIND_SPOT` (Unlogged night shifts & telemetry gaps)
  - **CSE-106**: `METRIC_GAMING` (SLA compliance gaming)

### B. Using Legitimate Real SOC Data
When authorized organizational SOC operational records become available:
1. **Format**: Structured records in `.csv` or `.json` matching the normalized table schemas (`cses`, `assets`, `analysts`, `alerts`, `tickets`, `investigation_notes`, `shift_logs`).
2. **Ingestion**: Upload via the Data & Reports UI tab, or POST to `/api/v1/ingest/upload`.
3. **Validation**: Relational foreign key and schema checks ensure data integrity before inserting into DuckDB.
4. **Zero Code Changes**: The normalized internal schema ensures analytics engines and UI operate without modification.

---

## 📁 Project Directory Structure

```
SAT-SA/
├── data/                       # Local DuckDB storage (sat_sa.duckdb)
├── src/                        # Platform Source Code
│   ├── analytics/              # Analytics & Scoring Engines
│   │   ├── anomaly.py          # Isolation Forest & Statistical Anomaly Engine
│   │   ├── dimensions.py       # 8 Capability Dimensions & Findings Engine
│   │   ├── gaps.py             # Execution Gaps Detection (SLA, Triage Speed)
│   │   ├── negative_space.py   # Negative Space Signals (Handover, Blindspots)
│   │   ├── outliers.py         # Peer Benchmarking Outliers (Z-Score & IQR)
│   │   ├── scoring.py          # Supervisory Attention Indicator Scoring
│   │   └── similarity.py       # TF-IDF Cosine Similarity Note Matcher
│   ├── api/                    # FastAPI REST Gateway
│   │   ├── main.py             # FastAPI App Entrypoint & Lifespan
│   │   ├── models.py           # Pydantic Request/Response Models
│   │   └── routes/             # REST Endpoints (ingest, analytics, reports)
│   ├── config.py               # Central Data Source & Configuration
│   ├── db/                     # Embedded Database Layer
│   │   ├── connection.py       # Thread-Safe DuckDB Connection Manager
│   │   └── schema.py           # DuckDB Schema Definitions (11 Tables)
│   ├── generator/              # Dataset Pipeline & Ingest Validator
│   │   └── mock_data.py        # Calibrated Dataset Generator & Validation
│   ├── reporting/              # Audit Exporter
│   │   └── pdf_generator.py    # ReportLab Executive PDF Exporter
│   └── ui/                     # Modernized Streamlit Supervisory UI
│       ├── app.py              # Main Application Router & Entrypoint
│       ├── db_helper.py        # Direct DuckDB Access & Query Helpers
│       ├── nav.py              # Top-Navigation Strip & Live Search
│       ├── styles.py           # Enterprise Light Theme CSS & Tokens
│       └── pages/              # 7 Core Views & Inspection Panels
│           ├── overview.py     # Supervisory Command Center
│           ├── entities.py     # Entities Register & Filtering
│           ├── entity_detail.py# Entity Deep-Dive Inspection Panel
│           ├── findings.py     # Findings & Evidence Directory
│           ├── finding_detail.py # Glass-Box Explainability Detail View
│           ├── reviews.py      # Supervisory Review Queue & Decision Form
│           ├── benchmarking.py # Peer Cohort Benchmarking (Plotly)
│           ├── assessment.py   # 5-Step Assessment Workflow Pipeline
│           └── reports.py      # PDF & CSV Audit Data Exports
├── tests/                      # Automated Pytest Suite (12 Tests)
├── ARCHITECTURE.md             # System Architecture & Technical Specifications
├── README.md                   # Platform Documentation & Guide
├── requirements.txt            # Python Dependencies
├── run.py                      # One-Step Unified Startup Launcher
└── run_tests.py                # Standalone System Verification Suite
```
