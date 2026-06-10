USE ROLE CLEARPATH_AI_POC;
USE WAREHOUSE CLEARPATH_APP_WH;
USE DATABASE CLEARPATH_AI_POC_DB;
USE SCHEMA SEMANTIC;

-- =========================================================
-- STEP 5A - SEMANTIC VIEW
-- Defines the Cortex Analyst semantic layer over the
-- ClearPath curated finance views
-- =========================================================

CREATE OR REPLACE SEMANTIC VIEW CLEARPATH_AI_POC_DB.SEMANTIC.CLEARPATH_ANALYST_SV
TABLES (
  customer_balance AS CLEARPATH_AI_POC_DB.CURATED_FINANCE.CUSTOMER_BALANCE_SUM_V
    PRIMARY KEY (CUSTOMER_ID),

  revenue_monthly AS CLEARPATH_AI_POC_DB.CURATED_FINANCE.CUSTOMER_REVENUE_MTH_V
    UNIQUE (CUSTOMER_ID, REVENUE_MONTH, REVENUE_CATEGORY),

  open_ar AS CLEARPATH_AI_POC_DB.CURATED_FINANCE.OPEN_ACCT_RECV_BY_INV_V
    PRIMARY KEY (INVOICE_ID),

  ar_aging AS CLEARPATH_AI_POC_DB.CURATED_FINANCE.ACCT_RECV_AGING
    PRIMARY KEY (INVOICE_ID),

  invoice_recon AS CLEARPATH_AI_POC_DB.CURATED_FINANCE.INVOICE_RECON_V
    PRIMARY KEY (INVOICE_ID)
)
RELATIONSHIPS (
  revenue_monthly (CUSTOMER_ID) REFERENCES customer_balance,
  open_ar         (CUSTOMER_ID) REFERENCES customer_balance,
  ar_aging        (INVOICE_ID)  REFERENCES open_ar,
  invoice_recon   (INVOICE_ID)  REFERENCES open_ar
)
FACTS (
  revenue_monthly.revenue_amount_row   AS revenue_monthly.revenue_amount,
  open_ar.invoice_amount_row           AS open_ar.invoice_amount,
  open_ar.paid_amount_row              AS open_ar.paid_amount,
  open_ar.open_amount_row              AS open_ar.open_amount,
  invoice_recon.erp_amount_row         AS invoice_recon.erp_amount,
  invoice_recon.doc_amount_row         AS invoice_recon.doc_amount
)
DIMENSIONS (
  customer_balance.customer_id         AS customer_balance.customer_id,
  customer_balance.customer_name       AS customer_balance.customer_name,
  customer_balance.region              AS customer_balance.region,
  customer_balance.industry            AS customer_balance.industry,

  revenue_monthly.revenue_month        AS revenue_monthly.revenue_month,
  revenue_monthly.revenue_category     AS revenue_monthly.revenue_category,

  open_ar.invoice_id                   AS open_ar.invoice_id,
  open_ar.invoice_date                 AS open_ar.invoice_date,
  open_ar.due_date                     AS open_ar.due_date,
  open_ar.currency                     AS open_ar.currency,
  open_ar.ar_status                    AS open_ar.ar_status,
  open_ar.payment_terms                AS open_ar.payment_terms,

  ar_aging.aging_bucket                AS ar_aging.aging_bucket,
  ar_aging.days_past_due               AS ar_aging.days_past_due,

  invoice_recon.overall_recon_status   AS invoice_recon.overall_recon_status,
  invoice_recon.recon_exception_detail AS invoice_recon.recon_exception_detail,
  invoice_recon.doc_po_number_status   AS invoice_recon.doc_po_number_status
)
METRICS (
  customer_balance.customer_count          AS COUNT(customer_balance.customer_id),
  customer_balance.invoice_count_total     AS SUM(customer_balance.invoice_count),
  customer_balance.total_invoiced_amount   AS SUM(customer_balance.total_invoiced_amount),
  customer_balance.total_paid_amount       AS SUM(customer_balance.total_paid_amount),
  customer_balance.total_open_amount       AS SUM(customer_balance.total_open_amount),
  customer_balance.total_overdue_amount    AS SUM(customer_balance.total_overdue_amount),

  revenue_monthly.revenue_amount_total     AS SUM(revenue_monthly.revenue_amount_row),

  open_ar.invoice_amount_total             AS SUM(open_ar.invoice_amount_row),
  open_ar.paid_amount_total                AS SUM(open_ar.paid_amount_row),
  open_ar.open_amount_total                AS SUM(open_ar.open_amount_row),
  open_ar.open_invoice_count               AS COUNT(open_ar.invoice_id),

  invoice_recon.mismatch_invoice_count     AS SUM(IFF(invoice_recon.overall_recon_status = 'MISMATCH', 1, 0)),
  invoice_recon.match_invoice_count        AS SUM(IFF(invoice_recon.overall_recon_status = 'MATCH', 1, 0)),
  invoice_recon.erp_amount_total           AS SUM(invoice_recon.erp_amount_row),
  invoice_recon.doc_amount_total           AS SUM(invoice_recon.doc_amount_row)
)
COMMENT = 'Semantic view for ClearPath Safety Solutions — order revenue, accounts receivable, and invoice reconciliation'
AI_SQL_GENERATION 'Use customer-level finance definitions consistently. Open amount means invoice amount minus posted payments. Total revenue refers to recognized revenue from CUSTOMER_REVENUE_MTH_V, not invoice amount. Overdue means open amount is greater than zero and due date is before the current date. ClearPath invoices contain product line items (SKUs, quantities, unit prices); total amount due is the sum of all line items. For mismatch questions use INVOICE_RECON_V and explain which field differs.'
AI_QUESTION_CATEGORIZATION 'Questions about revenue, monthly revenue, customer revenue, open balances, overdue invoices, AR aging, and invoice mismatches are in scope. If a question asks for invoice document text, SKU details, product descriptions, or supporting invoice passages, that should be answered by Cortex Search instead of this semantic view.'
;

GRANT SELECT ON SEMANTIC VIEW CLEARPATH_AI_POC_DB.SEMANTIC.CLEARPATH_ANALYST_SV TO ROLE CLEARPATH_AI_POC;

SHOW SEMANTIC VIEWS IN SCHEMA CLEARPATH_AI_POC_DB.SEMANTIC;

-- Validation queries
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
    invoice_recon.overall_recon_status
  METRICS
    invoice_recon.mismatch_invoice_count,
    invoice_recon.match_invoice_count
);
