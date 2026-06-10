USE ROLE CLEARPATH_AI_POC;
USE WAREHOUSE CLEARPATH_ETL_WH;
USE DATABASE CLEARPATH_AI_POC_DB;

-- =========================================================
-- STEP 2E - EXTRACT INVOICE FIELDS
-- Extracts structured fields from parsed ClearPath invoice
-- text including header fields and total amount due.
-- ClearPath invoices contain SKU line items; TOTAL_DUE is
-- the "Total Amount Due" value from the totals section.
-- =========================================================

TRUNCATE TABLE CLEARPATH_AI_POC_DB.CURATED_DOCS.INVOICE_EXTRACT;

INSERT INTO CLEARPATH_AI_POC_DB.CURATED_DOCS.INVOICE_EXTRACT (
    DOCUMENT_ID,
    RELATIVE_PATH,
    INVOICE_NUMBER,
    CUSTOMER_NAME,
    INVOICE_DATE,
    DUE_DATE,
    PAYMENT_TERMS,
    CURRENCY,
    TOTAL_DUE,
    PO_NUMBER
)
SELECT
    DOCUMENT_ID,
    RELATIVE_PATH,

    -- Invoice number from header
    REGEXP_SUBSTR(
        PARSED_TEXT,
        'Invoice No:\\s*([A-Z0-9-]+)',
        1, 1, 'ie', 1
    ) AS INVOICE_NUMBER,

    -- Customer name: first line after the Bill To separator row
    TRIM(
        REGEXP_SUBSTR(
            PARSED_TEXT,
            '\\| --- \\| --- \\|\\n\\|\\s+([^\\n|]+)\\n',
            1, 1, 'ie', 1
        )
    ) AS CUSTOMER_NAME,

    -- Invoice date
    TRY_TO_DATE(
        REGEXP_SUBSTR(
            PARSED_TEXT,
            'Invoice Date:\\s*([0-9]{4}-[0-9]{2}-[0-9]{2})',
            1, 1, 'ie', 1
        )
    ) AS INVOICE_DATE,

    -- Due date
    TRY_TO_DATE(
        REGEXP_SUBSTR(
            PARSED_TEXT,
            'Due Date:\\s*([0-9]{4}-[0-9]{2}-[0-9]{2})',
            1, 1, 'ie', 1
        )
    ) AS DUE_DATE,

    -- Payment terms (NET 30, NET 45 etc.)
    REGEXP_SUBSTR(
        PARSED_TEXT,
        'Payment Terms:\\s*(NET\\s*[0-9]+)',
        1, 1, 'ie', 1
    ) AS PAYMENT_TERMS,

    -- Currency
    REGEXP_SUBSTR(
        PARSED_TEXT,
        'Currency:\\s*([A-Z]{3})',
        1, 1, 'ie', 1
    ) AS CURRENCY,

    -- Total Amount Due from totals section
    TRY_TO_DECIMAL(
        REPLACE(
            REGEXP_SUBSTR(
                PARSED_TEXT,
                'Total Amount Due[^$]*\\$([0-9,]+\\.[0-9]{2})',
                1, 1, 'ie', 1
            ),
            ',', ''
        ),
        12, 2
    ) AS TOTAL_DUE,

    -- PO Number (optional on ClearPath invoices)
    REGEXP_SUBSTR(
        PARSED_TEXT,
        'PO Number:\\s*([A-Z0-9-]+)',
        1, 1, 'ie', 1
    ) AS PO_NUMBER

FROM CLEARPATH_AI_POC_DB.CURATED_DOCS.INVOICE_PARSED;

-- Verify extraction
SELECT
    DOCUMENT_ID,
    INVOICE_NUMBER,
    CUSTOMER_NAME,
    INVOICE_DATE,
    DUE_DATE,
    PAYMENT_TERMS,
    CURRENCY,
    TOTAL_DUE,
    PO_NUMBER
FROM CLEARPATH_AI_POC_DB.CURATED_DOCS.INVOICE_EXTRACT
ORDER BY INVOICE_NUMBER;
