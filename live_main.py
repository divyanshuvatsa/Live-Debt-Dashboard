"""
═══════════════════════════════════════════════════════════════════════════
JCL LIVE DEBT DASHBOARD — Main Entry Point
═══════════════════════════════════════════════════════════════════════════

A live, Excel-synced version of the JCL Debt Monitoring Dashboard.

KEY FEATURES vs v1/v2:
  ✅ Reads JCL_Debt_Model.xlsx DIRECTLY (no hardcoded data)
  ✅ When you save changes in Excel, the dashboard auto-refreshes
  ✅ Rule-based AI analyst — NO API KEY NEEDED, NO INTERNET REQUIRED
  ✅ All offline features removed (no live USD/INR fetch, no SOFR API)
  ✅ Single file to run: streamlit run live_main.py

HOW TO USE:
  1. Place JCL_Debt_Model.xlsx in the same folder as this file (or in /data/)
  2. Run: streamlit run live_main.py
  3. Open browser to http://localhost:8501
  4. Edit Excel → save → click "Reload from Excel" in sidebar (or refresh page)

EXCEL EDITS THAT WORK LIVE:
  ✅ Section A (Instructions tab): As-of date, FX rate, Full Util toggle, Basis
  ✅ Section B (Instructions tab): All 8 benchmark rates
  ✅ Section C (Instructions tab): All financials (EBITDA, Total Debt, etc.)
  ✅ Facility Master: Outstanding amounts (Col K), Rates (Col Q)

RUN COMMAND:
    streamlit run live_main.py

═══════════════════════════════════════════════════════════════════════════
"""

import sys
import os
from datetime import date

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="JCL Live Debt Dashboard",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "JCL Live Debt Dashboard — Live Excel-synced, offline AI analyst",
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
from live_jcl_data import (
    load_all_data, force_reload, get_excel_path, get_file_mtime,
)
from core.financial_logic import FinancialLogic
from ui.dashboard import DashboardUI
from ui.theme import CUSTOM_CSS

# Replace the AI analyst module reference - we use rule-based instead
import rule_based_analyst as ai_analyst

# Patch the dashboard's AI module so it uses our rule-based one
import core.ai_analyst as old_ai_module
old_ai_module.is_ai_available = ai_analyst.is_ai_available
old_ai_module.stream_ai_response = ai_analyst.stream_ai_response
old_ai_module.get_proactive_insights = ai_analyst.get_proactive_insights
old_ai_module.SUGGESTED_QUESTIONS = ai_analyst.SUGGESTED_QUESTIONS


# ─────────────────────────────────────────────────────────────────────────────
# INJECT CSS + LIVE BANNER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown("""
<style>
.live-banner {
    background: linear-gradient(90deg, #DC2626 0%, #EF4444 100%);
    color: white;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 600;
    text-align: center;
    margin-bottom: 12px;
    font-size: 13px;
    letter-spacing: 0.5px;
}
.live-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #FCA5A5;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    # Load data (live from Excel)
    raw = load_all_data()

    # Live banner
    excel_status = "🟢 LIVE" if raw["excel_exists"] else "🟡 FALLBACK"
    st.markdown(
        f'<div class="live-banner">'
        f'<span class="live-dot"></span>'
        f'{excel_status} · Live Debt Dashboard · '
        f'Excel: {raw["excel_mtime"]} · '
        f'Rule-based AI (no API)'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Sidebar reload button
    with st.sidebar:
        st.markdown("### 🔴 Live Excel Sync")
        if raw["excel_exists"]:
            st.caption(f"✅ Reading from:")
            st.code(str(get_excel_path()), language=None)
            st.caption(f"Last modified: {raw['excel_mtime']}")
            st.caption(f"File hash: `{raw['excel_hash'][:8]}...`")
        else:
            st.error(f"❌ Excel not found at expected path")
            st.code(str(get_excel_path()))
            st.caption("Using hardcoded fallback data")

        if st.button("🔄 Reload from Excel", use_container_width=True):
            force_reload()
            st.rerun()

        st.divider()

    # Initialize UI shell to render the sidebar and capture controls
    placeholder_logic = None
    ui = DashboardUI(placeholder_logic, raw)
    controls = ui.render_sidebar()

    # Build FinancialLogic engine with current controls
    logic = FinancialLogic(
        facility_master=raw["facility_master"],
        covenant_master=raw["covenant_master"],
        tl_schedule=raw["tl_schedule"],
        financials=raw["financials"],
        benchmark_rates=raw["benchmark_rates"],
        lender_caps=raw["lender_caps"],
        as_of_date=controls["as_of_date"],
        fx_rate=controls["fx_rate"],
        basis=controls["basis"],
    )

    # Re-bind UI to live logic
    ui.logic = logic

    # Render header & tabs
    ui.render_header(controls)

    tab_overview, tab_repayment, tab_covenants, tab_scenarios, tab_ai, tab_export = st.tabs([
        "📊 Overview",
        "💰 Repayment",
        "🛡️ Covenants",
        "🔬 Scenarios",
        "🤖 AI Analyst",
        "📥 Export",
    ])

    with tab_overview:
        ui.render_tab_executive_summary(controls)

    with tab_repayment:
        ui.render_tab_repayment(controls)

    with tab_covenants:
        ui.render_tab_covenants(controls)

    with tab_scenarios:
        ui.render_tab_scenarios(controls)

    with tab_ai:
        _render_ai_tab(logic, controls)

    with tab_export:
        ui.render_export(controls)

    # Footer
    st.divider()
    st.caption(
        f"JCL Live Debt Dashboard · "
        f"Excel-synced (no API) · "
        f"Source: {get_excel_path().name} · "
        f"As-of: {logic.as_of_date.strftime('%d-%b-%Y')} · "
        f"Basis: {logic.basis}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# AI TAB — uses rule-based engine (no API)
# ─────────────────────────────────────────────────────────────────────────────
def _render_ai_tab(logic, controls):
    st.markdown("### 🤖 Portfolio Analyst")
    st.caption("Rule-based engine · No API · Always available · Updates with Excel changes")

    # Proactive insights
    st.markdown("#### 💡 Proactive Insights")
    insights = ai_analyst.get_proactive_insights(logic, controls)
    if insights:
        cols = st.columns(len(insights))
        for col, ins in zip(cols, insights):
            with col:
                st.markdown(
                    f"<div style='background:#1E293B; padding:16px; border-radius:8px; border-left:3px solid #6366F1;'>"
                    f"<div style='font-weight:700; color:#A78BFA; font-size:13px; margin-bottom:8px;'>"
                    f"{ins['title']}</div>"
                    f"<div style='color:#CBD5E1; font-size:13px; line-height:1.5;'>"
                    f"{ins['body']}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
    st.divider()

    # Suggested questions
    st.markdown("#### 💬 Suggested Questions")
    cols = st.columns(2)
    if "ai_history" not in st.session_state:
        st.session_state.ai_history = []

    for i, q in enumerate(ai_analyst.SUGGESTED_QUESTIONS):
        with cols[i % 2]:
            if st.button(q, key=f"sq_{i}", use_container_width=True):
                st.session_state.ai_history.append({"role": "user", "content": q})
                # Generate response immediately
                response_text = ""
                for chunk in ai_analyst.stream_ai_response(q, logic, controls):
                    response_text += chunk
                st.session_state.ai_history.append({"role": "assistant", "content": response_text})
                st.rerun()

    st.divider()

    # Chat history
    st.markdown("#### 📝 Conversation")
    for msg in st.session_state.ai_history:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(msg["content"])
        st.markdown("---")

    # Chat input
    user_input = st.chat_input("Ask anything about JCL's debt portfolio...")
    if user_input:
        st.session_state.ai_history.append({"role": "user", "content": user_input})
        response_text = ""
        for chunk in ai_analyst.stream_ai_response(user_input, logic, controls):
            response_text += chunk
        st.session_state.ai_history.append({"role": "assistant", "content": response_text})
        st.rerun()

    if st.button("🗑️ Clear conversation"):
        st.session_state.ai_history = []
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
