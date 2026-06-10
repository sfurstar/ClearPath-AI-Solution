# ClearPath Safety Solutions — AI-Powered AR Reconciliation

A Snowflake Cortex AI proof-of-concept demonstrating hybrid structured + unstructured invoice reconciliation for a highway and work zone safety products company.

The application combines **Cortex Analyst** (ERP structured data via Text-to-SQL) and **Cortex Search** (AI-parsed PDF invoice retrieval) orchestrated by a **Cortex Agent** — all native to Snowflake, no external tools required.

---

## Business Context

ClearPath Safety Solutions sells highway and work zone safety products (barriers, attenuators, channelizers, delineators, signage) to state DOTs, municipal public works departments, and highway contractors. Their AR team manually reconciles ERP order data against PDF invoices sent to customers each month — a process that is error-prone, time-consuming, and does not scale.

This POC automates that reconciliation and surfaces exceptions automatically, enabling the finance team to focus on resolution rather than detection.

**Seeded reconciliation mismatches in this POC:**

| Invoice | Mismatch Type | ERP Value | Doc Value |
|---------|--------------|-----------|-----------|
| INV-2003 | Quantity discrepancy | 25 drums | 23 drums |
| INV-2009 | Unit price mismatch | $1,250.00 | $1,275.00 |
| INV-2023 | Customer name variant | Meridian Highway Services LLC | Meridian Hwy Services LLC |
| INV-2030 | Payment terms mismatch | NET 30 | NET 45 |

---

## Architecture

```
Sources                  Snowflake (CLEARPATH_AI_POC_DB)
─────────────────────────────────────────────────────────────────────
                         ┌─ SECURITY & ACCESS CONTROL ──────────────┐
PDF Invoices  ──Snowpipe─►  RAW_DOCS.INVOICE_STAGE_SSE              │
                         │    AI_PARSE_DOCUMENT → AI_EXTRACT         │
ERP Orders    ──Kafka────►  RAW_FINANCE (INVOICE/CUSTOMER/PAYMENT)  │
              ──JDBC     │                                            │
                         │  CURATED_FINANCE (views + recon)          │
                         │  CURATED_DOCS (parsed/extracted/chunked)  │
                         │  SEMANTIC (CLEARPATH_ANALYST_SV)          │
                         │  SEARCH (INVOICE_SEARCH_SVC)              │
                         │                                            │
                         │  APP.CLEARPATH_RECON_AGENT                │
                         │    ├─ Cortex Analyst (Text→SQL)           │
                         │    └─ Cortex Search (RAG retrieval)       │
                         │                                            │
                         │  APP.STREAMLIT_APP (SPCS container)       │
                         └─ LOGGING & MONITORING ────────────────────┘
```

**Key design decisions:**
- All AI inference runs inside Snowflake — no data leaves the platform
- Snowpipe `AUTO_INGEST` for event-driven invoice ingestion (production pattern)
- Server-side encrypted stage (`SNOWFLAKE_SSE`) for invoice PDF storage
- Semantic view YAML defines business metrics consumed by both BI tools and the AI agent
- Git-deployed Streamlit app via Snowflake CLI (`snow streamlit deploy`)

---

## Repository Structure

```
ClearPath-AI-Solution/
├── app/
│   ├── streamlit_app.py            # Main Streamlit application
│   ├── snowflake.yml               # Snowflake CLI deployment config
│   ├── pyproject.toml              # Python dependencies
│   └── .streamlit/
│       └── config.toml             # Streamlit server config for container runtime
├── setup_code/
│   ├── python/
│   │   └── Step_2a_generate_invoice_pdfs.py   # Invoice PDF generator (run locally)
│   └── sql/
│       ├── Step_1a_Create_Role.sql
│       ├── Step_1b_Create_Objects.sql
│       ├── Step_2b_Create_Stage_Target_Tables.sql
│       ├── Step_2c_Upload_Invoices.sql
│       ├── Step_2d_Parse_Invoices.sql
│       ├── Step_2e_Extract_Invoices.sql
│       ├── Step_2f_Chunk_Invoices.sql
│       ├── Step_2g_Validate_Tables.sql
│       ├── Step_3a_Create_Curated_Finance_Views.sql
│       ├── Step_3b_Create_Reconciliation_Views.sql
│       ├── Step_3c_Validate_Views.sql
│       ├── Step_4a_Create_Cortex_Search_Service.sql
│       ├── Step_5a_Build_Semantic_View.sql
│       ├── Step_5b_Validate_Semantic_View.sql
│       ├── Step_6a_Create_Agent.sql
│       ├── Step_7a_Create_Compute_Pool.sql
│       └── Step_7b_Create_App_Stage.sql
└── docs/
    └── rebuild-runbook.md
```

---

## Snowflake Objects

| Object | Name |
|--------|------|
| Database | `CLEARPATH_AI_POC_DB` |
| Role | `CLEARPATH_AI_POC` |
| App Warehouse | `CLEARPATH_APP_WH` |
| ETL Warehouse | `CLEARPATH_ETL_WH` |
| Invoice Stage | `RAW_DOCS.INVOICE_STAGE_SSE` |
| Cortex Search Service | `SEARCH.INVOICE_SEARCH_SVC` |
| Semantic View | `SEMANTIC.CLEARPATH_ANALYST_SV` |
| Cortex Agent | `APP.CLEARPATH_RECON_AGENT` |
| Streamlit App | `APP.STREAMLIT_APP` |

---

## Setup Sequence

### Prerequisites
- Snowflake account with Cortex AI features enabled
- Python 3.11+ with `reportlab` installed
- Snowflake CLI (`snow`) installed and configured
- ADMIN_DB with Git integration already set up (see step 0)

### Step 0 — Snowflake Git Integration (run once per account)

```sql
USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS ADMIN_DB;
CREATE SCHEMA IF NOT EXISTS ADMIN_DB.GIT_REPOS;

CREATE OR REPLACE API INTEGRATION github_integration
  API_PROVIDER = git_https_api
  API_ALLOWED_PREFIXES = ('https://github.com/sfurstar/')
  ENABLED = TRUE;

CREATE OR REPLACE GIT REPOSITORY clearpath_ai_solution_repo
  API_INTEGRATION = github_integration
  ORIGIN = 'https://github.com/sfurstar/ClearPath-AI-Solution';

ALTER GIT REPOSITORY clearpath_ai_solution_repo FETCH;
```

### Step 1 — Generate Invoice PDFs (local)

```bash
cd /path/to/ClearPath-AI-Solution
pip install reportlab
python setup_code/python/Step_2a_generate_invoice_pdfs.py
# Creates 30 PDFs in poc_invoices/
```

### Steps 2–7 — Run via Git Integration

After fetching the repo in Snowflake, execute each step in order:

```sql
-- Step 1: Role and objects
USE ROLE ACCOUNTADMIN;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_1a_Create_Role.sql;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_1b_Create_Objects.sql;

-- Step 2: Stage, tables, parse, extract, chunk
USE ROLE CLEARPATH_AI_POC;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_2b_Create_Stage_Target_Tables.sql;
-- Upload invoices via Snowsight UI or SnowSQL PUT (see Step_2c)
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_2d_Parse_Invoices.sql;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_2e_Extract_Invoices.sql;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_2f_Chunk_Invoices.sql;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_2g_Validate_Tables.sql;

-- Step 3: Curated views
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_3a_Create_Curated_Finance_Views.sql;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_3b_Create_Reconciliation_Views.sql;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_3c_Validate_Views.sql;

-- Step 4: Cortex Search
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_4a_Create_Cortex_Search_Service.sql;

-- Step 5: Semantic view
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_5a_Build_Semantic_View.sql;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_5b_Validate_Semantic_View.sql;

-- Step 6: Agent
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_6a_Create_Agent.sql;

-- Step 7: Compute pool and app stage
USE ROLE ACCOUNTADMIN;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_7a_Create_Compute_Pool.sql;
USE ROLE CLEARPATH_AI_POC;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_7b_Create_App_Stage.sql;
```

### Step 8 — Deploy the Streamlit App

```bash
cd app
snow streamlit deploy --connection <your-connection-name> --replace
```

---

## Demo Prompts

**Structured (Cortex Analyst)**
- `What is total revenue by customer for Q1 2026?`
- `Which customers have the highest open balances?`
- `Show me all overdue invoices`

**Document (Cortex Search)**
- `What does invoice INV-2009 say about the total amount due?`
- `What products and quantities are on invoice INV-2001?`
- `What is the due date on invoice INV-2003?`

**Hybrid (both tools)**
- `Compare ERP and invoice document values for INV-2009 — do they differ?`
- `Which invoices have reconciliation mismatches?`
- `Which customers have overdue balances and invoice mismatches?`

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Data Platform | Snowflake |
| AI Orchestration | Cortex Agent (Claude Sonnet) |
| Structured Query | Cortex Analyst + Semantic View |
| Document Retrieval | Cortex Search |
| Document Parsing | `AI_PARSE_DOCUMENT`, `AI_EXTRACT` |
| App Runtime | Streamlit in Snowflake (SPCS container) |
| Deployment | Snowflake CLI + GitHub Git Integration |
| Invoice Generation | Python / ReportLab |

---

## Notes

- `poc_invoices/` and `invoices/` are excluded from the repo via `.gitignore` — generate PDFs locally using `Step_2a`
- The `app/output/` build artifact directory is also excluded
- This POC uses `SYSTEM_COMPUTE_POOL_CPU` which is a Snowflake-managed compute pool — suspend it when not in use to avoid idle charges: `ALTER COMPUTE POOL SYSTEM_COMPUTE_POOL_CPU SUSPEND;`
- Monitor spend via `SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY`
