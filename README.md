# Google Ads Performance Reporter

End-to-end data pipeline for Google Ads (Search campaigns) focused on **ROAS-driven decision making** for affiliate marketing accounts.

This project collects Google Ads data via API, stores it in SQLite, applies deterministic rule-based analysis, and generates **actionable recommendations** using a local LLM (no external AI costs).

Designed as a **production-minded portfolio project**, prioritizing correctness, clarity, and operational realism over over-engineering.

---

## 🎯 Project Goals

- Collect reliable Google Ads performance data (multi-account via MCC)
- Ensure **idempotent**, low-cost, repeatable data ingestion
- Apply **explicit and explainable business rules**
- Generate **human-executable recommendations** (no automation)
- Maintain clean architecture and separation of concerns

---

## 🧠 Design Principles

- **Low cost**: SQLite + local LLM (Ollama)
- **Deterministic data layer**: metrics are computed once, never by AI
- **Explainability first**: rules before recommendations
- **Clean boundaries**: API, storage, analysis, and LLM clearly separated
- **Operational realism**: assumes manual execution in Google Ads UI

---

## 🏗️ High-Level Architecture

```text
Google Ads API
      |
      v
Data Fetchers (per client account)
      |
      v
SQLite (data.sqlite)
      |
      v
Rule-Based Analysis (analysis_rules.py)
      |
      v
Structured JSON (analysis_output.json)
      |
      v
Local LLM (Ollama)
      |
      v
Markdown Report (reports/)
```

---

## 📁 Project Structure

```text
.
├── data.sqlite                  # SQLite database (generated)
├── reports/                     # LLM-generated recommendations (gitignored)
│
├── src/
│   ├── run_all.py               # Pipeline orchestrator
│   ├── config.py                # Centralized configuration
│   │
│   ├── data/
│   │   ├── db.py                # DB connection + schema initialization
│   │   ├── schema.sql           # SQLite schema (idempotent)
│   │   └── client_accounts.py   # MCC client account discovery & persistence
│   │
│   ├── fetch_daily_metrics.py   # Campaign-level metrics ingestion
│   ├── fetch_search_terms.py    # Search term performance ingestion
│   │
│   ├── analysis_rules.py        # Rule-based performance analysis
│   └── llm_recommender.py       # Local LLM recommendation generator
│
├── google-ads.yaml               # Google Ads API credentials (not committed)
└── README.md
```

---

## 🔑 Configuration Management

All configuration is centralized in `src/config.py`:

- `db_path`: SQLite database location
- `ads_config_path`: path to `google-ads.yaml`
- `fetch_days`: how many days of data are ingested (e.g. 30)
- `analysis_window_days`: decision window for analysis (e.g. 7)
- `reports_dir`: where LLM outputs are stored

This avoids:
- hardcoded paths
- duplicated constants
- environment-specific bugs

---

## 🔄 Pipeline Flow (Step-by-Step)

### 1️⃣ Sync Client Accounts (MCC)
- Reads `login_customer_id` from `google-ads.yaml`
- Discovers active client accounts under the MCC
- Stores them locally for repeatable runs

### 2️⃣ Fetch Google Ads Data
- Campaign daily metrics
- Search term performance
- Data is fetched **per client account**
- Uses `INSERT ... ON CONFLICT DO UPDATE` to guarantee **idempotency**
- Safe to re-run weekly without creating duplicates

### 3️⃣ Store Data in SQLite
Main tables:
- `campaign_daily`
- `search_term_daily`

Composite primary keys enforce uniqueness per day, account, and entity.

---

## 📊 Rule-Based Analysis

`analysis_rules.py` applies explicit, explainable logic:

### Campaigns
- **Scale winners**
  - ROAS above threshold
  - Minimum conversions
  - Minimum spend
- **Pause / Restructure losers**
  - High spend
  - Zero conversions

### Search Terms
- Identify negative keyword candidates
- Based on clicks, cost, and zero conversions

### Modes
- `HISTORICAL`: long window (e.g. 180 days) for baseline evaluation
- `LIVE`: short window (e.g. 7 days) for weekly operations

Output:
- `analysis_output.json` (structured, deterministic, auditable)

---

## 🤖 LLM Recommendation Layer

`llm_recommender.py`:
- Uses a **local LLM via Ollama**
- Receives **pre-calculated metrics only**
- Does **not** compute metrics or suggest automation
- Produces a human-readable Markdown report

### Why LLM *after* rules?
- Prevents hallucinations
- Keeps decision logic auditable
- Uses AI only for **reasoning and communication**, not math

---

## 🛡️ Reliability & Safety

- Idempotent database writes
- Safe to re-run the pipeline multiple times
- Per-account isolation (one account failure does not block others)
- Credentials are never committed
- Generated reports are excluded from version control

---

## 🧪 Testing Strategy (Planned)

- Unit tests for:
  - Rule evaluation (winners / losers)
  - Threshold behavior
- Integration tests:
  - SQLite ingestion
  - Analysis output structure
- Manual validation:
  - Google Ads UI vs generated recommendations

---

## 🚀 How to Run

```bash
# Create virtualenv and install dependencies
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run full pipeline
python -m src.run_all
```

Outputs:

data.sqlite (updated)

analysis_output.json

reports/recommendations_YYYY-MM-DD.md

📌 Future Improvements
Environment-based analysis mode (LIVE vs HISTORICAL)

Per-account recommendation reports

Batch inserts for very large accounts

CI checks for schema and rule regressions

Optional lightweight dashboard layer

🧠 Author Notes
This project intentionally avoids over-engineering.

It focuses on:

correctness over cleverness

explicit logic over black-box automation

decisions that can actually be executed by humans

Built as a practical demonstration of backend engineering,
data pipelines, and applied decision systems.