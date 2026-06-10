USE ROLE SYSADMIN;

-- =========================================================
-- STEP 1B - OBJECT BOOTSTRAP
-- Run as SYSADMIN
-- Purpose:
--   1) Create warehouses
--   2) Create database
--   3) Create schemas
--   4) Grant baseline privileges to role
-- =========================================================

-- ---------------------------------------------------------
-- 1. Create warehouses
-- ---------------------------------------------------------
CREATE WAREHOUSE IF NOT EXISTS CLEARPATH_APP_WH
  WAREHOUSE_SIZE = 'SMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Warehouse for Streamlit app, Cortex Search, Analyst, and interactive POC usage';

CREATE WAREHOUSE IF NOT EXISTS CLEARPATH_ETL_WH
  WAREHOUSE_SIZE = 'SMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Warehouse for ingestion, parsing, transforms, and back-end prep jobs';

-- ---------------------------------------------------------
-- 2. Create database
-- ---------------------------------------------------------
CREATE DATABASE IF NOT EXISTS CLEARPATH_AI_POC_DB
  COMMENT = 'Database for the ClearPath Safety Solutions AI reconciliation POC';

-- ---------------------------------------------------------
-- 3. Create schemas
-- ---------------------------------------------------------
USE DATABASE CLEARPATH_AI_POC_DB;

CREATE SCHEMA IF NOT EXISTS RAW_FINANCE
  COMMENT = 'Raw structured ERP data — orders, customers, payments';

CREATE SCHEMA IF NOT EXISTS RAW_DOCS
  COMMENT = 'Raw document metadata and internal stage references for invoice PDFs';

CREATE SCHEMA IF NOT EXISTS CURATED_FINANCE
  COMMENT = 'Curated finance marts and views for revenue and AR analysis';

CREATE SCHEMA IF NOT EXISTS CURATED_DOCS
  COMMENT = 'Parsed, extracted, and chunked invoice document data for retrieval';

CREATE SCHEMA IF NOT EXISTS SEMANTIC
  COMMENT = 'Semantic views for Cortex Analyst';

CREATE SCHEMA IF NOT EXISTS SEARCH
  COMMENT = 'Cortex Search services and related retrieval objects';

CREATE SCHEMA IF NOT EXISTS APP
  COMMENT = 'Streamlit app and application support objects';

-- ---------------------------------------------------------
-- 4. Grant baseline warehouse usage
-- ---------------------------------------------------------
GRANT USAGE, OPERATE ON WAREHOUSE CLEARPATH_APP_WH TO ROLE CLEARPATH_AI_POC;
GRANT USAGE, OPERATE ON WAREHOUSE CLEARPATH_ETL_WH TO ROLE CLEARPATH_AI_POC;

-- ---------------------------------------------------------
-- 5. Grant database usage
-- ---------------------------------------------------------
GRANT USAGE ON DATABASE CLEARPATH_AI_POC_DB TO ROLE CLEARPATH_AI_POC;

-- ---------------------------------------------------------
-- 6. Grant schema usage
-- ---------------------------------------------------------
GRANT USAGE ON ALL SCHEMAS IN DATABASE CLEARPATH_AI_POC_DB TO ROLE CLEARPATH_AI_POC;

-- ---------------------------------------------------------
-- 7. Grant create privileges needed for the POC build
-- ---------------------------------------------------------
GRANT CREATE TABLE ON SCHEMA CLEARPATH_AI_POC_DB.RAW_FINANCE      TO ROLE CLEARPATH_AI_POC;
GRANT CREATE TABLE ON SCHEMA CLEARPATH_AI_POC_DB.RAW_DOCS         TO ROLE CLEARPATH_AI_POC;
GRANT CREATE TABLE ON SCHEMA CLEARPATH_AI_POC_DB.CURATED_FINANCE  TO ROLE CLEARPATH_AI_POC;
GRANT CREATE TABLE ON SCHEMA CLEARPATH_AI_POC_DB.CURATED_DOCS     TO ROLE CLEARPATH_AI_POC;

GRANT CREATE VIEW ON SCHEMA CLEARPATH_AI_POC_DB.CURATED_FINANCE   TO ROLE CLEARPATH_AI_POC;
GRANT CREATE VIEW ON SCHEMA CLEARPATH_AI_POC_DB.CURATED_DOCS      TO ROLE CLEARPATH_AI_POC;

GRANT CREATE SEMANTIC VIEW        ON SCHEMA CLEARPATH_AI_POC_DB.SEMANTIC TO ROLE CLEARPATH_AI_POC;
GRANT CREATE CORTEX SEARCH SERVICE ON SCHEMA CLEARPATH_AI_POC_DB.SEARCH  TO ROLE CLEARPATH_AI_POC;
GRANT CREATE PROCEDURE            ON SCHEMA CLEARPATH_AI_POC_DB.APP      TO ROLE CLEARPATH_AI_POC;
GRANT CREATE STAGE                ON SCHEMA CLEARPATH_AI_POC_DB.RAW_DOCS TO ROLE CLEARPATH_AI_POC;
GRANT CREATE STREAMLIT            ON SCHEMA CLEARPATH_AI_POC_DB.APP      TO ROLE CLEARPATH_AI_POC;

-- ---------------------------------------------------------
-- 8. Future grants for readable curated objects
-- ---------------------------------------------------------
GRANT SELECT ON FUTURE TABLES IN SCHEMA CLEARPATH_AI_POC_DB.CURATED_FINANCE TO ROLE CLEARPATH_AI_POC;
GRANT SELECT ON FUTURE VIEWS  IN SCHEMA CLEARPATH_AI_POC_DB.CURATED_FINANCE TO ROLE CLEARPATH_AI_POC;

GRANT SELECT ON FUTURE TABLES IN SCHEMA CLEARPATH_AI_POC_DB.CURATED_DOCS   TO ROLE CLEARPATH_AI_POC;
GRANT SELECT ON FUTURE VIEWS  IN SCHEMA CLEARPATH_AI_POC_DB.CURATED_DOCS   TO ROLE CLEARPATH_AI_POC;

GRANT SELECT ON FUTURE SEMANTIC VIEWS IN SCHEMA CLEARPATH_AI_POC_DB.SEMANTIC TO ROLE CLEARPATH_AI_POC;

-- ---------------------------------------------------------
-- 9. Transfer ownership to the POC role
-- ---------------------------------------------------------
GRANT OWNERSHIP ON WAREHOUSE CLEARPATH_APP_WH TO ROLE CLEARPATH_AI_POC COPY CURRENT GRANTS;
GRANT OWNERSHIP ON WAREHOUSE CLEARPATH_ETL_WH TO ROLE CLEARPATH_AI_POC COPY CURRENT GRANTS;

GRANT OWNERSHIP ON DATABASE CLEARPATH_AI_POC_DB TO ROLE CLEARPATH_AI_POC COPY CURRENT GRANTS;

GRANT OWNERSHIP ON SCHEMA CLEARPATH_AI_POC_DB.RAW_FINANCE     TO ROLE CLEARPATH_AI_POC COPY CURRENT GRANTS;
GRANT OWNERSHIP ON SCHEMA CLEARPATH_AI_POC_DB.RAW_DOCS        TO ROLE CLEARPATH_AI_POC COPY CURRENT GRANTS;
GRANT OWNERSHIP ON SCHEMA CLEARPATH_AI_POC_DB.CURATED_FINANCE TO ROLE CLEARPATH_AI_POC COPY CURRENT GRANTS;
GRANT OWNERSHIP ON SCHEMA CLEARPATH_AI_POC_DB.CURATED_DOCS    TO ROLE CLEARPATH_AI_POC COPY CURRENT GRANTS;
GRANT OWNERSHIP ON SCHEMA CLEARPATH_AI_POC_DB.SEMANTIC        TO ROLE CLEARPATH_AI_POC COPY CURRENT GRANTS;
GRANT OWNERSHIP ON SCHEMA CLEARPATH_AI_POC_DB.SEARCH          TO ROLE CLEARPATH_AI_POC COPY CURRENT GRANTS;
GRANT OWNERSHIP ON SCHEMA CLEARPATH_AI_POC_DB.APP             TO ROLE CLEARPATH_AI_POC COPY CURRENT GRANTS;

-- ---------------------------------------------------------
-- 10. Verification
-- ---------------------------------------------------------
SHOW WAREHOUSES LIKE 'CLEARPATH%';
SHOW DATABASES LIKE 'CLEARPATH_AI_POC_DB';
SHOW SCHEMAS IN DATABASE CLEARPATH_AI_POC_DB;
SHOW GRANTS TO ROLE CLEARPATH_AI_POC;
