"""
JCL LIVE DEBT DASHBOARD — Main Entry Point
Run with: streamlit run live_main.py
"""

import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

st.set_page_config(
    page_title="JCL Live Debt Dashboard",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded",
)

from live_jcl_data import (
    load_all_data, force_reload, get_excel_path, get_file_mtime,
)
from core.financial_logic import FinancialLogic
from ui.dashboard import DashboardUI
from ui.theme import CUSTOM_CSS

import rule_based_analyst as rba
import core.ai_analyst as ai_module
ai_module.is_ai_available        = rba.is_ai_available
ai_module.stream_ai_response     = rba.stream_ai_response
ai_module.get_proactive_insights = rba.get_proactive_insights
ai_module.SUGGESTED_QUESTIONS    = rba.SUGGESTED_QUESTIONS

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown("""
<style>
.live-banner {
    background: linear-gradient(90deg, #DC2626 0%, #EF4444 100%);
    color: white; padding: 8px 16px; border-radius: 6px;
    font-weight: 600; text-align: center; margin-bottom: 12px;
    font-size: 13px; letter-spacing: 0.5px;
}
</style>
""", unsafe_allow_html=True)

DEFAULT_CONTROLS = {
    "as_of_date":    date(2026, 4, 21),
    "fx_rate":       92.98,
    "basis":         "FY26E",
    "rate_shock":    0,
    "spread_shock":  0,
    "ebitda_change": 0,
    "export_format": "Word",
}


def build_logic(raw, controls):
    return FinancialLogic(
        facility_master = raw["facility_master"],
        covenant_master = raw["covenant_master"],
        tl_schedule     = raw["tl_schedule"],
        financials      = raw["financials"],
        benchmark_rates = raw["benchmark_rates"],
        as_of_date      = controls["as_of_date"],
        fx_rate         = controls["fx_rate"],
        basis           = controls["basis"],
    )


def main():
    raw = load_all_data()

    excel_status = "🟢 LIVE" if raw["excel_exists"] else "🟡 FALLBACK"
    st.markdown(
        f'<div class="live-banner">● {excel_status} · Live Debt Dashboard · '
        f'Excel: {raw["excel_mtime"]} · Rule-based AI (no API)</div>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("### 🔴 Live Excel Sync")
        if raw["excel_exists"]:
            st.caption("✅ Reading from:")
            st.code(str(get_excel_path()), language=None)
            st.caption(f"Last modified: {raw['excel_mtime']}")
            st.caption(f"Hash: `{raw['excel_hash'][:8]}...`")
        else:
            st.error("❌ Excel not found")
            st.code(str(get_excel_path()))
            st.caption("Using hardcoded fallback data")

        if st.button("🔄 Reload from Excel", use_container_width=True):
            force_reload()
            st.rerun()

        st.divider()

    # Build logic with defaults first so DashboardUI has a valid logic object
    logic = build_logic(raw, DEFAULT_CONTROLS)

    # Init UI + get real controls from sidebar
    ui = DashboardUI(logic, raw)
    controls = ui.render_sidebar()

    # Rebuild logic with real sidebar controls
    logic = build_logic(raw, controls)
    ui.logic = logic

    ui.render_header(controls)

    tab_overview, tab_repayment, tab_covenants, tab_scenarios, tab_ai, tab_export = st.tabs([
        "📊 Overview", "💰 Repayment", "🛡️ Covenants",
        "🔬 Scenarios", "🤖 AI Analyst", "📥 Export",
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

    st.divider()
    st.caption(
        f"JCL Live Debt Dashboard · Source: {get_excel_path().name} · "
        f"As-of: {logic.as_of_date.strftime('%d-%b-%Y')} · "
        f"Basis: {logic.basis} · Rule-based AI — no API"
    )


def _render_ai_tab(logic, controls):
    st.markdown("### 🤖 Portfolio Analyst")
    st.caption("Rule-based engine · No API key · Always available · Updates with Excel")

    st.markdown("#### 💡 Proactive Insights")
    try:
        insights = rba.get_proactive_insights(logic, controls)
        cols = st.columns(len(insights))
        for col, ins in zip(cols, insights):
            with col:
                st.markdown(
                    f"<div style='background:#1E293B;padding:16px;border-radius:8px;"
                    f"border-left:3px solid #6366F1;'>"
                    f"<div style='font-weight:700;color:#A78BFA;font-size:13px;"
                    f"margin-bottom:8px;'>{ins['title']}</div>"
                    f"<div style='color:#CBD5E1;font-size:13px;line-height:1.5;'>"
                    f"{ins['body']}</div></div>",
                    unsafe_allow_html=True,
                )
    except Exception as e:
        st.warning(f"Could not generate insights: {e}")

    st.divider()

    if "ai_history" not in st.session_state:
        st.session_state.ai_history = []

    st.markdown("#### 💬 Suggested Questions")
    cols = st.columns(2)
    for i, q in enumerate(rba.SUGGESTED_QUESTIONS):
        with cols[i % 2]:
            if st.button(q, key=f"sq_{i}", use_container_width=True):
                st.session_state.ai_history.append({"role": "user", "content": q})
                response_text = "".join(rba.stream_ai_response(q, logic, controls))
                st.session_state.ai_history.append({"role": "assistant", "content": response_text})
                st.rerun()

    st.divider()
    st.markdown("#### 📝 Conversation")
    for msg in st.session_state.ai_history:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(msg["content"])
        st.markdown("---")

    user_input = st.chat_input("Ask anything about JCL's debt portfolio...")
    if user_input:
        st.session_state.ai_history.append({"role": "user", "content": user_input})
        response_text = "".join(rba.stream_ai_response(user_input, logic, controls))
        st.session_state.ai_history.append({"role": "assistant", "content": response_text})
        st.rerun()

    if st.session_state.ai_history:
        if st.button("🗑️ Clear conversation"):
            st.session_state.ai_history = []
            st.rerun()


if __name__ == "__main__":
    main()
