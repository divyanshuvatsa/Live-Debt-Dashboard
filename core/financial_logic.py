"""
JCL Debt Monitoring Dashboard — Financial Logic
Handles all financial calculations: covenant ratios, interest accrual,
scenario analysis, FX conversion, maturity bucketing.
"""

from datetime import date, datetime
import pandas as pd
import numpy as np
from typing import Dict, List, Optional


class FinancialLogic:
    """Core financial engine for JCL Debt Monitoring Dashboard."""

    def __init__(
        self,
        facility_master: pd.DataFrame,
        covenant_master: pd.DataFrame,
        tl_schedule: pd.DataFrame,
        financials: Dict,
        benchmark_rates: Dict,
        as_of_date: date,
        fx_rate: float = 92.98,
        basis: str = "FY26E",
    ):
        self.facility_master   = facility_master.copy()
        self.covenant_master   = covenant_master.copy()
        self.tl_schedule       = tl_schedule.copy()
        self.financials        = financials
        self.benchmark_rates   = benchmark_rates
        self.as_of_date        = pd.Timestamp(as_of_date)
        self.fx_rate           = fx_rate
        self.basis             = basis
        # FX-adjust USD facilities: take MIN of (USD * FX, INR cap)
        self._apply_fx_logic()

    # =========================================================================
    # FX & UTILIZATION
    # =========================================================================
    def _apply_fx_logic(self):
        """For USD facilities, sanctioned INR = MIN(USD × FX, INR cap)."""
        for idx, row in self.facility_master.iterrows():
            if row["Currency"] == "USD":
                inr_cap = row["Sanction_INR"]  # INR cap is binding
                usd_value = row["Sanction_OrigCcy"] * self.fx_rate / 10  # /10 to convert to Cr
                effective_inr = min(usd_value, inr_cap)
                self.facility_master.at[idx, "Sanction_INR_Effective"] = effective_inr
                self.facility_master.at[idx, "USD_Equivalent_INR"] = usd_value
            else:
                self.facility_master.at[idx, "Sanction_INR_Effective"] = row["Sanction_INR"]
                self.facility_master.at[idx, "USD_Equivalent_INR"] = None

    # =========================================================================
    # COVENANT RATIO CALCULATIONS
    # =========================================================================
    def calculate_covenants(self, ebitda_change_pct: float = 0.0,
                            interest_change_pct: float = 0.0) -> pd.DataFrame:
        """Calculate all 24 covenant ratios with optional stress overlays."""
        f = self.financials[self.basis].copy()

        # Apply stress shocks
        ebitda      = f["EBITDA"] * (1 + ebitda_change_pct / 100)
        interest    = f["Interest Expense"] * (1 + interest_change_pct / 100)

        total_debt  = f["Total Debt"]
        term_debt   = f["Term Debt"]
        tnw         = f["TNW"]
        atnw        = f["ATNW"]
        ca          = f["Current Assets"]
        cl          = f["Current Liabilities"]
        tol         = f["TOL"]
        fa          = f["Fixed Assets"]
        tax_paid    = f["Tax Paid"]
        sched_repay = f["Sched TL Repay"]
        rating      = f["External Rating"]

        # Compute ratios
        dscr           = (ebitda - tax_paid) / (sched_repay + interest) if (sched_repay + interest) > 0 else 0
        td_ebitda      = total_debt / ebitda if ebitda > 0 else 999
        term_d_ebitda  = term_debt / ebitda if ebitda > 0 else 999
        tol_tnw        = tol / tnw if tnw > 0 else 999
        tol_atnw       = tol / atnw if atnw > 0 else 999
        td_atnw        = total_debt / atnw if atnw > 0 else 999
        facr           = fa / term_debt if term_debt > 0 else 999
        icr            = ebitda / interest if interest > 0 else 999
        current_ratio  = ca / cl if cl > 0 else 999
        der            = total_debt / tnw if tnw > 0 else 999

        # Map to each of the 24 covenants
        actuals = {
            "DSCR":                       dscr,
            "Term Debt / EBITDA":         term_d_ebitda,
            "TOL / TNW":                  tol_tnw,
            "External Rating ≥ A-":       rating,
            "Total Debt / EBITDA (≤FY27)": td_ebitda,
            "Total Debt / EBITDA (FY28+)": td_ebitda,
            "Total Debt / ATNW":          td_atnw,
            "FACR":                       facr,
            "External Rating ≥ A-/A1":    rating,
            "Total Debt / EBITDA":        td_ebitda,
            "ICR":                        icr,
            "TOL / ATNW (≤FY26)":         tol_atnw,
            "TOL / ATNW (≤FY27)":         tol_atnw,
            "TOL / ATNW (FY28+)":         tol_atnw,
            "Debt / Equity Ratio":        der,
            "Current Ratio":              current_ratio,
        }

        rows = []
        for _, cov in self.covenant_master.iterrows():
            name = cov["Covenant"]
            actual = actuals.get(name, None)
            threshold = cov["Threshold"]
            op = cov["Operator"]

            if op == "rating":
                # Rating check: A- or better
                rating_ok = "A" in str(actual) and "BB" not in str(actual)
                status = "Compliant" if rating_ok else "Breach"
                headroom = None
                headroom_pct = None
            elif actual is None or threshold is None:
                status = "N/A"; headroom = None; headroom_pct = None
            else:
                if op == ">":
                    headroom = actual - threshold
                    headroom_pct = (actual - threshold) / threshold * 100
                    if actual <= threshold:           status = "Breach"
                    elif headroom_pct < 5:            status = "Near Breach"
                    elif headroom_pct < 10:           status = "Watch"
                    else:                             status = "Compliant"
                elif op == ">=":
                    headroom = actual - threshold
                    headroom_pct = (actual - threshold) / threshold * 100
                    if actual < threshold:            status = "Breach"
                    elif headroom_pct < 5:            status = "Near Breach"
                    elif headroom_pct < 10:           status = "Watch"
                    else:                             status = "Compliant"
                elif op == "<":
                    headroom = threshold - actual
                    headroom_pct = (threshold - actual) / threshold * 100
                    if actual >= threshold:           status = "Breach"
                    elif headroom_pct < 5:            status = "Near Breach"
                    elif headroom_pct < 10:           status = "Watch"
                    else:                             status = "Compliant"
                elif op == "<=":
                    headroom = threshold - actual
                    headroom_pct = (threshold - actual) / threshold * 100
                    if actual > threshold:            status = "Breach"
                    elif headroom_pct < 5:            status = "Near Breach"
                    elif headroom_pct < 10:           status = "Watch"
                    else:                             status = "Compliant"
                else:
                    status = "N/A"; headroom = None; headroom_pct = None

            rows.append({
                **cov.to_dict(),
                "Actual": actual,
                "Headroom": headroom,
                "Headroom_Pct": headroom_pct,
                "Status": status,
            })
        return pd.DataFrame(rows)

    # =========================================================================
    # INTEREST COST CALCULATIONS
    # =========================================================================
    def calculate_annual_interest(self, rate_shock_bps: float = 0,
                                  spread_shock_bps: float = 0) -> Dict:
        """Calculate run-rate annual interest & commission across all 34 facilities."""
        rate_shock = rate_shock_bps / 10000
        spread_shock = spread_shock_bps / 10000

        total_fb_interest = 0
        total_nfb_commission = 0
        details = []

        for _, row in self.facility_master.iterrows():
            outstanding = row["Outstanding_INR"]
            if pd.isna(outstanding) or outstanding == 0:
                continue
            base_rate = row["Effective_Rate"] or 0
            if row["Rate_Type"] == "Floating":
                # Floating rate: apply rate shock + spread shock
                shocked_rate = base_rate + rate_shock + spread_shock
            else:
                shocked_rate = base_rate

            cost = outstanding * shocked_rate

            if row["Category"] in ["FB", "FB-Term", "FB-FCY", "FB-FDbacked"]:
                total_fb_interest += cost
            else:
                total_nfb_commission += cost

            details.append({
                "Facility": row["Facility"],
                "Lender": row["Lender"],
                "Outstanding": outstanding,
                "Base_Rate": base_rate,
                "Shocked_Rate": shocked_rate,
                "Annual_Cost": cost,
                "Category": row["Category"],
            })

        df = pd.DataFrame(details)
        return {
            "fb_interest": total_fb_interest,
            "nfb_commission": total_nfb_commission,
            "total": total_fb_interest + total_nfb_commission,
            "details": df,
        }

    # =========================================================================
    # WEIGHTED AVERAGE COST
    # =========================================================================
    def weighted_avg_cost(self, rate_shock_bps: float = 0,
                          spread_shock_bps: float = 0) -> float:
        """Weighted-average cost of fund-based debt only."""
        rate_shock = rate_shock_bps / 10000
        spread_shock = spread_shock_bps / 10000
        total_outstanding = 0
        weighted_cost_num = 0
        for _, row in self.facility_master.iterrows():
            if row["Category"] not in ["FB", "FB-Term", "FB-FCY", "FB-FDbacked"]:
                continue
            outstanding = row["Outstanding_INR"]
            if pd.isna(outstanding) or outstanding == 0: continue
            base_rate = row["Effective_Rate"] or 0
            if row["Rate_Type"] == "Floating":
                shocked_rate = base_rate + rate_shock + spread_shock
            else:
                shocked_rate = base_rate
            weighted_cost_num += outstanding * shocked_rate
            total_outstanding += outstanding
        return (weighted_cost_num / total_outstanding) if total_outstanding > 0 else 0

    # =========================================================================
    # MATURITY BUCKETING
    # =========================================================================
    def maturity_buckets(self) -> pd.DataFrame:
        """Categorize facilities by days-to-validity."""
        rows = []
        for _, row in self.facility_master.iterrows():
            validity = row["Validity_Date"]
            if pd.isna(validity):
                bucket = "No Validity"
                days = None
            else:
                days = (validity - self.as_of_date).days
                if days < 0:                bucket = "Expired"
                elif days <= 30:            bucket = "≤30 Days"
                elif days <= 60:            bucket = "31–60 Days"
                elif days <= 90:            bucket = "61–90 Days"
                elif days <= 180:           bucket = "91–180 Days"
                else:                       bucket = ">180 Days"
            rows.append({
                "Facility": row["Facility"],
                "Lender": row["Lender"],
                "Sanction_INR": row["Sanction_INR"],
                "Validity_Date": validity,
                "Days_to_Validity": days,
                "Bucket": bucket,
            })
        return pd.DataFrame(rows)

    # =========================================================================
    # LENDER SUMMARY AGGREGATION
    # =========================================================================
    def lender_summary(self) -> pd.DataFrame:
        """Aggregate metrics per lender."""
        rows = []
        for lender in self.facility_master["Lender"].unique():
            sub = self.facility_master[self.facility_master["Lender"] == lender]
            fb = sub[sub["Category"].isin(["FB", "FB-Term", "FB-FCY", "FB-FDbacked"])]["Sanction_INR"].sum()
            nfb = sub[sub["Category"].isin(["NFB", "NFB-FDbacked"])]["Sanction_INR"].sum()
            tl = sub[sub["Category"] == "FB-Term"]["Sanction_INR"].sum()
            hedge = sub[sub["Category"] == "Hedge"]["Sanction_INR"].sum()
            total = sub["Sanction_INR"].sum()
            outstanding = sub["Outstanding_INR"].sum()
            num_facilities = len(sub)

            # Weighted avg cost (FB only)
            fb_sub = sub[sub["Category"].isin(["FB", "FB-Term", "FB-FCY", "FB-FDbacked"])]
            wac = ((fb_sub["Outstanding_INR"] * fb_sub["Effective_Rate"]).sum()
                   / fb_sub["Outstanding_INR"].sum()) if fb_sub["Outstanding_INR"].sum() > 0 else 0

            rows.append({
                "Lender": lender,
                "Total_Sanction": total,
                "Outstanding": outstanding,
                "Headroom": total - outstanding,
                "FB_Sanction": fb,
                "NFB_Sanction": nfb,
                "TL_Sanction": tl,
                "Hedge_Sanction": hedge,
                "Num_Facilities": num_facilities,
                "Weighted_Avg_Cost": wac,
                "Utilization": (outstanding / total) if total > 0 else 0,
            })
        return pd.DataFrame(rows)

    # =========================================================================
    # TERM LOAN AGGREGATIONS
    # =========================================================================
    def annual_tl_principal(self) -> pd.DataFrame:
        """Sum quarterly principal repayments by FY for each TL."""
        df = self.tl_schedule.copy()
        df["FY"] = df["Period_End"].dt.year + (df["Period_End"].dt.month >= 4).astype(int)
        df["FY_Label"] = "FY" + df["FY"].astype(str).str[-2:]
        agg = df.groupby(["Lender", "FY_Label"]).agg(
            Principal=("Principal", "sum"),
            Interest=("Interest", "sum"),
            Total_DS=("Total_DS", "sum")
        ).reset_index()
        return agg

    # =========================================================================
    # SCENARIO ANALYSIS
    # =========================================================================
    def run_scenario(self, rate_shock_bps: float, spread_shock_bps: float,
                     ebitda_change_pct: float) -> Dict:
        """Combined scenario engine: returns delta vs baseline."""
        # Baseline
        base_int = self.calculate_annual_interest(0, 0)
        base_wac = self.weighted_avg_cost(0, 0)
        base_cov = self.calculate_covenants(0, 0)

        # Stress: interest cost change ratio drives the interest_change_pct passed to covenants
        stress_int = self.calculate_annual_interest(rate_shock_bps, spread_shock_bps)
        stress_wac = self.weighted_avg_cost(rate_shock_bps, spread_shock_bps)

        # The covenant Interest is from P&L, not run-rate. So we apply proportional change.
        if base_int["fb_interest"] > 0:
            interest_change_pct = (stress_int["fb_interest"] / base_int["fb_interest"] - 1) * 100
        else:
            interest_change_pct = 0

        stress_cov = self.calculate_covenants(ebitda_change_pct, interest_change_pct)

        return {
            "base": {
                "annual_interest": base_int["total"],
                "fb_interest": base_int["fb_interest"],
                "nfb_commission": base_int["nfb_commission"],
                "weighted_avg_cost": base_wac,
                "covenants": base_cov,
            },
            "stress": {
                "annual_interest": stress_int["total"],
                "fb_interest": stress_int["fb_interest"],
                "nfb_commission": stress_int["nfb_commission"],
                "weighted_avg_cost": stress_wac,
                "covenants": stress_cov,
            },
            "delta": {
                "annual_interest": stress_int["total"] - base_int["total"],
                "weighted_avg_cost_bps": (stress_wac - base_wac) * 10000,
            },
        }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/home/claude/jcl_dashboard")
    from data.jcl_data import (get_facility_master, get_covenant_master,
                               get_term_loan_schedule, FINANCIALS, BENCHMARK_RATES)

    fm = get_facility_master()
    cm = get_covenant_master()
    ts = get_term_loan_schedule()

    logic = FinancialLogic(fm, cm, ts, FINANCIALS, BENCHMARK_RATES,
                           as_of_date=date(2026, 4, 21), fx_rate=92.98, basis="FY26E")

    print("=== Covenant Status ===")
    cov = logic.calculate_covenants()
    print(cov[["Lender", "Covenant", "Actual", "Headroom_Pct", "Status"]].to_string(index=False))

    print("\n=== Annual Interest (Baseline) ===")
    interest = logic.calculate_annual_interest()
    print(f"FB Interest: ₹{interest['fb_interest']:.2f} Cr")
    print(f"NFB Commission: ₹{interest['nfb_commission']:.2f} Cr")
    print(f"Total: ₹{interest['total']:.2f} Cr")
    print(f"Weighted Avg Cost: {logic.weighted_avg_cost()*100:.2f}%")

    print("\n=== Lender Summary ===")
    print(logic.lender_summary().to_string(index=False))

    print("\n=== Scenario: Rate +100bps, EBITDA -20% ===")
    scenario = logic.run_scenario(100, 0, -20)
    print(f"Base Interest: ₹{scenario['base']['annual_interest']:.2f} Cr")
    print(f"Stress Interest: ₹{scenario['stress']['annual_interest']:.2f} Cr")
    print(f"Delta: ₹{scenario['delta']['annual_interest']:.2f} Cr")
