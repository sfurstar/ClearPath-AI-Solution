USE ROLE CLEARPATH_AI_POC;
USE DATABASE CLEARPATH_AI_POC_DB;
USE SCHEMA APP;

-- =========================================================
-- STEP 7B - APP STAGE
-- Creates the stage for Streamlit app file deployment
-- =========================================================

CREATE STAGE IF NOT EXISTS STREAMLIT_STAGE;
