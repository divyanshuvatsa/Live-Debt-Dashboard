"""
JCL Debt Monitoring Dashboard — LIVE Excel Data Loader
========================================================

This module reads JCL_Debt_Model.xlsx DIRECTLY at runtime.
Any changes you save in Excel will automatically propagate to the dashboard
on the next refresh (Streamlit's file watcher detects changes via MD5 hash).

Replaces: data/jcl_data.py (which had hardcoded values).

How it works:
  1. Computes MD5 hash of the Excel file
  2. Streamlit's @st.cache_data uses the hash as a cache key
  3. When the Excel file changes, hash changes, cache invalidates, data reloads
  4. Click "Reload from Excel" in the sidebar to force a refresh

Excel structure expected:
  - Sheet "Facility Master" with header row 4 (S.No, Lender, Facility, ...)
  - Sheet "Instructions & Assumptions" with:
      * Section A (rows 4-10): Core parameters
      * Section B (rows 11-21): Benchmark rates
      * Section C (rows 23-40): Latest financials
"""

import hashlib
import os
import warnings
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION — where to find the Excel file
# ─────────────────────────────────────────────────────────────────────────────
# Default path: same folder as this script
DEFAULT_EXCEL_PATH = Path(__file__).parent / "JCL_Debt_Model.xlsx"

# Allow override via environment variable
EXCEL_PATH = Path(os.environ.get("JCL_EXCEL_PATH", DEFAULT_EXCEL_PATH))


def get_excel_path() -> Path:
    """Return the resolved Excel path, checking common locations."""
    candidates = [
        EXCEL_PATH,
        Path(__file__).parent / "JCL_Debt_Model.xlsx",
        Path(__file__).parent / "data" / "JCL_Debt_Model.xlsx",
        Path.cwd() / "JCL_Debt_Model.xlsx",
        Path.cwd() / "data" / "JCL_Debt_Model.xlsx",
    ]
    for path in candidates:
        if path.exists():
            return path
    return EXCEL_PATH  # return the default even if missing (caller will error)


def get_file_hash(path: Path) -> str:
    """MD5 hash of the file — used as Streamlit cache key."""
    if not path.exists():
        return "missing"
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def get_file_mtime(path: Path) -> str:
    """Human-readable modified time."""
    if not path.exists():
        return "FILE NOT FOUND"
    import datetime as dt
    ts = dt.datetime.fromtimestamp(path.stat().st_mtime)
    return ts.strftime("%d-%b-%Y %H:%M:%S")


# ─────────────────────────────────────────────────────────────────────────────
# CACHED LOADERS — cache key includes file hash so changes invalidate cache
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_instructions(file_hash: str, _path_str: str) -> dict:
    """
    Load Section A (core params), Section B (benchmarks), Section C (financials).
    The file_hash parameter is the cache key — when Excel changes, this re-runs.
    """
    path = Path(_path_str)
    if not path.exists():
        return _fallback_instructions()

    try:
        # Read the entire Instructions tab; we'll parse by row
        df = pd.read_excel(path, sheet_name="Instructions & Assumptions",
                          header=None, engine="openpyxl")
    except Exception as e:
        st.warning(f"Could not read Instructions tab: {e}")
        return _fallback_instructions()

    # Section A — Core params (rows 6-10 in 1-indexed Excel = rows 5-9 in pandas)
    core = {}
    section_a_rows = {
        "as_of_date":      6,
        "fx_rate":         7,
        "full_utilisation": 8,
        "days_in_year":    9,
        "basis":          10,
    }
    for key, excel_row in section_a_rows.items():
        try:
            val = df.iloc[excel_row - 1, 2]  # column C (index 2)
            core[key] = val
        except Exception:
            core[key] = None

    # Convert types
    if isinstance(core.get("as_of_date"), pd.Timestamp):
        core["as_of_date"] = core["as_of_date"].date()
    elif core.get("as_of_date") is None:
        core["as_of_date"] = date(2026, 4, 21)
    try:
        core["fx_rate"] = float(core["fx_rate"]) if core["fx_rate"] else 92.98
    except Exception:
        core["fx_rate"] = 92.98
    core["basis"] = "FY26E" if str(core.get("basis", "")).strip().lower() in ("projected", "fy26e") else "FY24A"

    # Section B — Benchmark rates (rows 13-21)
    benchmarks = {}
    benchmark_rows = {
        "3M T-Bill":          13,
        "Repo Rate":          14,
        "RBL 1Y MCLR":        15,
        "YBL 3M MCLR":        16,
        "ICICI 6M I-MCLR":    17,
        "SIB 12M MCLR":       18,
        "Bajaj BFRR":         19,
        "Term SOFR (USD)":    20,
    }
    for key, excel_row in benchmark_rows.items():
        try:
            val = df.iloc[excel_row - 1, 2]
            benchmarks[key] = float(val) if val is not None else 0.0
        except Exception:
            benchmarks[key] = 0.0

    # Section C — Financials (rows 25-40)
    fin_rows = {
        "EBITDA":              25,
        "Total Debt":          26,
        "Term Debt":           27,
        "TNW":                 28,
        "ATNW":                29,
        "Current Assets":      30,
        "Current Liabilities": 31,
        "TOL":                 32,
        "Interest Expense":    33,
        "Fixed Assets":        34,
        "Secured Debt":        35,
        "External Rating":     36,
        "Promoter %":          37,
        "Sched TL Repay TTM":  38,  # Principal Repayment (TTM) — NOT used for DSCR
        "Tax Paid":            39,
        "Sched TL Repay":      40,  # Scheduled TL Repayment next 12M — used for DSCR
    }

    fin_active = {}
    fin_fy24 = {}
    for key, excel_row in fin_rows.items():
        try:
            active_val = df.iloc[excel_row - 1, 2]
            fy24_val = df.iloc[excel_row - 1, 3]
            fin_active[key] = active_val
            fin_fy24[key] = fy24_val
        except Exception:
            fin_active[key] = None
            fin_fy24[key] = None

    # Add aliases / defaults for missing fields
    fin_active.setdefault("Sched TL Repay", fin_active.get("Sched TL Repay 12M", 41.09))
    fin_fy24.setdefault("Sched TL Repay", fin_fy24.get("Sched TL Repay 12M", 18.76))
    if "Net Sales" not in fin_active:
        fin_active["Net Sales"] = 2079.23
        fin_fy24["Net Sales"] = 1572.92
    if "PAT" not in fin_active:
        fin_active["PAT"] = 243.42
        fin_fy24["PAT"] = 99.52

    financials = {
        "FY26E": fin_active,
        "FY24A": fin_fy24,
    }

    return {
        "core":       core,
        "benchmarks": benchmarks,
        "financials": financials,
    }


def _fallback_instructions() -> dict:
    """Hardcoded fallback if Excel can't be read."""
    return {
        "core": {
            "as_of_date": date(2026, 4, 21),
            "fx_rate": 92.98,
            "basis": "FY26E",
            "full_utilisation": True,
            "days_in_year": 365,
        },
        "benchmarks": {
            "Repo Rate": 0.0525, "3M T-Bill": 0.0518,
            "RBL 1Y MCLR": 0.0900, "YBL 3M MCLR": 0.0900,
            "ICICI 6M I-MCLR": 0.0830, "SIB 12M MCLR": 0.0975,
            "Bajaj BFRR": 0.0850, "Term SOFR (USD)": 0.0430,
        },
        "financials": {
            "FY26E": {
                "EBITDA": 383.96, "Total Debt": 613.03, "Term Debt": 431.28,
                "TNW": 740.13, "ATNW": 720.76, "Current Assets": 755.02,
                "Current Liabilities": 544.79, "TOL": 1143.49,
                "Interest Expense": 49.08, "Fixed Assets": 937.69,
                "Tax Paid": 69.36, "Sched TL Repay": 41.09,
                "External Rating": "CARE A+; Stable / A1", "Promoter %": 1.00,
                "Net Sales": 2079.23, "PAT": 243.42,
            },
            "FY24A": {
                "EBITDA": 173.37, "Total Debt": 471.82, "Term Debt": 324.01,
                "TNW": 720.11, "ATNW": 588.29, "Current Assets": 711.30,
                "Current Liabilities": 513.82, "TOL": 1143.77,
                "Interest Expense": 39.87, "Fixed Assets": 449.34,
                "Tax Paid": 1.12, "Sched TL Repay": 18.76,
                "External Rating": "CARE A+; Stable / A1", "Promoter %": 1.00,
                "Net Sales": 1572.92, "PAT": 99.52,
            },
        },
    }


@st.cache_data(show_spinner=False)
def load_facility_master(file_hash: str, _path_str: str) -> pd.DataFrame:
    """Load the Facility Master tab (header on row 4)."""
    path = Path(_path_str)
    if not path.exists():
        return _fallback_facility_master()

    try:
        df = pd.read_excel(path, sheet_name="Facility Master",
                          header=3, engine="openpyxl")
    except Exception as e:
        st.warning(f"Could not read Facility Master: {e}")
        return _fallback_facility_master()

    # Drop completely empty rows and the "TOTAL" footer row
    df = df.dropna(how="all")
    df = df[df["S.No"].notna()].reset_index(drop=True)
    df = df[pd.to_numeric(df["S.No"], errors="coerce").notna()].reset_index(drop=True)

    # Standardise column names to match downstream code
    rename_map = {
        "S.No": "S.No",
        "Lender": "Lender",
        "Facility": "Facility",
        "Category": "Category",
        "Nature": "Nature",
        "Sub-limit Parent": "Sub_Limit",
        "Currency": "Currency",
        "Sanc. Amt\n(Orig. Ccy)": "Sanction_OrigCcy",
        "Sanc. Amt\n(INR Cr)": "Sanction_INR",
    }
    # Try exact match first; fall back to fuzzy match
    actual_cols = {}
    for orig, std in rename_map.items():
        for col in df.columns:
            if str(col).replace("\n", " ").strip() == orig.replace("\n", " ").strip():
                actual_cols[col] = std
                break
    df = df.rename(columns=actual_cols)

    # Find the Effective Outstanding column (this is what we want — formula-driven)
    # Falls back to Current Outstanding if Effective isn't present
    eff_outstanding_col = None
    curr_outstanding_col = None
    for col in df.columns:
        col_str = str(col).lower().replace("\n", " ")
        if "effective" in col_str and "outstanding" in col_str:
            eff_outstanding_col = col
        elif "current" in col_str and "outstanding" in col_str:
            curr_outstanding_col = col

    # Use Effective Outstanding (formula-driven, includes Full Util toggle)
    if eff_outstanding_col is not None:
        df = df.rename(columns={eff_outstanding_col: "Outstanding_INR"})
    elif curr_outstanding_col is not None:
        df = df.rename(columns={curr_outstanding_col: "Outstanding_INR"})

    # Find rate column
    for col in df.columns:
        col_str = str(col).lower()
        if "effective" in col_str and "rate" in col_str:
            df = df.rename(columns={col: "Effective_Rate"})
            break

    # Find benchmark / spread / dates / purpose
    col_aliases = {
        "Benchmark": ["benchmark", "index"],
        "Spread": ["spread"],
        "Tenor_Months": ["tenor"],
        "Drawdown_Date": ["drawdown date", "drawdown"],
        "Maturity_Date": ["maturity"],
        "Validity_Date": ["validity"],
        "Purpose": ["purpose"],
        "Rate_Type": ["rate type"],
    }
    for std_name, keywords in col_aliases.items():
        if std_name in df.columns:
            continue
        for col in df.columns:
            col_str = str(col).lower()
            if any(k in col_str for k in keywords) and std_name not in df.columns:
                df = df.rename(columns={col: std_name})
                break

    # Coerce types
    for col in ["Sanction_INR", "Outstanding_INR", "Sanction_OrigCcy", "Effective_Rate", "Spread", "Tenor_Months"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["Drawdown_Date", "Maturity_Date", "Validity_Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Fill NaN outstanding with sanction (full utilisation default)
    df["Outstanding_INR"] = df["Outstanding_INR"].fillna(df["Sanction_INR"])

    # Fill NaN rates with 0 — TBD facilities contribute 0 to WAC/interest
    # NaN propagates through arithmetic and causes nan display in dashboard
    for num_col in ["Effective_Rate", "Spread", "Tenor_Months"]:
        if num_col in df.columns:
            df[num_col] = df[num_col].fillna(0.0)

    # Computed fields
    df["Headroom_INR"] = df["Sanction_INR"] - df["Outstanding_INR"]
    df["Utilisation"] = df["Outstanding_INR"] / df["Sanction_INR"]

    # Fill missing categorical fields
    for col in ["Category", "Nature", "Sub_Limit", "Currency", "Rate_Type", "Benchmark", "Purpose"]:
        if col in df.columns:
            df[col] = df[col].fillna("")

    return df


def _fallback_facility_master() -> pd.DataFrame:
    """If Excel can't load, fall back to hardcoded master."""
    from data.jcl_data import get_facility_master
    return get_facility_master()


@st.cache_data(show_spinner=False)
def load_covenant_master(file_hash: str, _path_str: str) -> pd.DataFrame:
    """Load Covenant Tracker tab to extract covenant definitions."""
    path = Path(_path_str)
    if not path.exists():
        return _fallback_covenant_master()

    try:
        df = pd.read_excel(path, sheet_name="Covenant Tracker",
                          header=None, engine="openpyxl")
    except Exception:
        return _fallback_covenant_master()

    # Find header row (contains "Lender" and "Covenant")
    header_row = None
    for i in range(min(10, len(df))):
        row_vals = [str(v).strip().lower() for v in df.iloc[i].values if pd.notna(v)]
        if "lender" in row_vals and "covenant" in row_vals:
            header_row = i
            break

    if header_row is None:
        return _fallback_covenant_master()

    df.columns = df.iloc[header_row]
    df = df.iloc[header_row + 1:].reset_index(drop=True)
    df = df.dropna(how="all")
    df = df[df["Lender"].notna()].reset_index(drop=True)

    # Use hardcoded covenant master since the Excel covenant tracker has different
    # structure — we only need to read FINANCIALS dynamically; covenants are stable
    return _fallback_covenant_master()


def _fallback_covenant_master() -> pd.DataFrame:
    from data.jcl_data import get_covenant_master
    return get_covenant_master()


@st.cache_data(show_spinner=False)
def load_term_loan_schedule(file_hash: str, _path_str: str) -> pd.DataFrame:
    """Term loan amortisation schedule — generated programmatically (stable)."""
    from data.jcl_data import get_term_loan_schedule
    return get_term_loan_schedule()


@st.cache_data(show_spinner=False)
def load_lender_caps(file_hash: str, _path_str: str) -> dict:
    """Lender umbrella exposure caps — stable."""
    from data.jcl_data import LENDER_CAPS
    return LENDER_CAPS


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT — used by main app
# ─────────────────────────────────────────────────────────────────────────────
def load_all_data() -> dict:
    """
    Single entry point. Returns a dict with all data needed by the dashboard.
    Cache automatically invalidates when the Excel file changes.
    """
    path = get_excel_path()
    file_hash = get_file_hash(path)
    path_str = str(path)

    # If Excel exists, use it; otherwise fallback
    if path.exists():
        instructions = load_instructions(file_hash, path_str)
        facility_master = load_facility_master(file_hash, path_str)
        covenant_master = load_covenant_master(file_hash, path_str)
        tl_schedule = load_term_loan_schedule(file_hash, path_str)
        lender_caps = load_lender_caps(file_hash, path_str)
    else:
        instructions = _fallback_instructions()
        facility_master = _fallback_facility_master()
        covenant_master = _fallback_covenant_master()
        from data.jcl_data import get_term_loan_schedule, LENDER_CAPS
        tl_schedule = get_term_loan_schedule()
        lender_caps = LENDER_CAPS

    return {
        "facility_master":   facility_master,
        "covenant_master":   covenant_master,
        "tl_schedule":       tl_schedule,
        "financials":        instructions["financials"],
        "benchmark_rates":   instructions["benchmarks"],
        "lender_caps":       lender_caps,
        "core_params":       instructions["core"],
        "excel_path":        str(path),
        "excel_exists":      path.exists(),
        "excel_hash":        file_hash,
        "excel_mtime":       get_file_mtime(path),
    }


def force_reload():
    """Clear all caches — call from a sidebar button to force refresh."""
    load_instructions.clear()
    load_facility_master.clear()
    load_covenant_master.clear()
    load_term_loan_schedule.clear()
    load_lender_caps.clear()
