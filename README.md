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

The SAT-SA user interface has been built from the ground up for high-density, mission-critical oversight:
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
# Option A: Run with Synthetic Demo Dataset (Default)
python run.py

# Option B: Run with Authentic Public Research Dataset (NSL-KDD)
python run.py --public
```

`run.py` automatically orchestrates:
- Checking Python environment & essential dependencies
- Initializing the local embedded DuckDB database safely
- Ingesting authentic NSL-KDD telemetry records when `--public` is specified
- Launching the **FastAPI REST API** at `http://127.0.0.1:8000` (Swagger UI at `/docs`)
- Launching the **Streamlit Dashboard** at `http://localhost:8501`
- Handling clean, coordinated teardown on `Ctrl+C`

> **Data Reset**: To explicitly reset and re-seed data:
> ```powershell
> python run.py --reset-demo     # Reset to fresh Synthetic Demo dataset
> python run.py --public         # Ingest authentic Public NSL-KDD dataset
> ```

---

## 🧪 Testing & Quantitative Verification

### 1. System Verification Suite (7-Step End-to-End Validation)
```powershell
python run_tests.py
```
Validates DuckDB schema initialization, synthetic dataset generator, 8 capability dimensions, analytics sub-engines, CSE supervisory attention scoring, ground-truth profile verification, and ReportLab PDF generation.

### 2. Full Pytest Integration Suite (16 Automated Tests)
```powershell
pytest
```
Executes complete test suite including public dataset adapter, zero-fabrication verification, and analytics consistency tests.

---

## 📊 Dataset Architecture & Source Modes

SAT-SA supports three distinct, decoupled data operational modes:

### A. Public Research Cybersecurity Dataset (NSL-KDD Benchmark)
For rigorous academic and jury evaluation on legitimate, published cybersecurity telemetry:
- **Dataset**: NSL-KDD Benchmark Security & Intrusion Dataset
- **Publisher**: Canadian Institute for Cybersecurity (CIC), University of New Brunswick (UNB)
- **Academic Citation**: Mahbod Tavallaee, Ebrahim Bagheri, Wei Lu, and Ali A. Ghorbani, *"A Detailed Analysis of the KDD CUP 99 Data Set"*, Proceedings of the 2009 IEEE Symposium on Computational Intelligence for Security and Defense Applications (IEEE CISDA 2009). **DOI: 10.1109/CISDA.2009.5356528**.
- **Source Mirror**: Official academic repository mirror (`defcom17/NSL_KDD`, IEEE CISDA 2009 benchmark).
- **Air-Gapped Local Cache**: Cached locally at `data/public/nsl_kdd_small.csv` for 100% offline air-gapped operation.
- **Record Volume**: 1,011 authentic multi-protocol connection event records (495 attack events across DoS, Probing, U2R, R2L categories; 516 benign baseline flows).
- **Date Range**: Authentic flow-duration sequenced timeline (`2024-01-15T08:00:02` to `2024-01-19T00:07:32`).
- **Strict Data Honesty Guarantee**: Telemetry records are mapped to normalized `cses`, `assets`, and `alerts` tables. Human operational tables (`analysts`, `tickets`, `investigation_notes`, `shift_logs`) remain strictly empty ($N=0$) without fabricating fictional personnel or mock notes.

#### Public Telemetry Analytics Compatibility Matrix
| Supervisory Capability / Analytic Engine | Compatibility Status | Telemetry Source in Public Dataset |
| :--- | :--- | :--- |
| **Threat Detection** | **SUPPORTED** | 495 authentic attack signatures (Neptune, Smurf, Satan, Buffer Overflow, etc.) |
| **Security Operations** | **SUPPORTED** | Connection duration outliers, anomalous TCP termination flags (`REJ`, `S0`, `SF`) |
| **Cyber Resilience** | **SUPPORTED** | Negative-space telemetry across service endpoints, flagging under-reporting nodes |
| **Statistical Outliers & Isolation Forest** | **SUPPORTED** | Continuous flow metrics (duration, source/destination bytes, error rates) |
| **Peer Benchmarking** | **SUPPORTED** | Cross-service infrastructure cohort comparative distributions |
| **Investigation Quality (TF-IDF)** | **NOT ASSESSABLE** | No triage notes in source network telemetry (Zero fabrication) |
| **Escalation Compliance** | **NOT ASSESSABLE** | No ticket escalation workflow in source (Zero fabrication) |
| **Incident Response SLA** | **NOT ASSESSABLE** | No incident case open/close timestamps in source (Zero fabrication) |
| **Operational Discipline** | **NOT ASSESSABLE** | No human analyst shift rosters in source (Zero fabrication) |

### B. Demo / Synthetic Dataset (Validation Baseline)
For prototype demonstration and reproducible evaluation of full-stack supervisory workflows:
- **Purpose**: Evaluates all 8 capability dimensions including human ticketing, SLA compliance, shift handovers, and text similarity.
- Calibrated with injected behavioral profiles across 6 Critical Sector Entities (CSEs) to verify detection rule coverage:
  - **CSE-101**: `MATURE_NORMAL` (Standard compliance baseline — zero attention findings)
  - **CSE-102**: `ESCALATION_WEAKNESS` (Critical alerts unescalated to Tier-2 / CSIRT)
  - **CSE-103**: `RAPID_CLOSURE` (Superficial ticket closures <30 seconds)
  - **CSE-104**: `REPETITIVE_INVESTIGATION` (High TF-IDF copy-paste triage notes)
  - **CSE-105**: `MONITORING_BLIND_SPOT` (Unlogged night shifts & telemetry gaps)
  - **CSE-106**: `METRIC_GAMING` (SLA compliance gaming)

### C. Using Legitimate Real SOC Data
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
│   └── public/                 # Authentic public dataset cache (nsl_kdd_small.csv)
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
│   ├── config.py               # Central Dynamic Provenance & Configuration
│   ├── db/                     # Embedded Database Layer
│   │   ├── connection.py       # Thread-Safe DuckDB Connection Manager
│   │   └── schema.py           # DuckDB Schema Definitions (11 Tables)
│   ├── generator/              # Dataset Pipeline & Ingest Validator
│   │   ├── mock_data.py        # Synthetic Dataset Generator & Validation
│   │   └── public_dataset_adapter.py # Authentic NSL-KDD Ingestion Adapter
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
├── tests/                      # Automated Pytest Suite (16 Tests)
├── ARCHITECTURE.md             # System Architecture & Technical Specifications
├── README.md                   # Platform Documentation & Guide
├── requirements.txt            # Python Dependencies
├── run.py                      # One-Step Unified Startup Launcher
└── run_tests.py                # Standalone System Verification Suite
```
