USE ROLE CLEARPATH_AI_POC;
USE WAREHOUSE CLEARPATH_ETL_WH;
USE DATABASE CLEARPATH_AI_POC_DB;
USE SCHEMA CURATED_DOCS;

-- =========================================================
-- STEP 2F - CHUNK INVOICES
-- Splits parsed ClearPath invoice text into semantic chunks
-- for Cortex Search indexing.
--
-- ClearPath invoice structure:
--   HEADER   — company header, invoice number, dates
--   SUMMARY  — Bill To, Order Summary (customer, terms, PO)
--   LINE_ITEMS — SKU table (SKU, Description, Qty, Unit Price, Line Total)
--   TOTALS   — Subtotal, Tax, Total Amount Due
--   FACTS    — Structured key-value summary for exact match queries
-- =========================================================

TRUNCATE TABLE INVOICE_CHUNK;

INSERT INTO INVOICE_CHUNK (
    CHUNK_ID,
    DOCUMENT_ID,
    RELATIVE_PATH,
    INVOICE_NUMBER,
    CUSTOMER_NAME,
    DUE_DATE,
    TOTAL_DUE,
    CHUNK_TYPE,
    CHUNK_INDEX,
    CHUNK_TEXT
)
WITH base AS (
    SELECT
        p.DOCUMENT_ID,
        p.RELATIVE_PATH,
        p.PARSED_TEXT,
        e.INVOICE_NUMBER,
        e.CUSTOMER_NAME,
        e.DUE_DATE,
        e.TOTAL_DUE,
        e.INVOICE_DATE,
        e.PAYMENT_TERMS,
        e.PO_NUMBER
    FROM CLEARPATH_AI_POC_DB.CURATED_DOCS.INVOICE_PARSED  p
    LEFT JOIN CLEARPATH_AI_POC_DB.CURATED_DOCS.INVOICE_EXTRACT e
      ON p.DOCUMENT_ID = e.DOCUMENT_ID
),

-- Structured key-value facts — used for exact lookups
facts_chunk AS (
    SELECT
        DOCUMENT_ID || '-FACTS'    AS CHUNK_ID,
        DOCUMENT_ID,
        RELATIVE_PATH,
        INVOICE_NUMBER,
        CUSTOMER_NAME,
        DUE_DATE,
        TOTAL_DUE,
        'FACTS'                    AS CHUNK_TYPE,
        1                          AS CHUNK_INDEX,
        TRIM(
            'Invoice Number: '    || COALESCE(INVOICE_NUMBER, '')                        || CHAR(10) ||
            'Customer Name: '     || COALESCE(CUSTOMER_NAME, '')                         || CHAR(10) ||
            'Invoice Date: '      || COALESCE(TO_VARCHAR(INVOICE_DATE, 'YYYY-MM-DD'), '') || CHAR(10) ||
            'Due Date: '          || COALESCE(TO_VARCHAR(DUE_DATE, 'YYYY-MM-DD'), '')     || CHAR(10) ||
            'Total Amount Due: '  || COALESCE(TO_VARCHAR(TOTAL_DUE, '99999990.00'), '')   || CHAR(10) ||
            'Payment Terms: '     || COALESCE(PAYMENT_TERMS, '')                         || CHAR(10) ||
            'PO Number: '         || COALESCE(PO_NUMBER, '')
        ) AS CHUNK_TEXT
    FROM base
),

-- Header section: company info, invoice number, dates (before Bill To)
header_chunk AS (
    SELECT
        DOCUMENT_ID || '-HEADER'   AS CHUNK_ID,
        DOCUMENT_ID,
        RELATIVE_PATH,
        INVOICE_NUMBER,
        CUSTOMER_NAME,
        DUE_DATE,
        TOTAL_DUE,
        'HEADER'                   AS CHUNK_TYPE,
        2                          AS CHUNK_INDEX,
        TRIM(
            SPLIT_PART(PARSED_TEXT, '| Bill To |', 1)
        ) AS CHUNK_TEXT
    FROM base
),

-- Summary section: Bill To, Order Summary, customer/terms/PO (before SKU table)
summary_chunk AS (
    SELECT
        DOCUMENT_ID || '-SUMMARY'  AS CHUNK_ID,
        DOCUMENT_ID,
        RELATIVE_PATH,
        INVOICE_NUMBER,
        CUSTOMER_NAME,
        DUE_DATE,
        TOTAL_DUE,
        'SUMMARY'                  AS CHUNK_TYPE,
        3                          AS CHUNK_INDEX,
        TRIM(
            '| Bill To |' ||
            SPLIT_PART(
                SPLIT_PART(PARSED_TEXT, '| Bill To |', 2),
                '|  SKU | Description |', 1
            )
        ) AS CHUNK_TEXT
    FROM base
),

-- Line items section: SKU table with product descriptions, quantities, prices
line_items_chunk AS (
    SELECT
        DOCUMENT_ID || '-LINEITEMS' AS CHUNK_ID,
        DOCUMENT_ID,
        RELATIVE_PATH,
        INVOICE_NUMBER,
        CUSTOMER_NAME,
        DUE_DATE,
        TOTAL_DUE,
        'LINE_ITEMS'                AS CHUNK_TYPE,
        4                           AS CHUNK_INDEX,
        TRIM(
            '|  SKU | Description |' ||
            SPLIT_PART(
                SPLIT_PART(PARSED_TEXT, '|  SKU | Description |', 2),
                'Remit payment by the due date',
                1
            )
        ) AS CHUNK_TEXT
    FROM base
),

-- Totals section: Subtotal, Tax, Total Amount Due
totals_chunk AS (
    SELECT
        DOCUMENT_ID || '-TOTALS'   AS CHUNK_ID,
        DOCUMENT_ID,
        RELATIVE_PATH,
        INVOICE_NUMBER,
        CUSTOMER_NAME,
        DUE_DATE,
        TOTAL_DUE,
        'TOTALS'                   AS CHUNK_TYPE,
        5                          AS CHUNK_INDEX,
        TRIM(
            'Remit payment by the due date' ||
            SPLIT_PART(
                SPLIT_PART(PARSED_TEXT, 'Remit payment by the due date', 2),
                'ClearPath Safety Solutions',
                1
            )
        ) AS CHUNK_TEXT
    FROM base
)

SELECT * FROM facts_chunk
UNION ALL
SELECT * FROM header_chunk     WHERE CHUNK_TEXT IS NOT NULL AND CHUNK_TEXT <> ''
UNION ALL
SELECT * FROM summary_chunk    WHERE CHUNK_TEXT IS NOT NULL AND CHUNK_TEXT <> ''
UNION ALL
SELECT * FROM line_items_chunk WHERE CHUNK_TEXT IS NOT NULL AND CHUNK_TEXT <> ''
UNION ALL
SELECT * FROM totals_chunk     WHERE CHUNK_TEXT IS NOT NULL AND CHUNK_TEXT <> '';


-- Verify chunk distribution
SELECT CHUNK_TYPE, COUNT(*) AS CNT
FROM CLEARPATH_AI_POC_DB.CURATED_DOCS.INVOICE_CHUNK
GROUP BY CHUNK_TYPE
ORDER BY CHUNK_TYPE;

-- Spot-check a specific invoice
SELECT
    DOCUMENT_ID,
    CHUNK_TYPE,
    CHUNK_INDEX,
    LEFT(CHUNK_TEXT, 400) AS CHUNK_PREVIEW
FROM CLEARPATH_AI_POC_DB.CURATED_DOCS.INVOICE_CHUNK
WHERE DOCUMENT_ID = 'INV-2001.pdf'
ORDER BY CHUNK_INDEX;
