USE ROLE CLEARPATH_AI_POC;
USE WAREHOUSE CLEARPATH_ETL_WH;
USE DATABASE CLEARPATH_AI_POC_DB;
USE SCHEMA CURATED_FINANCE;

-- =========================================================
-- STEP 3B - RECONCILIATION VIEW
-- Joins ERP order data against AI-extracted invoice fields
-- to surface mismatches between ClearPath's ERP and
-- the physical PDF invoices sent to customers.
--
-- Seeded mismatches in this POC:
--   INV-2003 — quantity discrepancy (ERP: 25 drums, doc: 23)
--   INV-2009 — unit price mismatch (ERP: $1,250, doc: $1,275)
--   INV-2023 — customer name variant (ERP: "Meridian Highway
--               Services LLC", doc: "Meridian Hwy Services LLC")
--   INV-2030 — payment terms mismatch (ERP: NET 30, doc: NET 45)
-- =========================================================

CREATE OR REPLACE VIEW INVOICE_RECON_V AS
SELECT
    i.INVOICE_ID,
    i.CUSTOMER_ID,
    c.CUSTOMER_NAME                     AS ERP_CUSTOMER_NAME,
    x.CUSTOMER_NAME                     AS DOC_CUSTOMER_NAME,
    i.INVOICE_DATE                      AS ERP_INVOICE_DATE,
    x.INVOICE_DATE                      AS DOC_INVOICE_DATE,
    i.DUE_DATE                          AS ERP_DUE_DATE,
    x.DUE_DATE                          AS DOC_DUE_DATE,
    c.PAYMENT_TERMS                     AS ERP_PAYMENT_TERMS,
    x.PAYMENT_TERMS                     AS DOC_PAYMENT_TERMS,
    i.AMOUNT                            AS ERP_AMOUNT,
    x.TOTAL_DUE                         AS DOC_AMOUNT,
    i.CURRENCY                          AS ERP_CURRENCY,
    x.CURRENCY                          AS DOC_CURRENCY,
    x.PO_NUMBER                         AS DOC_PO_NUMBER,
    x.DOCUMENT_ID,
    x.RELATIVE_PATH,

    CASE
        WHEN UPPER(TRIM(c.CUSTOMER_NAME))  = UPPER(TRIM(x.CUSTOMER_NAME))  THEN 'MATCH' ELSE 'MISMATCH'
    END AS CUSTOMER_NAME_MATCH,

    CASE
        WHEN i.INVOICE_DATE = x.INVOICE_DATE THEN 'MATCH' ELSE 'MISMATCH'
    END AS INVOICE_DATE_MATCH,

    CASE
        WHEN i.DUE_DATE = x.DUE_DATE THEN 'MATCH' ELSE 'MISMATCH'
    END AS DUE_DATE_MATCH,

    CASE
        WHEN UPPER(TRIM(c.PAYMENT_TERMS)) = UPPER(TRIM(x.PAYMENT_TERMS)) THEN 'MATCH' ELSE 'MISMATCH'
    END AS PAYMENT_TERMS_MATCH,

    CASE
        WHEN i.CURRENCY = x.CURRENCY THEN 'MATCH' ELSE 'MISMATCH'
    END AS CURRENCY_MATCH,

    CASE
        WHEN ABS(COALESCE(i.AMOUNT, 0) - COALESCE(x.TOTAL_DUE, 0)) < 0.01 THEN 'MATCH' ELSE 'MISMATCH'
    END AS AMOUNT_MATCH,

    CASE
        WHEN x.PO_NUMBER IS NOT NULL THEN 'PRESENT' ELSE 'MISSING'
    END AS DOC_PO_NUMBER_STATUS,

    CASE
        WHEN
            UPPER(TRIM(c.CUSTOMER_NAME))  = UPPER(TRIM(x.CUSTOMER_NAME))
            AND i.INVOICE_DATE            = x.INVOICE_DATE
            AND i.DUE_DATE                = x.DUE_DATE
            AND UPPER(TRIM(c.PAYMENT_TERMS)) = UPPER(TRIM(x.PAYMENT_TERMS))
            AND i.CURRENCY                = x.CURRENCY
            AND ABS(COALESCE(i.AMOUNT, 0) - COALESCE(x.TOTAL_DUE, 0)) < 0.01
        THEN 'MATCH'
        ELSE 'MISMATCH'
    END AS OVERALL_RECON_STATUS,

    CASE
        WHEN x.INVOICE_NUMBER IS NULL THEN 'NO_DOCUMENT_EXTRACT'
        WHEN
            UPPER(TRIM(c.CUSTOMER_NAME))  = UPPER(TRIM(x.CUSTOMER_NAME))
            AND i.INVOICE_DATE            = x.INVOICE_DATE
            AND i.DUE_DATE                = x.DUE_DATE
            AND UPPER(TRIM(c.PAYMENT_TERMS)) = UPPER(TRIM(x.PAYMENT_TERMS))
            AND i.CURRENCY                = x.CURRENCY
            AND ABS(COALESCE(i.AMOUNT, 0) - COALESCE(x.TOTAL_DUE, 0)) < 0.01
        THEN 'ERP_AND_DOC_MATCH'
        ELSE
            RTRIM(
                CASE WHEN UPPER(TRIM(c.CUSTOMER_NAME))    <> UPPER(TRIM(x.CUSTOMER_NAME))    THEN 'CUSTOMER_NAME,' ELSE '' END ||
                CASE WHEN i.INVOICE_DATE                  <> x.INVOICE_DATE                  THEN 'INVOICE_DATE,'  ELSE '' END ||
                CASE WHEN i.DUE_DATE                      <> x.DUE_DATE                      THEN 'DUE_DATE,'      ELSE '' END ||
                CASE WHEN UPPER(TRIM(c.PAYMENT_TERMS))    <> UPPER(TRIM(x.PAYMENT_TERMS))    THEN 'PAYMENT_TERMS,' ELSE '' END ||
                CASE WHEN i.CURRENCY                      <> x.CURRENCY                      THEN 'CURRENCY,'      ELSE '' END ||
                CASE WHEN ABS(COALESCE(i.AMOUNT,0) - COALESCE(x.TOTAL_DUE,0)) >= 0.01       THEN 'AMOUNT,'        ELSE '' END ||
                CASE WHEN x.PO_NUMBER IS NOT NULL                                            THEN 'PO_NUMBER_PRESENT_IN_DOC,' ELSE '' END,
                ','
            )
    END AS RECON_EXCEPTION_DETAIL

FROM CLEARPATH_AI_POC_DB.RAW_FINANCE.INVOICE_RAW   i
JOIN CLEARPATH_AI_POC_DB.RAW_FINANCE.CUSTOMER_RAW  c ON i.CUSTOMER_ID = c.CUSTOMER_ID
LEFT JOIN CLEARPATH_AI_POC_DB.CURATED_DOCS.INVOICE_EXTRACT x ON i.INVOICE_ID = x.INVOICE_NUMBER;
