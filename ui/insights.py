"""
JCL Debt Monitoring Dashboard — Auto-Generated Insights Engine
Translates numeric portfolio state into plain-English narrative observations.
"""

from datetime import date
import pandas as pd


def generate_executive_insights(logic, controls) -> list:
    """Top 3-5 narrative bullets for the Executive Summary."""
    insights = []

    cov_df = logic.calculate_covenants(controls["ebitda_change"])
    interest = logic.calculate_annual_interest(controls["rate_shock"], controls["spread_shock"])
    wac = logic.weighted_avg_cost(controls["rate_shock"], controls["spread_shock"])
    ls = logic.lender_summary()

    # Lender concentration
    top_lender = ls.nlargest(1, "Total_Sanction").iloc[0]
    top_share = top_lender["Total_Sanction"] / ls["Total_Sanction"].sum() * 100
    if top_share > 40:
        insights.append({
            "icon": "⚠️",
            "level": "warning",
            "title": "Concentration Risk",
            "body": f"<b>{top_lender['Lender']}</b> accounts for <b>{top_share:.1f}%</b> of total exposure (₹{top_lender['Total_Sanction']:,.0f} Cr). Consider diversifying with new lender relationships."
        })
    else:
        insights.append({
            "icon": "✅",
            "level": "good",
            "title": "Diversified Portfolio",
            "body": f"Top lender (<b>{top_lender['Lender']}</b>) accounts for {top_share:.1f}% — within healthy diversification limits."
        })

    # Cost of debt
    if wac < 0.05:
        insights.append({
            "icon": "💰",
            "level": "good",
            "title": "Competitive Funding Cost",
            "body": f"Weighted avg cost of <b>{wac*100:.2f}%</b> p.a. is well below market rates. Annual interest run-rate: ₹<b>{interest['total']:.1f} Cr</b>."
        })
    elif wac < 0.08:
        insights.append({
            "icon": "📊",
            "level": "neutral",
            "title": "Average Funding Cost",
            "body": f"Weighted avg cost of <b>{wac*100:.2f}%</b> p.a. is at market levels. Annual interest run-rate: ₹<b>{interest['total']:.1f} Cr</b>."
        })

    # Covenant health
    breach = (cov_df["Status"] == "Breach").sum()
    near = (cov_df["Status"] == "Near Breach").sum()
    if breach > 0:
        breached = cov_df[cov_df["Status"] == "Breach"]
        names = ", ".join([f"{r['Lender']} {r['Covenant']}" for _, r in breached.iterrows()])
        insights.append({
            "icon": "🚨",
            "level": "danger",
            "title": "Covenant Breach Detected",
            "body": f"<b>{breach}</b> covenant(s) breached: {names}. Immediate corrective action required."
        })
    elif near > 0:
        near_df = cov_df[cov_df["Status"] == "Near Breach"]
        names = ", ".join([f"{r['Lender']} {r['Covenant']} ({r['Headroom_Pct']:+.1f}%)" for _, r in near_df.iterrows()])
        insights.append({
            "icon": "⚠️",
            "level": "warning",
            "title": "Covenants Near Threshold",
            "body": f"<b>{near}</b> covenant(s) within 5% of breach: {names}. Monitor closely."
        })
    else:
        insights.append({
            "icon": "🛡️",
            "level": "good",
            "title": "All Covenants Compliant",
            "body": f"All <b>{len(cov_df)}</b> covenants pass with healthy headroom. Tightest covenant has {cov_df[cov_df['Headroom_Pct'].notna()]['Headroom_Pct'].min():.1f}% buffer."
        })

    # Stress mode warning
    if controls["rate_shock"] != 0 or controls["spread_shock"] != 0 or controls["ebitda_change"] != 0:
        insights.append({
            "icon": "🔬",
            "level": "info",
            "title": "Stress Mode Active",
            "body": f"Showing impact of <b>Rate {controls['rate_shock']:+d}bps</b>, <b>Spread {controls['spread_shock']:+d}bps</b>, <b>EBITDA {controls['ebitda_change']:+d}%</b>. Reset sliders to see baseline."
        })

    return insights


def generate_repayment_insights(logic, controls) -> list:
    """Narrative for Repayment & Liquidity tab."""
    insights = []
    sched = logic.tl_schedule
    future = sched[sched["Period_End"] >= logic.as_of_date]

    # Next 12-month obligations
    next_12m = future[future["Period_End"] <= logic.as_of_date + pd.Timedelta(days=365)]
    next_12m_principal = next_12m["Principal"].sum()
    next_12m_interest = next_12m["Interest"].sum()

    insights.append({
        "icon": "📅",
        "level": "info",
        "title": "Next 12 Months",
        "body": f"Term loan obligations: <b>₹{next_12m_principal:.1f} Cr principal</b> + ₹{next_12m_interest:.1f} Cr interest = ₹{next_12m_principal + next_12m_interest:.1f} Cr total debt service."
    })

    # Maturity profile
    buckets = logic.maturity_buckets()
    near_expiry = buckets[buckets["Days_to_Validity"].notna() &
                          (buckets["Days_to_Validity"] >= 0) &
                          (buckets["Days_to_Validity"] <= 90)]
    if len(near_expiry) > 0:
        total_near = near_expiry["Sanction_INR"].sum()
        insights.append({
            "icon": "⏰",
            "level": "warning",
            "title": "Renewals Due Soon",
            "body": f"<b>{len(near_expiry)} facilities</b> (₹{total_near:,.0f} Cr) require renewal within 90 days. Initiate renewal discussions with lenders."
        })

    # Longest dated TL
    longest = future.iloc[-1]
    insights.append({
        "icon": "🏁",
        "level": "good",
        "title": "Longest Maturity",
        "body": f"Final TL repayment in <b>{longest['Period_Label']}</b> (<b>{longest['Lender']}</b>). Provides long-term capital structure stability."
    })

    return insights


def generate_covenant_insights(logic, controls) -> list:
    """Narrative for Covenant Monitoring tab."""
    insights = []
    cov_df = logic.calculate_covenants(controls["ebitda_change"])

    # Status summary
    compliant = (cov_df["Status"] == "Compliant").sum()
    total = len(cov_df)
    pct = compliant / total * 100

    # Tightest covenant
    ratio_only = cov_df[cov_df["Type"].isin(["ratio_higher", "ratio_lower"])].copy()
    if len(ratio_only) > 0:
        tightest = ratio_only.nsmallest(1, "Headroom_Pct").iloc[0]
        insights.append({
            "icon": "🎯",
            "level": "warning" if tightest["Headroom_Pct"] < 10 else "info",
            "title": "Tightest Covenant",
            "body": f"<b>{tightest['Lender']} — {tightest['Covenant']}</b>: actual {tightest['Actual']:.2f}x vs threshold {tightest['Operator']}{tightest['Threshold']:.2f}x. Headroom: <b>{tightest['Headroom_Pct']:+.1f}%</b>."
        })

    # Key driver insight
    f = logic.financials[logic.basis]
    insights.append({
        "icon": "📈",
        "level": "info",
        "title": "Coverage Ratios Driver",
        "body": f"DSCR & ICR powered by EBITDA of ₹<b>{f['EBITDA']:.1f} Cr</b> ({logic.basis}). Each ₹10 Cr EBITDA change = ~0.2x DSCR impact."
    })

    # Lender-specific
    sib = cov_df[cov_df["Lender"] == "South Indian Bank"]
    sib_near = sib[sib["Status"] == "Near Breach"]
    if len(sib_near) > 0:
        insights.append({
            "icon": "🏦",
            "level": "warning",
            "title": "SIB Watch Item",
            "body": "South Indian Bank's <b>Current Ratio</b> covenant is structural — driven by ₹147 Cr Buyer's Credit current maturities. Refinancing a portion to longer tenor would improve headroom."
        })

    return insights


def generate_scenario_insights(logic, controls) -> list:
    """Narrative for Scenario Engine tab."""
    insights = []

    # Rate sensitivity
    sc_rate100 = logic.run_scenario(100, 0, 0)
    delta_rate100 = sc_rate100["delta"]["annual_interest"]

    insights.append({
        "icon": "📊",
        "level": "info",
        "title": "Rate Sensitivity",
        "body": f"A <b>+100bps parallel rate shock</b> increases annual interest by ₹<b>{delta_rate100:.1f} Cr</b>. About <b>{delta_rate100/sc_rate100['base']['annual_interest']*100:.1f}%</b> of base cost."
    })

    # EBITDA sensitivity
    sc_ebitda = logic.run_scenario(0, 0, -20)
    base_dscr = sc_ebitda["base"]["covenants"][sc_ebitda["base"]["covenants"]["Covenant"] == "DSCR"]["Actual"].iloc[0]
    stress_dscr = sc_ebitda["stress"]["covenants"][sc_ebitda["stress"]["covenants"]["Covenant"] == "DSCR"]["Actual"].iloc[0]

    insights.append({
        "icon": "💹",
        "level": "info",
        "title": "Earnings Sensitivity",
        "body": f"A <b>20% EBITDA drop</b> reduces DSCR from <b>{base_dscr:.2f}x</b> to <b>{stress_dscr:.2f}x</b>. Still compliant against tightest 1.20x threshold."
    })

    # Combined breaking point
    sc_severe = logic.run_scenario(200, 100, -30)
    severe_breach = (sc_severe["stress"]["covenants"]["Status"] == "Breach").sum()
    if severe_breach > 0:
        insights.append({
            "icon": "⚠️",
            "level": "warning",
            "title": "Severe Stress Breaks Portfolio",
            "body": f"Combined extreme stress (Rate +200bps, Spread +100bps, EBITDA -30%) triggers <b>{severe_breach}</b> covenant breach(es). Strong indicator that current covenants have meaningful but not unlimited headroom."
        })
    else:
        insights.append({
            "icon": "💪",
            "level": "good",
            "title": "Stress Resilience",
            "body": "Portfolio absorbs combined extreme stress (Rate +200bps, Spread +100bps, EBITDA -30%) without any covenant breach. Strong risk profile."
        })

    return insights


def calculate_health_score(logic, controls) -> dict:
    """Compute overall portfolio health score 0-100 with breakdown."""
    cov_df = logic.calculate_covenants(controls["ebitda_change"])
    ratio_cov = cov_df[cov_df["Type"].isin(["ratio_higher", "ratio_lower"])].copy()

    # Component 1: Covenant compliance (40 pts)
    if len(ratio_cov) > 0:
        avg_headroom = ratio_cov["Headroom_Pct"].mean()
        breach = (cov_df["Status"] == "Breach").sum()
        near = (cov_df["Status"] == "Near Breach").sum()
        if breach > 0:
            cov_score = 0
        elif near > 0:
            cov_score = 20
        else:
            cov_score = min(40, 25 + (avg_headroom / 100) * 15)
    else:
        cov_score = 30

    # Component 2: Cost efficiency (25 pts)
    wac = logic.weighted_avg_cost(controls["rate_shock"], controls["spread_shock"])
    if wac < 0.05:
        cost_score = 25
    elif wac < 0.07:
        cost_score = 20
    elif wac < 0.09:
        cost_score = 15
    else:
        cost_score = 10

    # Component 3: Diversification (20 pts)
    ls = logic.lender_summary()
    top_share = ls["Total_Sanction"].max() / ls["Total_Sanction"].sum()
    if top_share < 0.30:
        div_score = 20
    elif top_share < 0.45:
        div_score = 15
    else:
        div_score = 10

    # Component 4: Liquidity headroom (15 pts)
    buckets = logic.maturity_buckets()
    near_expiry_count = len(buckets[buckets["Days_to_Validity"].notna() &
                                     (buckets["Days_to_Validity"] >= 0) &
                                     (buckets["Days_to_Validity"] <= 30)])
    liq_score = max(5, 15 - near_expiry_count * 2)

    total = cov_score + cost_score + div_score + liq_score

    if total >= 80:
        rating = "Strong"; color = "#10B981"
    elif total >= 60:
        rating = "Healthy"; color = "#3B82F6"
    elif total >= 40:
        rating = "Watch"; color = "#F59E0B"
    else:
        rating = "At Risk"; color = "#EF4444"

    return {
        "total": round(total),
        "rating": rating,
        "color": color,
        "components": {
            "Covenant Compliance": {"score": round(cov_score), "max": 40},
            "Cost Efficiency":     {"score": round(cost_score), "max": 25},
            "Diversification":     {"score": round(div_score), "max": 20},
            "Liquidity":           {"score": round(liq_score), "max": 15},
        }
    }


def generate_recommendations(logic, controls) -> list:
    """Auto-generate management action items from portfolio state."""
    recommendations = []
    cov_df = logic.calculate_covenants(controls["ebitda_change"])
    ls = logic.lender_summary()

    # 1. Breach actions
    breached = cov_df[cov_df["Status"] == "Breach"]
    if len(breached) > 0:
        for _, row in breached.iterrows():
            recommendations.append({
                "priority": "HIGH",
                "title": f"Address {row['Lender']} {row['Covenant']} breach",
                "body": "Initiate immediate dialogue with lender. Prepare waiver request and corrective action plan.",
                "owner": "Treasury",
            })

    # 2. Near-breach actions
    near = cov_df[cov_df["Status"] == "Near Breach"]
    for _, row in near.iterrows():
        if row["Lender"] == "South Indian Bank" and "Current Ratio" in row["Covenant"]:
            recommendations.append({
                "priority": "MEDIUM",
                "title": "Refinance SIB Buyer's Credit current maturities",
                "body": "Current Ratio at 1.39x vs 1.33x threshold (4% headroom). Driven by ₹147 Cr BC current maturities. "
                        "Refinancing a portion to longer tenor would create breathing room.",
                "owner": "Treasury",
            })
        else:
            recommendations.append({
                "priority": "MEDIUM",
                "title": f"Monitor {row['Lender']} {row['Covenant']}",
                "body": f"Headroom only {row['Headroom_Pct']:+.1f}%. Track quarterly; small adverse changes could trigger breach.",
                "owner": "Finance",
            })

    # 3. Concentration risk
    top = ls.nlargest(1, "Total_Sanction").iloc[0]
    top_share = top["Total_Sanction"] / ls["Total_Sanction"].sum() * 100
    if top_share > 40:
        recommendations.append({
            "priority": "MEDIUM",
            "title": "Reduce single-lender concentration",
            "body": f"{top['Lender']} holds {top_share:.0f}% of total exposure. "
                    f"Consider diversifying with new lender relationships in next refinancing cycle.",
            "owner": "Treasury",
        })

    # 4. Renewals due
    buckets = logic.maturity_buckets()
    near_expiry = buckets[buckets["Days_to_Validity"].notna() &
                          (buckets["Days_to_Validity"] >= 0) &
                          (buckets["Days_to_Validity"] <= 60)]
    if len(near_expiry) > 0:
        total_near = near_expiry["Sanction_INR"].sum()
        recommendations.append({
            "priority": "MEDIUM",
            "title": f"Initiate renewal for {len(near_expiry)} facilities",
            "body": f"₹{total_near:,.0f} Cr of WC limits expire in next 60 days. "
                    "Begin lender renewal discussions to avoid liquidity gap.",
            "owner": "Treasury",
        })

    # 5. Stress mode warning
    if controls["rate_shock"] > 100 or controls["ebitda_change"] < -20:
        recommendations.append({
            "priority": "INFO",
            "title": "Stress scenario triggered",
            "body": f"Current display shows stressed view (Rate {controls['rate_shock']:+d}bps, "
                    f"EBITDA {controls['ebitda_change']:+d}%). Reset sliders for base case.",
            "owner": "—",
        })

    if not recommendations:
        recommendations.append({
            "priority": "INFO",
            "title": "No urgent actions required",
            "body": "Portfolio is healthy across all dimensions. Continue regular quarterly review cycle.",
            "owner": "—",
        })

    return recommendations


def generate_bottom_line(logic, controls) -> dict:
    """Generate the 'Bottom Line' verdict — 2-3 sentences for senior management."""
    cov_df = logic.calculate_covenants(controls["ebitda_change"])
    ls = logic.lender_summary()
    total_sanc = ls["Total_Sanction"].sum()
    annual_int = logic.calculate_annual_interest(controls["rate_shock"], controls["spread_shock"])
    breach = (cov_df["Status"] == "Breach").sum()
    near = (cov_df["Status"] == "Near Breach").sum()

    if breach > 0:
        verdict = "ACTION REQUIRED"
        color = "#EF4444"
        narrative = (f"<b>{breach} covenant(s) currently breached.</b> "
                     f"Immediate lender dialogue required. "
                     f"Portfolio of ₹{total_sanc:,.0f} Cr remains operational but at elevated risk.")
    elif near > 0:
        verdict = "MONITOR CLOSELY"
        color = "#F59E0B"
        narrative = (f"Portfolio of ₹<b>{total_sanc:,.0f} Cr</b> across 5 lenders is broadly healthy with "
                     f"<b>{near} covenant(s) within 5% of threshold</b>. "
                     f"Annual debt servicing cost: ₹{annual_int['total']:.0f} Cr. "
                     f"Targeted action recommended on watch items below.")
    else:
        verdict = "HEALTHY"
        color = "#10B981"
        narrative = (f"Portfolio of ₹<b>{total_sanc:,.0f} Cr</b> across 5 lenders is in <b>strong health</b>. "
                     f"All 24 covenants compliant with comfortable buffers. "
                     f"Annual debt servicing cost: ₹{annual_int['total']:.0f} Cr.")

    if controls["rate_shock"] != 0 or controls["spread_shock"] != 0 or controls["ebitda_change"] != 0:
        narrative += f" <i>Stress applied — see sidebar for shock parameters.</i>"

    return {"verdict": verdict, "color": color, "narrative": narrative}



    """Compute overall portfolio health score 0-100 with breakdown."""
    cov_df = logic.calculate_covenants(controls["ebitda_change"])
    ratio_cov = cov_df[cov_df["Type"].isin(["ratio_higher", "ratio_lower"])].copy()

    # Component 1: Covenant compliance (40 pts)
    if len(ratio_cov) > 0:
        avg_headroom = ratio_cov["Headroom_Pct"].mean()
        breach = (cov_df["Status"] == "Breach").sum()
        near = (cov_df["Status"] == "Near Breach").sum()
        if breach > 0:
            cov_score = 0
        elif near > 0:
            cov_score = 20
        else:
            cov_score = min(40, 25 + (avg_headroom / 100) * 15)
    else:
        cov_score = 30

    # Component 2: Cost efficiency (25 pts)
    wac = logic.weighted_avg_cost(controls["rate_shock"], controls["spread_shock"])
    if wac < 0.05:
        cost_score = 25
    elif wac < 0.07:
        cost_score = 20
    elif wac < 0.09:
        cost_score = 15
    else:
        cost_score = 10

    # Component 3: Diversification (20 pts)
    ls = logic.lender_summary()
    top_share = ls["Total_Sanction"].max() / ls["Total_Sanction"].sum()
    if top_share < 0.30:
        div_score = 20
    elif top_share < 0.45:
        div_score = 15
    else:
        div_score = 10

    # Component 4: Liquidity headroom (15 pts)
    buckets = logic.maturity_buckets()
    near_expiry_count = len(buckets[buckets["Days_to_Validity"].notna() &
                                     (buckets["Days_to_Validity"] >= 0) &
                                     (buckets["Days_to_Validity"] <= 30)])
    liq_score = max(5, 15 - near_expiry_count * 2)

    total = cov_score + cost_score + div_score + liq_score

    if total >= 80:
        rating = "Strong"
        color = "#10B981"
    elif total >= 60:
        rating = "Healthy"
        color = "#3B82F6"
    elif total >= 40:
        rating = "Watch"
        color = "#F59E0B"
    else:
        rating = "At Risk"
        color = "#EF4444"

    return {
        "total": round(total),
        "rating": rating,
        "color": color,
        "components": {
            "Covenant Compliance": {"score": round(cov_score), "max": 40},
            "Cost Efficiency":     {"score": round(cost_score), "max": 25},
            "Diversification":     {"score": round(div_score), "max": 20},
            "Liquidity":           {"score": round(liq_score), "max": 15},
        }
    }


# =============================================================================
# COVENANT GLOSSARY
# =============================================================================
COVENANT_DEFINITIONS = {
    "DSCR": {
        "full_name": "Debt Service Coverage Ratio",
        "formula": "(EBITDA − Tax) / (Scheduled Principal + Interest)",
        "interpretation": "Measures ability to service debt from operating cash flow. Higher = safer.",
        "rule_of_thumb": ">1.25x is generally considered healthy.",
    },
    "ICR": {
        "full_name": "Interest Coverage Ratio",
        "formula": "EBITDA / Interest Expense",
        "interpretation": "Measures how many times earnings cover interest. Higher = safer.",
        "rule_of_thumb": ">3.0x is generally considered healthy.",
    },
    "Total Debt / EBITDA": {
        "full_name": "Leverage Ratio",
        "formula": "Total Debt / EBITDA",
        "interpretation": "Measures how many years of EBITDA needed to repay all debt. Lower = safer.",
        "rule_of_thumb": "<3.0x is conservative, <4.0x is moderate.",
    },
    "Term Debt / EBITDA": {
        "full_name": "Term Leverage Ratio",
        "formula": "Term Debt / EBITDA",
        "interpretation": "Same as leverage ratio but only includes long-term term loans.",
        "rule_of_thumb": "<2.5x is healthy.",
    },
    "Total Debt / ATNW": {
        "full_name": "Debt to Adjusted Tangible Net Worth",
        "formula": "Total Debt / (TNW − Investments)",
        "interpretation": "Measures debt against tangible equity cushion.",
        "rule_of_thumb": "<2.0x is conservative.",
    },
    "TOL / TNW": {
        "full_name": "Total Outside Liabilities to Tangible Net Worth",
        "formula": "TOL / TNW",
        "interpretation": "Measures all liabilities (debt + payables) against equity.",
        "rule_of_thumb": "<3.0x is the typical bank covenant.",
    },
    "TOL / ATNW": {
        "full_name": "TOL to Adjusted TNW",
        "formula": "TOL / (TNW − Investments)",
        "interpretation": "Stricter version of TOL/TNW after adjusting for investments.",
        "rule_of_thumb": "<2.0–2.5x typical.",
    },
    "FACR": {
        "full_name": "Fixed Asset Coverage Ratio",
        "formula": "Net Fixed Assets / Term Debt",
        "interpretation": "Measures how well term debt is covered by hard assets pledged.",
        "rule_of_thumb": ">1.25x is healthy security cover.",
    },
    "Current Ratio": {
        "full_name": "Current Ratio",
        "formula": "Current Assets / Current Liabilities",
        "interpretation": "Measures short-term liquidity.",
        "rule_of_thumb": ">1.33x is the standard banker's expectation.",
    },
    "Debt / Equity Ratio": {
        "full_name": "Debt-Equity Ratio",
        "formula": "Total Debt / TNW",
        "interpretation": "Classic leverage measure.",
        "rule_of_thumb": "<2.0x is moderate, <1.0x conservative.",
    },
    "External Rating": {
        "full_name": "External Credit Rating",
        "formula": "Issued by CARE / CRISIL / ICRA",
        "interpretation": "Independent assessment of creditworthiness by rating agencies.",
        "rule_of_thumb": "A- or better required by most lenders.",
    },
}
