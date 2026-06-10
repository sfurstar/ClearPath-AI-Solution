USE ROLE ACCOUNTADMIN;

-- =========================================================
-- STEP 7A - COMPUTE POOL
-- Creates the SPCS compute pool for the Streamlit
-- container runtime app
-- =========================================================

CREATE COMPUTE POOL IF NOT EXISTS SYSTEM_COMPUTE_POOL_CPU
  MIN_NODES = 1
  MAX_NODES = 2
  INSTANCE_FAMILY = 'CPU_XSMALL';
