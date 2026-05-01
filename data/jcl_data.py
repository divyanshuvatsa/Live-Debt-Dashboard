"""
JCL Debt Monitoring Dashboard — Data Module
Holds the canonical facility master, covenant master, term-loan schedules,
benchmark rates, and financial inputs. All data is sourced from the JCL Debt Model
(JCL_Debt_Model.xlsx) as of 21-Apr-2026.
"""

import pandas as pd
from datetime import date


# =============================================================================
# BENCHMARK RATES (As of Apr-2026)
# =============================================================================
BENCHMARK_RATES = {
    "Repo Rate":          0.0525,   # RBI Repo Rate (Apr 2026)
    "3M T-Bill":          0.0518,   # India 3-Month Treasury Bill yield
    "RBL 1Y MCLR":        0.0900,   # RBL Bank 1-Year MCLR
    "YBL 3M MCLR":        0.0900,   # YES Bank 3-Month MCLR
    "ICICI 6M I-MCLR":    0.0830,   # ICICI Bank 6-Month I-MCLR
    "SIB 12M MCLR":       0.0975,   # South Indian Bank 12M MCLR
    "Bajaj BFRR":         0.0850,   # Bajaj Floating Reference Rate
    "Term SOFR (USD)":    0.0430,   # USD Term SOFR 3M
}


# =============================================================================
# FINANCIAL INPUTS (FY24A & FY26E from Mentor's KFI tab)
# =============================================================================
FINANCIALS = {
    "FY24A": {
        "EBITDA":              173.37,
        "PAT":                  99.52,
        "Net Sales":          1572.92,
        "Total Debt":          471.82,
        "Term Debt":           324.01,
        "TNW":                 720.11,
        "ATNW":                588.29,
        "Current Assets":      711.30,
        "Current Liabilities": 513.82,
        "TOL":                1143.77,
        "Interest Expense":     39.87,
        "Fixed Assets":        449.34,
        "Tax Paid":             1.12,    # Approx. from mentor model
        "Sched TL Repay":       18.76,   # Next 12M
        "External Rating":     "CARE A+; Stable / A1",
        "Promoter %":           1.00,
    },
    "FY26E": {
        "EBITDA":              383.96,
        "PAT":                 243.42,
        "Net Sales":          2079.23,
        "Total Debt":          613.03,
        "Term Debt":           431.28,
        "TNW":                 740.13,
        "ATNW":                720.76,
        "Current Assets":      755.02,
        "Current Liabilities": 544.79,
        "TOL":                1143.49,
        "Interest Expense":     49.08,
        "Fixed Assets":        937.69,
        "Tax Paid":             69.36,
        "Sched TL Repay":       41.09,
        "External Rating":     "CARE A+; Stable / A1",
        "Promoter %":           1.00,
    },
}


# =============================================================================
# FACILITY MASTER (34 facilities × 5 lenders)
# =============================================================================
def get_facility_master() -> pd.DataFrame:
    """Returns the canonical Facility Master DataFrame."""
    facilities = [
        # ----------------- RBL Bank (15 facilities) -----------------
        {"S.No": 1,  "Lender": "RBL Bank", "Facility": "Letter of Credit - Main Limit", "Category": "NFB",         "Nature": "Revolving", "Sub_Limit": "Main",                   "Currency": "INR", "Sanction_OrigCcy": 100,   "Sanction_INR": 100,   "Outstanding_INR": 100,   "Benchmark": "Fixed commission", "Spread": 0,      "Effective_Rate": 0.0045, "Rate_Type": "Fixed",     "Tenor_Months": 6,   "Drawdown_Date": "2025-12-31", "Maturity_Date": None,         "Validity_Date": "2026-11-30", "Purpose": "Working capital incl. service LC issuance"},
        {"S.No": 2,  "Lender": "RBL Bank", "Facility": "Bank Guarantee",                  "Category": "NFB",         "Nature": "Revolving", "Sub_Limit": "Sub-limit of LC (Main)", "Currency": "INR", "Sanction_OrigCcy": 25,    "Sanction_INR": 25,    "Outstanding_INR": 25,    "Benchmark": "Fixed commission", "Spread": 0,      "Effective_Rate": 0.0050, "Rate_Type": "Fixed",     "Tenor_Months": 12,  "Drawdown_Date": "2025-12-31", "Maturity_Date": None,         "Validity_Date": "2026-11-30", "Purpose": "PBG, Bid Bond, Govt/Semi-Govt guarantees"},
        {"S.No": 3,  "Lender": "RBL Bank", "Facility": "Invoice Discounting (PID)",       "Category": "FB",          "Nature": "Revolving", "Sub_Limit": "Standalone (under WC)",  "Currency": "INR", "Sanction_OrigCcy": 100,   "Sanction_INR": 100,   "Outstanding_INR": 100,   "Benchmark": "To be decided",   "Spread": 0,      "Effective_Rate": 0.0,    "Rate_Type": "TBD",       "Tenor_Months": 1,   "Drawdown_Date": "2025-12-31", "Maturity_Date": None,         "Validity_Date": "2026-11-30", "Purpose": "Working capital requirement"},
        {"S.No": 4,  "Lender": "RBL Bank", "Facility": "SBLC",                            "Category": "NFB",         "Nature": "Revolving", "Sub_Limit": "Sub-limit of LC (Main)", "Currency": "INR", "Sanction_OrigCcy": 100,   "Sanction_INR": 100,   "Outstanding_INR": 100,   "Benchmark": "To be decided",   "Spread": 0,      "Effective_Rate": 0.0050, "Rate_Type": "TBD",       "Tenor_Months": 6,   "Drawdown_Date": "2025-03-13", "Maturity_Date": None,         "Validity_Date": "2026-11-30", "Purpose": "Buyer's Credit from RBL GIFT City"},
        {"S.No": 5,  "Lender": "RBL Bank", "Facility": "Pre-Acceptance LCBD",             "Category": "FB",          "Nature": "Revolving", "Sub_Limit": "Standalone (under WC)",  "Currency": "INR", "Sanction_OrigCcy": 100,   "Sanction_INR": 100,   "Outstanding_INR": 100,   "Benchmark": "To be decided",   "Spread": 0,      "Effective_Rate": 0.0,    "Rate_Type": "TBD",       "Tenor_Months": 0,   "Drawdown_Date": "2025-12-31", "Maturity_Date": None,         "Validity_Date": "2026-11-30", "Purpose": "Working capital requirement"},
        {"S.No": 6,  "Lender": "RBL Bank", "Facility": "Cash Credit",                     "Category": "FB",          "Nature": "Revolving", "Sub_Limit": "Standalone (under WC)",  "Currency": "INR", "Sanction_OrigCcy": 100,   "Sanction_INR": 100,   "Outstanding_INR": 100,   "Benchmark": "1Y MCLR (RBL Bank)", "Spread": 5,  "Effective_Rate": 0.0905, "Rate_Type": "Floating",  "Tenor_Months": 0,   "Drawdown_Date": "2025-02-28", "Maturity_Date": None,         "Validity_Date": "2026-11-30", "Purpose": "Working capital requirement"},
        {"S.No": 7,  "Lender": "RBL Bank", "Facility": "Working Capital Demand Loan",     "Category": "FB",          "Nature": "Revolving", "Sub_Limit": "Sub-limit of LC (Main)", "Currency": "INR", "Sanction_OrigCcy": 100,   "Sanction_INR": 100,   "Outstanding_INR": 100,   "Benchmark": "To be decided",   "Spread": 0,      "Effective_Rate": 0.0,    "Rate_Type": "TBD",       "Tenor_Months": 4,   "Drawdown_Date": "2025-12-31", "Maturity_Date": None,         "Validity_Date": "2026-11-30", "Purpose": "Working capital"},
        {"S.No": 8,  "Lender": "RBL Bank", "Facility": "Loan Equivalent Risk (LER)",      "Category": "Hedge",       "Nature": "Revolving", "Sub_Limit": "Main",                   "Currency": "INR", "Sanction_OrigCcy": 20,    "Sanction_INR": 20,    "Outstanding_INR": 20,    "Benchmark": "Bank treasury",   "Spread": 0,      "Effective_Rate": 0.0,    "Rate_Type": "Fixed",     "Tenor_Months": 12,  "Drawdown_Date": "2025-12-31", "Maturity_Date": None,         "Validity_Date": "2026-11-30", "Purpose": "Forex hedging (MTM cap 75%)"},
        {"S.No": 9,  "Lender": "RBL Bank", "Facility": "Term Loan - Main Limit",          "Category": "FB-Term",     "Nature": "Non-Revolving", "Sub_Limit": "Main",               "Currency": "INR", "Sanction_OrigCcy": 200,   "Sanction_INR": 200,   "Outstanding_INR": 200,   "Benchmark": "1Y MCLR (RBL Bank)", "Spread": 75, "Effective_Rate": 0.0975, "Rate_Type": "Floating",  "Tenor_Months": 60,  "Drawdown_Date": "2024-01-24", "Maturity_Date": "2029-01-24", "Validity_Date": "2026-12-31", "Purpose": "Repayment of existing SBLC/BC + fresh capex"},
        {"S.No": 10, "Lender": "RBL Bank", "Facility": "SBLC for Buyer's Credit (GIFT)",  "Category": "NFB",         "Nature": "Revolving", "Sub_Limit": "Main",                   "Currency": "INR", "Sanction_OrigCcy": 190,   "Sanction_INR": 190,   "Outstanding_INR": 190,   "Benchmark": "Fixed commission", "Spread": 0,      "Effective_Rate": 0.0050, "Rate_Type": "Fixed",     "Tenor_Months": 36,  "Drawdown_Date": "2025-12-31", "Maturity_Date": None,         "Validity_Date": "2026-11-30", "Purpose": "Buyer's credit through RBL GIFT City"},
        {"S.No": 11, "Lender": "RBL Bank", "Facility": "Capex LC",                        "Category": "NFB",         "Nature": "Revolving", "Sub_Limit": "Main",                   "Currency": "INR", "Sanction_OrigCcy": 25,    "Sanction_INR": 25,    "Outstanding_INR": 25,    "Benchmark": "Fixed commission", "Spread": 0,      "Effective_Rate": 0.0050, "Rate_Type": "Fixed",     "Tenor_Months": 36,  "Drawdown_Date": "2025-12-31", "Maturity_Date": None,         "Validity_Date": "2026-11-30", "Purpose": "Purchase of capital goods"},
        {"S.No": 12, "Lender": "RBL Bank", "Facility": "Overdraft 100% FD (FDOD)",         "Category": "FB-FDbacked", "Nature": "Revolving", "Sub_Limit": "Main",                   "Currency": "INR", "Sanction_OrigCcy": 100,   "Sanction_INR": 100,   "Outstanding_INR": 100,   "Benchmark": "FD rate",          "Spread": 25,     "Effective_Rate": 0.0,    "Rate_Type": "Floating",  "Tenor_Months": 12,  "Drawdown_Date": "2024-01-24", "Maturity_Date": None,         "Validity_Date": "2026-11-30", "Purpose": "Cash flow mismatches"},
        {"S.No": 13, "Lender": "RBL Bank", "Facility": "LC backed by 100% FD",            "Category": "NFB-FDbacked","Nature": "Revolving", "Sub_Limit": "Sub-limit of FDOD",      "Currency": "INR", "Sanction_OrigCcy": 50,    "Sanction_INR": 50,    "Outstanding_INR": 50,    "Benchmark": "To be decided",   "Spread": 0,      "Effective_Rate": 0.0,    "Rate_Type": "TBD",       "Tenor_Months": 12,  "Drawdown_Date": "2024-01-24", "Maturity_Date": None,         "Validity_Date": "2026-11-30", "Purpose": "WC - import/purchase of RM"},
        {"S.No": 14, "Lender": "RBL Bank", "Facility": "Buyer's Credit GIFT - WC",        "Category": "FB-FCY",      "Nature": "Revolving", "Sub_Limit": "Backed by BG/SBLC",      "Currency": "USD", "Sanction_OrigCcy": 11,    "Sanction_INR": 100,   "Outstanding_INR": 100,   "Benchmark": "Term SOFR (USD)", "Spread": 0,      "Effective_Rate": 0.0,    "Rate_Type": "Floating",  "Tenor_Months": 6,   "Drawdown_Date": "2025-03-13", "Maturity_Date": None,         "Validity_Date": "2026-11-30", "Purpose": "Working capital requirements"},
        {"S.No": 15, "Lender": "RBL Bank", "Facility": "Buyer's Credit GIFT - CAPEX",     "Category": "FB-FCY",      "Nature": "Revolving", "Sub_Limit": "Backed by BG/SBLC",      "Currency": "USD", "Sanction_OrigCcy": 20,    "Sanction_INR": 172,   "Outstanding_INR": 172,   "Benchmark": "Term SOFR (USD)", "Spread": 0,      "Effective_Rate": 0.0,    "Rate_Type": "Floating",  "Tenor_Months": 36,  "Drawdown_Date": "2025-03-27", "Maturity_Date": None,         "Validity_Date": "2026-11-30", "Purpose": "CAPEX funding"},
        # ----------------- YES Bank (6 facilities) -----------------
        {"S.No": 16, "Lender": "YES Bank", "Facility": "Purchase Invoice Financing",      "Category": "FB",          "Nature": "Revolving", "Sub_Limit": "Main (New)",             "Currency": "INR", "Sanction_OrigCcy": 100,   "Sanction_INR": 100,   "Outstanding_INR": 100,   "Benchmark": "To be decided",   "Spread": 0,      "Effective_Rate": 0.0,    "Rate_Type": "TBD",       "Tenor_Months": 3,   "Drawdown_Date": "2026-03-19", "Maturity_Date": None,         "Validity_Date": "2026-04-30", "Purpose": "Working capital requirements"},
        {"S.No": 17, "Lender": "YES Bank", "Facility": "Cash Credit",                     "Category": "FB",          "Nature": "Revolving", "Sub_Limit": "Main",                   "Currency": "INR", "Sanction_OrigCcy": 25,    "Sanction_INR": 25,    "Outstanding_INR": 25,    "Benchmark": "3M MCLR (YBL)",   "Spread": 7,      "Effective_Rate": 0.0907, "Rate_Type": "Floating",  "Tenor_Months": 12,  "Drawdown_Date": "2026-03-19", "Maturity_Date": None,         "Validity_Date": "2027-03-19", "Purpose": "Working capital"},
        {"S.No": 18, "Lender": "YES Bank", "Facility": "Letter of Credit",                "Category": "NFB",         "Nature": "Revolving", "Sub_Limit": "Main",                   "Currency": "INR", "Sanction_OrigCcy": 200,   "Sanction_INR": 200,   "Outstanding_INR": 200,   "Benchmark": "Fixed commission", "Spread": 0,      "Effective_Rate": 0.0,    "Rate_Type": "Fixed",     "Tenor_Months": 7,   "Drawdown_Date": "2026-03-19", "Maturity_Date": None,         "Validity_Date": "2027-03-26", "Purpose": "Procurement of raw materials"},
        {"S.No": 19, "Lender": "YES Bank", "Facility": "Financial BG / SBLC",             "Category": "NFB",         "Nature": "Revolving", "Sub_Limit": "Sub-limit of LC (Main)", "Currency": "INR", "Sanction_OrigCcy": 200,   "Sanction_INR": 200,   "Outstanding_INR": 200,   "Benchmark": "Fixed commission", "Spread": 0,      "Effective_Rate": 0.0050, "Rate_Type": "Fixed",     "Tenor_Months": 6,   "Drawdown_Date": "2026-03-19", "Maturity_Date": None,         "Validity_Date": "2027-03-19", "Purpose": "Securing payment for RM"},
        {"S.No": 20, "Lender": "YES Bank", "Facility": "Working Capital Demand Loan",     "Category": "FB",          "Nature": "Revolving", "Sub_Limit": "Sub-limit of LC (Main)", "Currency": "INR", "Sanction_OrigCcy": 50,    "Sanction_INR": 50,    "Outstanding_INR": 50,    "Benchmark": "To be decided",   "Spread": 0,      "Effective_Rate": 0.0,    "Rate_Type": "TBD",       "Tenor_Months": 6,   "Drawdown_Date": "2026-03-19", "Maturity_Date": None,         "Validity_Date": "2027-03-19", "Purpose": "Working capital"},
        {"S.No": 21, "Lender": "YES Bank", "Facility": "Term Loan (Refinance Canara)",    "Category": "FB-Term",     "Nature": "Non-Revolving", "Sub_Limit": "Main",               "Currency": "INR", "Sanction_OrigCcy": 320.7, "Sanction_INR": 320.7, "Outstanding_INR": 320.7, "Benchmark": "3M T-Bill",       "Spread": 252,    "Effective_Rate": 0.0770, "Rate_Type": "Floating",  "Tenor_Months": 146, "Drawdown_Date": "2024-12-16", "Maturity_Date": "2036-09-30", "Validity_Date": "2026-08-19", "Purpose": "Refinance Canara TL"},
        # ----------------- Bajaj Finance (1 facility) -----------------
        {"S.No": 22, "Lender": "Bajaj Finance", "Facility": "Term Loan",                  "Category": "FB-Term",     "Nature": "Non-Revolving", "Sub_Limit": "Main",               "Currency": "INR", "Sanction_OrigCcy": 150,   "Sanction_INR": 150,   "Outstanding_INR": 150,   "Benchmark": "BFRR",            "Spread": 10,     "Effective_Rate": 0.0860, "Rate_Type": "Floating",  "Tenor_Months": 96,  "Drawdown_Date": "2025-08-18", "Maturity_Date": "2033-08-18", "Validity_Date": "2026-08-31", "Purpose": "CAPEX reimbursement + GCP"},
        # ----------------- ICICI Bank (6 facilities) -----------------
        {"S.No": 23, "Lender": "ICICI Bank", "Facility": "Cash Credit",                   "Category": "FB",          "Nature": "Revolving", "Sub_Limit": "Main",                   "Currency": "INR", "Sanction_OrigCcy": 50,    "Sanction_INR": 50,    "Outstanding_INR": 50,    "Benchmark": "6M I-MCLR (ICICI)", "Spread": 45,   "Effective_Rate": 0.0875, "Rate_Type": "Floating",  "Tenor_Months": 12,  "Drawdown_Date": "2025-09-16", "Maturity_Date": None,         "Validity_Date": "2026-09-03", "Purpose": "Working capital"},
        {"S.No": 24, "Lender": "ICICI Bank", "Facility": "Working Capital Demand Loan",   "Category": "FB",          "Nature": "Revolving", "Sub_Limit": "Sub-limit of CC",        "Currency": "INR", "Sanction_OrigCcy": 50,    "Sanction_INR": 50,    "Outstanding_INR": 50,    "Benchmark": "Repo Rate",        "Spread": 0,      "Effective_Rate": 0.0525, "Rate_Type": "Floating",  "Tenor_Months": 3,   "Drawdown_Date": "2025-11-11", "Maturity_Date": None,         "Validity_Date": "2026-09-03", "Purpose": "Working capital (bullet)"},
        {"S.No": 25, "Lender": "ICICI Bank", "Facility": "Letter of Credit",              "Category": "NFB",         "Nature": "Revolving", "Sub_Limit": "Main",                   "Currency": "INR", "Sanction_OrigCcy": 150,   "Sanction_INR": 150,   "Outstanding_INR": 150,   "Benchmark": "Fixed commission", "Spread": 0,      "Effective_Rate": 0.0050, "Rate_Type": "Fixed",     "Tenor_Months": 5,   "Drawdown_Date": "2025-09-16", "Maturity_Date": None,         "Validity_Date": "2026-09-03", "Purpose": "RM, consumables, stores"},
        {"S.No": 26, "Lender": "ICICI Bank", "Facility": "SBLC for Buyers' Credit",       "Category": "NFB",         "Nature": "Revolving", "Sub_Limit": "Sub-limit of LC",        "Currency": "INR", "Sanction_OrigCcy": 150,   "Sanction_INR": 150,   "Outstanding_INR": 150,   "Benchmark": "Fixed commission", "Spread": 0,      "Effective_Rate": 0.0050, "Rate_Type": "Fixed",     "Tenor_Months": 5,   "Drawdown_Date": "2025-09-16", "Maturity_Date": None,         "Validity_Date": "2026-09-03", "Purpose": "Buyer's credit"},
        {"S.No": 27, "Lender": "ICICI Bank", "Facility": "Bank Guarantee - Performance",  "Category": "NFB",         "Nature": "Revolving", "Sub_Limit": "Sub-limit of LC",        "Currency": "INR", "Sanction_OrigCcy": 25,    "Sanction_INR": 25,    "Outstanding_INR": 25,    "Benchmark": "Fixed commission", "Spread": 0,      "Effective_Rate": 0.0050, "Rate_Type": "Fixed",     "Tenor_Months": 36,  "Drawdown_Date": "2025-09-16", "Maturity_Date": None,         "Validity_Date": "2026-09-03", "Purpose": "Bid bond, EMD, performance"},
        {"S.No": 28, "Lender": "ICICI Bank", "Facility": "Bank Guarantee - Financial",    "Category": "NFB",         "Nature": "Revolving", "Sub_Limit": "Sub-limit of LC",        "Currency": "INR", "Sanction_OrigCcy": 5,     "Sanction_INR": 5,     "Outstanding_INR": 5,     "Benchmark": "Fixed commission", "Spread": 0,      "Effective_Rate": 0.0060, "Rate_Type": "Fixed",     "Tenor_Months": 36,  "Drawdown_Date": "2025-09-16", "Maturity_Date": None,         "Validity_Date": "2026-09-03", "Purpose": "Financial guarantees"},
        # ----------------- South Indian Bank (6 facilities) -----------------
        {"S.No": 29, "Lender": "South Indian Bank", "Facility": "CCOL (Cash Credit)",     "Category": "FB",          "Nature": "Revolving", "Sub_Limit": "Sub-limit of LC",        "Currency": "INR", "Sanction_OrigCcy": 50,    "Sanction_INR": 50,    "Outstanding_INR": 50,    "Benchmark": "12M MCLR (SIB)",    "Spread": 45,    "Effective_Rate": 0.1020, "Rate_Type": "Floating",  "Tenor_Months": 12,  "Drawdown_Date": "2025-06-21", "Maturity_Date": None,         "Validity_Date": "2026-06-21", "Purpose": "Pre/post-sale working capital"},
        {"S.No": 30, "Lender": "South Indian Bank", "Facility": "WCL / WCDL",             "Category": "FB",          "Nature": "Revolving", "Sub_Limit": "Sub-limit of CCOL",      "Currency": "INR", "Sanction_OrigCcy": 50,    "Sanction_INR": 50,    "Outstanding_INR": 50,    "Benchmark": "To be decided",     "Spread": 0,     "Effective_Rate": 0.0,    "Rate_Type": "TBD",       "Tenor_Months": 12,  "Drawdown_Date": "2025-06-21", "Maturity_Date": None,         "Validity_Date": "2026-06-21", "Purpose": "Working capital (bullet)"},
        {"S.No": 31, "Lender": "South Indian Bank", "Facility": "Inland / Import LC",     "Category": "NFB",         "Nature": "Revolving", "Sub_Limit": "Main",                   "Currency": "INR", "Sanction_OrigCcy": 150,   "Sanction_INR": 150,   "Outstanding_INR": 150,   "Benchmark": "Fixed commission", "Spread": 0,      "Effective_Rate": 0.0065, "Rate_Type": "Fixed",     "Tenor_Months": 6,   "Drawdown_Date": "2025-06-21", "Maturity_Date": None,         "Validity_Date": "2026-06-21", "Purpose": "Purchase / import of RM"},
        {"S.No": 32, "Lender": "South Indian Bank", "Facility": "Capex LC",               "Category": "NFB",         "Nature": "Revolving", "Sub_Limit": "Main (within LC)",       "Currency": "INR", "Sanction_OrigCcy": 50,    "Sanction_INR": 50,    "Outstanding_INR": 50,    "Benchmark": "Fixed commission", "Spread": 0,      "Effective_Rate": 0.0075, "Rate_Type": "Fixed",     "Tenor_Months": 12,  "Drawdown_Date": "2025-06-21", "Maturity_Date": None,         "Validity_Date": "2026-06-21", "Purpose": "Capital goods"},
        {"S.No": 33, "Lender": "South Indian Bank", "Facility": "SBLC",                   "Category": "NFB",         "Nature": "Revolving", "Sub_Limit": "Sub-limit of LC",        "Currency": "INR", "Sanction_OrigCcy": 150,   "Sanction_INR": 150,   "Outstanding_INR": 150,   "Benchmark": "Fixed commission", "Spread": 0,      "Effective_Rate": 0.0065, "Rate_Type": "Fixed",     "Tenor_Months": 4,   "Drawdown_Date": "2025-06-21", "Maturity_Date": None,         "Validity_Date": "2026-06-21", "Purpose": "Buyer's credit for imports"},
        {"S.No": 34, "Lender": "South Indian Bank", "Facility": "Forward Contract Limit", "Category": "Hedge",       "Nature": "Revolving", "Sub_Limit": "Main",                   "Currency": "INR", "Sanction_OrigCcy": 3,     "Sanction_INR": 3,     "Outstanding_INR": 3,     "Benchmark": "N/A",              "Spread": 0,      "Effective_Rate": 0.0,    "Rate_Type": "Fixed",     "Tenor_Months": 12,  "Drawdown_Date": "2025-06-21", "Maturity_Date": None,         "Validity_Date": "2026-06-21", "Purpose": "Hedging exchange risk"},
    ]
    df = pd.DataFrame(facilities)
    df["Drawdown_Date"]  = pd.to_datetime(df["Drawdown_Date"])
    df["Maturity_Date"]  = pd.to_datetime(df["Maturity_Date"])
    df["Validity_Date"]  = pd.to_datetime(df["Validity_Date"])
    df["Headroom_INR"]   = df["Sanction_INR"] - df["Outstanding_INR"]
    df["Utilisation"]    = df["Outstanding_INR"] / df["Sanction_INR"]
    return df


# =============================================================================
# COVENANT MASTER (24 covenants × 5 lenders)
# =============================================================================
def get_covenant_master() -> pd.DataFrame:
    covenants = [
        # RBL (4)
        {"#": 1,  "Lender": "RBL Bank",          "Covenant": "DSCR",                       "Threshold": 1.25, "Operator": ">",  "Type": "ratio_higher",  "Test_Freq": "At all times",       "Source": "RBL 24-Jan-2024"},
        {"#": 2,  "Lender": "RBL Bank",          "Covenant": "Term Debt / EBITDA",         "Threshold": 2.50, "Operator": "<",  "Type": "ratio_lower",   "Test_Freq": "Ongoing",            "Source": "RBL 25-Nov-2022"},
        {"#": 3,  "Lender": "RBL Bank",          "Covenant": "TOL / TNW",                  "Threshold": 3.00, "Operator": "<",  "Type": "ratio_lower",   "Test_Freq": "Ongoing",            "Source": "RBL 25-Nov-2022"},
        {"#": 4,  "Lender": "RBL Bank",          "Covenant": "External Rating ≥ A-",       "Threshold": None, "Operator": "rating", "Type": "rating",   "Test_Freq": "Throughout tenor",   "Source": "RBL (all)"},
        # YBL (6)
        {"#": 5,  "Lender": "YES Bank",          "Covenant": "DSCR",                       "Threshold": 1.20, "Operator": ">",  "Type": "ratio_higher",  "Test_Freq": "Within 180D of FY-end", "Source": "YBL 16-Dec-2024"},
        {"#": 6,  "Lender": "YES Bank",          "Covenant": "Total Debt / EBITDA (≤FY27)","Threshold": 4.50, "Operator": "<",  "Type": "ratio_lower",   "Test_Freq": "Within 180D of FY-end", "Source": "YBL 16-Dec-2024"},
        {"#": 7,  "Lender": "YES Bank",          "Covenant": "Total Debt / EBITDA (FY28+)","Threshold": 3.50, "Operator": "<",  "Type": "ratio_lower",   "Test_Freq": "Within 180D of FY-end", "Source": "YBL 16-Dec-2024"},
        {"#": 8,  "Lender": "YES Bank",          "Covenant": "Total Debt / ATNW",          "Threshold": 2.00, "Operator": "<",  "Type": "ratio_lower",   "Test_Freq": "Within 180D of FY-end", "Source": "YBL 16-Dec-2024"},
        {"#": 9,  "Lender": "YES Bank",          "Covenant": "FACR",                       "Threshold": 1.33, "Operator": ">",  "Type": "ratio_higher",  "Test_Freq": "Within 180D of FY-end", "Source": "YBL 19-Mar-2026"},
        {"#": 10, "Lender": "YES Bank",          "Covenant": "External Rating ≥ A-/A1",    "Threshold": None, "Operator": "rating", "Type": "rating",   "Test_Freq": "Throughout tenor",   "Source": "YBL 19-Mar-2026"},
        # Bajaj (5)
        {"#": 11, "Lender": "Bajaj Finance",     "Covenant": "Total Debt / EBITDA",        "Threshold": 4.00, "Operator": "<=", "Type": "ratio_lower",   "Test_Freq": "FY26 onwards",       "Source": "Bajaj 18-Aug-2025"},
        {"#": 12, "Lender": "Bajaj Finance",     "Covenant": "Total Debt / ATNW",          "Threshold": 2.00, "Operator": "<",  "Type": "ratio_lower",   "Test_Freq": "FY26 onwards",       "Source": "Bajaj 18-Aug-2025"},
        {"#": 13, "Lender": "Bajaj Finance",     "Covenant": "ICR",                        "Threshold": 3.50, "Operator": ">=", "Type": "ratio_higher",  "Test_Freq": "FY26 onwards",       "Source": "Bajaj 18-Aug-2025"},
        {"#": 14, "Lender": "Bajaj Finance",     "Covenant": "DSCR",                       "Threshold": 1.20, "Operator": ">",  "Type": "ratio_higher",  "Test_Freq": "FY26 onwards",       "Source": "Bajaj 18-Aug-2025"},
        {"#": 15, "Lender": "Bajaj Finance",     "Covenant": "FACR",                       "Threshold": 1.25, "Operator": ">",  "Type": "ratio_higher",  "Test_Freq": "Throughout tenor",   "Source": "Bajaj 18-Aug-2025"},
        # ICICI (5)
        {"#": 16, "Lender": "ICICI Bank",        "Covenant": "DSCR",                       "Threshold": 1.25, "Operator": ">",  "Type": "ratio_higher",  "Test_Freq": "Ongoing",            "Source": "ICICI 16-Sep-2025"},
        {"#": 17, "Lender": "ICICI Bank",        "Covenant": "Total Debt / EBITDA",        "Threshold": 3.00, "Operator": "<",  "Type": "ratio_lower",   "Test_Freq": "Ongoing",            "Source": "ICICI 16-Sep-2025"},
        {"#": 18, "Lender": "ICICI Bank",        "Covenant": "TOL / ATNW (≤FY26)",         "Threshold": 2.50, "Operator": "<",  "Type": "ratio_lower",   "Test_Freq": "Ongoing",            "Source": "ICICI 16-Sep-2025"},
        {"#": 19, "Lender": "ICICI Bank",        "Covenant": "TOL / ATNW (≤FY27)",         "Threshold": 2.10, "Operator": "<",  "Type": "ratio_lower",   "Test_Freq": "Ongoing",            "Source": "ICICI 16-Sep-2025"},
        {"#": 20, "Lender": "ICICI Bank",        "Covenant": "TOL / ATNW (FY28+)",         "Threshold": 2.00, "Operator": "<",  "Type": "ratio_lower",   "Test_Freq": "Ongoing",            "Source": "ICICI 16-Sep-2025"},
        # SIB (4)
        {"#": 21, "Lender": "South Indian Bank", "Covenant": "TOL / TNW",                  "Threshold": 3.00, "Operator": "<=", "Type": "ratio_lower",   "Test_Freq": "Annual",             "Source": "SIB 21-Jun-2025"},
        {"#": 22, "Lender": "South Indian Bank", "Covenant": "Debt / Equity Ratio",        "Threshold": 2.00, "Operator": "<=", "Type": "ratio_lower",   "Test_Freq": "Annual",             "Source": "SIB 21-Jun-2025"},
        {"#": 23, "Lender": "South Indian Bank", "Covenant": "Current Ratio",              "Threshold": 1.33, "Operator": ">",  "Type": "ratio_higher",  "Test_Freq": "Annual",             "Source": "SIB 21-Jun-2025"},
        {"#": 24, "Lender": "South Indian Bank", "Covenant": "ICR",                        "Threshold": 3.00, "Operator": ">",  "Type": "ratio_higher",  "Test_Freq": "Annual",             "Source": "SIB 21-Jun-2025"},
    ]
    return pd.DataFrame(covenants)


# =============================================================================
# TERM LOAN REPAYMENT SCHEDULES
# =============================================================================
def get_term_loan_schedule() -> pd.DataFrame:
    """Generate quarterly repayment schedule for all 3 term loans."""
    schedules = []

    # ---- RBL TL: 200 Cr, 12 EQI, drawdown 24-Jan-2024, 24m moratorium, repay start 31-Mar-2026
    rbl_eqi = 200 / 12
    rbl_rate = 0.0975
    rbl_starts = pd.date_range(start="2024-03-31", end="2029-03-31", freq="QE")
    rbl_open = 0
    drawn = False
    rep_start_idx = None
    for i, dt in enumerate(rbl_starts):
        if dt >= pd.Timestamp("2024-01-24") and not drawn:
            rbl_open = 200; drawn = True; drawdown = 200
        else:
            drawdown = 0
        if dt >= pd.Timestamp("2026-03-31") and rbl_open > 0:
            principal = min(rbl_eqi, rbl_open)
        else:
            principal = 0
        rbl_close = rbl_open + drawdown - principal
        days = (dt - (rbl_starts[i-1] if i > 0 else pd.Timestamp("2024-01-01"))).days
        interest = rbl_open * rbl_rate * days / 365 if rbl_open > 0 else 0
        schedules.append({
            "Lender": "RBL Bank", "Facility": "RBL TL", "Period_End": dt,
            "FY": f"FY{(dt.year + (1 if dt.month >= 4 else 0))}",
            "Quarter": f"Q{((dt.month-1)//3)+1}",
            "Opening": rbl_open, "Drawdown": drawdown, "Principal": principal,
            "Closing": rbl_close, "Interest": interest, "Total_DS": principal + interest
        })
        rbl_open = rbl_close

    # ---- YBL TL: 320.7 Cr, 47 EQI, drawdown 16-Dec-2024, no moratorium, repay start 31-Mar-2025
    ybl_eqi = 320.7 / 47
    ybl_rate = 0.0770
    ybl_starts = pd.date_range(start="2024-03-31", end="2036-12-31", freq="QE")
    ybl_open = 0
    drawn = False
    instalments_left = 47
    for i, dt in enumerate(ybl_starts):
        if dt >= pd.Timestamp("2024-12-16") and not drawn:
            ybl_open = 320.7; drawn = True; drawdown = 320.7
        else:
            drawdown = 0
        if dt >= pd.Timestamp("2025-03-31") and instalments_left > 0:
            principal = min(ybl_eqi, ybl_open); instalments_left -= 1
        else:
            principal = 0
        ybl_close = ybl_open + drawdown - principal
        days = (dt - (ybl_starts[i-1] if i > 0 else pd.Timestamp("2024-01-01"))).days
        interest = ybl_open * ybl_rate * days / 365 if ybl_open > 0 else 0
        schedules.append({
            "Lender": "YES Bank", "Facility": "YBL TL", "Period_End": dt,
            "FY": f"FY{(dt.year + (1 if dt.month >= 4 else 0))}",
            "Quarter": f"Q{((dt.month-1)//3)+1}",
            "Opening": ybl_open, "Drawdown": drawdown, "Principal": principal,
            "Closing": ybl_close, "Interest": interest, "Total_DS": principal + interest
        })
        ybl_open = ybl_close

    # ---- Bajaj TL: 150 Cr, 28 EQI, drawdown 18-Aug-2025, 12m moratorium, repay start 31-Aug-2026
    bajaj_eqi = 150 / 28
    bajaj_rate = 0.0860
    bajaj_starts = pd.date_range(start="2025-09-30", end="2033-12-31", freq="QE")
    bajaj_open = 0
    drawn = False
    instalments_left = 28
    for i, dt in enumerate(bajaj_starts):
        if dt >= pd.Timestamp("2025-08-18") and not drawn:
            bajaj_open = 150; drawn = True; drawdown = 150
        else:
            drawdown = 0
        if dt >= pd.Timestamp("2026-08-18") and instalments_left > 0:
            principal = min(bajaj_eqi, bajaj_open); instalments_left -= 1
        else:
            principal = 0
        bajaj_close = bajaj_open + drawdown - principal
        days = (dt - (bajaj_starts[i-1] if i > 0 else pd.Timestamp("2025-09-01"))).days
        interest = bajaj_open * bajaj_rate * days / 365 if bajaj_open > 0 else 0
        schedules.append({
            "Lender": "Bajaj Finance", "Facility": "Bajaj TL", "Period_End": dt,
            "FY": f"FY{(dt.year + (1 if dt.month >= 4 else 0))}",
            "Quarter": f"Q{((dt.month-1)//3)+1}",
            "Opening": bajaj_open, "Drawdown": drawdown, "Principal": principal,
            "Closing": bajaj_close, "Interest": interest, "Total_DS": principal + interest
        })
        bajaj_open = bajaj_close

    df = pd.DataFrame(schedules)
    df["Period_Label"] = df["Quarter"] + " " + df["FY"]
    return df


# =============================================================================
# LENDER UMBRELLA CAPS
# =============================================================================
LENDER_CAPS = {
    "RBL Bank":          {"Cap": 300,    "Description": "Overall exposure excl. FD-backed"},
    "YES Bank":          {"Cap": 488.85, "Description": "Total facilities (excl. TL)"},
    "Bajaj Finance":     {"Cap": 150,    "Description": "Term loan facility"},
    "ICICI Bank":        {"Cap": 200,    "Description": "Aggregate sanctioned"},
    "South Indian Bank": {"Cap": 150,    "Description": "LC + Capex LC combined"},
}


if __name__ == "__main__":
    fm = get_facility_master()
    cm = get_covenant_master()
    ts = get_term_loan_schedule()
    print(f"Facility Master: {len(fm)} rows")
    print(f"Covenant Master: {len(cm)} rows")
    print(f"Term Loan Schedule: {len(ts)} rows")
    print(f"\nTotal Sanction: ₹{fm['Sanction_INR'].sum():.2f} Cr")
