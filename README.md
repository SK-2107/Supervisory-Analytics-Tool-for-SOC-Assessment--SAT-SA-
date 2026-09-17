# SAT-SA — Supervisory Analytics Tool for SOC Assessment
**Problem Statement**: SIH26157 | Critical Sector Entity (CSE) SOC Capability Assessment  
**Environment**: NCIIPC Air-Gapped Local Prototype Environment  

---

## 📋 System Overview

**SAT-SA** (Supervisory Analytics Tool for SOC Assessment) is an explainable supervisory analytics platform designed to evaluate and monitor Security Operations Centers (SOCs) across Critical Sector Entities (CSEs). 

It replaces superficial, self-reported compliance checklists with **evidence-backed behavioral analytics** derived from operational logs across 8 capability dimensions:
1. **Threat Detection**
2. **Investigation**
3. **Escalation**
4. **Incident Response**
5. **Security Operations**
6. **Governance & Oversight**
7. **Operational Discipline**
8. **Cyber Resilience**

---

## 🔒 Air-Gapped & Offline Compliance

SAT-SA strictly satisfies NCIIPC offline supervisory requirements:
- ❌ **No Cloud Dependencies**
- ❌ **No External SaaS Applications**
- ❌ **No Third-Party AI / LLM APIs**
- ❌ **No Internet Connectivity Required**
- ✅ **100% Local Execution** using Python 3.14, DuckDB, NumPy, Scikit-Learn, ReportLab, FastAPI, and Streamlit.

---

## ⚙️ Prerequisites & Environment Setup

### System Requirements
- **OS**: Windows 10/11, Linux, or macOS
- **Python**: Python 3.10+ (Recommended: Python 3.14)
- **Database**: DuckDB (Embedded, zero external configuration required)

### Step 1: Clone / Navigate to Workspace
```powershell
cd "G:\My Drive\SIH_SOC_Prototype"
```

### Step 2: Install Dependencies
Install all required packages from `requirements.txt`:
```powershell
pip install -r requirements.txt
```

---

## 🚀 Quick Start Instructions

### Running the Complete Platform (Backend + Frontend)

#### Step 1: Launch FastAPI REST Backend
Open a terminal and start the Uvicorn server:
```powershell
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```
*API Interactive Swagger Documentation will be available at:* `http://127.0.0.1:8000/docs`

#### Step 2: Launch Streamlit Platform UI
Open a second terminal and start the Streamlit frontend:
```powershell
streamlit run src/ui/app.py
```
*The platform UI will automatically open in your browser at:* `http://localhost:8501`

---

## 🧪 Running the Verification & Test Suite

SAT-SA includes a comprehensive verification suite validating database schemas, analytics sub-engines, capability dimensions, ground-truth quality metrics, and ReportLab PDF exporters.

### System Verification Script
Execute the 7-step system verification suite:
```powershell
python run_tests.py
```

### Full Pytest Integration Suite
Execute unit and API integration tests:
```powershell
python -m pytest
```

---

## 📁 Project Directory Structure

```
G:\My Drive\SIH_SOC_Prototype\
├── data/                       # Local DuckDB storage (sat_sa.duckdb)
├── src/                        # Platform Source Code
│   ├── analytics/              # Analytics & Scoring Engines
│   │   ├── anomaly.py          # Isolation Forest Multivariate Anomaly Engine
│   │   ├── dimensions.py       # 8 Capability Dimensions & Findings Engine
│   │   ├── gaps.py             # Execution Gaps Detection (SLA, Triage)
│   │   ├── negative_space.py   # Negative Space Signals (Handover, Blindspots)
│   │   ├── outliers.py         # Peer Benchmarking Outliers (Z-Score & IQR)
│   │   ├── scoring.py          # Supervisory Attention Indicator Scoring
│   │   └── similarity.py       # TF-IDF Cosine Text Similarity Detector
│   ├── api/                    # FastAPI REST Application
│   │   ├── main.py             # FastAPI App Entrypoint & Lifespan
│   │   └── routes/             # REST Endpoints (ingest, analytics, reports)
│   ├── db/                     # Database Layer
│   │   ├── connection.py       # DuckDB Connection Manager & Recovery
│   │   └── schema.py           # DuckDB Schema Definitions (11 Tables)
│   ├── generator/              # Synthetic Dataset Pipeline
│   │   └── mock_data.py        # Relational Dataset Generator & Validation
│   ├── reporting/              # Audit Exporter
│   │   └── pdf_generator.py    # ReportLab Executive PDF Exporter
│   └── ui/                     # Streamlit Executive Dashboard UI
│       ├── app.py              # Main Streamlit App Router
│       ├── db_helper.py        # Data Access Helpers
│       ├── nav.py              # Top-Navigation Component
│       ├── styles.py           # Light Enterprise Theme CSS
│       └── pages/              # Platform Views (Overview, CSEs, Findings, etc.)
├── tests/                      # Pytest Integration & Unit Test Suite
├── ARCHITECTURE.md             # 2-Page Architectural Framework Document
├── README.md                   # Setup Instructions & Documentation
├── requirements.txt            # Python Dependencies
└── run_tests.py                # Standalone System Verification Suite
```

---

## 📊 Dataset Provenance & Prototype Validation

The prototype operates on a **"Synthetic SOC Operational Dataset for Prototype Validation"** (v1.0.0). 
It generates realistic SOC operational workflows containing ground-truth behavioral profiles for 6 Critical Sector Entities (CSEs):
- **CSE-101**: `MATURE_NORMAL` (Standard compliance baseline)
- **CSE-102**: `ESCALATION_WEAKNESS` (Critical incidents unescalated to Tier-2)
- **CSE-103**: `RAPID_CLOSURE` (Superficial ticket closures <30 seconds)
- **CSE-104**: `REPETITIVE_INVESTIGATION` (Copy-paste investigation notes)
- **CSE-105**: `MONITORING_BLIND_SPOT` (Unlogged night shifts & telemetry gaps)
- **CSE-106**: `METRIC_GAMING` (SLA compliance gaming)
