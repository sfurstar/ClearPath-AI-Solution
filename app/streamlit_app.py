import base64
import json
import re
from typing import Any, Dict, List, Optional

import streamlit as st
from snowflake.snowpark.context import get_active_session
import altair as alt
import pandas as pd



APP_TITLE = "AR Reconciliation Agent"
APP_SUBTITLE = "ClearPath Safety Solutions"
AGENT_NAME = "CLEARPATH_AI_POC_DB.APP.CLEARPATH_RECON_AGENT"

BRAND = {
    "navy": "#1B3A5C",
    "blue": "#F47920",
    "sky": "#FFF3E8",
    "slate": "#5B6B82",
    "ink": "#0D1F2D",
    "line": "#D9E3F0",
    "panel": "#FFFFFF",
    "panel_alt": "#F8F9FA",
    "success": "#2E7D32",
    "success_bg": "#F1F8F1",
    "warning": "#E65100",
    "warning_bg": "#FFF3E8",
    "danger": "#C62828",
    "danger_bg": "#FDEEEE",
}

SUGGESTION_GROUPS = {
    "Structured analysis": [
        "What is total revenue by customer?",
        "Show total revenue by customer for all customers",
        "Which customers have the highest open amount?",
        "Which customers have the highest overdue amounts?",
    ],
    "Document evidence": [
        "What does invoice INV-2009 say about the total amount due?",
        "What is the due date on invoice INV-2001?",
        "Summarize the invoice details for INV-2026.",
    ],
    "Hybrid comparison": [
        "Compare ERP and invoice document values for INV-2009 and tell me if they differ.",
        "Which customers have overdue balances and invoice mismatches?",
    ],
}

ANSWER_TYPE_STYLES = {
    "Structured analysis": {
        "bg": "#FFF3E8",
        "border": "#F47920",
        "text": "#4A2500",
        "pill": "#FFE0C4",
    },
    "Document evidence": {
        "bg": "#EAF8F3",
        "border": "#0F9D75",
        "text": "#0B5E46",
        "pill": "#D8F3EA",
    },
    "Hybrid comparison": {
        "bg": "#FFF5DF",
        "border": "#C98916",
        "text": "#7A5208",
        "pill": "#FDE8B6",
    },
    "Mismatch": {
        "bg": "#FDEEEE",
        "border": "#C94141",
        "text": "#7D1F1F",
        "pill": "#F9D1D1",
    },
    "Default": {
        "bg": "#F3F6FA",
        "border": "#B5C3D6",
        "text": "#334155",
        "pill": "#E8EEF5",
    },
}


def get_session():
    return get_active_session()


@st.cache_data(show_spinner=False)
def get_logo_data_uri() -> str:
    svg = f"""
    <svg width="180" height="180" viewBox="0 0 180 180" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="180" height="180" rx="28" fill="{BRAND['navy']}"/>
      <!-- Road surface -->
      <rect x="30" y="108" width="120" height="18" rx="4" fill="#2C5282" opacity="0.6"/>
      <!-- Dashed center line -->
      <rect x="82" y="112" width="16" height="6" rx="2" fill="#F47920" opacity="0.9"/>
      <!-- Chevron arrow pointing right = forward path = ClearPath -->
      <path d="M44 90 L78 60 L92 74 L68 96 L92 118 L78 132 Z" fill="{BRAND['blue']}" opacity="0.95"/>
      <path d="M72 90 L106 60 L120 74 L96 96 L120 118 L106 132 Z" fill="white" opacity="0.9"/>
      <!-- Orange accent dot -->
      <circle cx="136" cy="56" r="14" fill="{BRAND['blue']}"/>
      <path d="M130 56 L134 52 L142 60" stroke="white" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
    </svg>
    """.strip()
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


def apply_custom_theme() -> None:
    st.markdown(
        f"""
        <style>
            :root {{
                --brand-navy: {BRAND['navy']};
                --brand-blue: {BRAND['blue']};
                --brand-sky: {BRAND['sky']};
                --brand-slate: {BRAND['slate']};
                --brand-ink: {BRAND['ink']};
                --brand-line: {BRAND['line']};
                --brand-panel: {BRAND['panel']};
                --brand-panel-alt: {BRAND['panel_alt']};
            }}

            .stApp {{
                background:
                    radial-gradient(circle at top right, rgba(30, 94, 255, 0.08), transparent 26%),
                    linear-gradient(180deg, #f7faff 0%, #eef4fb 100%);
                color: var(--brand-ink);
            }}

            [data-testid="stSidebar"] {{
                background: linear-gradient(180deg, #102747 0%, #142f57 100%);
                border-right: 1px solid rgba(255,255,255,0.08);
            }}

            [data-testid="stSidebar"] * {{
                color: #F5F9FF !important;
            }}

            .main .block-container {{
                padding-top: 1.6rem;
                padding-bottom: 2rem;
                max-width: 1360px;
            }}

            div[data-testid="stMetric"] {{
                background: rgba(255, 255, 255, 0.9);
                border: 1px solid var(--brand-line);
                border-radius: 16px;
                padding: 0.85rem 1rem;
                box-shadow: 0 8px 20px rgba(15, 39, 71, 0.05);
            }}

            div[data-testid="stDataFrame"] {{
                background: rgba(255,255,255,0.88);
                border-radius: 16px;
                border: 1px solid var(--brand-line);
                overflow: hidden;
            }}

            .ns-hero {{
                background: linear-gradient(135deg, rgba(15,39,71,0.98) 0%, rgba(20,47,87,0.98) 58%, rgba(30,94,255,0.92) 100%);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 24px;
                padding: 1.4rem 1.5rem;
                box-shadow: 0 18px 35px rgba(15, 39, 71, 0.16);
                margin-bottom: 1.15rem;
                color: white;
            }}

            .ns-hero-grid {{
                display: grid;
                grid-template-columns: 92px 1fr auto;
                gap: 1.2rem;
                align-items: center;
            }}

            .ns-logo-wrap {{
                width: 92px;
                height: 92px;
                border-radius: 24px;
                background: rgba(255,255,255,0.08);
                display: flex;
                align-items: center;
                justify-content: center;
                border: 1px solid rgba(255,255,255,0.12);
                backdrop-filter: blur(8px);
            }}

            .ns-logo-wrap img {{
                width: 76px;
                height: 76px;
            }}

            .ns-eyebrow {{
                font-size: 0.76rem;
                letter-spacing: 0.16em;
                text-transform: uppercase;
                opacity: 0.78;
                margin-bottom: 0.35rem;
                font-weight: 700;
            }}

            .ns-title {{
                font-size: 2rem;
                line-height: 1.1;
                font-weight: 800;
                margin: 0;
            }}

            .ns-subtitle {{
                margin-top: 0.4rem;
                color: rgba(255,255,255,0.84);
                font-size: 1rem;
                max-width: 760px;
            }}

            .ns-hero-stat {{
                min-width: 220px;
                background: rgba(255,255,255,0.1);
                border: 1px solid rgba(255,255,255,0.14);
                border-radius: 18px;
                padding: 0.9rem 1rem;
            }}

            .ns-hero-stat-label {{
                font-size: 0.76rem;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                opacity: 0.74;
                margin-bottom: 0.28rem;
                font-weight: 700;
            }}

            .ns-hero-stat-value {{
                font-size: 1.1rem;
                font-weight: 700;
            }}

            .ns-section-card {{
                background: rgba(255,255,255,0.9);
                border: 1px solid var(--brand-line);
                border-radius: 20px;
                padding: 1rem 1rem 0.3rem 1rem;
                box-shadow: 0 10px 25px rgba(15,39,71,0.05);
                margin-bottom: 1rem;
            }}

            .ns-card-title {{
                font-size: 1.05rem;
                font-weight: 700;
                color: var(--brand-navy);
                margin-bottom: 0.15rem;
            }}

            .ns-card-copy {{
                color: var(--brand-slate);
                margin-bottom: 0.8rem;
                font-size: 0.95rem;
            }}

            .ns-chat-bubble {{
                border-radius: 18px;
                padding: 1rem 1.05rem;
                border: 1px solid var(--brand-line);
                box-shadow: 0 8px 22px rgba(15,39,71,0.05);
                margin-bottom: 0.9rem;
            }}

            .ns-user {{
                background: #F6F9FD;
            }}

            .ns-assistant {{
                background: white;
            }}

            .ns-chat-role {{
                font-size: 0.78rem;
                font-weight: 800;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: var(--brand-blue);
                margin-bottom: 0.45rem;
            }}

            .ns-kpi-row {{
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.8rem;
                margin-bottom: 0.8rem;
            }}

            .ns-kpi-card {{
                background: rgba(255,255,255,0.92);
                border: 1px solid var(--brand-line);
                border-radius: 18px;
                padding: 0.9rem 1rem;
                box-shadow: 0 10px 24px rgba(15,39,71,0.05);
            }}

            .ns-kpi-label {{
                color: var(--brand-slate);
                font-size: 0.82rem;
                margin-bottom: 0.35rem;
                font-weight: 600;
            }}

            .ns-kpi-value {{
                color: var(--brand-navy);
                font-size: 1.35rem;
                font-weight: 800;
                line-height: 1.1;
            }}

            .ns-kpi-foot {{
                color: var(--brand-slate);
                font-size: 0.78rem;
                margin-top: 0.28rem;
            }}

            .ns-pill {{
                display: inline-block;
                border-radius: 999px;
                padding: 0.28rem 0.6rem;
                font-size: 0.76rem;
                font-weight: 700;
                letter-spacing: 0.03em;
                margin-right: 0.4rem;
            }}

            .stButton > button, .stFormSubmitButton > button {{
                border-radius: 14px !important;
                border: 1px solid rgba(255,255,255,0.08) !important;
                background: linear-gradient(135deg, #1E5EFF 0%, #1747C9 100%) !important;
                color: white !important;
                font-weight: 700 !important;
                box-shadow: 0 10px 20px rgba(30,94,255,0.18);
            }}

            .stButton > button:hover, .stFormSubmitButton > button:hover {{
                filter: brightness(1.03);
                transform: translateY(-1px);
            }}

            .stTextArea textarea {{
                border-radius: 16px !important;
                border: 1px solid var(--brand-line) !important;
                background: rgba(255,255,255,0.94) !important;
            }}

            .stTabs [data-baseweb="tab-list"] {{
                gap: 0.5rem;
            }}

            .stTabs [data-baseweb="tab"] {{
                height: 46px;
                border-radius: 12px 12px 0 0;
                padding-left: 1rem;
                padding-right: 1rem;
                background: rgba(255,255,255,0.65);
            }}

            .stTabs [aria-selected="true"] {{
                background: white;
                color: var(--brand-navy);
                font-weight: 700;
            }}

            @media (max-width: 1100px) {{
                .ns-hero-grid {{
                    grid-template-columns: 88px 1fr;
                }}
                .ns-hero-stat {{
                    grid-column: 1 / -1;
                }}
                .ns-kpi-row {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_session_context() -> Dict[str, str]:
    session = get_session()
    row = session.sql(
        """
        SELECT
          CURRENT_USER() AS USER_NAME,
          CURRENT_ROLE() AS ROLE_NAME,
          CURRENT_DATABASE() AS DATABASE_NAME,
          CURRENT_SCHEMA() AS SCHEMA_NAME,
          CURRENT_WAREHOUSE() AS WAREHOUSE_NAME
        """
    ).collect()[0]

    return {
        "user": row["USER_NAME"],
        "role": row["ROLE_NAME"],
        "database": row["DATABASE_NAME"],
        "schema": row["SCHEMA_NAME"],
        "warehouse": row["WAREHOUSE_NAME"],
    }


@st.cache_data(show_spinner=False)
def get_reconciliation_summary() -> List[Dict[str, Any]]:
    session = get_session()
    rows = session.sql(
        """
        SELECT OVERALL_RECON_STATUS, COUNT(*) AS INVOICE_COUNT
        FROM CLEARPATH_AI_POC_DB.CURATED_FINANCE.INVOICE_RECON_V
        GROUP BY OVERALL_RECON_STATUS
        ORDER BY OVERALL_RECON_STATUS
        """
    ).collect()
    return [r.as_dict() for r in rows]


@st.cache_data(show_spinner=False)
def get_top_open_balances() -> List[Dict[str, Any]]:
    session = get_session()
    rows = session.sql(
        """
        SELECT CUSTOMER_NAME, TOTAL_OPEN_AMOUNT, TOTAL_OVERDUE_AMOUNT
        FROM CLEARPATH_AI_POC_DB.CURATED_FINANCE.CUSTOMER_BALANCE_SUM_V
        ORDER BY TOTAL_OPEN_AMOUNT DESC
        LIMIT 5
        """
    ).collect()
    return [r.as_dict() for r in rows]


@st.cache_data(show_spinner=False)
def get_recent_mismatches() -> List[Dict[str, Any]]:
    session = get_session()
    rows = session.sql(
        """
        SELECT INVOICE_ID, RECON_EXCEPTION_DETAIL, ERP_AMOUNT, DOC_AMOUNT
        FROM CLEARPATH_AI_POC_DB.CURATED_FINANCE.INVOICE_RECON_V
        WHERE OVERALL_RECON_STATUS = 'MISMATCH'
        ORDER BY INVOICE_ID
        LIMIT 10
        """
    ).collect()
    return [r.as_dict() for r in rows]


def build_request(prompt: str) -> Dict[str, Any]:
    return {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ],
            }
        ],
        "stream": False,
    }


def call_agent(prompt: str) -> Dict[str, Any]:
    session = get_session()
    payload = build_request(prompt)
    request_json = json.dumps(payload).replace("'", "''")

    sql = f"""
        SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
          '{AGENT_NAME}',
          $$ {request_json} $$
        ) AS RESPONSE
    """

    row = session.sql(sql).collect()[0]
    raw = row["RESPONSE"]

    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"raw_text": raw}
    elif isinstance(raw, dict):
        parsed = raw
    else:
        parsed = {"raw_text": str(raw)}

    parsed["_debug_request"] = payload
    parsed["_debug_agent_name"] = AGENT_NAME
    parsed["_debug_sql"] = sql
    return parsed


def extract_text_blocks(response: Dict[str, Any]) -> List[str]:
    content = response.get("content", [])
    texts: List[str] = []

    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
                texts.append(str(item["text"]))

    if texts:
        return texts

    if response.get("message"):
        code = response.get("code")
        if code:
            return [f"Agent error {code}: {response['message']}"]
        return [str(response["message"])]

    if response.get("raw_text"):
        return [str(response["raw_text"])]

    return ["No response returned."]


def extract_tool_hints(response: Dict[str, Any]) -> List[str]:
    hints: List[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                lower_key = str(key).lower()
                if lower_key in {"tool_name", "tool", "selected_tool", "name"} and isinstance(value, str):
                    if any(token in value.lower() for token in ["analyst", "search", "finance", "invoice"]):
                        hints.append(value)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(response)

    seen: List[str] = []
    for hint in hints:
        if hint not in seen:
            seen.append(hint)
    return seen[:10]


def infer_answer_type(response: Dict[str, Any]) -> str:
    hints = " ".join(extract_tool_hints(response)).lower()
    response_text = json.dumps(response).lower()

    used_analyst = "analyst" in hints or "financeanalyst" in response_text
    used_search = "search" in hints or "invoicesearch" in response_text

    if used_analyst and used_search:
        return "Hybrid comparison"
    if used_analyst:
        return "Structured analysis"
    if used_search:
        return "Document evidence"

    text = " ".join(extract_text_blocks(response)).lower()
    if "erp" in text and "invoice document" in text:
        return "Hybrid comparison"
    if "invoice" in text and ("total amount due" in text or "document" in text):
        return "Document evidence"
    return "Structured analysis"


def normalize_prompt(prompt: str) -> str:
    return " ".join(prompt.lower().strip().split())


def extract_invoice_id(text: str) -> Optional[str]:
    match = re.search(r"\bINV-\d{4}\b", text.upper())
    return match.group(0) if match else None


def format_currency(value: Any) -> str:
    try:
        return f"${float(value):,.2f}"
    except Exception:
        return str(value) if value is not None else ""


def render_answer_type_badge(answer_type: str) -> None:
    style = ANSWER_TYPE_STYLES.get(answer_type, ANSWER_TYPE_STYLES["Default"])
    st.markdown(
        f"""
        <div style="
            background-color: {style['bg']};
            border: 1px solid {style['border']};
            border-left: 7px solid {style['border']};
            padding: 12px 16px;
            border-radius: 14px;
            margin: 6px 0 14px 0;
            color: {style['text']};
            font-weight: 700;
            box-shadow: 0 8px 20px rgba(15,39,71,0.05);
        ">
            <span class="ns-pill" style="background:{style['pill']}; color:{style['text']};">Response profile</span>
            {answer_type}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_info_card(title: str, body: str, tone: str = "Default") -> None:
    style = ANSWER_TYPE_STYLES.get(tone, ANSWER_TYPE_STYLES["Default"])
    st.markdown(
        f"""
        <div style="
            background-color: {style['bg']};
            border: 1px solid {style['border']};
            padding: 14px 16px;
            border-radius: 16px;
            margin: 8px 0 14px 0;
            color: {style['text']};
            box-shadow: 0 8px 18px rgba(15,39,71,0.04);
        ">
            <div style="font-weight: 800; margin-bottom: 6px;">{title}</div>
            <div>{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_structured_result(prompt: str) -> Optional[Dict[str, Any]]:
    p = normalize_prompt(prompt)
    session = get_session()

    if "revenue" in p and "customer" in p and "total" in p:
        rows = session.sql(
            """
            SELECT
                CUSTOMER_NAME,
                SUM(REVENUE_AMOUNT) AS TOTAL_REVENUE
            FROM CLEARPATH_AI_POC_DB.CURATED_FINANCE.CUSTOMER_REVENUE_MTH_V
            GROUP BY CUSTOMER_NAME
            ORDER BY TOTAL_REVENUE DESC, CUSTOMER_NAME
            """
        ).collect()
        return {
            "title": "Structured results: Total revenue by customer",
            "rows": [r.as_dict() for r in rows],
        }

    if ("open amount" in p and "customer" in p) or ("open balance" in p and "customer" in p):
        rows = session.sql(
            """
            SELECT
                CUSTOMER_NAME,
                TOTAL_OPEN_AMOUNT,
                TOTAL_OVERDUE_AMOUNT
            FROM CLEARPATH_AI_POC_DB.CURATED_FINANCE.CUSTOMER_BALANCE_SUM_V
            ORDER BY TOTAL_OPEN_AMOUNT DESC, CUSTOMER_NAME
            """
        ).collect()
        return {
            "title": "Structured results: Open balance by customer",
            "rows": [r.as_dict() for r in rows],
        }

    if "overdue" in p and "customer" in p:
        rows = session.sql(
            """
            SELECT
                CUSTOMER_NAME,
                TOTAL_OVERDUE_AMOUNT,
                TOTAL_OPEN_AMOUNT
            FROM CLEARPATH_AI_POC_DB.CURATED_FINANCE.CUSTOMER_BALANCE_SUM_V
            ORDER BY TOTAL_OVERDUE_AMOUNT DESC, CUSTOMER_NAME
            """
        ).collect()
        return {
            "title": "Structured results: Overdue amount by customer",
            "rows": [r.as_dict() for r in rows],
        }

    if "customer" in p and "month" in p:
        rows = session.sql(
            """
            SELECT
                CUSTOMER_NAME,
                REVENUE_MONTH,
                REVENUE_CATEGORY,
                REVENUE_AMOUNT,
                REGION,
                INDUSTRY
            FROM CLEARPATH_AI_POC_DB.CURATED_FINANCE.CUSTOMER_REVENUE_MTH_V
            ORDER BY REVENUE_MONTH DESC, CUSTOMER_NAME
            """
        ).collect()
        return {
            "title": "Structured results: Customers by month",
            "rows": [r.as_dict() for r in rows],
        }

    return None


def get_document_evidence(invoice_id: str) -> Optional[Dict[str, Any]]:
    session = get_session()
    rows = session.sql(
        f"""
        SELECT
            INVOICE_NUMBER,
            CUSTOMER_NAME,
            INVOICE_DATE,
            DUE_DATE,
            TOTAL_DUE,
            PAYMENT_TERMS,
            PO_NUMBER
        FROM CLEARPATH_AI_POC_DB.CURATED_DOCS.INVOICE_EXTRACT
        WHERE INVOICE_NUMBER = '{invoice_id}'
        """
    ).collect()

    if not rows:
        return None

    return {
        "title": f"Document evidence: {invoice_id}",
        "rows": [r.as_dict() for r in rows],
    }


def get_hybrid_evidence(invoice_id: str) -> Optional[Dict[str, Any]]:
    session = get_session()
    rows = session.sql(
        f"""
        SELECT
            INVOICE_ID,
            ERP_CUSTOMER_NAME,
            DOC_CUSTOMER_NAME,
            ERP_INVOICE_DATE,
            DOC_INVOICE_DATE,
            ERP_DUE_DATE,
            DOC_DUE_DATE,
            ERP_PAYMENT_TERMS,
            DOC_PAYMENT_TERMS,
            ERP_AMOUNT,
            DOC_AMOUNT,
            DOC_PO_NUMBER_STATUS,
            OVERALL_RECON_STATUS,
            RECON_EXCEPTION_DETAIL
        FROM CLEARPATH_AI_POC_DB.CURATED_FINANCE.INVOICE_RECON_V
        WHERE INVOICE_ID = '{invoice_id}'
        """
    ).collect()

    if not rows:
        return None

    return {
        "title": f"Reconciliation evidence: {invoice_id}",
        "rows": [r.as_dict() for r in rows],
    }


def get_customer_mismatch_evidence() -> Optional[Dict[str, Any]]:
    session = get_session()
    rows = session.sql(
        """
        SELECT
            cb.CUSTOMER_NAME,
            cb.TOTAL_OVERDUE_AMOUNT,
            COUNT(ir.INVOICE_ID) AS MISMATCHED_INVOICE_COUNT
        FROM CLEARPATH_AI_POC_DB.CURATED_FINANCE.CUSTOMER_BALANCE_SUM_V cb
        JOIN CLEARPATH_AI_POC_DB.CURATED_FINANCE.INVOICE_RECON_V ir
          ON cb.CUSTOMER_NAME = ir.ERP_CUSTOMER_NAME
        WHERE cb.TOTAL_OVERDUE_AMOUNT > 0
          AND ir.OVERALL_RECON_STATUS = 'MISMATCH'
        GROUP BY cb.CUSTOMER_NAME, cb.TOTAL_OVERDUE_AMOUNT
        ORDER BY cb.TOTAL_OVERDUE_AMOUNT DESC, MISMATCHED_INVOICE_COUNT DESC, cb.CUSTOMER_NAME
        """
    ).collect()

    if not rows:
        return None

    return {
        "title": "Hybrid evidence: Customers with overdue balances and invoice mismatches",
        "rows": [r.as_dict() for r in rows],
    }


def get_supporting_evidence(prompt: str, answer_type: str) -> Optional[Dict[str, Any]]:
    invoice_id = extract_invoice_id(prompt)
    normalized = normalize_prompt(prompt)

    if answer_type == "Document evidence" and invoice_id:
        return get_document_evidence(invoice_id)

    if answer_type == "Hybrid comparison" and invoice_id:
        return get_hybrid_evidence(invoice_id)

    if answer_type == "Hybrid comparison" and "overdue" in normalized and "mismatch" in normalized:
        return get_customer_mismatch_evidence()

    return None


def render_kpi_card(label: str, value: str, foot: str) -> None:
    st.markdown(
        f"""
        <div class="ns-kpi-card">
            <div class="ns-kpi-label">{label}</div>
            <div class="ns-kpi-value">{value}</div>
            <div class="ns-kpi-foot">{foot}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_key_facts_card(answer_type: str, supporting: Optional[Dict[str, Any]]) -> None:
    if not supporting or not supporting.get("rows"):
        return

    row = supporting["rows"][0]

    if answer_type == "Document evidence":
        render_info_card(
            "Parsed invoice facts",
            "These values come from the parsed invoice extraction layer and support the document-grounded answer returned by the agent.",
            tone="Document evidence",
        )

        st.markdown("**Key facts**")
        st.markdown('<div class="ns-kpi-row">', unsafe_allow_html=True)
        cols = st.columns(3)
        with cols[0]:
            render_kpi_card("Invoice", str(row.get("INVOICE_NUMBER", "")), f"Invoice date: {row.get('INVOICE_DATE', '')}")
        with cols[1]:
            render_kpi_card("Customer", str(row.get("CUSTOMER_NAME", "")), f"Due date: {row.get('DUE_DATE', '')}")
        with cols[2]:
            render_kpi_card("Total Due", format_currency(row.get("TOTAL_DUE", "")), f"Terms: {row.get('PAYMENT_TERMS', '')}")
        st.markdown("</div>", unsafe_allow_html=True)

        po_number = row.get("PO_NUMBER")
        if po_number:
            st.caption(f"PO Number: {po_number}")

    elif answer_type == "Hybrid comparison":
        recon_status = str(row.get("OVERALL_RECON_STATUS", ""))
        if recon_status.upper() == "MISMATCH":
            render_info_card(
                "Mismatch detected",
                "ERP and invoice document values do not fully agree. Review the variance and exception detail below.",
                tone="Mismatch",
            )
        else:
            render_info_card(
                "Reconciliation status",
                "ERP and invoice document values are aligned for the key fields shown below.",
                tone="Hybrid comparison",
            )

        erp_amount = row.get("ERP_AMOUNT")
        doc_amount = row.get("DOC_AMOUNT")

        variance = None
        try:
            if erp_amount is not None and doc_amount is not None:
                variance = float(doc_amount) - float(erp_amount)
        except Exception:
            variance = None

        st.markdown("**Key facts**")
        cols = st.columns(3)
        with cols[0]:
            render_kpi_card("Invoice", str(row.get("INVOICE_ID", "")), f"Status: {recon_status or 'N/A'}")
        with cols[1]:
            render_kpi_card("ERP Amount", format_currency(erp_amount), f"ERP due: {row.get('ERP_DUE_DATE', '')}")
        with cols[2]:
            variance_text = f"Variance: {format_currency(variance)}" if variance is not None else "Variance unavailable"
            render_kpi_card("Document Amount", format_currency(doc_amount), f"Doc due: {row.get('DOC_DUE_DATE', '')} | {variance_text}")

        exception_detail = row.get("RECON_EXCEPTION_DETAIL")
        if exception_detail:
            st.caption(f"Exception Detail: {exception_detail}")


def init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Welcome to the ClearPath AR Reconciliation Agent. Ask about product revenue, open customer balances, invoice line-item evidence, or ERP-to-document reconciliation.",
            }
        ]

    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = ""

    if "show_debug" not in st.session_state:
        st.session_state.show_debug = False

    if "latest_response" not in st.session_state:
        st.session_state.latest_response = None

    if "latest_answer_type" not in st.session_state:
        st.session_state.latest_answer_type = ""

    if "latest_structured_result" not in st.session_state:
        st.session_state.latest_structured_result = None

    if "latest_supporting_evidence" not in st.session_state:
        st.session_state.latest_supporting_evidence = None


def render_sidebar() -> None:
    ctx = get_session_context()

    st.sidebar.markdown("### ClearPath Command Center")
    st.sidebar.caption("AR & Order reconciliation assistant")

    st.sidebar.write(f"**User:** {ctx['user']}")
    st.sidebar.write(f"**Role:** {ctx['role']}")
    st.sidebar.write(f"**Warehouse:** {ctx['warehouse']}")
    st.sidebar.write(f"**Database:** {ctx['database']}")
    st.sidebar.write(f"**Schema:** {ctx['schema']}")
    st.sidebar.divider()

    st.session_state.show_debug = st.sidebar.checkbox(
        "Show debug panels",
        value=st.session_state.show_debug,
    )

    if st.sidebar.button("Clear chat", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Chat cleared. Ask another AR or reconciliation question.",
            }
        ]
        st.session_state.pending_prompt = ""
        st.session_state.latest_response = None
        st.session_state.latest_answer_type = ""
        st.session_state.latest_structured_result = None
        st.session_state.latest_supporting_evidence = None
        st.experimental_rerun()

    st.sidebar.divider()
    st.sidebar.subheader("Starter questions")

    for section, questions in SUGGESTION_GROUPS.items():
        with st.sidebar.expander(section, expanded=(section == "Hybrid comparison")):
            for question in questions:
                if st.button(question, key=f"{section}_{question}"):
                    st.session_state.pending_prompt = question
                    st.experimental_rerun()


def render_hero() -> None:
    logo_data_uri = get_logo_data_uri()
    st.markdown(
        f"""
        <div class="ns-hero">
            <div class="ns-hero-grid">
                <div class="ns-logo-wrap">
                    <img src="{logo_data_uri}" alt="ClearPath Safety Solutions logo" />
                </div>
                <div>
                    <div class="ns-eyebrow">{APP_SUBTITLE}</div>
                    <h2 class="ns-title">{APP_TITLE}</h2>
                    <div class="ns-subtitle">
                        Hybrid AI agent combining ERP order data with PDF invoice evidence — automated reconciliation for highway safety product sales
                    </div>
                </div>
                <div class="ns-hero-stat">
                    <div class="ns-hero-stat-label">Assistant Focus</div>
                    <div class="ns-hero-stat-value">Order AR, Product Invoice QA, ERP Reconciliation</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_overview() -> None:
    recon = get_reconciliation_summary()
    top_open = get_top_open_balances()
    mismatches = get_recent_mismatches()

    total_invoices = sum(int(r.get("INVOICE_COUNT", 0)) for r in recon) if recon else 0
    mismatch_count = sum(int(r.get("INVOICE_COUNT", 0)) for r in recon if str(r.get("OVERALL_RECON_STATUS", "")).upper() == "MISMATCH") if recon else 0
    top_balance = max((float(r.get("TOTAL_OPEN_AMOUNT", 0) or 0) for r in top_open), default=0.0)

    k1, k2, k3 = st.columns(3)
    with k1:
        render_kpi_card("Invoices tracked", f"{total_invoices:,}", "Across reconciliation monitoring views")
    with k2:
        render_kpi_card("Mismatch count", f"{mismatch_count:,}", "Invoices currently flagged in recon")
    with k3:
        render_kpi_card("Largest open balance", format_currency(top_balance), "Highest customer open amount in summary view")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="ns-section-card"><div class="ns-card-title">Reconciliation status</div><div class="ns-card-copy">Current distribution of customer invoice reconciliation outcomes across the AR monitoring layer.</div></div>', unsafe_allow_html=True)
        if recon:
            df_recon = pd.DataFrame(recon)
            df_recon["INVOICE_COUNT"] = pd.to_numeric(df_recon["INVOICE_COUNT"], errors="coerce")
            pie = alt.Chart(df_recon).mark_arc(innerRadius=50).encode(
                theta=alt.Theta("INVOICE_COUNT:Q", title="Invoice count"),
                color=alt.Color(
                    "OVERALL_RECON_STATUS:N",
                    title="Status",
                    scale=alt.Scale(
                        domain=["MATCH", "MISMATCH"],
                        range=["#4CAF50", "#F44336"],
                    ),
                ),
                tooltip=[
                    alt.Tooltip("OVERALL_RECON_STATUS:N", title="Status"),
                    alt.Tooltip("INVOICE_COUNT:Q", title="Invoices"),
                ],
            ).properties(height=300)
            st.altair_chart(pie, use_container_width=True)
            st.dataframe(pd.DataFrame(recon), use_container_width=True)

    with c2:
        st.markdown('<div class="ns-section-card"><div class="ns-card-title">Top open balances</div><div class="ns-card-copy">Highest outstanding customer order balances surfaced for collections triage.</div></div>', unsafe_allow_html=True)
        if top_open:
            df_open = pd.DataFrame(top_open)
            df_open["TOTAL_OPEN_AMOUNT"] = pd.to_numeric(df_open["TOTAL_OPEN_AMOUNT"], errors="coerce")
            bar = alt.Chart(df_open).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                x=alt.X("CUSTOMER_NAME:N", sort="-y", title="Customer"),
                y=alt.Y("TOTAL_OPEN_AMOUNT:Q", title="Open amount"),
                color=alt.value("#F47920"),
                tooltip=[
                    alt.Tooltip("CUSTOMER_NAME:N", title="Customer"),
                    alt.Tooltip("TOTAL_OPEN_AMOUNT:Q", title="Open amount", format="$,.2f"),
                ],
            ).properties(height=300)
            st.altair_chart(bar, use_container_width=True)
            st.dataframe(pd.DataFrame(top_open), use_container_width=True)

    with st.expander("Recent mismatch examples", expanded=False):
        if mismatches:
            st.dataframe(pd.DataFrame(mismatches), use_container_width=True)

def render_chat_history() -> None:
    for msg in st.session_state.messages:
        role = msg["role"]
        role_label = "Assistant" if role == "assistant" else "You"
        css_class = "ns-assistant" if role == "assistant" else "ns-user"
        content = str(msg["content"]).replace("\n", "<br>")
        st.markdown(
            f"""
            <div class="ns-chat-bubble {css_class}">
                <div class="ns-chat-role">{role_label}</div>
                <div>{content}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_latest_answer_panel() -> None:
    if not st.session_state.latest_response:
        return

    st.markdown('<div class="ns-section-card"><div class="ns-card-title">Latest answer insights</div><div class="ns-card-copy">Grounding, evidence, and structured results associated with the most recent response.</div></div>', unsafe_allow_html=True)

    answer_type = st.session_state.latest_answer_type
    if answer_type:
        render_answer_type_badge(answer_type)

    response = st.session_state.latest_response
    tool_hints = extract_tool_hints(response)
    if tool_hints:
        st.caption("Possible tools used: " + ", ".join(tool_hints))

    supporting = st.session_state.latest_supporting_evidence
    if supporting and supporting.get("rows"):
        render_key_facts_card(answer_type, supporting)

    structured_result = st.session_state.latest_structured_result
    if structured_result and structured_result.get("rows"):
        st.markdown("**Supporting structured results**")
        st.dataframe(pd.DataFrame(structured_result["rows"]), use_container_width=True)

    if supporting and supporting.get("rows"):
        st.markdown(f"**{supporting['title']}**")
        st.dataframe(pd.DataFrame(supporting["rows"]), use_container_width=True)


def render_chat_input() -> None:
    default_prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = ""

    st.markdown('<div class="ns-section-card"><div class="ns-card-title">Ask the assistant</div><div class="ns-card-copy">Use natural language to query structured finance metrics, invoice document details, or hybrid reconciliation issues.</div></div>', unsafe_allow_html=True)

    with st.form("agent_chat_form", clear_on_submit=True):
        prompt = st.text_area(
            "Ask the Finance Hybrid Assistant",
            value=default_prompt,
            height=120,
            placeholder="Example: Compare ERP and invoice document values for INV-1036 and tell me if they differ.",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Send to agent", use_container_width=True)

    if not submitted:
        return

    prompt = (prompt or "").strip()
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Running finance agent..."):
        response = call_agent(prompt)
        structured_result = get_structured_result(prompt)

    texts = extract_text_blocks(response)
    answer = "\n\n".join(texts) if texts else "No response returned."
    answer_type = infer_answer_type(response)
    supporting_evidence = get_supporting_evidence(prompt, answer_type)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.latest_response = response
    st.session_state.latest_answer_type = answer_type
    st.session_state.latest_structured_result = structured_result
    st.session_state.latest_supporting_evidence = supporting_evidence

    st.experimental_rerun()


def render_debug_panel() -> None:
    response = st.session_state.latest_response
    if not response or not st.session_state.show_debug:
        return

    with st.expander("Raw agent response", expanded=False):
        st.json(response)

    with st.expander("Debug request payload", expanded=False):
        st.json(response.get("_debug_request", {}))

    with st.expander("Debug SQL", expanded=False):
        st.code(response.get("_debug_sql", ""), language="sql")


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="📈", layout="wide")
    init_state()
    apply_custom_theme()

    render_hero()
    render_sidebar()

    overview_tab, chat_tab = st.tabs(["Overview", "Agent Chat"])

    with overview_tab:
        render_overview()

    with chat_tab:
        st.markdown('<div class="ns-section-card"><div class="ns-card-title">Conversation workspace</div><div class="ns-card-copy">Review the dialog, then inspect the most recent grounding details and evidence tables.</div></div>', unsafe_allow_html=True)
        render_chat_history()
        render_latest_answer_panel()
        render_chat_input()
        render_debug_panel()


if __name__ == "__main__":
    main()
