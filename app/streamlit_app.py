import json
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
from snowflake.snowpark.context import get_active_session


APP_TITLE = "Finance Hybrid Assistant"
AGENT_NAME = "FIN_ENT_AI_POC.APP.FINANCE_HYBRID_AGENT_POC"
DEFAULT_SUGGESTIONS = [
    "What is total revenue by customer?",
    "Which customers have the highest open amount?",
    "What does invoice INV-1010 say about the total amount due?",
    "Compare ERP and invoice document values for INV-1010 and tell me if they differ.",
]


def get_session():
    return get_active_session()


@st.cache_data(show_spinner=False)
def get_session_context() -> Dict[str, str]:
    session = get_session()
    row = session.sql(
        """
        SELECT
          CURRENT_USER() AS USER_NAME,
          CURRENT_ROLE() AS ROLE_NAME,
          CURRENT_DATABASE() AS DATABASE_NAME,
          CURRENT_SCHEMA() AS SCHEMA_NAME,
          CURRENT_WAREHOUSE() AS WAREHOUSE_NAME,
          CURRENT_USER() AS USER_NAME
        """
    ).collect()[0]
    return {
        "user": row["USER_NAME"],
        "role": row["ROLE_NAME"],
        "database": row["DATABASE_NAME"],
        "schema": row["SCHEMA_NAME"],
        "warehouse": row["WAREHOUSE_NAME"],
        "user": row["USER_NAME"],
    }


@st.cache_data(show_spinner=False)
def get_reconciliation_summary() -> List[Dict[str, Any]]:
    session = get_session()
    rows = session.sql(
        """
        SELECT OVERALL_RECON_STATUS, COUNT(*) AS INVOICE_COUNT
        FROM FIN_ENT_AI_POC.CURATED_FINANCE.INVOICE_RECON_V
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
        FROM FIN_ENT_AI_POC.CURATED_FINANCE.CUSTOMER_BALANCE_SUM_V
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
        FROM FIN_ENT_AI_POC.CURATED_FINANCE.INVOICE_RECON_V
        WHERE OVERALL_RECON_STATUS = 'MISMATCH'
        ORDER BY INVOICE_ID
        LIMIT 10
        """
    ).collect()
    return [r.as_dict() for r in rows]


def build_request(messages: List[Dict[str, Any]]) -> str:
    payload = {
        "messages": messages,
        "stream": False,
    }
    return json.dumps(payload)


def call_agent(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    session = get_session()
    request_json = build_request(messages)
    escaped_request = request_json.replace("'", "''")
    sql = f"""
        SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
          '{AGENT_NAME}',
          $$ {escaped_request} $$
        ) AS RESPONSE
    """
    row = session.sql(sql).collect()[0]
    raw = row["RESPONSE"]

    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"raw_text": raw}

    if isinstance(raw, dict):
        return raw

    return {"raw_text": str(raw)}


def extract_text_blocks(response: Dict[str, Any]) -> List[str]:
    content = response.get("content", [])
    texts: List[str] = []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
                texts.append(str(item["text"]))
    if not texts and response.get("raw_text"):
        texts.append(str(response["raw_text"]))
    return texts


def extract_tool_hints(response: Dict[str, Any]) -> List[str]:
    hints: List[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                lower_key = str(key).lower()
                if lower_key in {"tool_name", "tool", "selected_tool", "name"} and isinstance(value, str):
                    if any(token in value.lower() for token in ["analyst", "search", "tool", "finance", "invoice"]):
                        hints.append(value)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(response)
    seen = []
    for hint in hints:
        if hint not in seen:
            seen.append(hint)
    return seen[:10]


def init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Ask a finance question about revenue, open balances, invoice mismatches, or invoice document evidence.",
            }
        ]
    if "raw_responses" not in st.session_state:
        st.session_state.raw_responses = []
    


def render_sidebar() -> None:
    ctx = get_session_context()
    st.sidebar.header("Session")
    st.sidebar.write(f"**User:** {ctx['user']}")
    st.sidebar.write(f"**Role:** {ctx['role']}")
    st.sidebar.write(f"**Warehouse:** {ctx['warehouse']}")
    st.sidebar.write(f"**Database:** {ctx['database']}")
    st.sidebar.write(f"**Schema:** {ctx['schema']}")
    st.sidebar.divider()

    show_debug = st.sidebar.checkbox("Show debug panels", value=True)
    st.session_state.show_debug = show_debug

    if st.sidebar.button("Clear chat", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Chat cleared. Ask another finance question.",
            }
        ]
        st.session_state.raw_responses = []
        st.rerun()

    st.sidebar.divider()
    st.sidebar.subheader("Starter questions")
    for suggestion in DEFAULT_SUGGESTIONS:
        if st.sidebar.button(suggestion, key=f"suggestion_{suggestion}"):
            st.session_state.pending_prompt = suggestion


def render_overview() -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Reconciliation status")
        recon = get_reconciliation_summary()
        if recon:
            st.dataframe(recon, use_container_width=True)
    with col2:
        st.subheader("Top open balances")
        top_open = get_top_open_balances()
        if top_open:
            st.dataframe(top_open, use_container_width=True)

    with st.expander("Recent mismatch examples", expanded=False):
        mismatches = get_recent_mismatches()
        if mismatches:
            st.dataframe(mismatches, use_container_width=True)


def convert_history_for_agent(chat_messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    payload_messages: List[Dict[str, Any]] = []
    for msg in chat_messages:
        role = msg.get("role", "user")
        if role not in {"user", "assistant"}:
            continue
        payload_messages.append(
            {
                "role": role,
                "content": [
                    {
                        "type": "text",
                        "text": msg.get("content", ""),
                    }
                ],
            }
        )
    return payload_messages


def render_chat() -> None:
    st.subheader("Chat")

    for msg in st.session_state.messages:
        role_label = "Assistant" if msg["role"] == "assistant" else "You"
        with st.container():
            st.markdown(f"**{role_label}:**")
            st.markdown(msg["content"])
            st.markdown("---")

    pending_prompt = st.session_state.pop("pending_prompt", None)

    with st.form("agent_chat_form", clear_on_submit=True):
        prompt_default = pending_prompt if pending_prompt else ""
        prompt = st.text_area("Ask the Finance Hybrid Assistant", value=prompt_default, height=100)
        submitted = st.form_submit_button("Send")

    if not submitted or not prompt or not prompt.strip():
        return

    prompt = prompt.strip()
    st.session_state.messages.append({"role": "user", "content": prompt})

    history = convert_history_for_agent(st.session_state.messages)
    with st.spinner("Running agent..."):
        response = call_agent(history)
        texts = extract_text_blocks(response)
        answer = "".join(texts) if texts else "No response text returned. Open the debug panel to inspect the raw payload."
        tool_hints = extract_tool_hints(response)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.raw_responses.append(response)

    st.markdown("**Assistant:**")
    st.markdown(answer)
    if tool_hints:
        st.caption("Possible tools used: " + ", ".join(tool_hints))

    if st.session_state.get("show_debug", True):
        with st.expander("Raw agent response", expanded=False):
            st.json(response)


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="💼", layout="wide")
    init_state()

    st.title(APP_TITLE)
    st.caption(
        "Hybrid Snowflake chatbot using Cortex Analyst for structured finance data and Cortex Search for invoice-document retrieval."
    )

    render_sidebar()

    overview_tab, chat_tab = st.tabs(["Overview", "Agent Chat"])
    with overview_tab:
        render_overview()
    with chat_tab:
        render_chat()


if __name__ == "__main__":
    main()
