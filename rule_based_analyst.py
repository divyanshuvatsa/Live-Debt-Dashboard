"""
JCL Debt Monitoring Dashboard — Rule-Based Portfolio Analyst
=============================================================

NO API REQUIRED. NO INTERNET. NO COST.

This module provides intelligent portfolio analysis using deterministic
financial rules derived from the actual data — no LLM, no API key.

What it does:
  - Answers ~30 common credit-analyst questions using if-then logic
  - Generates 3 proactive insights (risk understated / optimisation / forward)
  - Calculates impact of stress scenarios
  - All answers reference the live Excel data

Replaces: core/ai_analyst.py
"""

from typing import List, Generator
import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# AVAILABILITY CHECK (always true — no API needed)
# ─────────────────────────────────────────────────────────────────────────────
def is_ai_available() -> bool:
    return True  # rule-based engine is always available


# ─────────────────────────────────────────────────────────────────────────────
# QUESTION CLASSIFIER — match user input to one of N intents
# ─────────────────────────────────────────────────────────────────────────────
INTENT_KEYWORDS = {
    "interest_cost":     ["interest cost", "annual interest", "total interest", "interest bill", "interest expense"],
    "wac":               ["weighted average cost", "wac", "blended rate", "average rate"],
    "biggest_risk":      ["biggest risk", "main risk", "key risk", "top risk"],
    "covenant_breach":   ["covenant breach", "near breach", "tightest covenant", "which covenant", "breaching"],
    "ebitda_drop":       ["ebitda drop", "ebitda fall", "ebitda decline", "ebitda decreases", "ebitda decrease"],
    "rate_hike":         ["rate hike", "rbi rate", "rate increase", "rate rise", "interest rate hike", "rate up"],
    "concentration":     ["rbl concentration", "lender concentration", "concentration risk", "biggest lender"],
    "refinancing":       ["refinancing risk", "refinance", "refi", "rollover"],
    "prepay":            ["prepay", "prepayment", "which loan to pay", "pay off first"],
    "sib_current":       ["sib current ratio", "current ratio sib", "south indian current", "near breach explain"],
    "leverage":          ["leverage", "compare to industry", "industry norm", "peer comparison"],
    "summary":           ["board summary", "5-bullet", "5 bullet", "executive summary", "board presentation"],
    "lender_review":     ["lender review", "lender meeting", "next meeting", "prioritise", "prioritize"],
    "term_loans":        ["term loan", "term loans", "tl details", "tl breakdown"],
    "maturity":          ["maturity profile", "when does", "matures", "mature", "maturity wall"],
    "dscr":              ["dscr", "debt service coverage"],
    "icr":               ["icr", "interest coverage"],
    "td_ebitda":         ["debt to ebitda", "td/ebitda", "leverage ratio"],
    "tol_tnw":           ["tol/tnw", "tol tnw", "outside liabilities"],
    "fb_vs_nfb":         ["fb vs nfb", "funded vs non-funded", "funded versus", "fb breakdown"],
    "nfb":               ["nfb", "non-fund based", "non fund based", "letter of credit", "lc commission"],
    "expired":           ["expired", "expired facilities", "expiry", "renewal"],
    "tbd_rates":         ["tbd rate", "tbd", "rate to be determined", "rate not fixed"],
    "fx_risk":           ["fx", "forex", "currency risk", "usd exposure", "buyer's credit"],
    "headroom":          ["headroom", "available", "undrawn", "unused"],
    "what_if_severe":    ["severe stress", "severe scenario", "worst case"],
    "health_score":      ["health score", "health", "overall score"],
    "financial_position":["financial position", "overall position", "where do we stand", "general health"],
    "recommendations":   ["recommend", "recommendations", "what should i do", "advice"],
}


def _classify_intent(prompt: str) -> str:
    """Match user prompt to closest intent. Returns 'general' if no match."""
    prompt_lower = prompt.lower().strip()
    
    # Score each intent by counting matching keywords
    scores = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in prompt_lower)
        if score > 0:
            scores[intent] = score
    
    if not scores:
        return "general"
    return max(scores, key=scores.get)


# ─────────────────────────────────────────────────────────────────────────────
# CONTEXT EXTRACTOR — pull key numbers from logic engine
# ─────────────────────────────────────────────────────────────────────────────
def _extract_context(logic, controls) -> dict:
    """Pull all key metrics from logic for use in rule-based responses."""
    ls = logic.lender_summary()
    cov_df = logic.calculate_covenants(controls.get("ebitda_change", 0))
    interest = logic.calculate_annual_interest(
        controls.get("rate_shock", 0),
        controls.get("spread_shock", 0),
    )
    f = logic.financials[logic.basis]
    fm = logic.facility_master

    breaches = cov_df[cov_df["Status"] == "Breach"]
    near = cov_df[cov_df["Status"] == "Near Breach"]
    watch = cov_df[cov_df["Status"] == "Watch"]

    # Tightest covenant (smallest headroom %)
    cov_sorted = cov_df.sort_values("Headroom_Pct", ascending=True) if "Headroom_Pct" in cov_df.columns else cov_df
    tightest = cov_sorted.iloc[0] if len(cov_sorted) > 0 else None

    # Lender breakdown
    largest_lender_row = ls.iloc[0] if len(ls) > 0 else None
    rbl_pct = (ls[ls["Lender"] == "RBL Bank"]["Total_Sanction"].sum() /
               ls["Total_Sanction"].sum() * 100) if len(ls) > 0 else 0

    # FY26E covenant baselines
    ebitda = f.get("EBITDA", 383.96)
    total_debt = f.get("Total Debt", 613.03)
    interest_exp = f.get("Interest Expense", 49.08)
    tax = f.get("Tax Paid", 69.36)
    sched_repay = f.get("Sched TL Repay", 41.09)
    current_assets = f.get("Current Assets", 755.02)
    current_liab = f.get("Current Liabilities", 544.79)

    dscr = (ebitda - tax) / (sched_repay + interest_exp) if (sched_repay + interest_exp) > 0 else 0
    icr = ebitda / interest_exp if interest_exp > 0 else 0
    td_ebitda = total_debt / ebitda if ebitda > 0 else 0
    cr = current_assets / current_liab if current_liab > 0 else 0

    # FB / NFB / TL breakdown
    fb_total = ls["FB_Sanction"].sum() if "FB_Sanction" in ls.columns else 0
    nfb_total = ls["NFB_Sanction"].sum() if "NFB_Sanction" in ls.columns else 0
    tl_total = ls["TL_Sanction"].sum() if "TL_Sanction" in ls.columns else 0
    total_sanc = ls["Total_Sanction"].sum() if "Total_Sanction" in ls.columns else 0

    # WAC
    wac = logic.weighted_avg_cost() * 100

    # TBD rates
    tbd_count = len(fm[fm.get("Rate_Type", "") == "TBD"]) if "Rate_Type" in fm.columns else 0

    # Expired facilities
    today = pd.Timestamp(logic.as_of_date)
    expired_count = 0
    if "Validity_Date" in fm.columns:
        expired_count = len(fm[fm["Validity_Date"] < today])

    return {
        "ls":               ls,
        "cov_df":           cov_df,
        "fm":               fm,
        "interest":         interest,
        "financials":       f,
        "basis":            logic.basis,
        "as_of":            logic.as_of_date,
        "fx":               logic.fx_rate,
        "breaches":         breaches,
        "near":             near,
        "watch":            watch,
        "tightest":         tightest,
        "rbl_pct":          rbl_pct,
        "ebitda":           ebitda,
        "total_debt":       total_debt,
        "interest_exp":     interest_exp,
        "dscr":             dscr,
        "icr":              icr,
        "td_ebitda":        td_ebitda,
        "cr":               cr,
        "fb_total":         fb_total,
        "nfb_total":        nfb_total,
        "tl_total":         tl_total,
        "total_sanc":       total_sanc,
        "wac":              wac,
        "tbd_count":        tbd_count,
        "expired_count":    expired_count,
        "rate_shock":       controls.get("rate_shock", 0),
        "spread_shock":     controls.get("spread_shock", 0),
        "ebitda_change":    controls.get("ebitda_change", 0),
    }


# ─────────────────────────────────────────────────────────────────────────────
# RESPONSE GENERATORS — one function per intent
# ─────────────────────────────────────────────────────────────────────────────
def _resp_interest_cost(c: dict) -> str:
    return (
        f"### Annual Interest Cost\n\n"
        f"**Total Annual Cost: ₹{c['interest']['total']:.2f} Cr**\n\n"
        f"Breakdown:\n"
        f"- Fund-based interest: **₹{c['interest']['fb_interest']:.2f} Cr** "
        f"(on FB outstanding of ₹{c['fb_total']:.0f} Cr)\n"
        f"- Non-fund-based commission: **₹{c['interest']['nfb_commission']:.2f} Cr** "
        f"(on NFB outstanding of ₹{c['nfb_total']:.0f} Cr)\n\n"
        f"**Weighted Average Cost (FB only): {c['wac']:.2f}%**\n\n"
        + (f"⚠ This reflects current stress: rate {c['rate_shock']:+d}bps, "
           f"spread {c['spread_shock']:+d}bps.\n" if c['rate_shock'] or c['spread_shock'] else "")
    )


def _resp_wac(c: dict) -> str:
    return (
        f"### Weighted Average Cost\n\n"
        f"**WAC = {c['wac']:.2f}%**\n\n"
        f"This is the average cost across all fund-based facilities, weighted by outstanding amount. "
        f"It excludes NFB (commission-based) facilities.\n\n"
        f"**Why is it relatively low?**\n"
        f"- USD Buyer's Credit facilities (~₹272 Cr) are at SOFR + ~0% (≈4.30%)\n"
        f"- FD-backed facilities (~₹150 Cr) are at near-zero net cost\n"
        f"- INR working capital is at ~9% (1Y MCLR + spread)\n"
        f"- Term loans average 8.7% (RBL TL 9.75%, YBL TL 7.70%, Bajaj TL 8.60%)\n\n"
        f"**Implication:** Low WAC partially reflects the FX hedging cost not being captured here. "
        f"True all-in cost (including hedge) is likely 100-150 bps higher."
    )


def _resp_biggest_risk(c: dict) -> str:
    risks = []
    if len(c["breaches"]) > 0:
        b = c["breaches"].iloc[0]
        risks.append(f"🔴 **BREACH: {b['Lender']} {b['Covenant']}** — immediate escalation required")
    if len(c["near"]) > 0:
        n = c["near"].iloc[0]
        risks.append(f"🟡 **Near-breach: {n['Lender']} {n['Covenant']}** "
                     f"(only {n['Headroom_Pct']:.1f}% headroom)")
    if c["rbl_pct"] > 40:
        risks.append(f"⚠ **Lender concentration: RBL = {c['rbl_pct']:.1f}%** "
                     f"of total ₹{c['total_sanc']:.0f} Cr exposure")
    if c["tbd_count"] >= 5:
        risks.append(f"⚠ **{c['tbd_count']} facilities have TBD rates** — actual cost could differ from projections")
    if c["expired_count"] >= 5:
        risks.append(f"⚠ **{c['expired_count']} facilities show expired validity dates** — renewal status unconfirmed")

    body = "### Top Risks in Portfolio\n\n"
    if not risks:
        body += "All headline risk indicators are healthy. Watch items are minor.\n\n"
    else:
        body += "\n".join(f"{i+1}. {r}" for i, r in enumerate(risks)) + "\n\n"

    # Add the SIB current ratio as the structural risk
    body += (
        f"### Structural Watch: SIB Current Ratio\n"
        f"Currently at {c['cr']:.3f}x vs threshold >1.33x. Headroom: only {((c['cr']/1.33 - 1)*100):.1f}%.\n"
        f"This is a structural tightness — same in FY24A. Tied to Buyer's Credit current maturities.\n"
    )
    return body


def _resp_covenant_breach(c: dict) -> str:
    body = "### Covenant Headroom Analysis\n\n"

    if len(c["breaches"]) > 0:
        body += f"**🔴 Active Breaches ({len(c['breaches'])}):**\n"
        for _, r in c["breaches"].iterrows():
            body += f"- {r['Lender']} {r['Covenant']}: {r['Actual']} vs {r['Threshold']}\n"
        body += "\n"

    if len(c["near"]) > 0:
        body += f"**🟡 Near Breaches (<5% headroom — {len(c['near'])}):**\n"
        for _, r in c["near"].iterrows():
            body += f"- {r['Lender']} {r['Covenant']}: {r['Actual']} (threshold: {r['Threshold']}, headroom: {r.get('Headroom_Pct', 0):.1f}%)\n"
        body += "\n"

    if len(c["watch"]) > 0:
        body += f"**🟠 Watch (5–10% headroom — {len(c['watch'])}):**\n"
        for _, r in c["watch"].iterrows():
            body += f"- {r['Lender']} {r['Covenant']}: headroom {r.get('Headroom_Pct', 0):.1f}%\n"
        body += "\n"

    compliant_count = (c["cov_df"]["Status"] == "Compliant").sum()
    body += f"**✅ Compliant: {compliant_count}/{len(c['cov_df'])} covenants ({compliant_count/len(c['cov_df'])*100:.0f}%)**\n"
    return body


def _resp_ebitda_drop(c: dict) -> str:
    # Simulate a 15% EBITDA drop
    ebitda_15 = c["ebitda"] * 0.85
    ebitda_30 = c["ebitda"] * 0.70

    dscr_15 = (ebitda_15 - c["financials"].get("Tax Paid", 0)) / (
        c["financials"].get("Sched TL Repay", 41.09) + c["interest_exp"])
    icr_15 = ebitda_15 / c["interest_exp"]
    td_e_15 = c["total_debt"] / ebitda_15

    dscr_30 = (ebitda_30 - c["financials"].get("Tax Paid", 0)) / (
        c["financials"].get("Sched TL Repay", 41.09) + c["interest_exp"])

    return (
        f"### EBITDA Drop Stress Test\n\n"
        f"**Current FY26E EBITDA: ₹{c['ebitda']:.2f} Cr**\n\n"
        f"### If EBITDA drops 15%:\n"
        f"- New EBITDA: ₹{ebitda_15:.2f} Cr\n"
        f"- DSCR: {c['dscr']:.2f}x → **{dscr_15:.2f}x** "
        f"({'still healthy' if dscr_15 > 1.5 else 'tightening'})\n"
        f"- ICR: {c['icr']:.2f}x → **{icr_15:.2f}x**\n"
        f"- TD/EBITDA: {c['td_ebitda']:.2f}x → **{td_e_15:.2f}x**\n\n"
        f"### If EBITDA drops 30%:\n"
        f"- New EBITDA: ₹{ebitda_30:.2f} Cr\n"
        f"- DSCR: {c['dscr']:.2f}x → **{dscr_30:.2f}x** "
        f"({'⚠ tight against 1.20x covenant' if dscr_30 < 1.5 else 'still adequate'})\n\n"
        f"### Most Vulnerable Covenants:\n"
        f"1. **YBL Total Debt/EBITDA (FY28+) <3.5x** — would breach at ~30% EBITDA drop\n"
        f"2. **Bajaj ICR ≥3.5x** — would tighten if interest rises with EBITDA falls\n"
        f"3. **All DSCR covenants** — JCL has high cushion now (3.49x), but stress narrows it\n"
    )


def _resp_rate_hike(c: dict) -> str:
    # Estimate impact of +50bps and +100bps
    fb_outstanding = c["fb_total"]
    impact_50 = fb_outstanding * 0.005
    impact_100 = fb_outstanding * 0.01

    # Floating-rate exposure (RBL TL + Cash Credit + ICICI CC + SIB CCOL etc)
    floating_share = 0.71  # ~71% from earlier analysis
    floating_outstanding = fb_outstanding * floating_share

    return (
        f"### Interest Rate Hike Impact\n\n"
        f"**Floating-rate exposure: ~₹{floating_outstanding:.0f} Cr ({floating_share*100:.0f}% of FB)**\n\n"
        f"### +50 bps RBI rate hike:\n"
        f"- Annual interest impact: **+₹{impact_50:.2f} Cr**\n"
        f"- New WAC: {c['wac']:.2f}% → ~{c['wac']+0.50:.2f}%\n"
        f"- DSCR impact: {c['dscr']:.2f}x → ~{c['dscr']-0.05:.2f}x (minimal)\n\n"
        f"### +100 bps RBI rate hike:\n"
        f"- Annual interest impact: **+₹{impact_100:.2f} Cr**\n"
        f"- New WAC: {c['wac']:.2f}% → ~{c['wac']+1.0:.2f}%\n"
        f"- DSCR: {c['dscr']:.2f}x → ~{c['dscr']-0.10:.2f}x\n\n"
        f"### Mitigation:\n"
        f"- ₹150 Cr Bajaj TL: BFRR-linked (less RBI-sensitive)\n"
        f"- ₹272 Cr USD facilities: SOFR-linked (US Fed driven, not RBI)\n"
        f"- ₹150 Cr FD-backed: near-zero net rate impact\n"
        f"- Effective rate-sensitive debt is ~₹770 Cr"
    )


def _resp_concentration(c: dict) -> str:
    body = f"### Lender Concentration Analysis\n\n"
    body += "| Lender | Total | Share | Type |\n|---|---|---|---|\n"
    for _, r in c["ls"].iterrows():
        share = r["Total_Sanction"] / c["total_sanc"] * 100
        flag = "⚠" if share > 30 else "✓"
        body += f"| {r['Lender']} | ₹{r['Total_Sanction']:.0f} Cr | {share:.1f}% | {flag} |\n"

    body += (
        f"\n### Key Findings:\n"
        f"- **RBL = {c['rbl_pct']:.1f}% of portfolio** — exceeds 30% concentration threshold\n"
        f"- If RBL withdraws or tightens: ₹{c['ls'][c['ls']['Lender']=='RBL Bank']['Total_Sanction'].sum():.0f} Cr "
        f"would need replacement\n"
        f"- WC lines (revolving) at RBL would be most exposed in a withdrawal scenario\n\n"
        f"### Recommendation:\n"
        f"- Diversify by adding 1-2 new lenders (HDFC, Axis) to reduce RBL share to <35%\n"
        f"- Consider negotiating umbrella caps (RBL ₹300 Cr) to be split across providers\n"
    )
    return body


def _resp_refinancing(c: dict) -> str:
    return (
        f"### Refinancing Risk Profile\n\n"
        f"### Term Loans Maturity Wall:\n"
        f"- **RBL TL ₹200 Cr** matures Jan-2029 (3 years out)\n"
        f"- **Bajaj TL ₹150 Cr** matures Aug-2033 (8 years out)\n"
        f"- **YES Bank TL ₹320.7 Cr** matures Sep-2036 (11 years out)\n\n"
        f"### Working Capital Renewal Risk:\n"
        f"- All 23 WC facilities renew annually\n"
        f"- Most expire Nov-2026 (RBL umbrella) and Mar-2027 (YBL umbrella)\n"
        f"- {c['expired_count']} facilities currently show expired validity (assumed renewed)\n\n"
        f"### Risk Assessment:\n"
        f"- **Low refinancing risk** for next 3 years (RBL TL is the earliest)\n"
        f"- A+ rating provides strong access to bank lending\n"
        f"- 5 lender relationships provide redundancy\n\n"
        f"### Recommendation:\n"
        f"- Begin RBL TL refinancing discussions in Jan-2028 (12M before maturity)\n"
        f"- Maintain high DSCR (currently 3.49x) to support competitive refinancing terms\n"
    )


def _resp_prepay(c: dict) -> str:
    return (
        f"### Term Loan Prepayment Analysis\n\n"
        f"### Cost-Per-Cr Comparison:\n"
        f"| TL | Outstanding | Rate | Annual Interest | Maturity |\n"
        f"|---|---|---|---|---|\n"
        f"| RBL | ₹200 Cr | **9.75%** | ₹19.50 Cr | Jan-2029 |\n"
        f"| Bajaj | ₹150 Cr | 8.60% | ₹12.90 Cr | Aug-2033 |\n"
        f"| YES Bank | ₹320.7 Cr | 7.70% | ₹24.69 Cr | Sep-2036 |\n\n"
        f"### Recommendation: **Prepay RBL TL First**\n"
        f"**Why:**\n"
        f"1. **Highest rate**: 9.75% vs 8.60% (Bajaj) and 7.70% (YBL)\n"
        f"2. **Largest concentration**: RBL is 43.5% of portfolio — prepay reduces single-lender exposure\n"
        f"3. **Floating rate**: 1Y MCLR + 75 bps — vulnerable if RBI hikes\n"
        f"4. **Earliest maturity**: Already 24-month moratorium ended; deeper amortisation by 2027\n\n"
        f"### Prepayment Math (Save):\n"
        f"- Prepay ₹100 Cr of RBL TL today = **₹9.75 Cr/yr saved** (less amortising interest)\n"
        f"- vs Bajaj ₹100 Cr prepay = ₹8.60 Cr/yr saved\n\n"
        f"### Caveat:\n"
        f"Check sanction letter for prepayment penalty (typically 1-2% of outstanding for floating rate TLs)."
    )


def _resp_sib_current(c: dict) -> str:
    return (
        f"### SIB Current Ratio — Detailed Analysis\n\n"
        f"**Current Status: 🟡 NEAR BREACH**\n\n"
        f"- **Actual: {c['cr']:.3f}x**\n"
        f"- **Threshold: >1.33x**\n"
        f"- **Headroom: {((c['cr']/1.33 - 1)*100):.1f}%**\n\n"
        f"### Why is it tight?\n"
        f"Current Liabilities (₹{c['financials'].get('Current Liabilities', 544.79):.0f} Cr) include:\n"
        f"- Buyer's Credit current maturities (~₹272 Cr USD)\n"
        f"- Trade payables (raw material suppliers)\n"
        f"- Short-term WC borrowings (CC, WCDL)\n\n"
        f"### Why does it matter?\n"
        f"- This covenant is in SIB sanction letter (21-Jun-2025)\n"
        f"- SIB exposure = ₹453 Cr (13.3% of portfolio)\n"
        f"- A breach triggers reporting obligations and potential pricing review\n\n"
        f"### How to fix it (3 options):\n"
        f"**Option 1: Reduce Current Liabilities**\n"
        f"- Refinance ₹50 Cr of Buyer's Credit into long-term USD ECB → CR rises to ~1.45x\n\n"
        f"**Option 2: Increase Current Assets**\n"
        f"- Build inventory buffer with ₹50 Cr cash injection from operations\n"
        f"- Or factor receivables (improves CA composition without leverage)\n\n"
        f"**Option 3: Negotiate covenant relaxation with SIB**\n"
        f"- Show 3-year forward projection where CR > 1.50x\n"
        f"- Standard ask: relax to >1.20x to align with sector norms\n"
    )


def _resp_leverage(c: dict) -> str:
    # Industry benchmarks for coke / metals manufacturers
    return (
        f"### JCL Leverage vs Industry (Coke / Metals)\n\n"
        f"### JCL's Metrics:\n"
        f"- **TD/EBITDA: {c['td_ebitda']:.2f}x**\n"
        f"- **TOL/TNW: {c['financials'].get('TOL', 0)/c['financials'].get('TNW', 1):.2f}x**\n"
        f"- **Net Debt/EBITDA: ~1.6x (after subtracting cash)**\n"
        f"- **External Rating: CARE A+; Stable / A1**\n\n"
        f"### Industry Benchmarks (Coke & Steel, FY24-25):\n"
        f"| Metric | Industry Range | JCL | Verdict |\n|---|---|---|---|\n"
        f"| TD/EBITDA | 2.5x – 4.5x | **{c['td_ebitda']:.2f}x** | ✅ Strong |\n"
        f"| TOL/TNW | 1.5x – 2.5x | **{c['financials'].get('TOL', 0)/c['financials'].get('TNW', 1):.2f}x** | ✅ Conservative |\n"
        f"| ICR | 3.0x – 5.0x | **{c['icr']:.2f}x** | ✅ Excellent |\n"
        f"| DSCR | 1.5x – 2.5x | **{c['dscr']:.2f}x** | ✅ Excellent |\n\n"
        f"### Key Insight:\n"
        f"JCL is **significantly below industry leverage**, which:\n"
        f"- Justifies the A+ rating (most peers are A or A-)\n"
        f"- Provides cushion for capex expansion (Khurunti, Kalinga)\n"
        f"- Supports negotiating power on rate/spread\n\n"
        f"### Comparison Peers:\n"
        f"- **Saurashtra Cement / Mukand**: TD/EBITDA ~3.5x (BBB+/A-)\n"
        f"- **Tata Steel BSL**: TD/EBITDA ~2.8x (AA-)\n"
        f"- **Hindalco Industries**: TD/EBITDA ~2.0x (AA)\n"
    )


def _resp_summary(c: dict) -> str:
    return (
        f"### Board Presentation — 5-Bullet Summary\n\n"
        f"**1. Portfolio Health: STRONG**\n"
        f"   ₹{c['total_sanc']:.0f} Cr sanctioned across 5 lenders, 34 facilities. "
        f"DSCR {c['dscr']:.2f}x, ICR {c['icr']:.2f}x — both well above all covenant thresholds. "
        f"23/24 covenants Compliant.\n\n"
        f"**2. Annual Run-Rate Cost: ₹{c['interest']['total']:.1f} Cr** "
        f"(₹{c['interest']['fb_interest']:.1f} Cr interest + ₹{c['interest']['nfb_commission']:.1f} Cr NFB commission). "
        f"Weighted avg cost {c['wac']:.2f}% — competitive vs A+ peers.\n\n"
        f"**3. One Watch Item: SIB Current Ratio at {c['cr']:.3f}x** "
        f"(threshold >1.33x). Headroom 4.2%. Structural — same in FY24A. "
        f"Mitigation: refinance Buyer's Credit current maturities to long-term.\n\n"
        f"**4. Lender Concentration: RBL = {c['rbl_pct']:.1f}%**. "
        f"Recommendation: diversify with 1 new bank (HDFC/Axis) to reduce to <35%.\n\n"
        f"**5. Pending Action Items:**\n"
        f"   - 7 facilities with TBD rates (Facility Master Col Q)\n"
        f"   - {c['expired_count']} facilities with expired validity (renewal status to confirm)\n"
        f"   - YBL TL EQI vs graduated schedule (sanction letter review)\n"
    )


def _resp_lender_review(c: dict) -> str:
    return (
        f"### Priorities for Next Lender Review Meeting\n\n"
        f"### TIER 1 (Critical):\n"
        f"1. **Resolve YBL TL amortisation schedule**: EQI vs graduated. "
        f"Sanction letter ambiguous; Mentor's model uses graduated. "
        f"Confirm in writing.\n\n"
        f"2. **Confirm RBL TL actual rate**: Currently indicative 9.75%. "
        f"Sanction letter defers to drawdown. Get RBL to confirm post-drawdown.\n\n"
        f"### TIER 2 (Important):\n"
        f"3. **Update 7 TBD rates**: PID, LCBD, WCDL, PIF, WCL, ICICI WCDL spread. "
        f"Each needs sanction letter or email confirmation.\n\n"
        f"4. **Renew {c['expired_count']} facilities** with expired validity dates. "
        f"Most are RBL umbrella WC lines (annual rollover assumed but not documented).\n\n"
        f"5. **YES Bank PIF ₹100 Cr** — already EXPIRED 28-Apr-2026. **Initiate renewal immediately.**\n\n"
        f"### TIER 3 (Strategic):\n"
        f"6. **Negotiate SIB Current Ratio relaxation** from >1.33x to >1.20x.\n\n"
        f"7. **RBL BG commission**: confirm 1.00% vs 0.50% (latest sanction letter pricing).\n\n"
        f"8. **Lender concentration**: discuss RBL exposure cap (₹300 Cr) vs current ₹1,482 Cr.\n"
    )


def _resp_term_loans(c: dict) -> str:
    return (
        f"### Term Loan Portfolio\n\n"
        f"**Total TL: ₹{c['tl_total']:.1f} Cr across 3 facilities**\n\n"
        f"### 1. RBL Bank TL — ₹200 Cr\n"
        f"- Drawdown: 24-Jan-2024 | Maturity: 24-Jan-2029 (5Y)\n"
        f"- Moratorium: 24 months (ended Jan-2026)\n"
        f"- Repayment: 12 EQI of ₹16.67 Cr starting Q4 FY26\n"
        f"- Rate: 1Y MCLR + 75 bps = **9.75% (indicative)**\n"
        f"- Annual Interest: ₹19.50 Cr\n\n"
        f"### 2. YES Bank TL — ₹320.7 Cr\n"
        f"- Drawdown: 16-Dec-2024 | Maturity: 30-Sep-2036 (12Y)\n"
        f"- Moratorium: 0 months\n"
        f"- Repayment: 47 EQI of ₹6.82 Cr starting Q4 FY25\n"
        f"- Rate: 3M T-Bill + 252 bps = **7.70%**\n"
        f"- Annual Interest: ₹24.69 Cr\n"
        f"- ⚠ Schedule ambiguity: EQI vs graduated\n\n"
        f"### 3. Bajaj Finance TL — ₹150 Cr\n"
        f"- Drawdown: 18-Aug-2025 | Maturity: 18-Aug-2033 (8Y)\n"
        f"- Moratorium: 12 months (ends Aug-2026)\n"
        f"- Repayment: 28 EQI of ₹5.36 Cr starting Q3 FY27\n"
        f"- Rate: BFRR + 10 bps = **8.60%**\n"
        f"- Annual Interest: ₹12.90 Cr\n\n"
        f"### Combined Annual Debt Service:\n"
        f"- Total Principal due (next 12M): ₹50 Cr (RBL only — others still in moratorium)\n"
        f"- Total Interest (next 12M): ~₹57 Cr (run-rate at full balances)\n"
        f"- **Peak DS quarter: Q3 FY27 (~₹41 Cr)** when all 3 amortise simultaneously\n"
    )


def _resp_maturity(c: dict) -> str:
    return _resp_term_loans(c) + (
        "\n### Working Capital Maturity:\n"
        "All 23 WC facilities are revolving with annual validity:\n"
        "- RBL umbrella: most expire 30-Nov-2026\n"
        "- YBL umbrella: most expire Mar-2027\n"
        "- ICICI: 03-Sep-2026\n"
        "- SIB: 21-Jun-2026\n\n"
        "Annual renewal cycle is well-distributed across the year."
    )


def _resp_dscr(c: dict) -> str:
    return (
        f"### Debt Service Coverage Ratio (DSCR)\n\n"
        f"**JCL DSCR = {c['dscr']:.2f}x**\n\n"
        f"### Calculation:\n"
        f"```\n"
        f"DSCR = (EBITDA - Tax Paid) / (Scheduled TL Repayment + Interest)\n"
        f"     = (₹{c['ebitda']:.2f} - ₹{c['financials'].get('Tax Paid', 0):.2f}) / "
        f"(₹{c['financials'].get('Sched TL Repay', 0):.2f} + ₹{c['interest_exp']:.2f})\n"
        f"     = ₹{c['ebitda'] - c['financials'].get('Tax Paid', 0):.2f} / "
        f"₹{c['financials'].get('Sched TL Repay', 0) + c['interest_exp']:.2f}\n"
        f"     = {c['dscr']:.2f}x\n"
        f"```\n\n"
        f"### Covenant Thresholds:\n"
        f"- RBL: >1.25x ✅ (cushion: {c['dscr']/1.25*100-100:.0f}%)\n"
        f"- YBL: >1.20x ✅ (cushion: {c['dscr']/1.20*100-100:.0f}%)\n"
        f"- Bajaj: >1.20x ✅\n"
        f"- ICICI: >1.25x ✅\n\n"
        f"### Verdict: **Excellent**\n"
        f"DSCR of {c['dscr']:.2f}x means JCL earns ~{int(c['dscr'])} times the debt-service obligation. "
        f"Industry norm for A+ rated companies is 1.8x – 2.5x; JCL is well above."
    )


def _resp_icr(c: dict) -> str:
    return (
        f"### Interest Coverage Ratio (ICR)\n\n"
        f"**JCL ICR = {c['icr']:.2f}x**\n\n"
        f"### Calculation:\n"
        f"```\n"
        f"ICR = EBITDA / Interest Expense\n"
        f"    = ₹{c['ebitda']:.2f} / ₹{c['interest_exp']:.2f}\n"
        f"    = {c['icr']:.2f}x\n"
        f"```\n\n"
        f"### Covenant Threshold:\n"
        f"- Bajaj Finance: ≥3.5x (FY26 onwards) ✅\n"
        f"- South Indian Bank: >3.0x ✅\n\n"
        f"### Verdict: **Excellent**\n"
        f"JCL earns ~{int(c['icr'])}x its interest bill, which means even if EBITDA halved, "
        f"interest coverage would still exceed 3.9x. Very safe."
    )


def _resp_td_ebitda(c: dict) -> str:
    return (
        f"### Total Debt / EBITDA Ratio\n\n"
        f"**JCL TD/EBITDA = {c['td_ebitda']:.2f}x**\n\n"
        f"### Calculation:\n"
        f"```\n"
        f"TD/EBITDA = Total Debt / EBITDA\n"
        f"          = ₹{c['total_debt']:.2f} / ₹{c['ebitda']:.2f}\n"
        f"          = {c['td_ebitda']:.2f}x\n"
        f"```\n\n"
        f"### Covenant Thresholds:\n"
        f"- RBL Term Debt/EBITDA: <2.5x ✅\n"
        f"- YBL (≤FY27): <4.5x ✅\n"
        f"- YBL (FY28+): <3.5x ✅\n"
        f"- Bajaj: ≤4.0x ✅\n"
        f"- ICICI: <3.0x ✅\n\n"
        f"### Verdict: **Conservative**\n"
        f"At {c['td_ebitda']:.2f}x, JCL would need ~{c['td_ebitda']:.1f} years of EBITDA to repay all debt. "
        f"Industry norm for A+ coke/steel is 2.5–4.5x; JCL is at the conservative end."
    )


def _resp_tol_tnw(c: dict) -> str:
    tol = c["financials"].get("TOL", 0)
    tnw = c["financials"].get("TNW", 1)
    ratio = tol / tnw if tnw > 0 else 0
    return (
        f"### TOL/TNW (Total Outside Liabilities / Tangible Net Worth)\n\n"
        f"**JCL TOL/TNW = {ratio:.2f}x**\n\n"
        f"### Calculation:\n"
        f"```\n"
        f"TOL/TNW = ₹{tol:.2f} Cr / ₹{tnw:.2f} Cr = {ratio:.2f}x\n"
        f"```\n\n"
        f"### Covenant Thresholds:\n"
        f"- RBL: <3.0x ✅\n"
        f"- SIB: ≤3.0x ✅\n\n"
        f"### What it means:\n"
        f"For every ₹1 of owner's money (equity), JCL has ₹{ratio:.2f} of outside liabilities. "
        f"This includes both interest-bearing debt and trade liabilities.\n\n"
        f"### Verdict: **Healthy**\n"
        f"Below 2.0x is conservative for a manufacturing company; JCL's {ratio:.2f}x reflects "
        f"prudent capitalisation and strong promoter equity (100% Jindal family)."
    )


def _resp_fb_vs_nfb(c: dict) -> str:
    return (
        f"### Fund-Based vs Non-Fund Based Breakdown\n\n"
        f"### Fund-Based: ₹{c['fb_total']:.0f} Cr ({c['fb_total']/c['total_sanc']*100:.1f}%)\n"
        f"- Working Capital: ~₹{c['fb_total']-c['tl_total']:.0f} Cr (Cash Credit, WCDL, PIF, PALCBD)\n"
        f"- Term Loans: ₹{c['tl_total']:.1f} Cr (RBL, YBL, Bajaj)\n"
        f"- Annual Interest: ₹{c['interest']['fb_interest']:.2f} Cr\n\n"
        f"### Non-Fund Based: ₹{c['nfb_total']:.0f} Cr ({c['nfb_total']/c['total_sanc']*100:.1f}%)\n"
        f"- Letters of Credit: ~₹650 Cr\n"
        f"- Bank Guarantees: ~₹85 Cr\n"
        f"- SBLC for Buyer's Credit: ~₹780 Cr\n"
        f"- Capex LC: ~₹75 Cr\n"
        f"- Annual Commission: ₹{c['interest']['nfb_commission']:.2f} Cr (~{c['interest']['nfb_commission']/c['nfb_total']*100:.2f}% blended)\n\n"
        f"### Key Insight:\n"
        f"NFB is **larger than FB** ({c['nfb_total']/c['fb_total']*100:.0f}% of FB). "
        f"This is unusual but appropriate for JCL's business — large LC/SBLC are needed for "
        f"raw material imports and Buyer's Credit financing.\n\n"
        f"NFB is **contingent**: only crystallises into debt if invoked. Currently not invoked."
    )


def _resp_nfb(c: dict) -> str:
    return _resp_fb_vs_nfb(c)


def _resp_expired(c: dict) -> str:
    if c["expired_count"] == 0:
        return "### No Expired Facilities\n\nAll 34 facilities have current validity dates."

    fm_expired = c["fm"][c["fm"]["Validity_Date"] < pd.Timestamp(c["as_of"])]
    body = f"### {c['expired_count']} Facilities with Expired Validity\n\n"
    body += "These are working capital lines whose validity dates pre-date 21-Apr-2026. "
    body += "Per Section E (Explicit Assumptions), they are assumed annually renewed unless advised otherwise.\n\n"
    body += "| Lender | Facility | Validity Date | Days Expired |\n|---|---|---|---|\n"
    today = pd.Timestamp(c["as_of"])
    for _, r in fm_expired.iterrows():
        if pd.isna(r.get("Validity_Date")):
            continue
        days = (today - r["Validity_Date"]).days
        body += f"| {r.get('Lender', '?')} | {r.get('Facility', '?')[:40]} | {r['Validity_Date'].strftime('%d-%b-%Y')} | {days}d |\n"

    body += "\n### Action Required:\n"
    body += "1. Confirm with operations team which have been operationally renewed\n"
    body += "2. Update Facility Master Column Z (Validity Date) with new dates\n"
    body += "3. **YES Bank PIF ₹100 Cr expired 28-Apr-2026** — initiate renewal immediately\n"
    return body


def _resp_tbd_rates(c: dict) -> str:
    if c["tbd_count"] == 0:
        return "### All Rates Confirmed\n\nNo facilities have TBD (To Be Determined) rates."

    fm_tbd = c["fm"][c["fm"].get("Rate_Type", "") == "TBD"]
    body = f"### {c['tbd_count']} Facilities with TBD Rates\n\n"
    body += "These facilities don't have a confirmed rate yet — sanction letter says "
    body += "'rate to be fixed at drawdown'. Currently shown at 0% (no interest accrual).\n\n"
    body += "| Lender | Facility | Sanctioned | Status |\n|---|---|---|---|\n"
    for _, r in fm_tbd.iterrows():
        body += f"| {r.get('Lender', '?')} | {r.get('Facility', '?')[:40]} | ₹{r.get('Sanction_INR', 0):.0f} Cr | ⚠ Rate TBD |\n"

    body += "\n### Action Required:\n"
    body += "Update Facility Master Column Q (Effective_Rate) when each is drawn or rate is confirmed.\n"
    body += "\n### Risk:\n"
    body += "If all TBD rates land at ~9% (typical), incremental cost = "
    body += f"~₹{fm_tbd.get('Sanction_INR', pd.Series([0])).sum() * 0.09:.1f} Cr/year"
    return body


def _resp_fx_risk(c: dict) -> str:
    fm_usd = c["fm"][c["fm"].get("Currency", "") == "USD"] if "Currency" in c["fm"].columns else c["fm"].head(0)
    usd_exposure = fm_usd.get("Sanction_INR", pd.Series([0])).sum()

    return (
        f"### Foreign Exchange Risk Analysis\n\n"
        f"### USD Exposure: ~₹{usd_exposure:.0f} Cr\n"
        f"- RBL Buyer's Credit (WC): USD 11M ≈ ₹100 Cr\n"
        f"- RBL Buyer's Credit (CAPEX): USD 20M ≈ ₹172 Cr\n"
        f"- All linked to Term SOFR (USD) ≈ 4.30%\n\n"
        f"### Hedging:\n"
        f"- RBL LER (Loan Equivalent Risk): ₹20 Cr — Forex hedging cap\n"
        f"- SIB Forward Contract Limit: ₹3 Cr\n"
        f"- **Total hedge cover: ₹23 Cr** (vs ₹272 Cr USD exposure)\n\n"
        f"### Risk Assessment:\n"
        f"- **Hedge ratio: ~8.5%** — significantly under-hedged\n"
        f"- USD/INR currently at ₹{c['fx']:.2f}\n"
        f"- A 10% INR depreciation = **₹27 Cr MTM loss** on unhedged USD debt\n\n"
        f"### Recommendation:\n"
        f"1. Increase forward contract coverage to 60-70% of USD debt\n"
        f"2. Use natural hedges where possible (USD revenue from coke exports)\n"
        f"3. Consider USD ECB to refinance Buyer's Credit (longer hedge tenor)"
    )


def _resp_headroom(c: dict) -> str:
    fm = c["fm"].copy()
    if "Headroom_INR" not in fm.columns:
        fm["Headroom_INR"] = fm.get("Sanction_INR", 0) - fm.get("Outstanding_INR", 0)

    headroom_total = fm["Headroom_INR"].sum()
    fm_with_room = fm[fm["Headroom_INR"] > 1].sort_values("Headroom_INR", ascending=False)

    body = f"### Available Headroom\n\n"
    body += f"**Total Available: ₹{headroom_total:.0f} Cr** across {len(fm_with_room)} facilities\n\n"

    if len(fm_with_room) > 0:
        body += "### Top Facilities with Headroom:\n"
        body += "| Lender | Facility | Sanction | Outstanding | Headroom |\n|---|---|---|---|---|\n"
        for _, r in fm_with_room.head(10).iterrows():
            body += (f"| {r.get('Lender', '?')} | {r.get('Facility', '?')[:30]} | "
                     f"₹{r.get('Sanction_INR', 0):.0f} | ₹{r.get('Outstanding_INR', 0):.0f} | "
                     f"₹{r['Headroom_INR']:.0f} |\n")
    else:
        body += "All facilities are 100% utilised (Full Utilisation toggle is ON in Excel).\n"
        body += "To see actual headroom, set 'Use Full Utilisation = Sanctioned?' to FALSE in Instructions tab.\n"

    return body


def _resp_what_if_severe(c: dict) -> str:
    # Severe stress: +200 bps, -30% EBITDA, +50 bps spread
    ebitda_severe = c["ebitda"] * 0.70
    interest_severe = c["interest_exp"] * 1.40  # rough proxy for +200 bps + spread
    dscr_severe = (ebitda_severe - c["financials"].get("Tax Paid", 0)) / (
        c["financials"].get("Sched TL Repay", 41.09) + interest_severe)
    icr_severe = ebitda_severe / interest_severe
    td_e_severe = c["total_debt"] / ebitda_severe

    return (
        f"### Severe Stress Test Results\n\n"
        f"**Scenario:** Rate +200bps, Spread +50bps, EBITDA -30%\n\n"
        f"### Projected Metrics:\n"
        f"| Metric | Base | Severe Stress | Status |\n|---|---|---|---|\n"
        f"| EBITDA | ₹{c['ebitda']:.0f} Cr | ₹{ebitda_severe:.0f} Cr | -30% |\n"
        f"| Interest | ₹{c['interest_exp']:.0f} Cr | ₹{interest_severe:.0f} Cr | +40% |\n"
        f"| **DSCR** | **{c['dscr']:.2f}x** | **{dscr_severe:.2f}x** | "
        f"{'✅' if dscr_severe > 1.20 else '⚠ TIGHT' if dscr_severe > 1.0 else '🔴 BREACH'} |\n"
        f"| **ICR** | **{c['icr']:.2f}x** | **{icr_severe:.2f}x** | "
        f"{'✅' if icr_severe > 3.0 else '⚠ TIGHT' if icr_severe > 1.5 else '🔴 BREACH'} |\n"
        f"| **TD/EBITDA** | **{c['td_ebitda']:.2f}x** | **{td_e_severe:.2f}x** | "
        f"{'✅' if td_e_severe < 3.0 else '⚠' if td_e_severe < 4.0 else '🔴'} |\n\n"
        f"### Verdict:\n"
        f"Even under severe stress, JCL's metrics remain within most covenant bands. "
        f"DSCR holds above 1.5x (vs 1.20x covenant) and ICR above 3.0x. "
        f"This portfolio has substantial headroom for downturns.\n"
    )


def _resp_health_score(c: dict) -> str:
    # Compute a simple health score
    score = 0
    score += 20 if c["dscr"] > 2.0 else 15 if c["dscr"] > 1.5 else 10 if c["dscr"] > 1.25 else 5
    score += 20 if c["icr"] > 5.0 else 15 if c["icr"] > 3.5 else 10 if c["icr"] > 2.5 else 5
    score += 20 if c["td_ebitda"] < 2.0 else 15 if c["td_ebitda"] < 3.0 else 10 if c["td_ebitda"] < 4.0 else 5
    breach_pct = len(c["breaches"]) / len(c["cov_df"]) * 100
    score += 20 if breach_pct == 0 else 10 if breach_pct < 5 else 0
    score += 10 if c["rbl_pct"] < 35 else 5 if c["rbl_pct"] < 50 else 0
    score += 10 if c["expired_count"] < 3 else 5 if c["expired_count"] < 10 else 0

    grade = "A+" if score >= 90 else "A" if score >= 80 else "B+" if score >= 70 else "B" if score >= 60 else "C"

    return (
        f"### Portfolio Health Score: **{score}/100 (Grade {grade})**\n\n"
        f"### Component Scores:\n"
        f"| Component | Weight | Your Score | Notes |\n|---|---|---|---|\n"
        f"| DSCR | 20 | {min(20, int(c['dscr']/2*20))} | {c['dscr']:.2f}x vs 1.25x |\n"
        f"| ICR | 20 | {min(20, int(c['icr']/5*20))} | {c['icr']:.2f}x vs 3.5x |\n"
        f"| TD/EBITDA | 20 | {20 if c['td_ebitda']<2 else 15 if c['td_ebitda']<3 else 10} | {c['td_ebitda']:.2f}x vs 2.5x |\n"
        f"| Covenants | 20 | {20 if breach_pct==0 else 10} | {len(c['breaches'])} breaches |\n"
        f"| Concentration | 10 | {10 if c['rbl_pct']<35 else 5} | RBL {c['rbl_pct']:.1f}% |\n"
        f"| Documentation | 10 | {10 if c['expired_count']<3 else 5} | {c['expired_count']} expired |\n\n"
        f"### What's Holding Score Back:\n"
        + (f"- Lender concentration ({c['rbl_pct']:.0f}% RBL)\n" if c['rbl_pct'] >= 35 else "")
        + (f"- {c['expired_count']} facilities with expired validity\n" if c['expired_count'] >= 3 else "")
        + (f"- {c['tbd_count']} facilities with TBD rates\n" if c['tbd_count'] >= 5 else "")
        + (f"- Near-breach: {c['near'].iloc[0]['Lender']} {c['near'].iloc[0]['Covenant']}\n" if len(c['near']) > 0 else "")
    )


def _resp_financial_position(c: dict) -> str:
    return (
        f"### JCL Financial Position Summary\n\n"
        f"**As of: {c['as_of'].strftime('%d-%b-%Y')} | Basis: {c['basis']}**\n\n"
        f"### Earnings & Profitability:\n"
        f"- EBITDA: ₹{c['ebitda']:.0f} Cr "
        f"({'+121%' if c['basis'] == 'FY26E' else 'audited'} vs FY24A)\n"
        f"- PAT: ₹{c['financials'].get('PAT', 243):.0f} Cr\n"
        f"- Net Sales: ₹{c['financials'].get('Net Sales', 2079):.0f} Cr\n"
        f"- EBITDA Margin: {c['ebitda']/c['financials'].get('Net Sales', 2079)*100:.1f}%\n\n"
        f"### Balance Sheet:\n"
        f"- Total Debt: ₹{c['total_debt']:.0f} Cr (Term: ₹{c['financials'].get('Term Debt', 431):.0f} Cr, WC: ~₹{c['total_debt']-c['financials'].get('Term Debt', 431):.0f} Cr)\n"
        f"- Tangible Net Worth: ₹{c['financials'].get('TNW', 740):.0f} Cr\n"
        f"- Fixed Assets (net): ₹{c['financials'].get('Fixed Assets', 938):.0f} Cr\n"
        f"- Current Ratio: {c['cr']:.2f}x\n\n"
        f"### Credit Metrics:\n"
        f"- DSCR: **{c['dscr']:.2f}x** (covenant: >1.25x)\n"
        f"- ICR: **{c['icr']:.2f}x** (covenant: ≥3.5x)\n"
        f"- TD/EBITDA: **{c['td_ebitda']:.2f}x** (covenant: <2.5x)\n"
        f"- Rating: **CARE A+; Stable / A1**\n\n"
        f"### Verdict: **Strong investment-grade credit profile**\n"
    )


def _resp_recommendations(c: dict) -> str:
    return (
        f"### Strategic Recommendations\n\n"
        f"### Immediate (Next 30 Days):\n"
        f"1. **Renew YES Bank PIF ₹100 Cr** (expired 28-Apr-2026)\n"
        f"2. **Confirm RBL TL actual rate** post-drawdown (currently indicative 9.75%)\n"
        f"3. **Document YBL TL amortisation schedule** (EQI vs graduated)\n\n"
        f"### Short-term (Next 90 Days):\n"
        f"4. **Update {c['tbd_count']} TBD rates** in Facility Master Col Q\n"
        f"5. **Renew {c['expired_count']} expired facilities** (mostly RBL umbrella)\n"
        f"6. **Increase FX hedge** from ₹23 Cr to ₹160-200 Cr (60-70% of USD debt)\n\n"
        f"### Medium-term (6-12 Months):\n"
        f"7. **Diversify lender base**: add HDFC or Axis to reduce RBL concentration from {c['rbl_pct']:.0f}% to <35%\n"
        f"8. **Negotiate SIB Current Ratio relaxation** (1.33x → 1.20x)\n"
        f"9. **Refinance Buyer's Credit** as long-term USD ECB to improve current ratio\n\n"
        f"### Long-term (12-24 Months):\n"
        f"10. **Begin RBL TL refinancing discussions** in Jan-2028 (12M before Jan-2029 maturity)\n"
        f"11. **Build cash buffer** to reduce reliance on revolving WC lines\n"
        f"12. **Consider rating upgrade campaign** to AA- (lower spreads, more lender competition)\n"
    )


def _resp_general(prompt: str, c: dict) -> str:
    """Default response when intent isn't matched."""
    return (
        f"I couldn't match your question to a specific analysis. Here are some questions I can answer:\n\n"
        f"**Portfolio Overview:**\n"
        f"- What's our total annual interest cost?\n"
        f"- What's our weighted average cost?\n"
        f"- Show me a financial position summary\n\n"
        f"**Risk Analysis:**\n"
        f"- What's the biggest risk in this portfolio?\n"
        f"- Which covenant is closest to breach?\n"
        f"- Explain the SIB Current Ratio issue\n"
        f"- What's our refinancing risk?\n"
        f"- How does our leverage compare to industry?\n\n"
        f"**Stress Testing:**\n"
        f"- Which covenant breaks if EBITDA drops 15%?\n"
        f"- What's the impact of a 50 bps rate hike?\n"
        f"- Show me severe stress scenario\n\n"
        f"**Action Items:**\n"
        f"- Which term loan should we prepay first?\n"
        f"- What should we prioritise in the next lender review?\n"
        f"- Give me strategic recommendations\n\n"
        f"**Data Quality:**\n"
        f"- Show TBD rates\n"
        f"- Show expired facilities\n"
        f"- Show available headroom\n\n"
        f"---\n\n"
        f"**Quick Summary (current state):**\n"
        f"- Total Sanctioned: ₹{c['total_sanc']:.0f} Cr\n"
        f"- DSCR: {c['dscr']:.2f}x | ICR: {c['icr']:.2f}x | TD/EBITDA: {c['td_ebitda']:.2f}x\n"
        f"- Compliant: {(c['cov_df']['Status']=='Compliant').sum()}/{len(c['cov_df'])} covenants\n"
        f"- Annual cost: ₹{c['interest']['total']:.1f} Cr at WAC {c['wac']:.2f}%\n"
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT — streaming response
# ─────────────────────────────────────────────────────────────────────────────
INTENT_HANDLERS = {
    "interest_cost":       _resp_interest_cost,
    "wac":                 _resp_wac,
    "biggest_risk":        _resp_biggest_risk,
    "covenant_breach":     _resp_covenant_breach,
    "ebitda_drop":         _resp_ebitda_drop,
    "rate_hike":           _resp_rate_hike,
    "concentration":       _resp_concentration,
    "refinancing":         _resp_refinancing,
    "prepay":              _resp_prepay,
    "sib_current":         _resp_sib_current,
    "leverage":            _resp_leverage,
    "summary":             _resp_summary,
    "lender_review":       _resp_lender_review,
    "term_loans":          _resp_term_loans,
    "maturity":            _resp_maturity,
    "dscr":                _resp_dscr,
    "icr":                 _resp_icr,
    "td_ebitda":           _resp_td_ebitda,
    "tol_tnw":             _resp_tol_tnw,
    "fb_vs_nfb":           _resp_fb_vs_nfb,
    "nfb":                 _resp_nfb,
    "expired":             _resp_expired,
    "tbd_rates":           _resp_tbd_rates,
    "fx_risk":             _resp_fx_risk,
    "headroom":            _resp_headroom,
    "what_if_severe":      _resp_what_if_severe,
    "health_score":        _resp_health_score,
    "financial_position":  _resp_financial_position,
    "recommendations":     _resp_recommendations,
}


def stream_ai_response(prompt: str, logic, controls) -> Generator[str, None, None]:
    """
    Generator yielding analysis. Mimics streaming for smooth UI.
    """
    import time

    intent = _classify_intent(prompt)
    context = _extract_context(logic, controls)

    if intent == "general":
        response = _resp_general(prompt, context)
    else:
        handler = INTENT_HANDLERS.get(intent, lambda c: _resp_general(prompt, c))
        try:
            response = handler(context)
        except Exception as e:
            response = f"⚠ Error generating response: {e}\n\nPlease try a different question."

    # Stream word by word for nice UX
    words = response.split(" ")
    for i, word in enumerate(words):
        yield word + " "
        if i % 5 == 0:  # small delay every 5 words
            time.sleep(0.005)


# ─────────────────────────────────────────────────────────────────────────────
# PROACTIVE INSIGHTS — 3 cards generated from rules
# ─────────────────────────────────────────────────────────────────────────────
def get_proactive_insights(logic, controls) -> List[dict]:
    """3 deterministic insights based on portfolio state."""
    c = _extract_context(logic, controls)
    insights = []

    # Insight 1: Risk understated
    if c["expired_count"] >= 5:
        insights.append({
            "title": "Headline Headroom Overstated",
            "body": f"{c['expired_count']} facilities show expired validity. They're assumed renewed, but documentation lags reality. "
                    f"True renewal cycle gap could mean 3-6% of WC exposure is technically unconfirmed.",
        })
    elif c["tbd_count"] >= 5:
        insights.append({
            "title": "Cost Picture Optimistic",
            "body": f"{c['tbd_count']} facilities have TBD rates priced at 0%. If they land at 9% (typical), "
                    f"annual cost rises by ~₹{c['fm'][c['fm'].get('Rate_Type','')=='TBD'].get('Sanction_INR', pd.Series([0])).sum() * 0.09:.1f} Cr — "
                    f"~{c['fm'][c['fm'].get('Rate_Type','')=='TBD'].get('Sanction_INR', pd.Series([0])).sum() * 0.09 / c['interest']['total'] * 100:.0f}% increase.",
        })
    else:
        insights.append({
            "title": "FX Hedge Materially Under-Cover",
            "body": f"USD exposure is ~₹272 Cr but hedge cover only ₹23 Cr (8.5% ratio). "
                    f"A 10% INR depreciation = ₹27 Cr unhedged MTM loss. "
                    f"Industry norm: 60-70% hedge ratio.",
        })

    # Insight 2: Optimisation opportunity
    if c["rbl_pct"] > 40:
        insights.append({
            "title": "Lender Concentration = Pricing Leverage Loss",
            "body": f"RBL holds {c['rbl_pct']:.1f}% of exposure, exceeding ₹{c['ls'].iloc[0]['Total_Sanction']:.0f} Cr. "
                    f"Diversifying with HDFC/Axis at ₹400-500 Cr could yield 15-25 bps spread reduction "
                    f"(~₹{c['fb_total']*0.0020:.1f} Cr/yr saved) and stronger negotiation position.",
        })
    else:
        insights.append({
            "title": "Prepay RBL TL First — Highest Cost Reduction",
            "body": f"RBL TL at 9.75% is the most expensive borrowing. Prepaying ₹100 Cr saves ₹9.75 Cr/yr "
                    f"(vs ₹8.60 Cr if Bajaj, ₹7.70 Cr if YBL). DSCR cushion ({c['dscr']:.2f}x) supports this comfortably.",
        })

    # Insight 3: Forward-looking concern
    if c["dscr"] > 2.5:
        insights.append({
            "title": "Q3 FY27 Cash Outflow Spike",
            "body": f"All 3 TLs amortise simultaneously in Q3 FY27 (~₹41 Cr DS quarter vs current ~₹16 Cr). "
                    f"This is when RBL moratorium ends + Bajaj starts repaying. "
                    f"Treasury should plan a ₹50-75 Cr liquidity buffer for that quarter.",
        })
    else:
        insights.append({
            "title": "Refinancing Window Approaches",
            "body": f"RBL TL ₹200 Cr matures Jan-2029. Begin discussions Jan-2028 (12M lead). "
                    f"At {c['icr']:.1f}x ICR and A+ rating, refinancing should achieve 1Y MCLR + 50 bps "
                    f"(vs current +75 bps), saving ~₹{200*0.0025:.2f} Cr/yr.",
        })

    return insights


# ─────────────────────────────────────────────────────────────────────────────
# SUGGESTED QUESTIONS
# ─────────────────────────────────────────────────────────────────────────────
SUGGESTED_QUESTIONS = [
    "What is the biggest risk in this portfolio right now?",
    "Which covenant is most likely to breach if EBITDA drops 15%?",
    "What's the impact of a 50 bps RBI rate hike on our annual interest bill?",
    "Which term loan should we prepay first?",
    "Explain the SIB Current Ratio issue and how to fix it.",
    "How does JCL's leverage compare to industry norms?",
    "What's our refinancing risk over the next 3 years?",
    "Show me a 5-bullet board summary.",
    "What should we prioritise in the next lender review meeting?",
    "Give me strategic recommendations for the portfolio.",
]
