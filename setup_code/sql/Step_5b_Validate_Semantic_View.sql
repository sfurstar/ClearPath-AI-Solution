USE ROLE CLEARPATH_AI_POC;
USE WAREHOUSE CLEARPATH_APP_WH;
USE DATABASE CLEARPATH_AI_POC_DB;
USE SCHEMA SEMANTIC;

SELECT *
FROM SEMANTIC_VIEW(
  CLEARPATH_AI_POC_DB.SEMANTIC.CLEARPATH_ANALYST_SV
  DIMENSIONS
    customer_balance.customer_name,
    customer_balance.region
  METRICS
    customer_balance.total_open_amount,
    customer_balance.total_overdue_amount
)
ORDER BY total_open_amount DESC
LIMIT 20;

SELECT *
FROM SEMANTIC_VIEW(
  CLEARPATH_AI_POC_DB.SEMANTIC.CLEARPATH_ANALYST_SV
  DIMENSIONS
    revenue_monthly.revenue_month,
    customer_balance.customer_name
  METRICS
    revenue_monthly.revenue_amount_total
)
ORDER BY revenue_month, customer_name;

SELECT *
FROM SEMANTIC_VIEW(
  CLEARPATH_AI_POC_DB.SEMANTIC.CLEARPATH_ANALYST_SV
  DIMENSIONS
    invoice_recon.overall_recon_status
  METRICS
    invoice_recon.mismatch_invoice_count,
    invoice_recon.match_invoice_count
);
