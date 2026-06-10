USE ROLE CLEARPATH_AI_POC;
USE WAREHOUSE CLEARPATH_APP_WH;
USE DATABASE CLEARPATH_AI_POC_DB;
USE SCHEMA APP;

-- =========================================================
-- STEP 6A - CORTEX AGENT
-- Creates the hybrid AI agent for ClearPath Safety Solutions
-- combining Cortex Analyst (ERP structured data) and
-- Cortex Search (PDF invoice document retrieval)
-- =========================================================

CREATE OR REPLACE AGENT CLEARPATH_RECON_AGENT
  COMMENT = 'Hybrid AR reconciliation agent for ClearPath Safety Solutions — structured ERP analysis and invoice document retrieval'
  FROM SPECIFICATION
$$
models:
  orchestration: claude-4-sonnet

orchestration:
  budget:
    seconds: 45
    tokens: 24000

instructions:
  system: "You are an AR reconciliation copilot for ClearPath Safety Solutions, a highway and work zone safety products company. Use Cortex Analyst for structured ERP questions about customer orders, revenue, and accounts receivable. Use Cortex Search for invoice document evidence including line items, SKUs, quantities, and unit prices. Prefer precise numeric answers. If ERP and document-derived values differ, surface both and explain the discrepancy clearly."
  orchestration: "Route revenue, AR balance, aging, and structured order questions to OrderAnalyst. Route invoice document questions — including line item details, SKU lookups, quantity or price evidence — to InvoiceSearch. For reconciliation questions comparing ERP to invoice documents, use both tools."
  response: "Answer clearly and concisely. For structured answers include key numbers and customer names. For document answers include relevant invoice evidence such as SKU, quantity, and unit price. For reconciliation answers, state the ERP value, the document value, and which field mismatches."
  sample_questions:
    - question: "What is total revenue by customer for Q1 2026?"
    - question: "Which invoices have reconciliation mismatches?"
    - question: "What does invoice INV-2009 say about the total amount due?"
    - question: "Compare ERP and invoice document values for INV-2009 — do they differ?"
    - question: "What products and quantities are on invoice INV-2001?"
    - question: "Which customers have overdue balances?"

tools:
  - tool_spec:
      type: "cortex_analyst_text_to_sql"
      name: "OrderAnalyst"
      description: "Use for structured ERP questions about customer revenue, AR balances, aging, and invoice reconciliation status"
  - tool_spec:
      type: "cortex_search"
      name: "InvoiceSearch"
      description: "Use for invoice document retrieval — line items, SKU details, quantities, unit prices, and document evidence"

tool_resources:
  OrderAnalyst:
    semantic_view: "CLEARPATH_AI_POC_DB.SEMANTIC.CLEARPATH_ANALYST_SV"
    warehouse: CLEARPATH_APP_WH
  InvoiceSearch:
    name: "CLEARPATH_AI_POC_DB.SEARCH.INVOICE_SEARCH_SVC"
    max_results: "5"
    title_column: "DOCUMENT_ID"
    id_column: "DOCUMENT_ID"
$$;

SHOW AGENTS IN SCHEMA CLEARPATH_AI_POC_DB.APP;

DESCRIBE AGENT CLEARPATH_AI_POC_DB.APP.CLEARPATH_RECON_AGENT;
