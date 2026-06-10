# ClearPath Safety Solutions — Rebuild Runbook

Step-by-step guide to rebuilding the full ClearPath AR Reconciliation POC environment from scratch using the Git integration.

---

## Prerequisites

- Snowflake account with Cortex AI features enabled (paid account required — `AI_PARSE_DOCUMENT` is not available on trial accounts)
- `ADMIN_DB` with Git integration set up (see Step 0)
- Python 3.11+ with `reportlab` installed locally
- Snowflake CLI (`snow`) installed and configured with key-pair auth
- GitHub repo accessible at `https://github.com/sfurstar/ClearPath-AI-Solution`

---

## Step 0 — Snowflake Git Integration (one-time account setup)

Run as `ACCOUNTADMIN` in a Snowflake worksheet:

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

-- Verify repo contents are visible
LS @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/;
```

---

## Step 1 — Generate Invoice PDFs (local Mac)

```bash
cd /path/to/ClearPath-AI-Solution
pip install reportlab
python setup_code/python/Step_2a_generate_invoice_pdfs.py
# Output: 30 PDFs in poc_invoices/
```

---

## Step 2 — Run Setup Scripts via Git Integration

All scripts run via `EXECUTE IMMEDIATE FROM` against the Git repo stage. Fetch first to pull latest:

```sql
ALTER GIT REPOSITORY ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo FETCH;
```

### 2a — Role (run as ACCOUNTADMIN)

```sql
USE ROLE ACCOUNTADMIN;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_1a_Create_Role.sql;
```

### 2b — Objects (run as SYSADMIN)

```sql
USE ROLE SYSADMIN;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_1b_Create_Objects.sql;
```

### 2c — Stage and Tables

```sql
USE ROLE CLEARPATH_AI_POC;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_2b_Create_Stage_Target_Tables.sql;
```

### 2d — Upload Invoices

Upload the 30 PDFs from `poc_invoices/` to the stage. Two options:

**Option A — Snowsight UI:**
Navigate to `Data > Databases > CLEARPATH_AI_POC_DB > RAW_DOCS > Stages > INVOICE_STAGE_SSE`, click `+ Files`, select all PDFs.

**Option B — SnowSQL PUT:**
```bash
snowsql -a <account> -u <user>
```
```sql
PUT 'file:///path/to/poc_invoices/*.pdf'
  @CLEARPATH_AI_POC_DB.RAW_DOCS.INVOICE_STAGE_SSE
  AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
```

Verify:
```sql
LIST @CLEARPATH_AI_POC_DB.RAW_DOCS.INVOICE_STAGE_SSE;
-- Should return 30 rows
```

### 2e — Parse, Extract, Chunk, Validate

```sql
USE ROLE CLEARPATH_AI_POC;

EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_2d_Parse_Invoices.sql;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_2e_Extract_Invoices.sql;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_2f_Chunk_Invoices.sql;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_2g_Validate_Tables.sql;
```

Expected counts after validation: 30 staged files, 30 parsed, 30 extracted, ~150 chunks (5 per invoice).

> **Note:** Before running `Step_2f`, spot-check the parsed text anchors on one invoice:
> ```sql
> SELECT LEFT(PARSED_TEXT, 2000) FROM CLEARPATH_AI_POC_DB.CURATED_DOCS.INVOICE_PARSED
> WHERE DOCUMENT_ID = 'INV-2001.pdf';
> ```
> Confirm `| Bill To |`, `| SKU |`, and `Remit payment by the due date` appear in the text.
> If the anchor strings differ, update the `SPLIT_PART` calls in `Step_2f` accordingly.

### 2f — Curated Finance Views

```sql
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_3a_Create_Curated_Finance_Views.sql;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_3b_Create_Reconciliation_Views.sql;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_3c_Validate_Views.sql;
```

Expected: 4 mismatches surfaced — INV-2003, INV-2009, INV-2023, INV-2030.

### 2g — Cortex Search Service

```sql
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_4a_Create_Cortex_Search_Service.sql;
```

### 2h — Semantic View

```sql
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_5a_Build_Semantic_View.sql;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_5b_Validate_Semantic_View.sql;
```

### 2i — Cortex Agent

```sql
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_6a_Create_Agent.sql;
```

### 2j — Compute Pool and App Stage

```sql
USE ROLE ACCOUNTADMIN;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_7a_Create_Compute_Pool.sql;

USE ROLE CLEARPATH_AI_POC;
EXECUTE IMMEDIATE FROM @ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo/branches/main/setup_code/sql/Step_7b_Create_App_Stage.sql;
```

---

## Step 3 — Deploy the Streamlit App

```bash
cd /path/to/ClearPath-AI-Solution/app
snow streamlit deploy --connection <your-connection-name> --replace
```

The app URL will be returned in the output. Format:
`https://app.snowflake.com/<org>/<account>/#/streamlit-apps/CLEARPATH_AI_POC_DB.APP.STREAMLIT_APP`

---

## Post-Deploy Checks

```sql
-- Verify agent exists
SHOW AGENTS IN SCHEMA CLEARPATH_AI_POC_DB.APP;

-- Verify search service is indexed
DESCRIBE CORTEX SEARCH SERVICE CLEARPATH_AI_POC_DB.SEARCH.INVOICE_SEARCH_SVC;

-- Verify reconciliation mismatches
SELECT INVOICE_ID, RECON_EXCEPTION_DETAIL
FROM CLEARPATH_AI_POC_DB.CURATED_FINANCE.INVOICE_RECON_V
WHERE OVERALL_RECON_STATUS = 'MISMATCH'
ORDER BY INVOICE_ID;

-- Check warehouse auto-suspend settings
SHOW WAREHOUSES LIKE 'CLEARPATH%';
```

---

## Cost Management

```sql
-- Credit consumption by service type
SELECT
    DATE_TRUNC('day', START_TIME) AS consumption_date,
    SERVICE_TYPE,
    SUM(CREDITS_USED) AS credits_used,
    ROUND(SUM(CREDITS_USED) * 2.00, 4) AS estimated_dollars
FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY
WHERE START_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP)
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;
```

**When not actively demoing — suspend the compute pool:**
```sql
ALTER COMPUTE POOL SYSTEM_COMPUTE_POOL_CPU SUSPEND;
```

---

## Key Object Reference

| Object | Full Name |
|--------|-----------|
| Role | `CLEARPATH_AI_POC` |
| Database | `CLEARPATH_AI_POC_DB` |
| App Warehouse | `CLEARPATH_APP_WH` |
| ETL Warehouse | `CLEARPATH_ETL_WH` |
| Invoice Stage | `CLEARPATH_AI_POC_DB.RAW_DOCS.INVOICE_STAGE_SSE` |
| Search Service | `CLEARPATH_AI_POC_DB.SEARCH.INVOICE_SEARCH_SVC` |
| Semantic View | `CLEARPATH_AI_POC_DB.SEMANTIC.CLEARPATH_ANALYST_SV` |
| Agent | `CLEARPATH_AI_POC_DB.APP.CLEARPATH_RECON_AGENT` |
| Streamlit App | `CLEARPATH_AI_POC_DB.APP.STREAMLIT_APP` |
| Git Repo Object | `ADMIN_DB.GIT_REPOS.clearpath_ai_solution_repo` |
