USE ROLE CLEARPATH_AI_POC;
USE WAREHOUSE CLEARPATH_ETL_WH;
USE DATABASE CLEARPATH_AI_POC_DB;
USE SCHEMA RAW_FINANCE;

-- =========================================================
-- STEP 1C - LOAD RAW ERP DATA
-- Loads simulated ERP data for ClearPath Safety Solutions:
--   - CUSTOMER_RAW  — 10 customers (DOTs, municipalities, contractors)
--   - INVOICE_RAW   — 30 invoices (3 per customer, Jan–Mar 2026)
--   - PAYMENT_RAW   — partial and full payments against invoices
--   - REVENUE_RAW   — recognized revenue by customer by month
--
-- ERP amounts intentionally differ from PDF invoice amounts
-- on 4 invoices to seed reconciliation mismatches:
--   INV-2003  — ERP has 25 drums @ $88 = $1,056 more than doc (23 drums)
--   INV-2009  — ERP has unit price $1,250; doc shows $1,275 (delta $25)
--   INV-2023  — ERP customer name "Meridian Highway Services LLC";
--               doc shows "Meridian Hwy Services LLC"
--   INV-2030  — ERP payment terms NET 30; doc shows NET 45
-- =========================================================

-- ---------------------------------------------------------
-- CUSTOMERS
-- ---------------------------------------------------------
CREATE OR REPLACE TABLE CUSTOMER_RAW (
    CUSTOMER_ID     STRING,
    CUSTOMER_NAME   STRING,
    REGION          STRING,
    INDUSTRY        STRING,
    CUSTOMER_STATUS STRING,
    PAYMENT_TERMS   STRING
);

INSERT INTO CUSTOMER_RAW
    (CUSTOMER_ID, CUSTOMER_NAME, REGION, INDUSTRY, CUSTOMER_STATUS, PAYMENT_TERMS)
VALUES
    ('DOT001', 'Texas Department of Transportation',    'South',     'Government - DOT',       'ACTIVE', 'NET 45'),
    ('DOT002', 'Illinois Department of Transportation', 'Midwest',   'Government - DOT',       'ACTIVE', 'NET 45'),
    ('DOT003', 'North Carolina DOT — Division 5',       'Southeast', 'Government - DOT',       'ACTIVE', 'NET 30'),
    ('CON001', 'Granite Horizon Contractors LLC',       'South',     'Highway Construction',   'ACTIVE', 'NET 30'),
    ('CON002', 'Apex Infrastructure Group Inc.',        'Midwest',   'Highway Construction',   'ACTIVE', 'NET 30'),
    ('CON003', 'Summit Roads & Bridges Corp.',          'Southeast', 'Highway Construction',   'ACTIVE', 'NET 21'),
    ('MUN001', 'City of Phoenix — Public Works Dept.',  'Southwest', 'Government - Municipal', 'ACTIVE', 'NET 45'),
    ('CON004', 'Meridian Highway Services LLC',         'Southwest', 'Highway Construction',   'ACTIVE', 'NET 30'),
    ('DOT004', 'Colorado DOT — Region 1',               'West',      'Government - DOT',       'ACTIVE', 'NET 45'),
    ('CON005', 'PeakLine Construction Partners',        'West',      'Highway Construction',   'ACTIVE', 'NET 30');


-- ---------------------------------------------------------
-- INVOICES
-- ERP amounts match PDF amounts EXCEPT for the 4 seeded
-- mismatches noted above.
-- ---------------------------------------------------------
CREATE OR REPLACE TABLE INVOICE_RAW (
    INVOICE_ID          STRING,
    CUSTOMER_ID         STRING,
    INVOICE_DATE        DATE,
    DUE_DATE            DATE,
    AMOUNT              NUMBER(12,2),
    CURRENCY            STRING,
    STATUS              STRING,
    INVOICE_DESCRIPTION STRING
);

INSERT INTO INVOICE_RAW
    (INVOICE_ID, CUSTOMER_ID, INVOICE_DATE, DUE_DATE, AMOUNT, CURRENCY, STATUS, INVOICE_DESCRIPTION)
VALUES
    -- Texas DOT
    ('INV-2001', 'DOT001', '2026-01-08', '2026-02-22',  21390.00, 'USD', 'OPEN',   'Barriers, delineator posts, channelizer drums — Jan order'),
    ('INV-2002', 'DOT001', '2026-02-10', '2026-03-27',   5880.00, 'USD', 'PAID',   'Reflective pavement markers, work zone signs, cones — Feb order'),
    -- MISMATCH: ERP shows 25 drums ($88 ea = $2,200); doc shows 23 drums ($2,024) — delta $176
    ('INV-2003', 'DOT001', '2026-03-05', '2026-04-19',  14360.00, 'USD', 'OPEN',   'Barriers, channelizer drums (25 units per ERP), PCB rental — Mar order'),

    -- Illinois DOT
    ('INV-2004', 'DOT002', '2026-01-12', '2026-02-26',   9775.00, 'USD', 'OPEN',   'Crash attenuators, work zone signs, delineator posts — Jan order'),
    ('INV-2005', 'DOT002', '2026-02-14', '2026-03-31',  13665.00, 'USD', 'OPEN',   'Barriers, traffic cones, reflective markers — Feb order'),
    ('INV-2006', 'DOT002', '2026-03-08', '2026-04-22',   6610.00, 'USD', 'OPEN',   'Channelizer drums, PCB rental, work zone signs — Mar order'),

    -- NC DOT
    ('INV-2007', 'DOT003', '2026-01-15', '2026-02-14',  10722.50, 'USD', 'PAID',   'Delineator posts, cones, channelizer drums — Jan order'),
    ('INV-2008', 'DOT003', '2026-02-18', '2026-03-20',  11504.00, 'USD', 'OPEN',   'Work zone signs, barriers, reflective markers — Feb order'),
    -- MISMATCH: ERP has unit price $1,250 for attenuator; doc shows $1,275 — delta $25
    ('INV-2009', 'DOT003', '2026-03-10', '2026-04-09',   6580.00, 'USD', 'OPEN',   'Crash attenuator (unit price $1,250 per ERP), channelizer drums, delineator posts — Mar order'),

    -- Granite Horizon Contractors
    ('INV-2010', 'CON001', '2026-01-07', '2026-02-06',  18595.00, 'USD', 'PAID',   'Traffic cones, delineator posts, reflective markers — Jan order'),
    ('INV-2011', 'CON001', '2026-02-09', '2026-03-11',  11660.00, 'USD', 'OPEN',   'Barriers, channelizer drums, work zone signs — Feb order'),
    ('INV-2012', 'CON001', '2026-03-03', '2026-04-02',   3830.00, 'USD', 'OPEN',   'PCB rental, LED arrow board rental, traffic cones — Mar order'),

    -- Apex Infrastructure Group
    ('INV-2013', 'CON002', '2026-01-10', '2026-02-09',  13935.00, 'USD', 'PAID',   'TMA retrofit kit, work zone signs, delineator posts — Jan order'),
    ('INV-2014', 'CON002', '2026-02-12', '2026-03-14',  13398.00, 'USD', 'OPEN',   'Barriers, channelizer drums, reflective markers — Feb order'),
    ('INV-2015', 'CON002', '2026-03-06', '2026-04-05',   8105.00, 'USD', 'OPEN',   'Traffic cones, PCB rental, work zone signs — Mar order'),

    -- Summit Roads & Bridges
    ('INV-2016', 'CON003', '2026-01-14', '2026-02-04',   8284.00, 'USD', 'PAID',   'Delineator posts, traffic cones, channelizer drums — Jan order'),
    ('INV-2017', 'CON003', '2026-02-17', '2026-03-10',   9256.00, 'USD', 'OPEN',   'Work zone signs, barriers, reflective markers — Feb order'),
    ('INV-2018', 'CON003', '2026-03-09', '2026-03-30',   8219.00, 'USD', 'OPEN',   'Channelizer drums, LED arrow board rental, delineator posts — Mar order'),

    -- City of Phoenix
    ('INV-2019', 'MUN001', '2026-01-09', '2026-02-23',  18065.00, 'USD', 'OPEN',   'Traffic cones, delineator posts, work zone signs — Jan order'),
    ('INV-2020', 'MUN001', '2026-02-11', '2026-03-28',  19881.00, 'USD', 'OPEN',   'Barriers, channelizer drums, reflective markers — Feb order'),
    ('INV-2021', 'MUN001', '2026-03-07', '2026-04-21',  10845.00, 'USD', 'OPEN',   'PCB rental, work zone signs, delineator posts — Mar order'),

    -- Meridian Highway Services
    ('INV-2022', 'CON004', '2026-01-13', '2026-02-12',   9859.50, 'USD', 'PAID',   'Channelizer drums, traffic cones, reflective markers — Jan order'),
    -- MISMATCH: ERP customer name "Meridian Highway Services LLC"; doc shows "Meridian Hwy Services LLC"
    ('INV-2023', 'CON004', '2026-02-16', '2026-03-18',  10875.00, 'USD', 'OPEN',   'Barriers, work zone signs, delineator posts — Feb order'),
    ('INV-2024', 'CON004', '2026-03-11', '2026-04-10',   7101.00, 'USD', 'OPEN',   'LED arrow board rental, traffic cones, channelizer drums — Mar order'),

    -- Colorado DOT
    ('INV-2025', 'DOT004', '2026-01-11', '2026-02-25',  13380.00, 'USD', 'OPEN',   'Crash attenuators, work zone signs, delineator posts — Jan order'),
    ('INV-2026', 'DOT004', '2026-02-13', '2026-03-30',  23463.00, 'USD', 'OPEN',   'Barriers, channelizer drums, reflective markers — Feb order'),
    ('INV-2027', 'DOT004', '2026-03-04', '2026-04-18',  10772.50, 'USD', 'OPEN',   'Traffic cones, PCB rental, work zone signs — Mar order'),

    -- PeakLine Construction
    ('INV-2028', 'CON005', '2026-01-16', '2026-02-06',  13924.00, 'USD', 'PAID',   'Channelizer drums, delineator posts, traffic cones — Jan order'),
    ('INV-2029', 'CON005', '2026-02-19', '2026-03-12',  10844.00, 'USD', 'OPEN',   'Work zone signs, barriers, reflective markers — Feb order'),
    -- MISMATCH: ERP payment terms NET 30; doc shows NET 45
    ('INV-2030', 'CON005', '2026-03-12', '2026-04-11',   4785.00, 'USD', 'OPEN',   'PCB rental, LED arrow board rental, channelizer drums (NET 30 per ERP) — Mar order');


-- ---------------------------------------------------------
-- PAYMENTS
-- ---------------------------------------------------------
CREATE OR REPLACE TABLE PAYMENT_RAW (
    PAYMENT_ID      STRING,
    INVOICE_ID      STRING,
    PAYMENT_DATE    DATE,
    PAYMENT_AMOUNT  NUMBER(12,2),
    PAYMENT_METHOD  STRING
);

INSERT INTO PAYMENT_RAW
    (PAYMENT_ID, INVOICE_ID, PAYMENT_DATE, PAYMENT_AMOUNT, PAYMENT_METHOD)
VALUES
    -- Full payments
    ('PAY-3001', 'INV-2002', '2026-03-20',  5880.00, 'ACH'),
    ('PAY-3002', 'INV-2007', '2026-02-12', 10722.50, 'WIRE'),
    ('PAY-3003', 'INV-2010', '2026-02-04', 18595.00, 'ACH'),
    ('PAY-3004', 'INV-2013', '2026-02-06', 13935.00, 'WIRE'),
    ('PAY-3005', 'INV-2016', '2026-02-02',  8284.00, 'ACH'),
    ('PAY-3006', 'INV-2022', '2026-02-10',  9859.50, 'ACH'),
    ('PAY-3007', 'INV-2028', '2026-02-04', 13924.00, 'WIRE'),

    -- Partial payments
    ('PAY-3008', 'INV-2001', '2026-03-01', 10000.00, 'ACH'),
    ('PAY-3009', 'INV-2004', '2026-02-20',  5000.00, 'ACH'),
    ('PAY-3010', 'INV-2011', '2026-03-05',  6000.00, 'WIRE'),
    ('PAY-3011', 'INV-2014', '2026-03-10',  7000.00, 'ACH'),
    ('PAY-3012', 'INV-2019', '2026-03-01',  9000.00, 'WIRE'),
    ('PAY-3013', 'INV-2020', '2026-03-20', 10000.00, 'ACH'),
    ('PAY-3014', 'INV-2025', '2026-03-01',  6500.00, 'WIRE'),
    ('PAY-3015', 'INV-2026', '2026-03-25', 12000.00, 'ACH');


-- ---------------------------------------------------------
-- REVENUE
-- Recognized product revenue by customer by month.
-- Categories reflect ClearPath product lines.
-- ---------------------------------------------------------
CREATE OR REPLACE TABLE REVENUE_RAW (
    REVENUE_ID      STRING,
    CUSTOMER_ID     STRING,
    REVENUE_DATE    DATE,
    REVENUE_AMOUNT  NUMBER(12,2),
    REVENUE_CATEGORY STRING
);

INSERT INTO REVENUE_RAW
    (REVENUE_ID, CUSTOMER_ID, REVENUE_DATE, REVENUE_AMOUNT, REVENUE_CATEGORY)
VALUES
    -- Texas DOT
    ('REV-4001', 'DOT001', '2026-01-31', 21390.00, 'Barriers & Attenuators'),
    ('REV-4002', 'DOT001', '2026-02-28',  5880.00, 'Signage & Delineation'),
    ('REV-4003', 'DOT001', '2026-03-31', 14360.00, 'Barriers & Attenuators'),

    -- Illinois DOT
    ('REV-4004', 'DOT002', '2026-01-31',  9775.00, 'Barriers & Attenuators'),
    ('REV-4005', 'DOT002', '2026-02-28', 13665.00, 'Barriers & Attenuators'),
    ('REV-4006', 'DOT002', '2026-03-31',  6610.00, 'Channelizers & Drums'),

    -- NC DOT
    ('REV-4007', 'DOT003', '2026-01-31', 10722.50, 'Signage & Delineation'),
    ('REV-4008', 'DOT003', '2026-02-28', 11504.00, 'Barriers & Attenuators'),
    ('REV-4009', 'DOT003', '2026-03-31',  6580.00, 'Barriers & Attenuators'),

    -- Granite Horizon Contractors
    ('REV-4010', 'CON001', '2026-01-31', 18595.00, 'Channelizers & Drums'),
    ('REV-4011', 'CON001', '2026-02-28', 11660.00, 'Barriers & Attenuators'),
    ('REV-4012', 'CON001', '2026-03-31',  3830.00, 'Rental Equipment'),

    -- Apex Infrastructure Group
    ('REV-4013', 'CON002', '2026-01-31', 13935.00, 'Barriers & Attenuators'),
    ('REV-4014', 'CON002', '2026-02-28', 13398.00, 'Barriers & Attenuators'),
    ('REV-4015', 'CON002', '2026-03-31',  8105.00, 'Channelizers & Drums'),

    -- Summit Roads & Bridges
    ('REV-4016', 'CON003', '2026-01-31',  8284.00, 'Signage & Delineation'),
    ('REV-4017', 'CON003', '2026-02-28',  9256.00, 'Barriers & Attenuators'),
    ('REV-4018', 'CON003', '2026-03-31',  8219.00, 'Rental Equipment'),

    -- City of Phoenix
    ('REV-4019', 'MUN001', '2026-01-31', 18065.00, 'Channelizers & Drums'),
    ('REV-4020', 'MUN001', '2026-02-28', 19881.00, 'Barriers & Attenuators'),
    ('REV-4021', 'MUN001', '2026-03-31', 10845.00, 'Rental Equipment'),

    -- Meridian Highway Services
    ('REV-4022', 'CON004', '2026-01-31',  9859.50, 'Channelizers & Drums'),
    ('REV-4023', 'CON004', '2026-02-28', 10875.00, 'Barriers & Attenuators'),
    ('REV-4024', 'CON004', '2026-03-31',  7101.00, 'Rental Equipment'),

    -- Colorado DOT
    ('REV-4025', 'DOT004', '2026-01-31', 13380.00, 'Barriers & Attenuators'),
    ('REV-4026', 'DOT004', '2026-02-28', 23463.00, 'Barriers & Attenuators'),
    ('REV-4027', 'DOT004', '2026-03-31', 10772.50, 'Channelizers & Drums'),

    -- PeakLine Construction
    ('REV-4028', 'CON005', '2026-01-31', 13924.00, 'Channelizers & Drums'),
    ('REV-4029', 'CON005', '2026-02-28', 10844.00, 'Barriers & Attenuators'),
    ('REV-4030', 'CON005', '2026-03-31',  4785.00, 'Rental Equipment');


-- ---------------------------------------------------------
-- Verification
-- ---------------------------------------------------------
SELECT 'CUSTOMER_RAW'  AS tbl, COUNT(*) AS rows FROM CUSTOMER_RAW
UNION ALL
SELECT 'INVOICE_RAW',  COUNT(*) FROM INVOICE_RAW
UNION ALL
SELECT 'PAYMENT_RAW',  COUNT(*) FROM PAYMENT_RAW
UNION ALL
SELECT 'REVENUE_RAW',  COUNT(*) FROM REVENUE_RAW;
