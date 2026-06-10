USE ROLE ACCOUNTADMIN;

-- =========================================================
-- STEP 1A - ACCOUNT BOOTSTRAP
-- Run as ACCOUNTADMIN
-- Purpose:
--   1) Create custom role for the ClearPath AI POC
--   2) Grant AI privileges needed for Cortex features
-- =========================================================

-- ---------------------------------------------------------
-- 1. Create custom role
-- ---------------------------------------------------------
CREATE ROLE IF NOT EXISTS CLEARPATH_AI_POC
  COMMENT = 'Role for the ClearPath Safety Solutions AI reconciliation POC';

-- ---------------------------------------------------------
-- 2. AI privileges for Cortex features
-- ---------------------------------------------------------
GRANT USE AI FUNCTIONS ON ACCOUNT TO ROLE CLEARPATH_AI_POC;

GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE CLEARPATH_AI_POC;

-- ---------------------------------------------------------
-- 3. Verification
-- ---------------------------------------------------------
SHOW ROLES LIKE 'CLEARPATH_AI_POC';
SHOW GRANTS TO ROLE CLEARPATH_AI_POC;
