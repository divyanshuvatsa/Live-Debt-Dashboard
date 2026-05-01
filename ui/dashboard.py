"""
JCL Debt Monitoring Dashboard — UI Module
Streamlit-based interactive dashboard with 4 tabs:
  1. Executive Summary
  2. Repayment & Liquidity
  3. Covenant Monitoring
  4. Scenario Engine
"""

from datetime import date, datetime
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from ui.theme import (
    COLORS, LENDER_COLORS, CATEGORY_COLORS, STATUS_COLORS,
    CHART_LAYOUT, CUSTOM_CSS,
)
from ui.insights import (
    generate_executive_insights, generate_repayment_insights,
    generate_covenant_insights, generate_scenario_insights,
    calculate_health_score, COVENANT_DEFINITIONS,
    generate_recommendations, generate_bottom_line,
)


# =============================================================================
# RENDERING HELPERS
# =============================================================================
def render_hero(verdict: str, color: str, narrative: str):
    """Senior-management hero section with verdict badge + narrative."""
    st.markdown(f"""
    <div class="hero-section">
        <div class="hero-verdict-badge" style="background: {color}; color: white;">
            ● {verdict}
        </div>
        <p class="hero-narrative">{narrative}</p>
    </div>
    """, unsafe_allow_html=True)


def render_tab_header(label: str, title: str, subtitle: str = ""):
    """Section header for each tab."""
    sub_html = f'<div class="tab-header-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""
    <div class="tab-header">
        <div class="tab-header-label">{label}</div>
        <div class="tab-header-title">{title}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def render_big_kpi(label: str, value: str, sub: str = "", color: str = "#F1F5F9"):
    """Render a single big KPI tile."""
    st.markdown(f"""
    <div class="big-kpi">
        <div class="big-kpi-label">{label}</div>
        <div class="big-kpi-value" style="color: {color};">{value}</div>
        <div class="big-kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


def render_recommendations(recs: list):
    """Render recommended actions panel."""
    if not recs:
        return
    # Sort by priority: HIGH > MEDIUM > LOW > INFO
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
    recs_sorted = sorted(recs, key=lambda r: priority_order.get(r["priority"], 99))
    for r in recs_sorted:
        st.markdown(f"""
        <div class="action-card {r['priority']}">
            <div class="action-priority {r['priority']}">{r['priority']}</div>
            <div class="action-content">
                <div class="action-title">{r['title']}</div>
                <div class="action-body">{r['body']}</div>
                <div class="action-owner">Owner: {r['owner']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_insight_cards(insights: list, cols: int = 2):
    """Render a grid of insight cards."""
    if not insights:
        return
    columns = st.columns(cols)
    for i, ins in enumerate(insights):
        with columns[i % cols]:
            st.markdown(f"""
            <div class="insight-card {ins['level']}">
                <div class="insight-icon">{ins['icon']}</div>
                <div class="insight-content">
                    <div class="insight-title">{ins['title']}</div>
                    <div class="insight-body">{ins['body']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_narrative_banner(title: str, body: str):
    """Render a narrative banner with rich text."""
    st.markdown(f"""
    <div class="narrative-banner">
        <div class="narrative-banner-title">📖 {title}</div>
        <div class="narrative-banner-body">{body}</div>
    </div>
    """, unsafe_allow_html=True)


def render_health_gauge(health: dict):
    """Render a health score gauge with components breakdown."""
    components_html = ""
    for name, data in health["components"].items():
        pct = data["score"] / data["max"] * 100
        components_html += f"""
        <div class="health-component">
            <span>{name}</span>
            <span style="display: flex; align-items: center; gap: 8px;">
                <strong style="color: #F1F5F9;">{data['score']}/{data['max']}</strong>
                <span class="health-component-bar">
                    <span class="health-component-bar-fill" style="width: {pct}%;"></span>
                </span>
            </span>
        </div>
        """
    st.markdown(f"""
    <div class="health-gauge">
        <div style="font-size: 0.78rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600;">
            Portfolio Health Score
        </div>
        <div class="health-score" style="color: {health['color']};">{health['total']}</div>
        <div class="health-rating" style="color: {health['color']};">{health['rating']}</div>
        <div style="margin-top: 16px;">
            {components_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================
def fmt_inr(amount: float, decimals: int = 1) -> str:
    """Format INR Cr with comma separation."""
    if pd.isna(amount): return "—"
    return f"₹{amount:,.{decimals}f}"

def fmt_pct(value: float, decimals: int = 2) -> str:
    if pd.isna(value): return "—"
    return f"{value*100:.{decimals}f}%"

def fmt_ratio(value: float, decimals: int = 2) -> str:
    if pd.isna(value): return "—"
    if isinstance(value, str): return value
    return f"{value:.{decimals}f}x"

def status_class(status: str) -> str:
    return {
        "Compliant":   "compliant",
        "Watch":       "watch",
        "Near Breach": "near",
        "Breach":      "breach",
    }.get(status, "watch")


def chart_layout(**overrides) -> dict:
    """Return CHART_LAYOUT merged with caller's overrides (overrides win)."""
    out = dict(CHART_LAYOUT)
    out.update(overrides)
    return out


def chart_layout_no_margin() -> dict:
    """Backwards-compat helper: CHART_LAYOUT without margin."""
    return {k: v for k, v in CHART_LAYOUT.items() if k != "margin"}


# =============================================================================
# DASHBOARD UI CLASS
# =============================================================================
class DashboardUI:
    def __init__(self, logic_engine, raw_data):
        self.logic = logic_engine
        self.raw = raw_data

    # =========================================================================
    # SIDEBAR
    # =========================================================================
    def render_sidebar(self):
        with st.sidebar:
            st.markdown("""
            <div style="padding: 16px 0; border-bottom: 1px solid #334155;">
                <h1 style="font-size: 1.4rem; margin: 0;
                    background: linear-gradient(90deg, #60A5FA 0%, #C084FC 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;">
                    📊 JCL Debt Monitor
                </h1>
                <p style="color: #94A3B8; font-size: 0.78rem; margin: 4px 0 0 0;">
                    Jindal Coke Limited
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("### ⚙️ Controls")

            as_of_date = st.date_input(
                "📅 As-of Date",
                value=date(2026, 4, 21),
                help="Drives remaining-tenor and maturity calculations. All days-to-validity and aging buckets are computed against this date.",
                key="as_of_date_input",
            )

            fx_rate = st.number_input(
                "💱 USD / INR Rate",
                min_value=70.0,
                max_value=120.0,
                value=92.98,
                step=0.50,
                help="Used for USD Buyer's Credit conversions. The effective INR exposure for USD facilities = MIN(USD × FX, INR cap).",
                key="fx_rate_input",
            )

            basis = st.radio(
                "📊 Financial Basis",
                options=["FY26E", "FY24A"],
                index=0,
                horizontal=True,
                help="FY26E = Projected (forward-looking). FY24A = Audited (historical reality). Toggle to compare covenant compliance under different financial states.",
                key="basis_input",
            )

            st.markdown("---")
            st.markdown("### 🔬 Scenario Engine")
            st.caption("Real-time stress overlay on covenants & interest cost.")

            # Quick action buttons (preset scenarios)
            st.markdown("**Quick Scenarios:**")
            qa1, qa2 = st.columns(2)
            with qa1:
                preset_rate100 = st.button("📈 Rate +100", width="stretch", help="100bps parallel rate shock")
                preset_severe  = st.button("⛈️ Severe Stress", width="stretch", help="Rate +200, Spread +100, EBITDA -30%")
            with qa2:
                preset_ebitda  = st.button("📉 EBITDA -20%", width="stretch", help="Earnings stress only")
                preset_reset   = st.button("🔄 Reset", width="stretch", help="Return to base case")

            # Apply preset BEFORE rendering sliders so the slider's default takes effect
            if preset_rate100:
                st.session_state["rate_shock_input"] = 100
                st.session_state["spread_shock_input"] = 0
                st.session_state["ebitda_change_input"] = 0
            elif preset_severe:
                st.session_state["rate_shock_input"] = 200
                st.session_state["spread_shock_input"] = 100
                st.session_state["ebitda_change_input"] = -30
            elif preset_ebitda:
                st.session_state["rate_shock_input"] = 0
                st.session_state["spread_shock_input"] = 0
                st.session_state["ebitda_change_input"] = -20
            elif preset_reset:
                st.session_state["rate_shock_input"] = 0
                st.session_state["spread_shock_input"] = 0
                st.session_state["ebitda_change_input"] = 0

            # Initialize defaults if first run (only if preset wasn't pressed)
            if "rate_shock_input" not in st.session_state:
                st.session_state["rate_shock_input"] = 0
            if "spread_shock_input" not in st.session_state:
                st.session_state["spread_shock_input"] = 0
            if "ebitda_change_input" not in st.session_state:
                st.session_state["ebitda_change_input"] = 0

            # Sliders use only key (no value=) since session_state is set
            rate_shock = st.slider(
                "Rate Shock (bps)",
                min_value=-100, max_value=200, step=25,
                help="Parallel shift in floating-rate benchmarks (Repo, MCLR, BFRR). Affects only floating-rate facilities.",
                key="rate_shock_input",
            )
            spread_shock = st.slider(
                "Spread Increase (bps)",
                min_value=0, max_value=200, step=25,
                help="Lender-imposed spread widening on top of benchmark. Models credit-rating-driven repricing.",
                key="spread_shock_input",
            )
            ebitda_change = st.slider(
                "EBITDA Change (%)",
                min_value=-30, max_value=20, step=5,
                help="Earnings shock for covenant testing. Negative values stress DSCR, ICR, leverage ratios.",
                key="ebitda_change_input",
            )

            if rate_shock != 0 or spread_shock != 0 or ebitda_change != 0:
                st.markdown(
                    f"<div class='alert-banner'>⚠️ <b>Stress Mode Active</b><br/>"
                    f"Rate {rate_shock:+d}bps • Spread {spread_shock:+d}bps • EBITDA {ebitda_change:+d}%</div>",
                    unsafe_allow_html=True,
                )

            st.markdown("---")
            with st.expander("📖 Covenant Glossary", expanded=False):
                st.caption("Quick reference for all financial covenants")
                for name, defn in COVENANT_DEFINITIONS.items():
                    st.markdown(f"""
                    <div class="glossary-entry">
                        <div class="glossary-name">{name}</div>
                        <div class="glossary-formula">{defn['formula']}</div>
                        <div class="glossary-interpretation">{defn['interpretation']}</div>
                        <div class="glossary-rot">💡 {defn['rule_of_thumb']}</div>
                    </div>
                    """, unsafe_allow_html=True)

            with st.expander("🎓 How to Use", expanded=False):
                st.markdown("""
                **1. Set the snapshot date** at the top — drives maturity calculations.

                **2. Choose Financial Basis** — FY26E (projected) shows forward outlook; FY24A (audited) shows historical reality.

                **3. Tab through the dashboard:**
                - 📈 **Executive Summary** — Top-level KPIs and portfolio health
                - 💰 **Repayment** — Term loan obligations and renewal schedule
                - 🛡️ **Covenants** — All 24 covenants with status
                - 🔬 **Scenarios** — Stress test the portfolio
                - 📥 **Export** — Download CSV reports

                **4. Stress test** with the sliders — every slider triggers real-time recomputation.

                **5. Filter by lender** to focus on a specific bank's exposure.

                **6. Hover** any chart, value, or icon for details.
                """)

            st.markdown("---")
            st.markdown("### 📥 Export")
            export_format = st.radio(
                "Format",
                options=["CSV", "Excel"],
                horizontal=True,
                key="export_format",
            )

            return {
                "as_of_date": as_of_date,
                "fx_rate": fx_rate,
                "basis": basis,
                "rate_shock": rate_shock,
                "spread_shock": spread_shock,
                "ebitda_change": ebitda_change,
                "export_format": export_format,
            }

    # =========================================================================
    # HEADER BANNER
    # =========================================================================
    def render_header(self, controls):
        col1, col2, col3 = st.columns([5, 2, 2])
        with col1:
            st.markdown(f"""
            <div class="brand-bar">
                <div class="brand-title">JCL Debt Monitoring Dashboard</div>
                <div class="brand-subtitle">
                    Lender-wise Facility Tracking · Covenant Compliance · Scenario Stress Testing
                    · As-of {controls['as_of_date'].strftime('%d-%b-%Y')}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="background: #1E293B; border-radius: 12px; padding: 14px 18px; text-align: right;">
                <div style="color: #94A3B8; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">FX Rate</div>
                <div style="color: #F1F5F9; font-size: 1.3rem; font-weight: 700;">₹{controls['fx_rate']:.2f}/USD</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div style="background: #1E293B; border-radius: 12px; padding: 14px 18px; text-align: right;">
                <div style="color: #94A3B8; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Basis</div>
                <div style="color: #F1F5F9; font-size: 1.3rem; font-weight: 700;">{controls['basis']}</div>
            </div>
            """, unsafe_allow_html=True)

    # =========================================================================
    # TAB 1: EXECUTIVE SUMMARY (SENIOR MANAGEMENT VIEW)
    # =========================================================================
    def render_tab_executive_summary(self, controls):
        # 1. HERO — verdict + bottom-line narrative
        bl = generate_bottom_line(self.logic, controls)
        render_hero(bl["verdict"], bl["color"], bl["narrative"])

        # 2. THE FOUR KEY METRICS — big tiles, lots of breathing room
        render_tab_header("AT A GLANCE", "Portfolio Metrics", "")

        ls = self.logic.lender_summary()
        total_sanc = ls["Total_Sanction"].sum()
        wac        = self.logic.weighted_avg_cost(controls["rate_shock"], controls["spread_shock"])
        annual_int = self.logic.calculate_annual_interest(controls["rate_shock"], controls["spread_shock"])
        cov_df     = self.logic.calculate_covenants(controls["ebitda_change"])
        compliant  = (cov_df["Status"] == "Compliant").sum()
        near       = (cov_df["Status"] == "Near Breach").sum()
        breach     = (cov_df["Status"] == "Breach").sum()
        health     = calculate_health_score(self.logic, controls)

        c1, c2, c3, c4 = st.columns(4)
        with c1: render_big_kpi(
            "Total Debt Portfolio",
            f"₹{total_sanc:,.0f} Cr",
            f"Across {len(self.logic.facility_master)} facilities, 5 lenders",
        )
        with c2: render_big_kpi(
            "Annual Cost",
            f"₹{annual_int['total']:.0f} Cr",
            f"Weighted avg rate: {wac*100:.2f}%",
            color="#FBBF24" if wac > 0.08 else "#F1F5F9",
        )
        with c3: render_big_kpi(
            "Covenant Status",
            f"{compliant}/{len(cov_df)}",
            "All compliant" if (breach + near) == 0 else
            f"{breach} breach, {near} near breach",
            color=health["color"],
        )
        with c4: render_big_kpi(
            "Health Score",
            f"{health['total']}/100",
            health["rating"],
            color=health["color"],
        )

        # 3. RECOMMENDED ACTIONS — what management actually cares about
        render_tab_header(
            "PRIORITY",
            "Recommended Actions",
            "Auto-generated from current portfolio state. Updates live with stress sliders."
        )
        recs = generate_recommendations(self.logic, controls)
        render_recommendations(recs)

        # 4. PORTFOLIO COMPOSITION — single donut, prominent
        render_tab_header(
            "STRUCTURE",
            "Lender Concentration",
            "Distribution of total exposure across our 5 banking partners.",
        )

        c1, c2 = st.columns([2, 1])
        with c1:
            ls_sorted = ls.sort_values("Total_Sanction", ascending=False)
            fig = go.Figure(data=[go.Pie(
                labels=ls_sorted["Lender"],
                values=ls_sorted["Total_Sanction"],
                hole=0.60,
                marker=dict(
                    colors=[LENDER_COLORS[l] for l in ls_sorted["Lender"]],
                    line=dict(color=COLORS["bg_secondary"], width=3),
                ),
                textinfo="label+percent",
                textposition="outside",
                textfont=dict(size=13, color=COLORS["text_primary"]),
                hovertemplate="<b>%{label}</b><br>Sanctioned: ₹%{value:.1f} Cr<br>Share: %{percent}<extra></extra>",
            )])
            fig.update_layout(
                **CHART_LAYOUT,
                height=420,
                showlegend=False,
                annotations=[dict(
                    text=f"<b>₹{total_sanc:,.0f}</b><br><span style='font-size: 0.95rem; color:#94A3B8'>Cr Total</span>",
                    x=0.5, y=0.5, font=dict(size=26, color=COLORS["text_primary"]), showarrow=False,
                )],
            )
            st.plotly_chart(fig, width="stretch")

        with c2:
            top_lender = ls_sorted.iloc[0]
            top_share = top_lender["Total_Sanction"] / total_sanc * 100
            st.markdown(f"""
            <div style="padding: 16px 0;">
                <div style="font-size: 0.78rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600;">
                    Largest Lender
                </div>
                <div style="font-size: 1.6rem; font-weight: 700; color: #F1F5F9; margin: 4px 0;">
                    {top_lender['Lender']}
                </div>
                <div style="font-size: 0.95rem; color: #CBD5E1;">
                    ₹{top_lender['Total_Sanction']:,.0f} Cr
                    <span class="mini-stat">{top_share:.0f}% of total</span>
                </div>
            </div>
            <div style="padding: 16px 0; border-top: 1px solid #334155; margin-top: 12px;">
                <div style="font-size: 0.78rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600;">
                    Concentration
                </div>
                <div style="font-size: 1.6rem; font-weight: 700; color: {'#F59E0B' if top_share > 40 else '#10B981'}; margin: 4px 0;">
                    {'Moderate' if top_share > 40 else 'Diversified'}
                </div>
                <div style="font-size: 0.85rem; color: #94A3B8;">
                    {'Top lender > 40%' if top_share > 40 else 'No lender exceeds 40%'}
                </div>
            </div>
            <div style="padding: 16px 0; border-top: 1px solid #334155;">
                <div style="font-size: 0.78rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600;">
                    Number of Lenders
                </div>
                <div style="font-size: 1.6rem; font-weight: 700; color: #F1F5F9; margin: 4px 0;">
                    {len(ls)}
                </div>
                <div style="font-size: 0.85rem; color: #94A3B8;">
                    Active banking relationships
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 5. DETAIL VIEW — hidden by default, available on demand
        with st.expander("🔍 View detailed lender breakdown", expanded=False):
            ls_display = ls.copy()
            ls_display = ls_display.rename(columns={
                "Total_Sanction": "Total Sanc.", "Outstanding": "Outstanding",
                "Headroom": "Headroom", "FB_Sanction": "FB",
                "NFB_Sanction": "NFB", "TL_Sanction": "Term Loan",
                "Num_Facilities": "# Facilities", "Weighted_Avg_Cost": "WAC",
                "Utilization": "Utilization",
            })
            ls_display["WAC"] = ls_display["WAC"].apply(lambda x: f"{x*100:.2f}%")
            ls_display["Utilization"] = ls_display["Utilization"].apply(lambda x: f"{x*100:.1f}%")
            for col in ["Total Sanc.", "Outstanding", "Headroom", "FB", "NFB", "Term Loan"]:
                ls_display[col] = ls_display[col].apply(lambda x: f"₹{x:,.1f}")
            ls_display = ls_display[["Lender", "Total Sanc.", "Outstanding", "Headroom",
                                     "FB", "NFB", "Term Loan", "# Facilities", "WAC", "Utilization"]]
            st.dataframe(ls_display, width="stretch", hide_index=True)

            st.markdown("**Glossary:** FB = Fund-Based · NFB = Non-Fund-Based (LCs/BGs) · "
                        "WAC = Weighted Avg Cost of Debt")

        with st.expander("📊 View facility category breakdown", expanded=False):
            cat_agg = self.logic.facility_master.groupby("Category").agg(
                Sanction=("Sanction_INR", "sum"), Count=("Facility", "count")
            ).reset_index().sort_values("Sanction", ascending=True)
            fig = go.Figure(go.Bar(
                x=cat_agg["Sanction"], y=cat_agg["Category"], orientation="h",
                text=[f"₹{v:,.0f} Cr ({c} fac.)" for v, c in zip(cat_agg["Sanction"], cat_agg["Count"])],
                textposition="outside",
                marker=dict(color=[CATEGORY_COLORS.get(c, COLORS["blue"]) for c in cat_agg["Category"]]),
                hovertemplate="<b>%{y}</b><br>Sanctioned: ₹%{x:.1f} Cr<extra></extra>",
            ))
            fig.update_layout(
                **chart_layout_no_margin(), height=320, xaxis_title="Sanctioned (INR Cr)",
                yaxis=dict(showgrid=False), xaxis=dict(showgrid=True, gridcolor="#334155"),
                margin=dict(l=120, r=80, t=20, b=40),
            )
            st.plotly_chart(fig, width="stretch")

    # =========================================================================
    # TAB 2: LIQUIDITY & REPAYMENT (SENIOR MANAGEMENT VIEW)
    # =========================================================================
    def render_tab_repayment(self, controls):
        # Hero / bottom line
        sched = self.logic.tl_schedule
        future = sched[sched["Period_End"] >= self.logic.as_of_date]
        next_12m = future[future["Period_End"] <= self.logic.as_of_date + pd.Timedelta(days=365)]
        next_12m_total = next_12m["Principal"].sum() + next_12m["Interest"].sum()

        buckets = self.logic.maturity_buckets()
        renewals_60d = buckets[buckets["Days_to_Validity"].notna() &
                                (buckets["Days_to_Validity"] >= 0) &
                                (buckets["Days_to_Validity"] <= 60)]

        if len(renewals_60d) > 5:
            verdict, color = "RENEWALS DUE", "#F59E0B"
            narrative = (f"<b>{len(renewals_60d)} working capital facilities</b> (₹{renewals_60d['Sanction_INR'].sum():,.0f} Cr) "
                         f"require renewal in the next 60 days. "
                         f"Next 12 months of term loan obligations: ₹<b>{next_12m_total:.0f} Cr</b>.")
        else:
            verdict, color = "ON TRACK", "#10B981"
            narrative = (f"Term loan portfolio is on a structured path with <b>3 facilities</b> "
                         f"(RBL, YBL, Bajaj) maturing between <b>2029 and 2036</b>. "
                         f"Next 12 months require ₹<b>{next_12m_total:.0f} Cr</b> in debt servicing.")

        render_hero(verdict, color, narrative)

        # Big KPIs
        render_tab_header("LIQUIDITY", "Cash Flow Obligations", "")
        c1, c2, c3, c4 = st.columns(4)
        with c1: render_big_kpi("Term Loans Outstanding", "₹670.7 Cr", "3 active facilities")
        with c2: render_big_kpi("Next 12 Months", f"₹{next_12m_total:.0f} Cr",
                                 f"Principal ₹{next_12m['Principal'].sum():.0f} + Interest ₹{next_12m['Interest'].sum():.0f}")
        with c3: render_big_kpi("Longest Maturity", "Sep-2036", "YBL Term Loan")
        with c4:
            base_dscr = self.logic.calculate_covenants()["Actual"].iloc[0]
            render_big_kpi("DSCR Coverage", f"{base_dscr:.2f}x",
                            "vs 1.25x threshold",
                            color="#10B981" if base_dscr > 1.5 else "#F59E0B")

        # Maturity profile chart
        render_tab_header(
            "TIMELINE",
            "Annual Principal Maturity Profile",
            "When does our term debt actually have to be repaid? "
            "Stacked bars show repayment burden by financial year, color-coded by lender."
        )

        annual = self.logic.annual_tl_principal()
        annual_pivot = annual.pivot(index="FY_Label", columns="Lender", values="Principal").fillna(0).sort_index()
        fig = go.Figure()
        for lender in annual_pivot.columns:
            fig.add_trace(go.Bar(
                name=lender, x=annual_pivot.index, y=annual_pivot[lender],
                marker_color=LENDER_COLORS.get(lender, COLORS["blue"]),
                hovertemplate=f"<b>{lender}</b><br>%{{x}}<br>₹%{{y:.1f}} Cr<extra></extra>",
            ))
        fig.update_layout(
            **CHART_LAYOUT, height=400, barmode="stack",
            xaxis=dict(title="Financial Year", showgrid=False),
            yaxis=dict(title="Principal Repayment (INR Cr)", showgrid=True, gridcolor="#334155"),
            legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.20),
        )
        st.plotly_chart(fig, width="stretch")

        # Renewals required
        render_tab_header("ATTENTION", "Upcoming Renewals", "Facilities expiring in next 90 days.")

        buckets_show = buckets[buckets["Days_to_Validity"].notna() &
                                (buckets["Days_to_Validity"] >= 0) &
                                (buckets["Days_to_Validity"] <= 90)] \
            .sort_values("Days_to_Validity")

        if len(buckets_show) == 0:
            st.markdown("""
            <div class='callout-good'>
                <strong>✅ No renewals required in the next 90 days.</strong>
                Working capital lines are well-positioned.
            </div>
            """, unsafe_allow_html=True)
        else:
            buckets_show_display = buckets_show[["Lender", "Facility", "Validity_Date", "Days_to_Validity",
                                                  "Sanction_INR"]].copy()
            buckets_show_display["Validity_Date"] = buckets_show_display["Validity_Date"].dt.strftime("%d-%b-%Y")
            buckets_show_display["Sanction_INR"] = buckets_show_display["Sanction_INR"].apply(lambda x: f"₹{x:,.1f}")
            buckets_show_display.columns = ["Lender", "Facility", "Expires", "Days Away", "Sanction (Cr)"]
            st.dataframe(buckets_show_display, width="stretch", hide_index=True)

        # Detailed views in expanders
        with st.expander("📊 Detailed quarterly TL repayment schedule (next 12 years)", expanded=False):
            st.caption("Stacked principal by lender + total interest line")
            future_short = future.head(48).copy()
            fig = go.Figure()
            for lender, color in [("RBL Bank", COLORS["rbl"]), ("YES Bank", COLORS["ybl"]), ("Bajaj Finance", COLORS["bajaj"])]:
                sub = future_short[future_short["Lender"] == lender]
                fig.add_trace(go.Bar(
                    name=lender, x=sub["Period_Label"], y=sub["Principal"],
                    marker=dict(color=color, line=dict(color=COLORS["bg_secondary"], width=0.5)),
                    hovertemplate=f"<b>{lender}</b><br>%{{x}}<br>Principal: ₹%{{y:.2f}} Cr<extra></extra>",
                ))
            int_agg = future_short.groupby("Period_Label", sort=False)["Interest"].sum().reset_index()
            fig.add_trace(go.Scatter(
                name="Total Interest", x=int_agg["Period_Label"], y=int_agg["Interest"],
                mode="lines+markers", marker=dict(size=6, color=COLORS["accent_gold"]),
                line=dict(color=COLORS["accent_gold"], width=2.5, dash="dot"),
                hovertemplate="<b>Interest</b><br>%{x}<br>₹%{y:.2f} Cr<extra></extra>",
                yaxis="y2",
            ))
            fig.update_layout(
                **CHART_LAYOUT, height=480, barmode="stack",
                xaxis=dict(title="", tickangle=-45, showgrid=False),
                yaxis=dict(title="Principal (INR Cr)", side="left", showgrid=True, gridcolor="#334155"),
                yaxis2=dict(title="Interest (INR Cr)", side="right", overlaying="y", showgrid=False),
                legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.25),
                hovermode="x unified",
            )
            st.plotly_chart(fig, width="stretch")

        with st.expander("🔍 Browse all 34 facilities (search/filter)", expanded=False):
            search_col1, search_col2, search_col3 = st.columns([2, 1, 1])
            with search_col1:
                search = st.text_input("🔎 Search facility / lender", "", key="facility_search",
                                       placeholder="Type 'LC', 'Term Loan', 'RBL'...")
            with search_col2:
                cat_filter = st.selectbox("Category", ["All"] + sorted(self.logic.facility_master["Category"].unique().tolist()),
                                          key="cat_filter")
            with search_col3:
                sort_by = st.selectbox("Sort by", ["Sanction (high to low)", "Validity (soonest)", "Lender"],
                                       key="sort_by")

            fb_df = self.logic.facility_master.copy()
            if search:
                mask = (fb_df["Facility"].str.contains(search, case=False, na=False) |
                        fb_df["Lender"].str.contains(search, case=False, na=False))
                fb_df = fb_df[mask]
            if cat_filter != "All":
                fb_df = fb_df[fb_df["Category"] == cat_filter]
            if sort_by == "Sanction (high to low)":
                fb_df = fb_df.sort_values("Sanction_INR", ascending=False)
            elif sort_by == "Validity (soonest)":
                fb_df = fb_df.sort_values("Validity_Date", na_position="last")
            else:
                fb_df = fb_df.sort_values("Lender")

            if len(fb_df) == 0:
                st.info("No facilities match your filters.")
            else:
                display = fb_df[["Lender", "Facility", "Category", "Sanction_INR", "Effective_Rate",
                                 "Validity_Date", "Maturity_Date"]].copy()
                display["Sanction_INR"] = display["Sanction_INR"].apply(lambda x: f"₹{x:,.1f} Cr")
                display["Effective_Rate"] = display["Effective_Rate"].apply(lambda x: f"{x*100:.2f}%" if x and x > 0 else "TBD")
                display["Validity_Date"] = display["Validity_Date"].dt.strftime("%d-%b-%Y").fillna("—")
                display["Maturity_Date"] = display["Maturity_Date"].dt.strftime("%d-%b-%Y").fillna("Revolving")
                display.columns = ["Lender", "Facility", "Category", "Sanction", "Rate", "Validity", "Maturity"]
                st.dataframe(display, width="stretch", hide_index=True, height=300)
                st.caption(f"Showing {len(display)} of 34 facilities")

    # =========================================================================
    # TAB 3: COVENANT COMPLIANCE (SENIOR MANAGEMENT VIEW)
    # =========================================================================
    def render_tab_covenants(self, controls):
        cov_df = self.logic.calculate_covenants(controls["ebitda_change"])
        compliant = (cov_df["Status"] == "Compliant").sum()
        watch     = (cov_df["Status"] == "Watch").sum()
        near      = (cov_df["Status"] == "Near Breach").sum()
        breach    = (cov_df["Status"] == "Breach").sum()
        total     = len(cov_df)

        # Hero
        if breach > 0:
            verdict, color = "BREACH", "#EF4444"
            narrative = (f"<b>{breach} covenant(s) currently breached.</b> "
                         f"Lender notification and waiver discussions required. "
                         f"Compliance restoration plan needed within 30 days.")
        elif near > 0:
            verdict, color = "MONITOR", "#F59E0B"
            tightest = cov_df[cov_df["Status"] == "Near Breach"].iloc[0]
            narrative = (f"<b>{compliant} of {total}</b> covenants safely compliant. "
                         f"<b>{near}</b> covenant(s) near threshold — most notably "
                         f"<b>{tightest['Lender']}'s {tightest['Covenant']}</b> at <b>{tightest['Headroom_Pct']:+.1f}%</b> headroom.")
        else:
            verdict, color = "ALL CLEAR", "#10B981"
            ratio_only = cov_df[cov_df["Type"].isin(["ratio_higher", "ratio_lower"])]
            avg_hr = ratio_only["Headroom_Pct"].mean()
            narrative = (f"All <b>{total}</b> covenants compliant with healthy buffers. "
                         f"Average headroom across ratio covenants: <b>{avg_hr:.0f}%</b>. "
                         f"Continue regular quarterly testing cycle.")

        render_hero(verdict, color, narrative)

        # Status traffic lights
        render_tab_header("STATUS", "Compliance Dashboard", "")
        c1, c2, c3, c4 = st.columns(4)
        with c1: render_big_kpi("Compliant", str(compliant), f"{compliant/total*100:.0f}% of total", color="#10B981")
        with c2: render_big_kpi("Watch", str(watch), "5–10% buffer", color="#3B82F6")
        with c3: render_big_kpi("Near Breach", str(near), "<5% buffer",
                                 color="#F59E0B" if near > 0 else "#94A3B8")
        with c4: render_big_kpi("Breach", str(breach), "Action required",
                                 color="#EF4444" if breach > 0 else "#94A3B8")

        # Watch items
        watch_items = cov_df[cov_df["Status"].isin(["Breach", "Near Breach", "Watch"])]
        if len(watch_items) > 0:
            render_tab_header(
                "ATTENTION",
                f"Covenants Requiring Attention",
                "Covenants ranked by tightness — these are the ones that bear watching."
            )

            for _, row in watch_items.iterrows():
                if row["Status"] == "Breach":
                    border_color, bg_color, icon = "#EF4444", "rgba(239,68,68,0.1)", "🚨"
                elif row["Status"] == "Near Breach":
                    border_color, bg_color, icon = "#F59E0B", "rgba(245,158,11,0.1)", "⚠️"
                else:
                    border_color, bg_color, icon = "#3B82F6", "rgba(59,130,246,0.05)", "👁️"

                actual_str = fmt_ratio(row["Actual"]) if row["Type"] != "rating" else str(row["Actual"])[:30]
                threshold_str = f"{row['Operator']}{row['Threshold']:.2f}x" if row["Type"] != "rating" else "≥ A-"
                hr_str = f"{row['Headroom_Pct']:+.1f}%" if row["Headroom_Pct"] is not None else "—"

                st.markdown(f"""
                <div style="background: {bg_color}; border-left: 4px solid {border_color};
                             border-radius: 12px; padding: 16px 20px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <div style="font-size: 0.78rem; color: {border_color}; text-transform: uppercase;
                                        letter-spacing: 0.08em; font-weight: 700;">
                                {icon} {row['Status']} · {row['Lender']}
                            </div>
                            <div style="font-size: 1.15rem; font-weight: 700; color: #F1F5F9; margin: 4px 0;">
                                {row['Covenant']}
                            </div>
                            <div style="color: #CBD5E1; font-size: 0.92rem;">
                                Actual: <b>{actual_str}</b> · Threshold: {threshold_str}
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 0.72rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em;">
                                Headroom
                            </div>
                            <div style="font-size: 1.6rem; font-weight: 800; color: {border_color};">
                                {hr_str}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='callout-good'>
                <strong>✅ No covenants require special attention.</strong> All thresholds are comfortably met.
            </div>
            """, unsafe_allow_html=True)

        # Detail expanders
        with st.expander("📋 View all 24 covenants by lender", expanded=False):
            lenders = cov_df["Lender"].unique()
            for lender in lenders:
                sub = cov_df[cov_df["Lender"] == lender]
                sub_compliant = (sub["Status"] == "Compliant").sum()
                sub_total = len(sub)
                st.markdown(f"**🏦 {lender}** — {sub_compliant}/{sub_total} compliant")
                cols = st.columns(min(3, sub_total))
                for i, (_, row) in enumerate(sub.iterrows()):
                    with cols[i % len(cols)]:
                        cls = status_class(row["Status"])
                        if row["Type"] == "rating":
                            actual_str = str(row["Actual"])[:30]
                            threshold_str = "≥ A-"
                            hr_str = "Maintained"
                            hr_class = "headroom-good"
                        else:
                            actual_str = fmt_ratio(row["Actual"])
                            threshold_str = f"{row['Operator']}{row['Threshold']:.2f}x"
                            hr_class = "headroom-good" if row["Status"] == "Compliant" else \
                                       "headroom-watch" if row["Status"] == "Watch" else \
                                       "headroom-warn" if row["Status"] == "Near Breach" else "headroom-bad"
                            if row["Headroom"] is not None:
                                sign = "+" if row["Headroom"] >= 0 else ""
                                hr_str = f"{sign}{row['Headroom']:.2f}x ({row['Headroom_Pct']:+.1f}%)"
                            else:
                                hr_str = "—"

                        st.markdown(f"""
                        <div class="cov-card {cls}">
                            <div class="cov-card-title" style="font-size: 0.9rem;">{row['Covenant']}</div>
                            <div class="cov-card-actual">{actual_str}</div>
                            <div class="cov-card-threshold">Threshold {threshold_str}</div>
                            <div class="cov-card-headroom {hr_class}">{hr_str}</div>
                            <div class="status-pill status-{cls}" style="margin-top: 8px;">{row['Status']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                st.markdown("&nbsp;", unsafe_allow_html=True)

        with st.expander("🔥 Covenant headroom heatmap", expanded=False):
            ratio_cov = cov_df[cov_df["Type"].isin(["ratio_higher", "ratio_lower"])].copy()
            if len(ratio_cov) > 0:
                ratio_cov["Display_Headroom"] = ratio_cov["Headroom_Pct"].clip(-50, 200)
                fig = px.scatter(
                    ratio_cov, x="Lender", y="Covenant", size=ratio_cov["Display_Headroom"].abs() + 30,
                    color="Headroom_Pct",
                    color_continuous_scale=[(0, COLORS["breach"]), (0.05, COLORS["near_breach"]),
                                            (0.20, COLORS["watch"]), (1.0, COLORS["compliant"])],
                    range_color=[-10, 100], size_max=40,
                    hover_data={"Actual": ":.2f", "Threshold": True, "Headroom_Pct": ":.1f", "Status": True},
                )
                fig.update_layout(
                    **chart_layout_no_margin(), height=580,
                    xaxis=dict(title=""), yaxis=dict(title=""),
                    coloraxis_colorbar=dict(title="Headroom %"),
                    margin=dict(l=200, r=20, t=20, b=80),
                )
                st.plotly_chart(fig, width="stretch")

        st.caption("📖 Refer to the **Covenant Glossary** in the sidebar for definitions and rules-of-thumb.")

    # =========================================================================
    # TAB 4: WHAT-IF SCENARIOS (SENIOR MANAGEMENT VIEW)
    # =========================================================================
    def render_tab_scenarios(self, controls):
        # Test severe stress
        sc_severe = self.logic.run_scenario(200, 100, -30)
        severe_breach = (sc_severe["stress"]["covenants"]["Status"] == "Breach").sum()

        if severe_breach > 0:
            verdict, color = "RESILIENT TO MODERATE", "#3B82F6"
            narrative = (f"Portfolio absorbs <b>moderate stress</b> (rate +100bps, EBITDA -20%) without breach. "
                         f"<b>Severe combined stress</b> (rate +200bps, spread +100bps, EBITDA -30%) "
                         f"would trigger {severe_breach} covenant breach(es).")
        else:
            verdict, color = "HIGHLY RESILIENT", "#10B981"
            narrative = (f"Portfolio is <b>highly resilient</b>. Even severe combined stress "
                         f"(rate +200bps, spread +100bps, EBITDA -30%) does not trigger any covenant breach.")

        render_hero(verdict, color, narrative)

        # Active stress display
        if controls["rate_shock"] != 0 or controls["spread_shock"] != 0 or controls["ebitda_change"] != 0:
            st.markdown(f"""
            <div class='callout-info'>
                <strong>🔬 Currently displaying stressed view:</strong>
                <span class="mini-stat">Rate {controls['rate_shock']:+d} bps</span>
                <span class="mini-stat">Spread {controls['spread_shock']:+d} bps</span>
                <span class="mini-stat">EBITDA {controls['ebitda_change']:+d}%</span>
                · Use sidebar Quick Scenarios or sliders to adjust.
            </div>
            """, unsafe_allow_html=True)

        # Live impact
        scenario = self.logic.run_scenario(
            rate_shock_bps=controls["rate_shock"],
            spread_shock_bps=controls["spread_shock"],
            ebitda_change_pct=controls["ebitda_change"],
        )
        base_int = scenario["base"]["annual_interest"]
        stress_int = scenario["stress"]["annual_interest"]
        delta_int = stress_int - base_int
        base_dscr = scenario["base"]["covenants"][scenario["base"]["covenants"]["Covenant"] == "DSCR"]["Actual"].iloc[0]
        stress_dscr = scenario["stress"]["covenants"][scenario["stress"]["covenants"]["Covenant"] == "DSCR"]["Actual"].iloc[0]
        base_icr = scenario["base"]["covenants"][scenario["base"]["covenants"]["Covenant"] == "ICR"]["Actual"].iloc[0]
        stress_icr = scenario["stress"]["covenants"][scenario["stress"]["covenants"]["Covenant"] == "ICR"]["Actual"].iloc[0]

        render_tab_header(
            "IMPACT",
            "Current Scenario Impact",
            "What changes between base case and current stress settings."
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            int_pct = (delta_int/base_int*100) if base_int else 0
            render_big_kpi(
                "Annual Interest",
                f"₹{stress_int:.0f} Cr",
                f"{delta_int:+.1f} Cr ({int_pct:+.1f}%)",
                color="#EF4444" if delta_int > 5 else "#F1F5F9",
            )
        with c2:
            wac_delta = (scenario["stress"]["weighted_avg_cost"] - scenario["base"]["weighted_avg_cost"]) * 10000
            render_big_kpi(
                "Cost of Debt",
                f"{scenario['stress']['weighted_avg_cost']*100:.2f}%",
                f"{wac_delta:+.0f} bps from base",
                color="#EF4444" if wac_delta > 100 else "#F1F5F9",
            )
        with c3:
            d_dscr = stress_dscr - base_dscr
            render_big_kpi(
                "DSCR",
                f"{stress_dscr:.2f}x",
                f"{d_dscr:+.2f}x vs base · threshold 1.25x",
                color="#10B981" if stress_dscr >= 1.25 else "#EF4444",
            )
        with c4:
            d_icr = stress_icr - base_icr
            render_big_kpi(
                "ICR",
                f"{stress_icr:.2f}x",
                f"{d_icr:+.2f}x vs base · threshold 3.00x",
                color="#10B981" if stress_icr >= 3.0 else "#EF4444",
            )

        # Pre-defined scenario comparison
        render_tab_header(
            "SENSITIVITY",
            "Pre-Defined Scenario Library",
            "How key ratios respond to a range of stress scenarios. Dotted red line marks DSCR breach threshold."
        )

        scenarios_to_test = [
            ("Base Case",       0,   0, 0),
            ("Rate +50 bps",    50,  0, 0),
            ("Rate +100 bps",   100, 0, 0),
            ("Spread +50 bps",  0,  50, 0),
            ("EBITDA −10%",     0,   0, -10),
            ("EBITDA −20%",     0,   0, -20),
            ("Combined Stress", 100, 50, -20),
            ("Severe Stress",   200, 100, -30),
        ]
        results = []
        for name, rs, ss, es in scenarios_to_test:
            sc = self.logic.run_scenario(rs, ss, es)
            cv = sc["stress"]["covenants"]
            results.append({
                "Scenario": name,
                "Annual Interest": sc["stress"]["annual_interest"],
                "WAC": sc["stress"]["weighted_avg_cost"] * 100,
                "DSCR": cv[cv["Covenant"] == "DSCR"]["Actual"].iloc[0],
                "ICR": cv[cv["Covenant"] == "ICR"]["Actual"].iloc[0],
                "TD/EBITDA": cv[cv["Covenant"] == "Total Debt / EBITDA (≤FY27)"]["Actual"].iloc[0]
                              if "Total Debt / EBITDA (≤FY27)" in cv["Covenant"].values
                              else cv[cv["Covenant"] == "Total Debt / EBITDA"]["Actual"].iloc[0],
            })
        results_df = pd.DataFrame(results)

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(
            x=results_df["Scenario"], y=results_df["DSCR"],
            mode="lines+markers", name="DSCR",
            line=dict(color=COLORS["compliant"], width=3),
            marker=dict(size=11),
            hovertemplate="<b>DSCR</b><br>%{x}<br>%{y:.2f}x<extra></extra>",
        ), secondary_y=False)
        fig.add_trace(go.Scatter(
            x=results_df["Scenario"], y=results_df["ICR"],
            mode="lines+markers", name="ICR",
            line=dict(color=COLORS["watch"], width=3, dash="dash"),
            marker=dict(size=11),
            hovertemplate="<b>ICR</b><br>%{x}<br>%{y:.2f}x<extra></extra>",
        ), secondary_y=False)
        fig.add_trace(go.Bar(
            x=results_df["Scenario"], y=results_df["Annual Interest"],
            name="Annual Interest (₹Cr)",
            marker=dict(color=COLORS["accent_gold"], opacity=0.35),
            hovertemplate="<b>Annual Interest</b><br>%{x}<br>₹%{y:.2f} Cr<extra></extra>",
        ), secondary_y=True)
        fig.add_hline(y=1.25, line_dash="dot", line_color=COLORS["breach"],
                      annotation_text="DSCR Breach Threshold (1.25x)", secondary_y=False)
        fig.update_xaxes(title="", tickangle=-30)
        fig.update_yaxes(title_text="Coverage Ratio (x)", secondary_y=False, gridcolor="#334155")
        fig.update_yaxes(title_text="Annual Interest (INR Cr)", secondary_y=True, showgrid=False)
        fig.update_layout(
            **CHART_LAYOUT, height=500, barmode="group",
            legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.25),
        )
        st.plotly_chart(fig, width="stretch")

        # Detail in expander
        with st.expander("📋 Detailed sensitivity table", expanded=False):
            sens_display = results_df.copy()
            sens_display["Annual Interest"] = sens_display["Annual Interest"].apply(lambda x: f"₹{x:.2f} Cr")
            sens_display["WAC"] = sens_display["WAC"].apply(lambda x: f"{x:.2f}%")
            sens_display["DSCR"] = sens_display["DSCR"].apply(lambda x: f"{x:.2f}x")
            sens_display["ICR"] = sens_display["ICR"].apply(lambda x: f"{x:.2f}x")
            sens_display["TD/EBITDA"] = sens_display["TD/EBITDA"].apply(lambda x: f"{x:.2f}x")
            st.dataframe(sens_display, width="stretch", hide_index=True)

        with st.expander("🎯 All covenants under current stress (vs base)", expanded=False):
            compare_df = pd.merge(
                scenario["base"]["covenants"][["Covenant", "Lender", "Actual", "Threshold", "Status", "Headroom_Pct"]]
                    .rename(columns={"Actual": "Base_Actual", "Status": "Base_Status", "Headroom_Pct": "Base_Headroom_Pct"}),
                scenario["stress"]["covenants"][["Covenant", "Lender", "Actual", "Status", "Headroom_Pct"]]
                    .rename(columns={"Actual": "Stress_Actual", "Status": "Stress_Status", "Headroom_Pct": "Stress_Headroom_Pct"}),
                on=["Covenant", "Lender"], how="inner"
            )
            compare_df = compare_df[pd.to_numeric(compare_df["Base_Actual"], errors="coerce").notna()].copy()
            compare_df["Δ Actual"] = pd.to_numeric(compare_df["Stress_Actual"], errors="coerce") - \
                                      pd.to_numeric(compare_df["Base_Actual"], errors="coerce")

            compare_display = compare_df.copy()
            compare_display["Base"] = compare_display["Base_Actual"].apply(lambda x: f"{x:.2f}x")
            compare_display["Stress"] = compare_display["Stress_Actual"].apply(lambda x: f"{x:.2f}x")
            compare_display["Δ"] = compare_display["Δ Actual"].apply(lambda x: f"{x:+.2f}x")
            compare_display["Threshold"] = compare_display["Threshold"].apply(lambda x: f"{x:.2f}x")
            compare_display["Stress Headroom"] = compare_display["Stress_Headroom_Pct"].apply(lambda x: f"{x:+.1f}%")
            compare_display = compare_display[["Lender", "Covenant", "Threshold", "Base", "Stress", "Δ", "Stress Headroom", "Stress_Status"]]
            compare_display.columns = ["Lender", "Covenant", "Threshold", "Base", "Stress", "Δ", "Headroom (Stress)", "Status"]
            st.dataframe(compare_display, width="stretch", hide_index=True, height=400)


    # =========================================================================
    # EXPORT
    # =========================================================================
    def render_export(self, controls):
        from core.board_memo import generate_board_memo, generate_email_summary

        cov_df = self.logic.calculate_covenants(controls["ebitda_change"])
        ls = self.logic.lender_summary()
        fm = self.logic.facility_master.copy()

        # Board-ready outputs section
        render_tab_header(
            "BOARD-READY",
            "Executive Outputs",
            "One-click downloads for board reviews, management updates, and email digests."
        )

        bm_col, em_col = st.columns(2)
        with bm_col:
            try:
                memo_bytes = generate_board_memo(self.logic, controls)
                st.download_button(
                    "📄 Download Board Memo (Word)",
                    memo_bytes,
                    file_name=f"JCL_Board_Memo_{controls['as_of_date']}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    width="stretch",
                    help="2-page Word document with executive summary, KPIs, recommended actions, "
                         "lender breakdown, watch items, and stress test results. "
                         "Reflects current stress slider settings.",
                )
                st.caption("✓ 2-page Word doc · Reflects current stress settings")
            except Exception as e:
                st.error(f"Memo generation failed: {e}")

        with em_col:
            email_text = generate_email_summary(self.logic, controls)
            st.download_button(
                "📧 Download Email Summary (Text)",
                email_text.encode("utf-8"),
                file_name=f"JCL_Email_Summary_{controls['as_of_date']}.txt",
                mime="text/plain",
                width="stretch",
                help="Copy-paste ready email body with status, KPIs, and priority actions.",
            )
            st.caption("✓ Plain text · Copy-paste into email")

        with st.expander("📧 Preview email summary text", expanded=False):
            st.code(email_text, language="text")

        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

        # Raw data downloads
        render_tab_header("RAW DATA", "CSV Exports", "Underlying data tables for audit / detail review.")

        col1, col2, col3 = st.columns(3)
        with col1:
            csv_cov = cov_df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Covenant Report (CSV)", csv_cov,
                               file_name=f"jcl_covenants_{controls['as_of_date']}.csv",
                               mime="text/csv", width="stretch")
        with col2:
            csv_fm = fm.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Facility Master (CSV)", csv_fm,
                               file_name=f"jcl_facilities_{controls['as_of_date']}.csv",
                               mime="text/csv", width="stretch")
        with col3:
            csv_ls = ls.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Lender Summary (CSV)", csv_ls,
                               file_name=f"jcl_lenders_{controls['as_of_date']}.csv",
                               mime="text/csv", width="stretch")

        # TL Schedule
        col4, _, _ = st.columns(3)
        with col4:
            csv_tl = self.logic.tl_schedule.to_csv(index=False).encode("utf-8")
            st.download_button("📥 TL Schedule (CSV)", csv_tl,
                               file_name=f"jcl_tl_schedule_{controls['as_of_date']}.csv",
                               mime="text/csv", width="stretch")
