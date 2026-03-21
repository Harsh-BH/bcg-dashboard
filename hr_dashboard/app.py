import io
import re
import calendar
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# STREAMLIT CONFIG
# ============================================================
st.set_page_config(page_title="Headcount Dashboard", layout="wide")

# ============================================================
# GLOBAL STYLING — Fancy, high-contrast, large typography
# ============================================================
st.markdown(
    """
    <style>
        /* ----- Base & app ----- */
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&display=swap');
        html, body, [class*="css"], .stApp {
            font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
            font-size: 20px !important;
            color: #1a1a2e !important;
        }
        .stApp {
            background: linear-gradient(160deg, #f8fafc 0%, #e2e8f0 50%, #f1f5f9 100%) !important;
        }
        /* ----- Main content area ----- */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 3rem !important;
            max-width: 1400px !important;
        }
        /* ----- Page title ----- */
        h1 {
            font-size: 2.85rem !important;
            font-weight: 700 !important;
            color: #0f172a !important;
            letter-spacing: -0.02em !important;
            margin-bottom: 0.5rem !important;
            text-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }
        h2, h3 {
            font-size: 1.65rem !important;
            font-weight: 600 !important;
            color: #1e293b !important;
            margin-top: 1.5rem !important;
            margin-bottom: 0.75rem !important;
        }
        /* ----- Sidebar ----- */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%) !important;
            padding: 1.5rem 1rem !important;
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown {
            color: #f1f5f9 !important;
        }
        [data-testid="stSidebar"] .stSelectbox label, [data-testid="stSidebar"] .stTextInput label,
        [data-testid="stSidebar"] .stFileUploader label, [data-testid="stSidebar"] .stDateInput label {
            font-size: 1.05rem !important;
            font-weight: 600 !important;
        }
        [data-testid="stSidebar"] .stButton > button {
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            padding: 0.6rem 1.2rem !important;
            border-radius: 10px !important;
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4) !important;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5) !important;
        }
        /* ----- Tabs ----- */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem !important;
            margin-bottom: 1.25rem !important;
        }
        .stTabs [data-baseweb="tab"] {
            font-size: 1.15rem !important;
            font-weight: 600 !important;
            padding: 0.75rem 1.5rem !important;
            border-radius: 12px !important;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            color: white !important;
        }
        /* ----- Metrics ----- */
        [data-testid="stMetric"] {
            background: white !important;
            padding: 1.25rem 1.5rem !important;
            border-radius: 14px !important;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04) !important;
            border: 1px solid rgba(0,0,0,0.06) !important;
        }
        [data-testid="stMetric"] label {
            font-size: 1.05rem !important;
            font-weight: 600 !important;
            color: #475569 !important;
        }
        [data-testid="stMetric"] div[data-testid="stMetricValue"] {
            font-size: 1.85rem !important;
            font-weight: 700 !important;
            color: #0f172a !important;
        }
        /* ----- Selectboxes, inputs, uploaders ----- */
        .stSelectbox label, .stDateInput label, .stTextInput label, .stFileUploader label {
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            color: #334155 !important;
        }
        .stSelectbox div, .stDateInput div, .stTextInput input {
            font-size: 1.05rem !important;
        }
        .stButton > button {
            font-size: 1.05rem !important;
            font-weight: 600 !important;
            padding: 0.5rem 1.25rem !important;
            border-radius: 10px !important;
        }
        /* ----- DataFrames ----- */
        div[data-testid="stDataFrame"] {
            border-radius: 12px !important;
            overflow: hidden !important;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important;
        }
        div[data-testid="stDataFrame"] div {
            font-size: 1.05rem !important;
        }
        div[data-testid="stDataFrame"] th, div[data-testid="stDataFrame"] td {
            padding: 0.6rem 0.75rem !important;
        }
        /* ----- Alerts: success, info, error ----- */
        .stSuccess, .stInfo, .stError, .stWarning {
            font-size: 1.1rem !important;
            padding: 1rem 1.25rem !important;
            border-radius: 12px !important;
        }
        .stSuccess { box-shadow: 0 2px 10px rgba(34, 197, 94, 0.15); }
        .stInfo    { box-shadow: 0 2px 10px rgba(59, 130, 246, 0.15); }
        .stError   { box-shadow: 0 2px 10px rgba(239, 68, 68, 0.15); }
        /* ----- Expanders ----- */
        .streamlit-expanderHeader {
            font-size: 1.1rem !important;
            font-weight: 600 !important;
        }
        /* ----- Dividers ----- */
        hr {
            margin: 1.5rem 0 !important;
            border-color: rgba(0,0,0,0.08) !important;
        }
        /* ----- General text in main ----- */
        .stMarkdown p, .stMarkdown li {
            font-size: 1.05rem !important;
            line-height: 1.55 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# CONSTANTS
# ============================================================
HR_MANDATORY_STD = ["EMPLOYEE ID", "BUSINESS UNIT", "BUSINESS"]

BUCKET_CONNEQT = "Conneqt Business Solution"
BUCKET_ALLDIGI = "Alldigi"
BUCKET_TECHDIG = "Tech & Digital"
BUCKET_CXO = "CXO"
SUPPORT_PREFIX = "Support Functions - "

TECH_DIGITAL_BUSINESS = {"tech & digital", "ai, data & analytics"}
BPM_BUSINESS = "bpm - practices & ops"
VERTICAL_BUSINESS = "vertical"
HR_BUSINESS = {"hr", "communication"}

CXO_CODES_TYPE2 = {"CXO", "CX1", "CX2", "CX3"}

HR_FILE_RE = re.compile(r"^HRMS_(\d{4})_(0[1-9]|1[0-2])_(0[1-9]|[12]\d|3[01])\.xlsx$", re.IGNORECASE)

# ============================================================
# UTILITIES
# ============================================================
def keyify(s: str) -> str:
    return (
        str(s).strip().lower()
        .replace("\n", " ")
        .replace("\r", " ")
        .replace("_", " ")
        .replace("-", " ")
    )

def to_id_string(x):
    if pd.isna(x):
        return pd.NA
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    s = str(x).strip()
    if s.endswith(".0") and s[:-2].isdigit():
        return s[:-2]
    return s


def span_normalize_hrms_ids(df: pd.DataFrame) -> pd.DataFrame:
    """
    Align EMPLOYEE ID and MANAGER1 ECODE after Excel reads (e.g. float 149346.0 vs int 149346).
    Without this, manager/reportee edges fail to match and people with reports look like IC (n_rep=0).
    """
    if "EMPLOYEE ID" in df.columns:
        df["EMPLOYEE ID"] = df["EMPLOYEE ID"].map(to_id_string).fillna("").astype(str).str.strip()
    if "MANAGER1 ECODE" in df.columns:
        df["MANAGER1 ECODE"] = df["MANAGER1 ECODE"].map(to_id_string).fillna("").astype(str).str.strip()
    return df


def clean_text_series(s: pd.Series) -> pd.Series:
    s = s.astype("string").str.strip()
    s = s.replace({"": pd.NA, "(Blanks)": pd.NA, "nan": pd.NA})
    return s

def ensure_cols(df: pd.DataFrame, required: list[str], kind: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"{kind}: Missing mandatory columns {missing}. "
            f"Expected these (case/spacing can vary): {HR_MANDATORY_STD}. "
            f"Found: {list(df.columns)}"
        )

def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

def read_excel_best_sheet(source) -> pd.DataFrame:
    """Read the sheet with the most non-empty rows; parse one sheet at a time to save memory."""
    xls = pd.ExcelFile(source)
    best_df = None
    best_rows = -1
    for sheet_name in xls.sheet_names:
        d = xls.parse(sheet_name)
        if d is None:
            continue
        d2 = d.dropna(how="all")
        n = len(d2)
        if n > best_rows:
            best_rows = n
            best_df = d2.copy()
    if best_df is None:
        best_df = xls.parse(xls.sheet_names[0]).dropna(how="all")
    return best_df


@st.cache_data(show_spinner=False)
def get_raw_hr(path_str: str, mtime: float) -> pd.DataFrame:
    """Read HR Excel once per (path, mtime); used by validation and snapshot load."""
    return read_excel_best_sheet(path_str)

def read_spartan_auto(uploaded_file) -> tuple[pd.DataFrame, str, int]:
    xls = pd.ExcelFile(uploaded_file)
    for sheet in xls.sheet_names:
        for header in [0, 1, 2, 3, 4, 5, 6, 7, 8]:
            try:
                d = pd.read_excel(uploaded_file, sheet_name=sheet, header=header)
            except Exception:
                continue
            d = d.dropna(how="all")
            cols = [keyify(c) for c in d.columns.astype(str)]
            if ("employee id" in cols) and ("d3" in cols):
                return d, sheet, header
            if ("employee id" in cols) and ("spartan category" in cols):
                return d, sheet, header
    d = pd.read_excel(uploaded_file, sheet_name=0, header=1).dropna(how="all")
    return d, xls.sheet_names[0], 1

def read_payroll_auto(uploaded_file) -> tuple[pd.DataFrame, str, int]:
    xls = pd.ExcelFile(uploaded_file)
    for sheet in xls.sheet_names:
        for header in [0, 1, 2, 3, 4, 5, 6, 7, 8]:
            try:
                d = pd.read_excel(uploaded_file, sheet_name=sheet, header=header)
            except Exception:
                continue
            d = d.dropna(how="all")
            cols = [keyify(c) for c in d.columns.astype(str)]
            if ("employee id" in cols) or ("emp id" in cols) or ("employeeid" in cols):
                return d, sheet, header
    d = pd.read_excel(uploaded_file, sheet_name=0, header=0).dropna(how="all")
    return d, xls.sheet_names[0], 0

def month_end(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def format_snapshot_date(year: int, month: int, day: int) -> str:
    """Format YYYY_MM_DD as human-readable e.g. '14th March, 2026'."""
    d = date(year, month, day)
    day_str = str(day)
    if 10 <= day % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day_str}{suffix} {d.strftime('%B')}, {year}"


# ============================================================
# NORMALIZATION
# ============================================================
def normalize_hr_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    col_map = {keyify(c): c for c in df.columns}

    aliases = {
        "EMPLOYEE ID": ["employee id", "employeeid", "emp id", "empid", "employee code", "employee no", "employee number", "employee_id"],
        "BUSINESS UNIT": ["business unit", "businessunit", "bu"],
        "BUSINESS": ["business"],
        "EMPLOYEE TYPE": ["employee type", "employeetype", "emp type", "employee_type", "emp_type"],
        "LEVEL": ["level", "employee level"],
        "DESIGNATION": ["designation", "designation name", "role", "title"],
        "GRADE": ["grade", "employee grade", "emp grade"],
        "SEPARATION": ["separation", "separations", "separation status", "separation_status", "separationstatus"],
    }

    rename = {}
    for std, alist in aliases.items():
        for a in alist:
            if a in col_map:
                rename[col_map[a]] = std
                break
    return df.rename(columns=rename)

def normalize_spartan_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    col_map = {keyify(c): c for c in df.columns}

    aliases = {
        "EMPLOYEE ID": ["employee id", "employeeid", "emp id", "empid", "employee code", "employee number", "employee_id"],
        "SPARTAN CATEGORY": ["spartan category", "category", "status", "spartan status", "spartan_category"],
        "LWD": ["lwd", "last working date", "lastworkingdate", "last working day", "lastworkingday"],
        "NAME": ["name", "employee name", "full name", "emp name"],
        "D3": ["d3"],
    }

    rename = {}
    for std, alist in aliases.items():
        for a in alist:
            if a in col_map:
                rename[col_map[a]] = std
                break
    return df.rename(columns=rename)

def normalize_payroll_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    col_map = {keyify(c): c for c in df.columns}

    aliases = {
        "EMPLOYEE ID": ["employee id", "employeeid", "emp id", "empid", "employee code", "employee number", "employee_id", "emp code"],
        "EMPLOYEE NAME": ["employee name", "name", "emp name"],
    }

    rename = {}
    for std, alist in aliases.items():
        for a in alist:
            if a in col_map:
                rename[col_map[a]] = std
                break
    return df.rename(columns=rename)


def normalize_span_hrms_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names for Span movement HRMS file (keeps all columns, standardizes key ones)."""
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    col_map = {keyify(c): c for c in df.columns}
    aliases = {
        "EMPLOYEE ID": ["employee id", "employeeid", "emp id", "empid", "employee code", "employee number", "employee_id", "employee-id"],
        "MANAGER1 ECODE": [
            "manager1 ecode",
            "manager ecode",
            "manager1 e code",
            "manager_ecode",
            "reporting manager id",
            "manager id",
            "managerid",
            "manager_id",
            "reporting manager",
            "manager emp id",
            "manager employee id",
            "manager empid",
        ],
        "GRADE": ["grade", "employee grade", "emp grade"],
        "LEVEL": ["level", "employee level"],
        "DESIGNATION": ["designation", "designation name", "role", "title"],
        "BUSINESS UNIT": ["business unit", "businessunit", "bu"],
        "BUSINESS": ["business"],
        "PROCESS": ["process", "process name", "process description"],
        "DIVISION": ["division", "emp division", "employee division", "division name", "div"],
        "JOB_FUNCTION": [
            "job function",
            "jobfunction",
            "job_function",
            "function",
            "job role",
            "jobfunction name",
            "employee job function",
        ],
        "ACCOUNT NAME": [
            "account name",
            "account_name",
            "client name",
            "account",
        ],
        "LEGAL EMPLOYER NAME": [
            "legal employer name",
            "legal_employer_name",
            "legal employer",
        ],
        "MANPOWER": ["manpower"],
        "SEPARATIONS": [
            "separations",
            "separation",
            "separation_status",
            "separation status",
        ],
        "SUB PROCESS": [
            "sub process",
            "sub_process",
            "subprocess",
        ],
        "MANPOWER CHECK": ["manpower check", "manpower_check", "manpowercheck", "mp check", "man power check"],
        "COST CENTER": ["cost center", "costcenter", "cost_center", "cost centre", "cc", "cost centre code"],
    }
    rename = {}
    for std, alist in aliases.items():
        for a in alist:
            if a in col_map:
                rename[col_map[a]] = std
                break
    out = df.rename(columns=rename)
    # Jan/Dec-style extract: column literally named FUNCTION (not caught by alias) → JOB_FUNCTION
    if "JOB_FUNCTION" not in out.columns:
        fn_col = None
        for c in out.columns:
            if keyify(str(c)) == "function":
                fn_col = c
                break
        if fn_col is not None:
            out = out.rename(columns={fn_col: "JOB_FUNCTION"})
    return out


# Span movement: Rule 2 — exact normalized grades only (no A3.1-style variants; data uses A3, A4, …)
SPAN_GRADES_IC = {"naps", "nats", "pt", "at", "a1.1", "a1.2", "a1.3"}
SPAN_GRADES_TL = {"a3", "a4", "a5", "e1", "e2", "e3", "e4", "e5", "e6", "e7", "e8"}


def span_conneqt_row_mask(raw_hr_df: pd.DataFrame) -> pd.Series:
    """
    Same rows as **Overall view** bucket **Conneqt Business Solution**:
    - Type 1: BUSINESS UNIT = Conneqt Business Solution
    - Type 2: BUSINESS in BPM/Vertical + BUSINESS UNIT = Digitide Solutions Limited
    """
    hr = normalize_hr_cols(raw_hr_df)
    if "BUSINESS UNIT" not in hr.columns or "BUSINESS" not in hr.columns:
        return pd.Series(False, index=raw_hr_df.index)
    ftype = _detect_file_type_from_normalized(hr)
    if ftype == "type1":
        bucket = classify_bucket_type1(hr)
    else:
        bucket = classify_bucket_type2(hr)
    m = bucket.eq(BUCKET_CONNEQT)
    if not m.index.equals(raw_hr_df.index):
        m = m.reindex(raw_hr_df.index, fill_value=False)
    return m.fillna(False)


def _span_grade_normalized(grade_series: pd.Series) -> pd.Series:
    """Normalize grade for comparison: strip, lower, collapse spaces."""
    return grade_series.astype(str).str.strip().str.lower().str.replace(r"\s+", "", regex=True).fillna("")

def _span_choose_grade_series(df: pd.DataFrame) -> pd.Series:
    """Use LEVEL and GRADE interchangeably; pick the more-populated column."""
    g = df.get("GRADE", pd.Series([""] * len(df), index=df.index))
    l = df.get("LEVEL", pd.Series([""] * len(df), index=df.index))
    g_nonempty = g.astype(str).str.strip().replace({"nan": ""}).ne("").sum()
    l_nonempty = l.astype(str).str.strip().replace({"nan": ""}).ne("").sum()
    return g if g_nonempty >= l_nonempty else l


def _span_series_process_contains_manpower(proc_series: pd.Series) -> pd.Series:
    """
    True where **PROCESS** contains the substring **manpower** (case-insensitive),
    anywhere — including inside a token (e.g. `processmanpower`, `x-Manpower-y`).
    Used for Span Conneqt load and service-line tables so those rows never enter IC/TL/service-line logic.
    """
    s = proc_series.fillna("").astype(str)
    return s.str.contains("manpower", case=False, regex=False, na=False)


def span_prepare_and_detect_unknown(
    raw_hr_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series, set[str], set[str]]:
    """
    Filter to the same **Conneqt** population as Tab 1 (bucket Conneqt Business Solution).
    `raw_hr_df` = raw HRMS extract (same rows as Tab 1). Span columns are normalized inside.
    Returns: (conneqt_df, reportee_count_series index by emp_id, all_grades_in_data, unknown_grades).
    """
    df = normalize_span_hrms_cols(raw_hr_df)
    if "EMPLOYEE ID" not in df.columns:
        raise ValueError("Span HRMS file must have an EMPLOYEE ID column.")
    if "MANAGER1 ECODE" not in df.columns:
        raise ValueError("Span HRMS file must have a MANAGER1 ECODE column.")

    conneqt_mask = span_conneqt_row_mask(raw_hr_df)
    conneqt_df = df.loc[conneqt_mask].copy()

    # Span only: exclude manpower rows — PROCESS must not contain substring **manpower** (any case, any position);
    # else **MANPOWER CHECK == 1** if no PROCESS column
    if not conneqt_df.empty:
        if "PROCESS" in conneqt_df.columns:
            exclude_mp = _span_series_process_contains_manpower(conneqt_df["PROCESS"])
            conneqt_df = conneqt_df.loc[~exclude_mp].copy()
        elif "MANPOWER CHECK" in conneqt_df.columns:
            mc = conneqt_df["MANPOWER CHECK"]
            num = pd.to_numeric(mc, errors="coerce")
            exclude_mp = (num == 1) | (mc.astype(str).str.strip() == "1")
            conneqt_df = conneqt_df.loc[~exclude_mp].copy()

    if conneqt_df.empty:
        return conneqt_df, pd.Series(dtype=int), set(), set()

    span_normalize_hrms_ids(conneqt_df)

    # Normalize IDs for matching (vectorized)
    emp_id = conneqt_df["EMPLOYEE ID"]
    mgr_id = conneqt_df["MANAGER1 ECODE"].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})

    # Reportee count: for each distinct EMPLOYEE ID, how many Conneqt rows have MANAGER1 ECODE = that ID
    reportee_counts = mgr_id.dropna().value_counts()
    unique_emp_ids = pd.Index(emp_id.unique())
    reportee_count_series = reportee_counts.reindex(unique_emp_ids).fillna(0).astype(int)

    # Grades in data (normalized). In some HRMS extracts, grade codes are in LEVEL (e.g., A3, A1.2).
    if "GRADE" not in conneqt_df.columns:
        conneqt_df["GRADE"] = ""
    if "LEVEL" not in conneqt_df.columns:
        conneqt_df["LEVEL"] = ""
    grade_src = _span_choose_grade_series(conneqt_df)
    grades_norm = _span_grade_normalized(grade_src)
    all_grades_raw = set(grade_src.astype(str).str.strip().replace({"nan": ""}).unique()) - {""}

    def is_unknown(g_raw: str) -> bool:
        if not g_raw or not str(g_raw).strip():
            return False
        gn = str(g_raw).strip().lower().replace(" ", "")
        # Known grade tokens in the latest rules:
        # IC-grade set: A1.x, A2.x, PT, AT, NAPS, NATS
        # TL-grade exception set: A3, A4 (used with designation list)
        # Also treat A5, P1–P7, E1–E8, CX1 as known (they default to M1+ unless they satisfy TL/IC conditions).
        if gn in {"pt", "at", "naps", "nats", "int", "a-rt", "p-rt", "a3", "a4", "a5", "cx1"}:
            return False
        if re.fullmatch(r"p[1-7]", gn):
            return False
        if re.fullmatch(r"e[1-8]", gn):
            return False
        if gn.startswith("a1."):
            return False
        if gn == "a2" or gn.startswith("a2."):
            return False
        return True

    unknown_grades = {g for g in all_grades_raw if is_unknown(g)}

    return conneqt_df, reportee_count_series, all_grades_raw, unknown_grades


def span_prepare_and_detect_unknown_all_business_units(
    raw_hr_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series, set[str], set[str]]:
    """
    Same as `span_prepare_and_detect_unknown`, but DOES NOT filter to Conneqt Business Solution.
    It includes all business units for Span/service-line calculations, while still:
    - normalizing Span HRMS columns
    - applying the manpower exclusion logic
    """
    df = normalize_span_hrms_cols(raw_hr_df)
    if "EMPLOYEE ID" not in df.columns:
        raise ValueError("Span HRMS file must have an EMPLOYEE ID column.")
    if "MANAGER1 ECODE" not in df.columns:
        raise ValueError("Span HRMS file must have a MANAGER1 ECODE column.")

    # Include all rows (no Conneqt BU filtering)
    span_df = df.copy()

    # Span only: exclude manpower rows — PROCESS must not contain substring **manpower** (any case, any position);
    # else **MANPOWER CHECK == 1** if no PROCESS column
    if not span_df.empty:
        if "PROCESS" in span_df.columns:
            exclude_mp = _span_series_process_contains_manpower(span_df["PROCESS"])
            span_df = span_df.loc[~exclude_mp].copy()
        elif "MANPOWER CHECK" in span_df.columns:
            mc = span_df["MANPOWER CHECK"]
            num = pd.to_numeric(mc, errors="coerce")
            exclude_mp = (num == 1) | (mc.astype(str).str.strip() == "1")
            span_df = span_df.loc[~exclude_mp].copy()

    if span_df.empty:
        return span_df, pd.Series(dtype=int), set(), set()

    span_normalize_hrms_ids(span_df)

    emp_id = span_df["EMPLOYEE ID"]
    mgr_id = span_df["MANAGER1 ECODE"].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})

    reportee_counts = mgr_id.dropna().value_counts()
    unique_emp_ids = pd.Index(emp_id.unique())
    reportee_count_series = reportee_counts.reindex(unique_emp_ids).fillna(0).astype(int)

    if "GRADE" not in span_df.columns:
        span_df["GRADE"] = ""
    if "LEVEL" not in span_df.columns:
        span_df["LEVEL"] = ""
    grade_src = _span_choose_grade_series(span_df)
    grades_norm = _span_grade_normalized(grade_src)
    all_grades_raw = set(grade_src.astype(str).str.strip().replace({"nan": ""}).unique()) - {""}

    def is_unknown(g_raw: str) -> bool:
        if not g_raw or not str(g_raw).strip():
            return False
        gn = str(g_raw).strip().lower().replace(" ", "")
        if gn in {"pt", "at", "naps", "nats", "int", "a-rt", "p-rt", "a3", "a4", "a5", "cx1"}:
            return False
        if re.fullmatch(r"p[1-7]", gn):
            return False
        if re.fullmatch(r"e[1-8]", gn):
            return False
        if gn.startswith("a1."):
            return False
        if gn == "a2" or gn.startswith("a2."):
            return False
        return True

    unknown_grades = {g for g in all_grades_raw if is_unknown(g)}
    return span_df, reportee_count_series, all_grades_raw, unknown_grades


def span_direct_report_sets(conneqt_df: pd.DataFrame) -> dict[str, set[str]]:
    """Manager EMPLOYEE ID -> set of direct-report EMPLOYEE IDs (Conneqt rows only; manager must appear in Conneqt)."""
    df = conneqt_df.copy()
    span_normalize_hrms_ids(df)
    emp = df["EMPLOYEE ID"]
    mgr = df["MANAGER1 ECODE"].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    all_ids = pd.Index(emp.unique())
    edges = pd.DataFrame({"mgr": mgr, "rep": emp})
    edges = edges[edges["mgr"].notna()].copy()
    edges["mgr"] = edges["mgr"].astype(str).str.strip()
    edges = edges[edges["mgr"].isin(set(all_ids))].copy()
    # Build sets per manager (faster than python looping over rows)
    return edges.groupby("mgr")["rep"].agg(lambda s: set(s.astype(str))).to_dict()


def _span_grade_is_a2_family(g_norm: str) -> bool:
    """True for A2, A2.1, A2.2, etc. (not e.g. BA2)."""
    if not g_norm or g_norm == "nan":
        return False
    return g_norm == "a2" or g_norm.startswith("a2.")

def _span_grade_is_a1_family(g_norm: str) -> bool:
    """True for A1.x family (e.g., A1.1, A1.2, A1.3)."""
    if not g_norm or g_norm == "nan":
        return False
    return g_norm.startswith("a1.")

# Match on **normalized** designation (lowercase). Matching is **space-insensitive**: all whitespace
# is removed from both the designation and each phrase before substring check — e.g. list entry
# "team lead" matches "teamlead", "Team  Lead", "x-team-lead-y".
# A1.x / A2.x employees matching any phrase here are **mandatory TL** (overrides no-reportee IC).
SPAN_TL_DESIGNATIONS = {
    # Original / HR-style titles
    "team lead",
    "team leader",
    "team manager",
    "senior manager",
    "senior manager quality",
    "senior officer",
    # Requested tokens (substring after removing all spaces from designation and phrase)
    "lead",
    "srtl",
    "supervisor",
}


def _span_designation_normalized(des_series: pd.Series) -> pd.Series:
    return des_series.astype(str).str.strip().str.lower().str.replace(r"\s+", " ", regex=True).fillna("")


def _span_mandatory_tl_designation_match(des_norm_lower: pd.Series) -> pd.Series:
    """
    True where designation contains any phrase in SPAN_TL_DESIGNATIONS.
    **Space-insensitive:** whitespace is stripped from both sides before substring match
    (so "team lead" matches "teamlead", "Team Lead", etc.). Input series should already be lowercased.
    """
    phrases = tuple(p.strip().lower() for p in SPAN_TL_DESIGNATIONS if str(p).strip())
    if not phrases:
        return pd.Series(False, index=des_norm_lower.index)
    des_compact = des_norm_lower.astype(str).str.replace(r"\s+", "", regex=True)
    out = pd.Series(False, index=des_norm_lower.index)
    for p in phrases:
        p_compact = re.sub(r"\s+", "", p)
        if not p_compact:
            continue
        out = out | des_compact.str.contains(re.escape(p_compact), regex=True, na=False)
    return out


def span_rule1_ic_tl_m1(all_emp_ids: set[str], direct_reports: dict[str, set[str]]) -> dict[str, str]:
    """
    Rule 1 only (structural, Conneqt IDs):
    - 0 direct reportees -> IC
    - >=1 reportee, all direct reports IC -> TL
    - >=1 reportee, any direct report TL or M1+ -> M1+
    Cycles -> IC.
    """
    role: dict[str, str] = {}
    ids = set(all_emp_ids)

    def reps(e: str) -> set[str]:
        return direct_reports.get(e, set())

    changed = True
    while changed:
        changed = False
        for e in ids:
            if e in role:
                continue
            rset = reps(e)
            if not rset:
                role[e] = "IC"
                changed = True
                continue
            if not rset.issubset(role.keys()):
                continue
            if all(role[x] == "IC" for x in rset):
                role[e] = "TL"
            else:
                role[e] = "M1+"
            changed = True

    for e in ids:
        if e not in role:
            role[e] = "IC"
    return role


def span_classify_ic_tl_m1(
    conneqt_df: pd.DataFrame,
    reportee_count_series=None,
    unknown_grade_to_rule=None,
) -> pd.Series:
    """
    Implements the latest Span rules (IC / TL / M1+) **exactly**:

    - **IC**: [(no reportees) AND (grade ∈ A1.x, A2.x, PT, AT, NAPS, NATS)]
    - **TL**: (A1.x or A2.x) AND (designation matches any phrase in **SPAN_TL_DESIGNATIONS**) [mandatory]; OR (≥1 reportee AND all IC); OR (A3/A4 AND IC-like: **0 direct reportees** in Conneqt)
    - **M1+**: all remaining people

    Unknown-grade handling: `unknown_grade_to_rule` may map grade -> "IC" | "TL" | "M1+" (forces output).
    """
    _ = reportee_count_series
    df = conneqt_df.copy()
    if "MANAGER1 ECODE" not in df.columns:
        df["MANAGER1 ECODE"] = ""
    span_normalize_hrms_ids(df)
    if "GRADE" not in df.columns:
        df["GRADE"] = ""
    if "LEVEL" not in df.columns:
        df["LEVEL"] = ""
    if "DESIGNATION" not in df.columns:
        df["DESIGNATION"] = ""

    # Use LEVEL and GRADE interchangeably (pick the more-populated column).
    grade_src = _span_choose_grade_series(df)
    grades_norm_row = _span_grade_normalized(grade_src)
    grades_raw_row = grade_src.astype(str).fillna("").map(lambda x: str(x).strip())
    des_norm_row = _span_designation_normalized(df["DESIGNATION"])

    unknown_grade_to_rule = unknown_grade_to_rule or {}

    # Build an employee-level table (one row per EMPLOYEE ID) picking the first non-empty grade/designation.
    emp_tbl = pd.DataFrame(
        {
            "EMPLOYEE ID": df["EMPLOYEE ID"],
            "_grade_norm": grades_norm_row,
            "_grade_raw": grades_raw_row,
            "_des_norm": des_norm_row,
        }
    )
    emp_tbl["_grade_norm"] = emp_tbl["_grade_norm"].replace({"": pd.NA, "nan": pd.NA})
    emp_tbl["_grade_raw"] = emp_tbl["_grade_raw"].replace({"": pd.NA, "nan": pd.NA})
    emp_tbl["_des_norm"] = emp_tbl["_des_norm"].replace({"": pd.NA, "nan": pd.NA})
    emp_one = (
        emp_tbl.groupby("EMPLOYEE ID", as_index=False)
        .agg({"_grade_norm": "first", "_grade_raw": "first", "_des_norm": "first"})
        .fillna("")
    )

    # Edges (manager -> reportee) within Conneqt IDs only
    edges = pd.DataFrame(
        {
            "rep": df["EMPLOYEE ID"],
            "mgr": df["MANAGER1 ECODE"].astype(str).str.strip().replace({"": pd.NA, "nan": pd.NA, "None": pd.NA}),
        }
    )
    edges = edges[edges["mgr"].notna()].copy()
    edges["mgr"] = edges["mgr"].astype(str).str.strip()
    ids_set = set(emp_one["EMPLOYEE ID"].astype(str))
    edges = edges[edges["mgr"].isin(ids_set)].copy()

    n_rep = edges.groupby("mgr")["rep"].nunique()
    eids = emp_one["EMPLOYEE ID"].astype(str)
    emp_one["n_rep"] = eids.map(n_rep).fillna(0).astype(int)

    ugr = unknown_grade_to_rule
    m_raw = emp_one["_grade_raw"].map(ugr)
    m_norm = emp_one["_grade_norm"].map(ugr)
    valid = {"IC", "TL", "M1+"}
    emp_one["forced_role"] = ""
    ok_raw = m_raw.isin(list(valid))
    emp_one.loc[ok_raw, "forced_role"] = m_raw[ok_raw].astype(str)
    ok_norm = ~ok_raw & m_norm.isin(list(valid))
    emp_one.loc[ok_norm, "forced_role"] = m_norm[ok_norm].astype(str)

    g = emp_one["_grade_norm"].astype(str)
    des_l = emp_one["_des_norm"].astype(str).str.lower()
    is_a1_or_a2 = g.str.startswith("a1.") | (g == "a2") | g.str.startswith("a2.")
    has_tl_desig = _span_mandatory_tl_designation_match(des_l)
    # Mandatory TL: A1.x / A2.x + designation matches SPAN_TL_DESIGNATIONS (overrides IC)
    emp_one["mandatory_tl_a1a2"] = is_a1_or_a2 & has_tl_desig

    # IC condition: (no reportees) AND (IC-grade) AND not mandatory TL above
    is_ic_grade = is_a1_or_a2 | g.isin(["pt", "at", "naps", "nats", "int", "a-rt", "p-rt"])
    emp_one["is_ic"] = (emp_one["forced_role"] == "IC") & (emp_one["n_rep"] == 0)
    emp_one.loc[emp_one["forced_role"] == "", "is_ic"] = (
        (emp_one["n_rep"] == 0) & is_ic_grade & ~emp_one["mandatory_tl_a1a2"]
    )

    ic_set = set(emp_one.loc[emp_one["is_ic"], "EMPLOYEE ID"].astype(str))

    # TL condition 1: (>=1 reportee) AND (all reportees are IC)
    edges["rep_is_ic"] = edges["rep"].astype(str).isin(ic_set)
    all_rep_ic = edges.groupby("mgr")["rep_is_ic"].all()
    cond_tl1 = eids.map(all_rep_ic).fillna(False).astype(bool) & (emp_one["n_rep"] >= 1)

    # TL condition 2: A3/A4 + IC-like (no direct reportees in Conneqt). A3/A4 are not IC-grade, so do not use `is_ic` here.
    is_a3_or_a4 = emp_one["_grade_norm"].isin(["a3", "a4"])
    cond_tl2 = is_a3_or_a4 & (emp_one["n_rep"] == 0) & ~emp_one["forced_role"].isin(["M1+", "TL"])

    emp_one["is_tl"] = emp_one["forced_role"] == "TL"
    emp_one.loc[emp_one["forced_role"] == "", "is_tl"] = cond_tl1 | cond_tl2

    # Final: mandatory TL; else forced; else IC; else TL; else M1+ (vectorized)
    mand = emp_one["mandatory_tl_a1a2"].to_numpy()
    fr = emp_one["forced_role"].to_numpy()
    icv = emp_one["is_ic"].to_numpy()
    tlv = emp_one["is_tl"].to_numpy()
    n = len(emp_one)
    out_emp = np.full(n, "M1+", dtype=object)
    out_emp[mand] = "TL"
    forced_ok = np.isin(fr, ["IC", "TL", "M1+"]) & ~mand
    out_emp[forced_ok] = fr[forced_ok]
    rest = ~mand & ~forced_ok
    out_emp[rest & icv] = "IC"
    rest2 = rest & ~icv
    out_emp[rest2 & tlv] = "TL"
    emp_one["final_role"] = out_emp
    role_ser = pd.Series(out_emp, index=eids.values)
    out = df["EMPLOYEE ID"].astype(str).map(role_ser).fillna("M1+")
    return pd.Series(out.values, index=conneqt_df.index)


@st.cache_data(show_spinner=False)
def span_load_conneqt_cached(path_str: str, mtime: float):
    """Cached Span load: raw excel -> Conneqt rows + reportee counts + unknown grades."""
    raw = get_raw_hr(path_str, mtime).dropna(how="all")
    return span_prepare_and_detect_unknown(raw)


@st.cache_data(show_spinner=False)
def span_load_all_business_units_cached(path_str: str, mtime: float):
    """Cached Span load: raw excel -> all business units + reportee counts + unknown grades."""
    raw = get_raw_hr(path_str, mtime).dropna(how="all")
    return span_prepare_and_detect_unknown_all_business_units(raw)


@st.cache_data(show_spinner=False)
def span_roles_cached(path_str: str, mtime: float, choices_key: tuple):
    """Cached IC/TL/M1+ classification for a snapshot + unknown-grade choices (avoids recomputation on rerun)."""
    conneqt_df, rc, _, _ = span_load_conneqt_cached(path_str, mtime)
    if conneqt_df.empty:
        return pd.Series(dtype=object)
    return span_classify_ic_tl_m1(conneqt_df, rc, unknown_grade_to_rule=dict(choices_key))


@st.cache_data(show_spinner=False)
def span_roles_all_business_units_cached(path_str: str, mtime: float, choices_key: tuple):
    """Cached IC/TL/M1+ classification for a snapshot across all business units."""
    span_df, rc, _, _ = span_load_all_business_units_cached(path_str, mtime)
    if span_df.empty:
        return pd.Series(dtype=object)
    return span_classify_ic_tl_m1(span_df, rc, unknown_grade_to_rule=dict(choices_key))


def find_conneqt_cost_mapping_path(folder_path: str):
    """Locate Conneqt_CostCode_Mapping (or similar) in the HR folder."""
    p = Path(folder_path)
    if not p.is_dir():
        return None
    for name in (
        "Conneqt_CostCode_Mapping.xlsx",
        "Conneqt_CostCode_Mapping.xlsm",
        "Conneqt CostCode Mapping.xlsx",
        "Conneqt_Cost_Code_Mapping.xlsx",
    ):
        f = p / name
        if f.is_file():
            return f
    for f in sorted(p.glob("*.xlsx"), key=lambda x: x.name.lower()):
        low = f.name.lower()
        if "conneqt" in low and "cost" in low and "mapp" in low:
            return f
    return None


def _conneqt_mapping_code_cluster_cols(df: pd.DataFrame):
    """Return (code_col_name, cluster_col_name) or (None, None)."""

    def ck(c):
        return keyify(str(c)).strip()

    code_col = None
    cluster_col = None
    for c in df.columns:
        if str(c).lower().startswith("unnamed"):
            continue
        k = ck(c)
        if k in ("cost code", "costcode") or ("cost" in k and "code" in k and "cluster" not in k):
            if code_col is None or k in ("cost code", "costcode"):
                code_col = c
        if k == "cluster" and "head" not in k:
            cluster_col = c
    if cluster_col is None:
        for c in df.columns:
            if str(c).lower().startswith("unnamed"):
                continue
            if ck(c) == "cluster":
                cluster_col = c
                break
    if cluster_col is None:
        col_map = {ck(c): c for c in df.columns if not str(c).lower().startswith("unnamed")}
        for alias in ("vertical", "cluster name", "business cluster"):
            if alias in col_map:
                cluster_col = col_map[alias]
                break
    return code_col, cluster_col


def _build_cluster_mapping_table(df: pd.DataFrame):
    code_col, cluster_col = _conneqt_mapping_code_cluster_cols(df)
    if code_col is None or cluster_col is None:
        return None
    m = df[[code_col, cluster_col]].dropna(how="all").copy()
    m.columns = ["_code", "_cluster"]
    m["_cc_key"] = m["_code"].astype(str).str.strip().str.upper()
    # Blank Excel cells read as NaN; astype(str) would become literal "nan" — treat as missing cluster
    m["_cluster"] = m["_cluster"].fillna("").astype(str).str.strip()
    m = m[m["_cc_key"].ne("") & m["_cc_key"].ne("NAN")]
    if m.empty:
        return None
    m = m.drop_duplicates(subset=["_cc_key"], keep="first")
    return m.rename(columns={"_cc_key": "cc_key", "_cluster": "Cluster"})[["cc_key", "Cluster"]]


@st.cache_data(show_spinner=False)
def load_conneqt_cluster_mapping(path_str: str, mtime: float) -> pd.DataFrame:
    """
    Read Conneqt_CostCode_Mapping: **Cost code** -> **Cluster**.
    Tries multiple **header rows** and **sheets** (file often has title rows above headers → Unnamed columns if read wrong).
    """
    xls = pd.ExcelFile(path_str)
    last_cols = []
    for sheet in xls.sheet_names:
        for header_row in range(0, 30):
            try:
                d = pd.read_excel(path_str, sheet_name=sheet, header=header_row)
            except Exception:
                continue
            d = d.dropna(how="all")
            if d.empty or len(d.columns) < 2:
                continue
            d.columns = [str(c).strip() for c in d.columns]
            last_cols = list(d.columns)
            # Skip obvious junk reads (all Unnamed)
            if all(str(c).lower().startswith("unnamed") for c in d.columns):
                continue
            out = _build_cluster_mapping_table(d)
            if out is not None and len(out) >= 1:
                return out
    raise ValueError(
        "Conneqt cost mapping file must have **Cost code** and **Cluster** columns. "
        "The first row may be a title — we scan header rows 0–29 on every sheet. "
        f"Last columns seen: {last_cols[:12]}{'…' if len(last_cols) > 12 else ''}"
    )


def span_attach_cluster_and_summarize(out_df: pd.DataFrame, hr_folder: str):
    """
    Join Cluster from Conneqt_CostCode_Mapping on COST CENTER == Cost Code.
    Returns (out_df with Cluster column, pivot summary or None, status message).
    """
    msg_parts = []
    mp = find_conneqt_cost_mapping_path(hr_folder)
    if mp is None:
        msg_parts.append("Cost mapping file not found (expected e.g. **Conneqt_CostCode_Mapping.xlsx** in the HR folder).")
        out = out_df.copy()
        out["Cluster"] = "Unmapped (no mapping file)"
        return out, None, " ".join(msg_parts)

    try:
        map_df = load_conneqt_cluster_mapping(str(mp), mp.stat().st_mtime)
    except Exception as e:
        msg_parts.append(f"Could not read mapping file: {e}")
        out = out_df.copy()
        out["Cluster"] = "Unmapped (mapping error)"
        return out, None, " ".join(msg_parts)

    if "COST CENTER" not in out_df.columns:
        msg_parts.append("HRMS extract has no **COST CENTER** column after normalization.")
        out = out_df.copy()
        out["Cluster"] = "Unmapped (no cost center)"
        return out, None, " ".join(msg_parts)

    out = out_df.copy()
    out["_cc_key"] = out["COST CENTER"].astype(str).str.strip().str.upper().replace({"NAN": "", "NONE": ""})
    out = out.merge(map_df, left_on="_cc_key", right_on="cc_key", how="left", suffixes=("", "_map"))
    out.drop(columns=["cc_key"], errors="ignore", inplace=True)
    n_miss = int(out["Cluster"].isna().sum())
    out["Cluster"] = out["Cluster"].fillna("Unmapped")
    # Merge hit but mapping had empty / junk cluster name, or legacy "nan" string from file
    _cl = out["Cluster"].astype(str).str.strip()
    _bad = _cl.str.lower().isin(["", "nan", "none", "nat", "<na>", "#n/a"])
    out.loc[_bad, "Cluster"] = "Unmapped"
    out.drop(columns=["_cc_key"], errors="ignore", inplace=True)
    n_blank = int(_bad.sum())
    if n_miss:
        msg_parts.append(f"**{n_miss:,}** row(s) with no matching Cost Code in mapping → **Unmapped**.")
    if n_blank:
        msg_parts.append(
            f"**{n_blank:,}** row(s) matched a cost code but **Cluster** was blank or invalid in the mapping file → **Unmapped**."
        )

    role_col = "IC / TL / M1+"
    if role_col not in out.columns:
        return out, None, " ".join(msg_parts)

    pv = (
        out.groupby(["Cluster", role_col], dropna=False)
        .size()
        .unstack(fill_value=0)
        .reindex(columns=["IC", "TL", "M1+"], fill_value=0)
    )
    pv["Total rows"] = pv.sum(axis=1)
    pv = pv.reset_index()
    pv["_u"] = pv["Cluster"].eq("Unmapped")
    pv = pv.sort_values(["_u", "Cluster"]).drop(columns=["_u"])
    msg_parts.append(f"Mapping: **{mp.name}**")
    return out, pv, " ".join(msg_parts)


def span_mapping_mtime_key(hr_folder: str) -> tuple | None:
    """Cache key fragment for Conneqt cost→cluster mapping (path + mtime)."""
    mp = find_conneqt_cost_mapping_path(hr_folder)
    if mp is None:
        return None
    return (str(mp), float(mp.stat().st_mtime))


def span_collect_unknown_grades_union(metas: list) -> set[str]:
    """Union of unknown grades across selected HRMS snapshots (Span rules)."""
    u: set[str] = set()
    for m in metas:
        _, _, _, unk = span_load_conneqt_cached(str(m["path"]), m["mtime"])
        u |= unk
    return u


@st.cache_data(show_spinner=False)
def span_trend_ic_tl_by_cluster_cached(
    snap_key: tuple,
    choices_key: tuple,
    hr_folder: str,
    mapping_key: tuple | None,
) -> pd.DataFrame:
    """
    One row per (snapshot, Cluster): IC, TL, M1+, Total rows, Span = IC/TL (NaN if TL=0).
    `snap_key` entries: (path_str, mtime, month_short, year, month, day).
    `mapping_key` is only for cache invalidation when the cost-code file changes.
    """
    _ = mapping_key
    pieces: list[pd.DataFrame] = []
    for i, (path_str, mtime, month_short, y, mo, d) in enumerate(snap_key):
        conneqt_df, _, _, _ = span_load_conneqt_cached(path_str, mtime)
        if conneqt_df.empty:
            continue
        role_s = span_roles_cached(path_str, mtime, choices_key)
        if role_s.empty or len(role_s) != len(conneqt_df):
            continue
        out_df = conneqt_df.copy()
        out_df["IC / TL / M1+"] = role_s.values
        _, cluster_summary, _ = span_attach_cluster_and_summarize(out_df, hr_folder)
        if cluster_summary is None or cluster_summary.empty:
            continue
        t = cluster_summary.copy()
        t["month_short"] = month_short
        t["snapshot_order"] = i
        t["snapshot_date"] = pd.Timestamp(year=int(y), month=int(mo), day=int(d))
        t["Span (IC÷TL)"] = np.where(t["TL"] > 0, t["IC"].astype(float) / t["TL"].astype(float), np.nan)
        pieces.append(t)
    if not pieces:
        return pd.DataFrame()
    return pd.concat(pieces, ignore_index=True)


# --- Span movement: service line × month (PROCESS-driven; extend mapping as rules are added) ---

# Core Delivery keys (Step 1 — PROCESS pipe mapping; Sub-total sums these three).
SPAN_SL_CORE_KEYS = ("core_collections", "core_clm", "core_fa_back_office")

# Display order: (Category label, Service line label, internal key or None for Sub-total row).
SPAN_SERVICE_LINE_ROW_SPEC: tuple[tuple[str, str, str | None], ...] = (
    ("Core Delivery", "Collections", "core_collections"),
    ("Core Delivery", "CLM", "core_clm"),
    ("Core Delivery", "F&A & back office", "core_fa_back_office"),
    ("Core Delivery", "Sub-total", None),
    ("Delivery support", "Quality", "ds_quality"),
    ("Delivery support", "Training", "ds_training"),
    ("Delivery support", "WFM", "ds_wfm"),
    ("Delivery support", "Others", "ds_others"),
    ("Delivery support", "Unclassified (PROCESS mapping TBD)", "unclassified"),
)

# Cache-bust version for service-line routing logic.
_SPAN_SERVICE_LINE_RULES_VERSION = 10

# Cost-center overrides (Jan/Dec pivot alignment). Prefer external config long-term.
SPAN_SL_CC_OVERRIDE: dict[str, str] = {
    "40FSHBLAG1": "core_fa_back_office",
    "40FSHBLAGR": "core_collections",
    "40FSHBLTW1": "core_collections",
    "40FSHBLMAN": "core_collections",
    "40LDHBLAGR": "core_collections",
    "40FSHDFALC": "core_collections",
    "40KOSBITCO": "core_clm",
    "40RBSBITCO": "core_clm",
    "40KOSBITC1": "core_collections",
    "40ARTAIGCC": "core_clm",
    "40ARTAIGOB": "core_clm",
    "90PU2CROMA": "core_clm",
    "13HYATLDTH": "core_clm",
    "90HYATELBO": "core_clm",
    "40COMFCVOI": "core_clm",
    "40KSGHFBLO": "core_clm",
    "40KSGHFLCC": "core_clm",
    "40CH2MFLBO": "core_fa_back_office",
    "40KSGHFLBO": "core_fa_back_office",
    "40ARGHFL2E": "core_fa_back_office",
    "40KSGHFINV": "core_fa_back_office",
    "40KONABPLM": "core_collections",
    "40HYMMFCPC": "core_fa_back_office",
    "40LDJLRPO": "core_fa_back_office",
    "40LDJLRAP": "core_fa_back_office",
    "40KSTCFSPD": "core_fa_back_office",
    "40COTCSSAP": "core_fa_back_office",
    "40KSKSFBOF": "core_fa_back_office",
}

DIVISION_CLM_WHEN_PROCESS_BLANK: frozenset[str] = frozenset(
    {
        "customer service",
        "clm domestic bfsi",
        "clm domestic diversified",
        "customer contact center generalist",
        "customer contact center training / coaching",
    }
)

COLLECTIONS_DESIG_TOKENS: tuple[str, ...] = (
    "collection",
    "collections",
    "coll - exe",
    "customer relationship executive",
    "fos",
    "tele caller",
)

BACKOFFICE_DESIG_TOKENS: tuple[str, ...] = (
    "accounts",
    "finance",
    "shared service",
)

DS_OTHERS_DESIG_TOKENS: tuple[str, ...] = (
    "director operations",
    "vice president",
    "senior vice president",
)

CLM_GENERIC_DESIG_TOKENS: tuple[str, ...] = (
    "executive",
    "operations executive",
    "customer care executive",
    "cce",
    "ops - exe",
)


def _span_hrms_cell_blank(val) -> bool:
    """
    Blank = None / NaN / pandas NA / empty string / 0 / 0.0 / "0"
    and NA-like strings such as:
    na, n/a, #n/a, n.a., n-a, <na>, nan, none, null, nat
    """
    if val is None:
        return True

    try:
        if pd.isna(val):
            return True
    except Exception:
        pass

    if isinstance(val, (int, float, np.integer, np.floating)) and not isinstance(val, bool):
        try:
            if float(val) == 0.0:
                return True
        except Exception:
            pass

    s = str(val).strip()
    if s == "":
        return True

    if re.fullmatch(r"0+(\.0+)?", s):
        return True

    low = s.lower().strip()
    if low in {"nan", "none", "null", "nat", "<na>"}:
        return True

    na_like = re.sub(r"[^a-z0-9]", "", low)
    if na_like in {"na", "notapplicable"}:
        return True

    return False


def _sl_norm(x) -> str:
    if _span_hrms_cell_blank(x):
        return ""
    return re.sub(r"\s+", " ", str(x).strip().lower())


def _sl_contains_any(text: str, needles: tuple[str, ...]) -> bool:
    t = _sl_norm(text)
    return any(n in t for n in needles)


def _span_classify_service_line_row(
    process,
    division,
    job_function,
    designation="",
    account_name="",
    cost_center="",
) -> tuple[str, str]:
    """Returns (service_line_key, service_line_trace). Single pass: overrides then base doc rules."""
    _ = account_name  # reserved for future pivot-aligned rules
    p = _sl_norm(process)
    d = _sl_norm(division)
    jf = _sl_norm(job_function)
    cc = ""
    if not _span_hrms_cell_blank(cost_center):
        cc = str(cost_center).strip().upper()

    if cc in SPAN_SL_CC_OVERRIDE:
        k = SPAN_SL_CC_OVERRIDE[cc]
        return k, f"CC override → {k} (cc={cc!r})"

    if _span_hrms_cell_blank(process):
        if d in DIVISION_CLM_WHEN_PROCESS_BLANK:
            if _sl_contains_any(designation, COLLECTIONS_DESIG_TOKENS):
                return "core_collections", "Blank PROCESS + Division override → core_collections (designation: collections-like)"
            if _sl_contains_any(designation, BACKOFFICE_DESIG_TOKENS):
                return "core_fa_back_office", "Blank PROCESS + Division override → core_fa_back_office (designation: back-office-like)"
            if _sl_contains_any(designation, DS_OTHERS_DESIG_TOKENS):
                return "ds_others", "Blank PROCESS + Division override → ds_others (designation: leadership / DS others)"
            return "core_clm", "Blank PROCESS + Division override → core_clm (default CLM division bucket)"

        if "f&a" in d or "f & a" in d:
            return "core_fa_back_office", "Base Step 2 → core_fa_back_office (F&A in division)"

        if d == "collections":
            return "core_collections", "Base Step 2 → core_collections (division equals collections)"

        if jf == "call center collections":
            return "core_collections", "Base Step 3 → core_collections (JOB_FUNCTION)"
        if jf in {"customer contact center generalist", "customer service"}:
            return "core_clm", "Base Step 3 → core_clm (JOB_FUNCTION)"
        if jf == "customer contact center training / coaching":
            return "ds_training", "Base Step 3 → ds_training (JOB_FUNCTION)"

        return "unclassified", "unclassified (blank PROCESS; no division/JOB_FUNCTION match)"

    if p.startswith("delivery assurance & practices - bpm |"):
        if "quality" in p:
            return "ds_quality", "Base Step 1 → ds_quality (delivery assurance | quality)"
        if "training" in p:
            return "ds_training", "Base Step 1 → ds_training (delivery assurance | training)"
        if "wfm" in p:
            return "ds_wfm", "Base Step 1 → ds_wfm (delivery assurance | wfm)"
        return "ds_others", "Base Step 1 → ds_others (delivery assurance | other right segment)"

    if p.startswith("digital - bpm |"):
        return "ds_others", "Base Step 1 → ds_others (digital - bpm)"

    if p in {
        "clm domestic bfsi | back office",
        "clm domestic diversified | back office",
        "clm international | back office",
    }:
        return "core_clm", "Process override → core_clm (CLM | back office remap)"

    if p in {"collections | fos", "collections | telecollection"}:
        if _sl_contains_any(designation, CLM_GENERIC_DESIG_TOKENS) and not _sl_contains_any(
            designation, COLLECTIONS_DESIG_TOKENS
        ):
            return "core_clm", "Process override → core_clm (Collections | FOS/Tele + generic CLM designation)"
        return "core_collections", "Process override → core_collections (Collections | FOS/Tele)"

    if p in {
        "clm domestic bfsi | inbound",
        "clm domestic bfsi | outbound",
        "clm domestic diversified | inbound",
        "clm domestic diversified | outbound",
        "clm international | inbound",
        "clm international | outbound",
    }:
        return "core_clm", "Base Step 1 → core_clm (CLM inbound/outbound)"

    if p in {"collections", "collections | fos", "collections | telecollection"}:
        return "core_collections", "Base Step 1 → core_collections (collections PROCESS)"

    return "unclassified", f"unclassified (PROCESS did not match rules; normalized={p!r})"


def _span_service_line_key_from_row(
    process,
    division,
    job_function,
    designation="",
    account_name="",
    cost_center="",
) -> str:
    return _span_classify_service_line_row(
        process, division, job_function, designation, account_name, cost_center
    )[0]


def span_service_line_keys_series(
    process_series: pd.Series,
    division_series: pd.Series | None = None,
    job_function_series: pd.Series | None = None,
    designation_series: pd.Series | None = None,
    account_name_series: pd.Series | None = None,
    cost_center_series: pd.Series | None = None,
) -> pd.Series:
    n = len(process_series)
    idx = process_series.index

    if division_series is None:
        division_series = pd.Series([""] * n, index=idx)
    if job_function_series is None:
        job_function_series = pd.Series([""] * n, index=idx)
    if designation_series is None:
        designation_series = pd.Series([""] * n, index=idx)
    if account_name_series is None:
        account_name_series = pd.Series([""] * n, index=idx)
    if cost_center_series is None:
        cost_center_series = pd.Series([""] * n, index=idx)

    division_series = division_series.reindex(idx)
    job_function_series = job_function_series.reindex(idx)
    designation_series = designation_series.reindex(idx)
    account_name_series = account_name_series.reindex(idx)
    cost_center_series = cost_center_series.reindex(idx)

    out = pd.Series(index=idx, dtype=object)
    for i in idx:
        out.loc[i] = _span_service_line_key_from_row(
            process_series.loc[i],
            division_series.loc[i],
            job_function_series.loc[i],
            designation_series.loc[i],
            account_name_series.loc[i],
            cost_center_series.loc[i],
        )
    return out


def _span_service_line_key_and_trace_from_row(
    process,
    division,
    job_function,
    designation="",
    account_name="",
    cost_center="",
) -> tuple[str, str]:
    return _span_classify_service_line_row(
        process, division, job_function, designation, account_name, cost_center
    )


def filter_code_delivery_population(df: pd.DataFrame) -> pd.DataFrame:
    """Restrict to the population used in the Jan/Dec code-delivery pivot (optional UI path)."""
    out = df.copy()

    if "LEGAL EMPLOYER NAME" in out.columns:
        out = out[out["LEGAL EMPLOYER NAME"].astype(str).str.strip().eq("Digitide Solutions Limited")]

    if "BUSINESS UNIT" in out.columns:
        out = out[out["BUSINESS UNIT"].astype(str).str.strip().eq("BPM - Practices & Ops")]

    if "SEPARATIONS" in out.columns:
        def _sep_active(x) -> bool:
            if _span_hrms_cell_blank(x):
                return True
            s = str(x).strip().lower()
            return s in {"0", "0.0"}

        out = out[out["SEPARATIONS"].map(_sep_active)]

    if "MANPOWER" in out.columns:
        out = out[out["MANPOWER"].map(_span_hrms_cell_blank)]

    return out


def _span_normalize_bu_value(bu_val) -> str:
    """Normalize BUSINESS UNIT values for filter comparisons."""
    if bu_val is None:
        return ""
    try:
        if pd.isna(bu_val):
            return ""
    except Exception:
        pass
    return str(bu_val).strip().lower()


@st.cache_data(show_spinner=False)
def span_service_line_wide_table_cached(
    snap_key: tuple,
    bu_filter_norm_key: tuple[str, ...] = (),
    rules_version: int = _SPAN_SERVICE_LINE_RULES_VERSION,
    use_code_delivery_pivot_filter: bool = False,
) -> pd.DataFrame:
    """
    Wide table: Category, Service line, one column per snapshot (`month_short`),
    optional Δ (first → last month) for employee **row counts** in Conneqt
    (after Span exclusions: **PROCESS** must not contain substring **manpower**, any case, any position).
    For service-line tables we classify across **all business units** (not only Conneqt).
    Sub-total = sum of Core Delivery’s three lines only.

    When ``use_code_delivery_pivot_filter`` is True, rows are further restricted to the Jan/Dec pivot-style
    population (Digitide legal employer, BPM - Practices & Ops, active separations, blank MANPOWER).
    """
    month_order = [t[2] for t in snap_key]
    counts_by_month: dict[str, dict[str, int]] = {m: defaultdict(int) for m in month_order}

    for path_str, mtime, month_short, *_rest in snap_key:
        span_df, _, _, _ = span_load_all_business_units_cached(path_str, mtime)
        if span_df.empty:
            continue

        if bu_filter_norm_key and "BUSINESS UNIT" in span_df.columns:
            bu_norm = span_df["BUSINESS UNIT"].astype(str).map(_span_normalize_bu_value)
            span_df = span_df.loc[bu_norm.isin(set(bu_filter_norm_key))].copy()
            if span_df.empty:
                continue

        if use_code_delivery_pivot_filter:
            span_df = filter_code_delivery_population(span_df)
            if span_df.empty:
                continue

        proc = span_df["PROCESS"] if "PROCESS" in span_df.columns else pd.Series([""] * len(span_df), index=span_df.index)
        div = span_df["DIVISION"] if "DIVISION" in span_df.columns else None
        jf = span_df["JOB_FUNCTION"] if "JOB_FUNCTION" in span_df.columns else None
        des = span_df["DESIGNATION"] if "DESIGNATION" in span_df.columns else None
        acc = span_df["ACCOUNT NAME"] if "ACCOUNT NAME" in span_df.columns else None
        cc = span_df["COST CENTER"] if "COST CENTER" in span_df.columns else None
        keys = span_service_line_keys_series(proc, div, jf, des, acc, cc)
        for k, v in keys.value_counts().items():
            counts_by_month[month_short][str(k)] = int(v)

    rows: list[list] = []
    for cat, slabel, ikey in SPAN_SERVICE_LINE_ROW_SPEC:
        if ikey is None:
            rlist: list = [cat, slabel]
            for m in month_order:
                rlist.append(sum(counts_by_month[m].get(k, 0) for k in SPAN_SL_CORE_KEYS))
            rows.append(rlist)
        else:
            rlist = [cat, slabel]
            for m in month_order:
                rlist.append(int(counts_by_month[m].get(ikey, 0)))
            rows.append(rlist)

    cols = ["Category", "Service line", *month_order]
    out = pd.DataFrame(rows, columns=cols)
    if len(month_order) >= 2:
        first_m, last_m = month_order[0], month_order[-1]
        out[f"Δ ({first_m} → {last_m})"] = pd.to_numeric(out[last_m], errors="coerce").fillna(0) - pd.to_numeric(
            out[first_m], errors="coerce"
        ).fillna(0)
    return out


def _span_sl_row_ic_tl_m1(
    ikey: str | None,
    month_short: str,
    ic_by: dict[str, dict[str, int]],
    tl_by: dict[str, dict[str, int]],
    m1_by: dict[str, dict[str, int]],
) -> tuple[int, int, int]:
    """IC, TL, M1+ counts for one service-line spec row and one month."""
    if ikey is None:
        keys = SPAN_SL_CORE_KEYS
        ic = sum(ic_by[month_short].get(k, 0) for k in keys)
        tl = sum(tl_by[month_short].get(k, 0) for k in keys)
        m1 = sum(m1_by[month_short].get(k, 0) for k in keys)
        return ic, tl, m1
    return (
        ic_by[month_short].get(ikey, 0),
        tl_by[month_short].get(ikey, 0),
        m1_by[month_short].get(ikey, 0),
    )


@st.cache_data(show_spinner=False)
def span_service_line_span_and_role_counts_cached(
    snap_key: tuple,
    choices_key: tuple,
    bu_filter_norm_key: tuple[str, ...] = (),
    rules_version: int = _SPAN_SERVICE_LINE_RULES_VERSION,
    use_code_delivery_pivot_filter: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Per service-line row (same spec as row counts): **IC**, **TL**, **M1+** using `span_roles_cached`
    (same rules as cluster trend), and **Span = IC ÷ TL** (NaN if TL = 0).

    Same row filter as `span_service_line_wide_table_cached`: manpower exclusion on PROCESS (defense in depth),
    optional Jan/Dec pivot population filter, and extended service-line inputs (designation / account / cost center).

    Returns:
        (span_wide, role_wide)
        - span_wide: Category, Service line, one column per month (float span), optional Δ(span)
        - role_wide: Category, Service line, per month three columns ``{m}_IC``, ``{m}_TL``, ``{m}_M1+``
    """
    month_order = [t[2] for t in snap_key]
    ic_by: dict[str, dict[str, int]] = {m: defaultdict(int) for m in month_order}
    tl_by: dict[str, dict[str, int]] = {m: defaultdict(int) for m in month_order}
    m1_by: dict[str, dict[str, int]] = {m: defaultdict(int) for m in month_order}

    for path_str, mtime, month_short, *_rest in snap_key:
        span_df, _, _, _ = span_load_all_business_units_cached(path_str, mtime)
        if span_df.empty:
            continue

        if bu_filter_norm_key and "BUSINESS UNIT" in span_df.columns:
            bu_norm = span_df["BUSINESS UNIT"].astype(str).map(_span_normalize_bu_value)
            span_df = span_df.loc[bu_norm.isin(set(bu_filter_norm_key))].copy()
            if span_df.empty:
                continue

        if use_code_delivery_pivot_filter:
            span_df = filter_code_delivery_population(span_df)
            if span_df.empty:
                continue

        role_s = span_roles_all_business_units_cached(path_str, mtime, choices_key)
        if role_s.empty:
            continue

        proc = (
            span_df["PROCESS"]
            if "PROCESS" in span_df.columns
            else pd.Series([""] * len(span_df), index=span_df.index)
        )
        div = span_df["DIVISION"] if "DIVISION" in span_df.columns else None
        jf = span_df["JOB_FUNCTION"] if "JOB_FUNCTION" in span_df.columns else None
        des = span_df["DESIGNATION"] if "DESIGNATION" in span_df.columns else None
        acc = span_df["ACCOUNT NAME"] if "ACCOUNT NAME" in span_df.columns else None
        cc = span_df["COST CENTER"] if "COST CENTER" in span_df.columns else None
        keys = span_service_line_keys_series(proc, div, jf, des, acc, cc)
        tmp = pd.DataFrame(
            {
                "sl": keys.astype(str).values,
                "role": role_s.reindex(span_df.index).astype(str).values,
            },
            index=span_df.index,
        )
        vc = tmp.groupby(["sl", "role"], observed=False).size()
        for (slk, role), cnt in vc.items():
            c = int(cnt)
            if role == "IC":
                ic_by[month_short][slk] += c
            elif role == "TL":
                tl_by[month_short][slk] += c
            elif role == "M1+":
                m1_by[month_short][slk] += c

    span_rows: list[list] = []
    role_rows: list[list] = []
    for cat, slabel, ikey in SPAN_SERVICE_LINE_ROW_SPEC:
        sr = [cat, slabel]
        rr = [cat, slabel]
        for m in month_order:
            ic, tl, m1 = _span_sl_row_ic_tl_m1(ikey, m, ic_by, tl_by, m1_by)
            rr.extend([ic, tl, m1])
            sr.append(round(ic / tl, 4) if tl > 0 else np.nan)
        span_rows.append(sr)
        role_rows.append(rr)

    span_cols = ["Category", "Service line", *month_order]
    span_out = pd.DataFrame(span_rows, columns=span_cols)
    role_col_list = ["Category", "Service line"]
    for m in month_order:
        role_col_list.extend([f"{m}_IC", f"{m}_TL", f"{m}_M1+"])
    role_out = pd.DataFrame(role_rows, columns=role_col_list)

    if len(month_order) >= 2:
        first_m, last_m = month_order[0], month_order[-1]
        a = pd.to_numeric(span_out[first_m], errors="coerce")
        b = pd.to_numeric(span_out[last_m], errors="coerce")
        span_out[f"Δ span ({first_m} → {last_m})"] = b - a

    return span_out, role_out


def _span_service_line_trace_step_label(tr: str) -> str:
    """Short label from trace (e.g. ``CC override``, ``Base Step 2``) for filtering."""
    t = str(tr).strip()
    if " →" in t:
        return t.split(" →", 1)[0].strip()
    if ":" in t:
        return t.split(":", 1)[0].strip()
    return t


@st.cache_data(show_spinner=False)
def span_service_line_classified_rows_cached(
    snap_key: tuple,
    bu_filter_norm_key: tuple[str, ...] = (),
    rules_version: int = _SPAN_SERVICE_LINE_RULES_VERSION,
    use_code_delivery_pivot_filter: bool = False,
) -> pd.DataFrame:
    """
    Debug export for service-line mismatches: one row per row used in the service-line tables.
    Includes computed service_line_key and ``service_line_trace`` (CC override, blank-PROCESS overrides, etc.).
    """
    key_to_display: dict[str, tuple[str, str]] = {}
    for cat, slabel, ikey in SPAN_SERVICE_LINE_ROW_SPEC:
        if ikey is None:
            continue
        key_to_display[str(ikey)] = (cat, slabel)

    pieces: list[pd.DataFrame] = []
    for path_str, mtime, month_short, *_rest in snap_key:
        span_df, _, _, _ = span_load_all_business_units_cached(path_str, mtime)
        if span_df.empty:
            continue

        if bu_filter_norm_key and "BUSINESS UNIT" in span_df.columns:
            bu_norm = span_df["BUSINESS UNIT"].astype(str).map(_span_normalize_bu_value)
            span_df = span_df.loc[bu_norm.isin(set(bu_filter_norm_key))].copy()
            if span_df.empty:
                continue

        if use_code_delivery_pivot_filter:
            span_df = filter_code_delivery_population(span_df)
            if span_df.empty:
                continue

        n = len(span_df)
        idx = span_df.index
        # snap_key is created as: (path_str, mtime, month_short, year, month, day)
        year = int(_rest[0]) if len(_rest) >= 1 else 0
        month = int(_rest[1]) if len(_rest) >= 2 else 0
        day = int(_rest[2]) if len(_rest) >= 3 else 0
        snapshot_date = pd.Timestamp(year=int(year), month=int(month), day=int(day)) if (year and month and day) else pd.NaT

        if "EMPLOYEE ID" in span_df.columns:
            emp_arr = span_df["EMPLOYEE ID"].astype(str).values
        else:
            emp_arr = np.array([""] * n, dtype=object)

        proc_arr = span_df["PROCESS"].values if "PROCESS" in span_df.columns else np.array([""] * n, dtype=object)
        div_arr = span_df["DIVISION"].values if "DIVISION" in span_df.columns else np.array([""] * n, dtype=object)
        jf_arr = span_df["JOB_FUNCTION"].values if "JOB_FUNCTION" in span_df.columns else np.array([""] * n, dtype=object)
        des_arr = span_df["DESIGNATION"].values if "DESIGNATION" in span_df.columns else np.array([""] * n, dtype=object)
        acc_arr = span_df["ACCOUNT NAME"].values if "ACCOUNT NAME" in span_df.columns else np.array([""] * n, dtype=object)
        cc_arr = span_df["COST CENTER"].values if "COST CENTER" in span_df.columns else np.array([""] * n, dtype=object)

        keys: list[str] = []
        traces: list[str] = []
        for p, d, jf, des, acc, ccc in zip(proc_arr, div_arr, jf_arr, des_arr, acc_arr, cc_arr):
            k, tr = _span_service_line_key_and_trace_from_row(p, d, jf, des, acc, ccc)
            keys.append(str(k))
            traces.append(str(tr))

        cats: list[str] = []
        slabels: list[str] = []
        for k in keys:
            cat, sl = key_to_display.get(k, ("", ""))
            cats.append(cat)
            slabels.append(sl)

        steps = [_span_service_line_trace_step_label(tr) for tr in traces]

        out = pd.DataFrame(
            {
                "snapshot_date": [snapshot_date] * n,
                "month_short": [month_short] * n,
                "EMPLOYEE ID": emp_arr,
                "PROCESS": proc_arr,
                "DIVISION": div_arr,
                "DESIGNATION": des_arr,
                "ACCOUNT NAME": acc_arr,
                "COST CENTER": cc_arr,
                "JOB_FUNCTION": jf_arr,
                "service_line_key": keys,
                "service_line_category": cats,
                "service_line_label": slabels,
                "service_line_step": steps,
                "service_line_trace": traces,
                "classification_status": ["Unclassified" if k == "unclassified" else "Classified" for k in keys],
                "is_unclassified": [k == "unclassified" for k in keys],
                "row_in_export": list(range(n)),
            },
            index=idx,
        )
        pieces.append(out.reset_index(drop=True))

    if not pieces:
        return pd.DataFrame()
    return pd.concat(pieces, ignore_index=True)


# ============================================================
# HR FILE FOLDER SCAN / VALIDATION
# ============================================================
def _hr_folder_skip_non_snapshot_xlsx(filename: str) -> bool:
    """Excel files allowed in the HR folder alongside HRMS_YYYY_MM_DD snapshots (not validated as HR)."""
    low = filename.lower()
    if low.startswith("~$"):
        return True
    if "conneqt" in low and "cost" in low and "mapp" in low:
        return True
    if "costcode" in low.replace(" ", "") and "mapp" in low:
        return True
    return False


def scan_hr_folder(folder_path: str):
    folder = Path(folder_path)
    if not folder.exists():
        raise ValueError(f"Folder does not exist: {folder_path}")
    if not folder.is_dir():
        raise ValueError(f"Path is not a folder: {folder_path}")

    xlsx_files = sorted(folder.glob("*.xlsx"))
    if not xlsx_files:
        raise ValueError("No .xlsx files found in the folder.")

    invalid = []
    valid = []
    seen_display_labels = set()

    for f in xlsx_files:
        m = HR_FILE_RE.match(f.name)
        if not m:
            if _hr_folder_skip_non_snapshot_xlsx(f.name):
                continue
            invalid.append(f.name)
            continue

        year = int(m.group(1))
        month = int(m.group(2))
        day = int(m.group(3))
        month_key = (year, month, day)
        file_stem = f.stem  # e.g. HRMS_2026_03_14

        # Human-readable date e.g. "14th March, 2026"; keep unique if same date appears twice
        display_label = format_snapshot_date(year, month, day)
        if display_label in seen_display_labels:
            display_label = f"{display_label} – {file_stem}"
        seen_display_labels.add(display_label)

        valid.append(
            {
                "path": f,
                "year": year,
                "month": month,
                "day": day,
                "file_name": f.name,
                "month_key": month_key,
                "month_short": display_label,
                "month_label": display_label,
                "mtime": f.stat().st_mtime,
            }
        )

    if invalid:
        raise ValueError(
            "Invalid HR file name(s) found. Allowed format is exactly HRMS_YYYY_MM_DD.xlsx. "
            f"Invalid files: {invalid}"
        )

    valid = sorted(valid, key=lambda x: x["month_key"])
    if len(valid) < 2:
        raise ValueError("At least 2 valid HR files are required in the folder.")

    return valid

# ============================================================
# FILE TYPE DETECTION
# ============================================================
def _detect_file_type_from_normalized(d: pd.DataFrame) -> str:
    """Expects already normalized columns."""
    if "BUSINESS UNIT" not in d.columns:
        return "type2"
    bu = clean_text_series(d["BUSINESS UNIT"]).fillna("").str.lower().str.strip()
    c_conneqt = int((bu == "conneqt business solution").sum())
    c_digitide = int((bu == "digitide solutions limited").sum())
    if c_conneqt >= 10:
        return "type1"
    if c_digitide >= 10:
        return "type2"
    return "type2"


def detect_file_type(df_raw: pd.DataFrame) -> str:
    d = normalize_hr_cols(df_raw)
    return _detect_file_type_from_normalized(d)

# ============================================================
# BUCKETING
# ============================================================
# Consolidate support function names: Admin/Administration → one; Strategy/AI/Strategy & AI → one
# Map these variants to "Support Functions - Admin" (including common typo Adminstration)
ADMIN_BUCKET_VARIANTS_TO_COLLAPSE = {
    "support functions - administration",
    "support functions - adminstration",  # common typo (missing 'i')
}
def normalize_support_buckets(bucket: pd.Series) -> pd.Series:
    """Map support function variants to canonical names (Admin, Strategy & AI)."""
    out = bucket.copy()
    bucket_lower = out.str.strip().str.lower()
    # Administration / Adminstration → Support Functions - Admin (combine with Admin)
    admin_mask = bucket_lower.isin(ADMIN_BUCKET_VARIANTS_TO_COLLAPSE)
    out = out.mask(admin_mask, "Support Functions - Admin")
    # Strategy, AI, Strategy and AI → Strategy & AI (case-insensitive)
    strategy_ai_mask = bucket_lower.isin({
        "support functions - strategy",
        "support functions - ai",
        "support functions - strategy and ai",
    })
    out = out.mask(strategy_ai_mask, "Support Functions - Strategy & AI")
    return out


def classify_bucket_type1(df: pd.DataFrame) -> pd.Series:
    business_l = clean_text_series(df["BUSINESS"]).fillna("").str.lower().str.strip()
    bu_raw = clean_text_series(df["BUSINESS UNIT"]).fillna("")
    bu_l = bu_raw.str.lower().str.strip()

    is_conneqt = bu_l.eq("conneqt business solution")
    is_alldigi = business_l.eq(BPM_BUSINESS) & bu_l.str.contains("alldigi", na=False)
    is_techdig = bu_l.str.contains("tech & digital", na=False)
    is_cxo = bu_l.eq("cxo")

    is_support_bu = bu_l.str.startswith("support function -", na=False)
    support_suffix = bu_raw.str.replace("Support Function -", "", regex=False).str.strip()
    support_bucket_from_support = SUPPORT_PREFIX + support_suffix
    support_bucket_from_other = SUPPORT_PREFIX + bu_raw

    bucket = support_bucket_from_other
    bucket = bucket.mask(is_support_bu, support_bucket_from_support)
    bucket = bucket.mask(is_techdig, BUCKET_TECHDIG)
    bucket = bucket.mask(is_alldigi, BUCKET_ALLDIGI)
    bucket = bucket.mask(is_conneqt, BUCKET_CONNEQT)
    bucket = bucket.mask(is_cxo, BUCKET_CXO)

    return normalize_support_buckets(bucket)


def classify_bucket_type2(df: pd.DataFrame) -> pd.Series:
    business = clean_text_series(df["BUSINESS"]).fillna("")
    business_l = business.str.lower().str.strip()

    bu = clean_text_series(df["BUSINESS UNIT"]).fillna("")
    bu_l = bu.str.lower().str.strip()

    lvl_u = (
        clean_text_series(df["LEVEL"]).fillna("").str.upper().str.strip()
        if "LEVEL" in df.columns else pd.Series([""] * len(df), index=df.index)
    )
    des_u = (
        clean_text_series(df["DESIGNATION"]).fillna("").str.upper().str.strip()
        if "DESIGNATION" in df.columns else pd.Series([""] * len(df), index=df.index)
    )
    grd_u = (
        clean_text_series(df["GRADE"]).fillna("").str.upper().str.strip()
        if "GRADE" in df.columns else pd.Series([""] * len(df), index=df.index)
    )

    cxo_tokens = set(CXO_CODES_TYPE2) | {"CEO"}
    is_cxo = lvl_u.isin(cxo_tokens) | des_u.isin(cxo_tokens) | grd_u.isin(cxo_tokens)

    bucket = SUPPORT_PREFIX + business

    is_techdig = business_l.isin(TECH_DIGITAL_BUSINESS)
    is_alldigi = business_l.eq(BPM_BUSINESS) & bu_l.str.contains("alldigi", na=False)
    is_conneqt = business_l.isin({BPM_BUSINESS, VERTICAL_BUSINESS}) & bu_l.eq("digitide solutions limited")

    bucket = bucket.mask(is_techdig, BUCKET_TECHDIG)
    bucket = bucket.mask(is_alldigi, BUCKET_ALLDIGI)
    bucket = bucket.mask(is_conneqt, BUCKET_CONNEQT)
    bucket = bucket.mask(is_cxo, BUCKET_CXO)

    is_hr = business_l.isin(HR_BUSINESS)
    bucket = bucket.mask(
        is_hr & (~bucket.isin([BUCKET_CONNEQT, BUCKET_ALLDIGI, BUCKET_TECHDIG, BUCKET_CXO])),
        SUPPORT_PREFIX + "HR"
    )
    return normalize_support_buckets(bucket)


# ============================================================
# SNAPSHOT PREP
# ============================================================
def prepare_hr_snapshot(df_raw: pd.DataFrame, *, is_previous: bool) -> tuple[pd.DataFrame, pd.Series, str]:
    df = normalize_hr_cols(df_raw)
    file_type = _detect_file_type_from_normalized(df)
    ensure_cols(df, HR_MANDATORY_STD, "Previous HR" if is_previous else "Current HR")

    if "SEPARATION" in df.columns:
        sep_raw = clean_text_series(df["SEPARATION"]).fillna("").astype(str).str.strip().str.lower()
        sep_num = pd.to_numeric(sep_raw, errors="coerce")
        is_one = (sep_num.eq(1) | sep_raw.eq("1")).fillna(False)
        df = df[~is_one].copy()

    df["BUSINESS UNIT"] = clean_text_series(df["BUSINESS UNIT"])
    df = df[df["BUSINESS UNIT"].notna()].copy()

    # Strictly only consider employees with EMPLOYEE_TYPE = C or E (case-insensitive)
    if "EMPLOYEE TYPE" in df.columns:
        emp_type = df["EMPLOYEE TYPE"].astype(str).str.strip().str.upper()
        df = df[emp_type.isin({"C", "E"})].copy()

    df["EMPLOYEE ID"] = df["EMPLOYEE ID"].map(to_id_string)
    df = df[df["EMPLOYEE ID"].notna()].copy()

    df["BUSINESS"] = clean_text_series(df["BUSINESS"]).fillna("")
    df = df.drop_duplicates(subset=["EMPLOYEE ID"], keep="first").copy()

    if file_type == "type1":
        df["BUCKET"] = classify_bucket_type1(df)
    else:
        df["BUCKET"] = classify_bucket_type2(df)

    counts = df.groupby("BUCKET")["EMPLOYEE ID"].nunique()
    return df, counts, file_type

@st.cache_data(show_spinner=False)
def load_snapshot_from_path(path, is_previous: bool, mtime: float):
    raw = get_raw_hr(str(path), mtime)
    return prepare_hr_snapshot(raw, is_previous=is_previous)

# ============================================================
# TABLE BUILDERS
# ============================================================
def build_hier_table(prev_counts: pd.Series, curr_counts: pd.Series, prev_label: str, curr_label: str) -> pd.DataFrame:
    all_buckets = sorted(set(prev_counts.index).union(set(curr_counts.index)))

    delivery_children = [BUCKET_CONNEQT, BUCKET_ALLDIGI, BUCKET_TECHDIG]
    support_children = [b for b in all_buckets if b not in delivery_children and b != BUCKET_CXO]

    support_sorted = []
    if SUPPORT_PREFIX + "HR" in support_children:
        support_sorted.append(SUPPORT_PREFIX + "HR")
    support_sorted.extend(sorted([b for b in support_children if b != SUPPORT_PREFIX + "HR"]))

    def get_count(series: pd.Series, key: str) -> int:
        return int(series.get(key, 0))

    rows = []
    prev_total = int(prev_counts.sum())
    curr_total = int(curr_counts.sum())
    rows.append(("Grand total", prev_total, curr_total, "grand"))

    prev_delivery = sum(get_count(prev_counts, k) for k in delivery_children)
    curr_delivery = sum(get_count(curr_counts, k) for k in delivery_children)
    rows.append(("Delivery", prev_delivery, curr_delivery, "header"))

    for child in delivery_children:
        rows.append((f"  {child}", get_count(prev_counts, child), get_count(curr_counts, child), "child"))

    rows.append((BUCKET_CXO, get_count(prev_counts, BUCKET_CXO), get_count(curr_counts, BUCKET_CXO), "header"))

    prev_support = prev_total - prev_delivery - get_count(prev_counts, BUCKET_CXO)
    curr_support = curr_total - curr_delivery - get_count(curr_counts, BUCKET_CXO)
    rows.append(("Support Functions", prev_support, curr_support, "header"))

    for child in support_sorted:
        rows.append((f"  {child}", get_count(prev_counts, child), get_count(curr_counts, child), "child"))

    out = pd.DataFrame(rows, columns=["Headcount", prev_label, curr_label, "_rowtype"])
    out["Abs change"] = out[curr_label] - out[prev_label]
    out["% change"] = np.where(
        out[prev_label] == 0,
        np.where(out[curr_label] == 0, 0.0, 1.0),
        out["Abs change"] / out[prev_label],
    )
    return out

def build_reconciliation_table(
    base_counts: pd.Series,
    spartan_counts: pd.Series,
    bau_counts: pd.Series,
    hire_counts: pd.Series,
    end_counts: pd.Series,
    base_label: str,
    spartan_label: str,
    bau_label: str,
    hire_label: str,
    end_label: str,
) -> pd.DataFrame:
    all_buckets = sorted(
        set(base_counts.index)
        .union(set(spartan_counts.index))
        .union(set(bau_counts.index))
        .union(set(hire_counts.index))
        .union(set(end_counts.index))
    )

    delivery_children = [BUCKET_CONNEQT, BUCKET_ALLDIGI, BUCKET_TECHDIG]
    support_children = [b for b in all_buckets if b not in delivery_children and b != BUCKET_CXO]

    support_sorted = []
    if SUPPORT_PREFIX + "HR" in support_children:
        support_sorted.append(SUPPORT_PREFIX + "HR")
    support_sorted.extend(sorted([b for b in support_children if b != SUPPORT_PREFIX + "HR"]))

    def get_count(series: pd.Series, key: str) -> int:
        return int(series.get(key, 0))

    rows = []

    def add_row(label: str, key: str | None, rowtype: str):
        if key is None:
            b = int(base_counts.sum())
            s = int(spartan_counts.sum())
            a = int(bau_counts.sum())
            h = int(hire_counts.sum())
            e = int(end_counts.sum())
        elif key == "DELIVERY_TOTAL":
            b = sum(get_count(base_counts, k) for k in delivery_children)
            s = sum(get_count(spartan_counts, k) for k in delivery_children)
            a = sum(get_count(bau_counts, k) for k in delivery_children)
            h = sum(get_count(hire_counts, k) for k in delivery_children)
            e = sum(get_count(end_counts, k) for k in delivery_children)
        elif key == "SUPPORT_TOTAL":
            b = int(base_counts.sum()) - sum(get_count(base_counts, k) for k in delivery_children) - get_count(base_counts, BUCKET_CXO)
            s = int(spartan_counts.sum()) - sum(get_count(spartan_counts, k) for k in delivery_children) - get_count(spartan_counts, BUCKET_CXO)
            a = int(bau_counts.sum()) - sum(get_count(bau_counts, k) for k in delivery_children) - get_count(bau_counts, BUCKET_CXO)
            h = int(hire_counts.sum()) - sum(get_count(hire_counts, k) for k in delivery_children) - get_count(hire_counts, BUCKET_CXO)
            e = int(end_counts.sum()) - sum(get_count(end_counts, k) for k in delivery_children) - get_count(end_counts, BUCKET_CXO)
        else:
            b = get_count(base_counts, key)
            s = get_count(spartan_counts, key)
            a = get_count(bau_counts, key)
            h = get_count(hire_counts, key)
            e = get_count(end_counts, key)

        abs_change = e - b
        pct_change = 0.0 if b == 0 and e == 0 else (1.0 if b == 0 else abs_change / b)
        rows.append((label, b, s, a, h, e, abs_change, pct_change, rowtype))

    add_row("Grand total", None, "grand")
    add_row("Delivery", "DELIVERY_TOTAL", "header")
    for child in delivery_children:
        add_row(child, child, "child")

    add_row(BUCKET_CXO, BUCKET_CXO, "header")
    add_row("Support Functions", "SUPPORT_TOTAL", "header")
    for child in support_sorted:
        add_row(child, child, "child")

    out = pd.DataFrame(
        rows,
        columns=["Headcount", base_label, spartan_label, bau_label, hire_label, end_label, "Abs. change", "% change", "_rowtype"]
    )
    return out

def make_plotly_table(df: pd.DataFrame) -> go.Figure:
    display_df = df.copy()
    raw_pct = df["% change"].tolist()
    display_df["% change"] = (display_df["% change"] * 100.0).round(1).astype(str) + "%"

    cols = [c for c in display_df.columns if c != "_rowtype"]
    values = [display_df[c].tolist() for c in cols]
    rowtype = display_df["_rowtype"].tolist()

    fill = []
    for rt in rowtype:
        if rt == "grand":
            fill.append("#D6ECF3")
        elif rt == "header":
            fill.append("#F6E7B2")
        else:
            fill.append("white")

    abs_vals = df["Abs. change"].tolist() if "Abs. change" in df.columns else df["Abs change"].tolist()

    font_colors = []
    for c in cols:
        if c in ("Abs. change", "Abs change", "% change"):
            col_colors = []
            for i, rt in enumerate(rowtype):
                if rt in ("grand", "header"):
                    col_colors.append("#111827")
                    continue
                v = abs_vals[i] if c in ("Abs. change", "Abs change") else raw_pct[i]
                if v > 0:
                    col_colors.append("#DC2626")
                elif v < 0:
                    col_colors.append("#16A34A")
                else:
                    col_colors.append("#111827")
            font_colors.append(col_colors)
        else:
            font_colors.append(["#111827"] * len(display_df))

    col_widths = [190]
    for c in cols[1:]:
        if c in ("Abs. change", "Abs change"):
            col_widths.append(85)
        elif c == "% change":
            col_widths.append(80)
        else:
            col_widths.append(100)

    fig = go.Figure(
        data=[
            go.Table(
                columnwidth=col_widths,
                header=dict(
                    values=cols,
                    fill_color="#5A002F",
                    font=dict(color="white", size=18),
                    align=["left"] + ["right"] * (len(cols) - 1),
                    height=44,
                ),
                cells=dict(
                    values=values,
                    fill_color=[fill] * len(cols),
                    font=dict(color=font_colors, size=17),
                    align=["left"] + ["right"] * (len(cols) - 1),
                    height=36,
                ),
            )
        ]
    )
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=max(520, 48 + 38 * len(display_df)))
    return fig


# ============================================================
# RECON HELPERS
# ============================================================
def counts_from_ids(df: pd.DataFrame, ids: set[str]) -> pd.Series:
    if not ids:
        return pd.Series(dtype="int64")
    return df[df["EMPLOYEE ID"].astype(str).isin(ids)].groupby("BUCKET")["EMPLOYEE ID"].nunique()

def expand_bucket_selection(label: str, all_buckets: list[str]) -> list[str]:
    """Expand a displayed row label (e.g. Delivery) into underlying bucket names."""
    delivery_children = [BUCKET_CONNEQT, BUCKET_ALLDIGI, BUCKET_TECHDIG]
    lab = str(label).strip()
    if lab.lower() == "grand total":
        return list(all_buckets)
    if lab.lower() == "delivery":
        return [b for b in delivery_children if b in all_buckets]
    if lab == BUCKET_CXO:
        return [BUCKET_CXO] if BUCKET_CXO in all_buckets else []
    if lab.lower() == "support functions":
        return [b for b in all_buckets if b not in delivery_children and b != BUCKET_CXO]
    # Child rows may be indented (e.g. "  Conneqt Business Solution")
    if lab in all_buckets:
        return [lab]
    return [lab] if lab else []

def people_for_ids_and_buckets(df: pd.DataFrame, ids: set[str], buckets: list[str]) -> pd.DataFrame:
    """Return rows for the given ids and buckets."""
    if df is None or df.empty:
        return pd.DataFrame()
    if not ids:
        return pd.DataFrame(columns=df.columns)
    out = df[df["EMPLOYEE ID"].astype(str).isin(ids)].copy()
    if "BUCKET" in out.columns and buckets:
        out = out[out["BUCKET"].astype(str).isin(buckets)].copy()
    return out


def _selection_get(sel, key, default=None):
    if sel is None:
        return default
    if isinstance(sel, dict):
        return sel.get(key, default)
    return getattr(sel, key, default)


def dataframe_cell_selection(event, df: pd.DataFrame) -> tuple[int | None, str | None]:
    """Return (row_index, column_name) from st.dataframe single-cell selection, or (None, None)."""
    sel = getattr(event, "selection", None)
    if sel is None and isinstance(event, dict):
        sel = event.get("selection")
    if sel is None:
        return None, None

    # single-cell mode often fills `cells` only; rows/columns may be empty
    cells = _selection_get(sel, "cells") or []
    if cells:
        try:
            first = cells[0]
            if isinstance(first, dict):
                ri = first.get("row", first.get("Row"))
                cname = first.get("column", first.get("Column", first.get("col")))
            elif isinstance(first, (list, tuple)) and len(first) >= 2:
                ri, cname = first[0], first[1]
            else:
                ri, cname = None, None
            if ri is not None and cname is not None:
                ri = int(ri)
                cname = str(cname)
                if 0 <= ri < len(df):
                    if cname in df.columns:
                        return ri, cname
                    try:
                        ci = int(cname)
                        if 0 <= ci < len(df.columns):
                            return ri, str(df.columns[ci])
                    except (TypeError, ValueError):
                        pass
        except (TypeError, ValueError, IndexError, KeyError):
            pass

    rows = _selection_get(sel, "rows") or []
    cols = _selection_get(sel, "columns") or []
    if not rows or not cols:
        return None, None
    try:
        ri = int(rows[0])
        if not (0 <= ri < len(df)):
            return None, None
        c0 = cols[0]
        if isinstance(c0, str) and c0 in df.columns:
            return ri, c0
        ci = int(c0)
        if 0 <= ci < len(df.columns):
            return ri, str(df.columns[ci])
    except (TypeError, ValueError, IndexError):
        pass
    return None, None


def build_metric_trend(hr_files):
    rows = []
    for meta in hr_files:
        _, counts, _ = load_snapshot_from_path(meta["path"], False, meta["mtime"])
        total = int(counts.sum())
        delivery = int(
            counts.get(BUCKET_CONNEQT, 0)
            + counts.get(BUCKET_ALLDIGI, 0)
            + counts.get(BUCKET_TECHDIG, 0)
        )
        cxo = int(counts.get(BUCKET_CXO, 0))
        support = total - delivery - cxo
        rows.append(
            {
                "Month": meta["month_short"],
                "Total headcount": total,
                "Delivery": delivery,
                "Support Functions": support,
                "CXO": cxo,
            }
        )
    return pd.DataFrame(rows)

def make_trend_chart(chart_df: pd.DataFrame, metric_choice: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=chart_df["Month"],
            y=chart_df[metric_choice],
            mode="lines+markers+text",
            text=chart_df[metric_choice].map(lambda x: f"{int(x):,}"),
            textposition="top center",
            hovertemplate="<b>%{x}</b><br>" + metric_choice + ": %{y:,}<extra></extra>",
            line=dict(width=3),
            marker=dict(size=11),
            name=metric_choice,
        )
    )
    fig.update_layout(
        title=dict(text=f"{metric_choice} trend", font=dict(size=20)),
        xaxis_title="Month",
        yaxis_title=metric_choice,
        margin=dict(l=20, r=20, t=60, b=20),
        height=460,
        hovermode="x unified",
        font=dict(size=17),
    )
    fig.update_yaxes(tickformat=",", separatethousands=True)
    return fig

# ============================================================
# SESSION STATE
# ============================================================
if "run_dashboard" not in st.session_state:
    st.session_state["run_dashboard"] = False

if "overview_cache_key" not in st.session_state:
    st.session_state["overview_cache_key"] = None

if "overview_rows" not in st.session_state:
    st.session_state["overview_rows"] = []

if "pair_tables" not in st.session_state:
    st.session_state["pair_tables"] = {}

if "all_pair_tables_cache_key" not in st.session_state:
    st.session_state["all_pair_tables_cache_key"] = None

if "all_pair_tables" not in st.session_state:
    st.session_state["all_pair_tables"] = {}

if "reconciliation_cache_key" not in st.session_state:
    st.session_state["reconciliation_cache_key"] = None

if "reconciliation_results" not in st.session_state:
    st.session_state["reconciliation_results"] = {}

if "spartan_cache_key" not in st.session_state:
    st.session_state["spartan_cache_key"] = None

if "spartan_results" not in st.session_state:
    st.session_state["spartan_results"] = {}

if "validation_cache_key" not in st.session_state:
    st.session_state["validation_cache_key"] = None

if "spartan_session_key" not in st.session_state:
    st.session_state["spartan_session_key"] = None

if "payroll_session_key" not in st.session_state:
    st.session_state["payroll_session_key"] = None

# ============================================================
# UI
# ============================================================
st.title("Headcount Dashboard")

# Animated loading strip (cleared when run completes)
_loading_placeholder = st.empty()

with st.sidebar:
    st.header("HR folder")
    hr_folder = st.text_input(
        "Folder path containing monthly HR files",
        value=r"C:\Users\Singh2 Mayank\OneDrive - The Boston Consulting Group, Inc\Desktop\HRMS_FOLDER",
        help="Allowed HR file format: HRMS_YYYY_MM_DD.xlsx"
    )
    c_refresh1, c_refresh2 = st.columns([1, 1])
    with c_refresh1:
        if st.button("Refresh data now", use_container_width=True, key="refresh_data_now"):
            try:
                get_raw_hr.clear()
            except Exception:
                try:
                    st.cache_data.clear()
                except Exception:
                    pass
            st.rerun()
    with c_refresh2:
        st.caption("Use after saving HRMS files")

    st.divider()
    st.header("D2 Spartan (optional)")
    spartan_file = st.file_uploader("Upload D2 Spartan Excel", type=["xlsx"], key="spartan")

    st.divider()
    st.header("Payroll cross-check (optional)")
    payroll_file = st.file_uploader("Upload Payroll Excel", type=["xlsx"], key="payroll")
    payroll_cycle_start = st.date_input("Payroll cycle start date", value=date.today().replace(day=1), key="pay_cycle_start")
    payroll_cycle_end = st.date_input("Payroll cycle end date", value=date.today(), key="pay_cycle_end")

    st.divider()
    generate = st.button("Generate", type="primary", use_container_width=True)

    if generate:
        st.session_state["run_dashboard"] = True

if not st.session_state["run_dashboard"]:
    st.info("Enter the HR folder path and click **Generate**.")
    st.stop()

if payroll_cycle_end < payroll_cycle_start:
    st.error("Payroll cycle end date cannot be before payroll cycle start date.")
    st.stop()

try:
    hr_files = scan_hr_folder(hr_folder)
except Exception as e:
    st.error(str(e))
    st.stop()

# Show engaging loading animation while code runs
_loading_placeholder.markdown(
    """
    <div class="loading-animation-wrap">
        <div class="loading-shimmer"></div>
        <p class="loading-dots">Preparing your dashboard<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span></p>
    </div>
    <style>
        .loading-animation-wrap { margin: 0.5rem 0 1rem 0; }
        .loading-shimmer {
            height: 4px;
            border-radius: 2px;
            background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 25%, #06b6d4 50%, #8b5cf6 75%, #3b82f6 100%);
            background-size: 200% 100%;
            animation: shimmer 2s ease-in-out infinite;
        }
        @keyframes shimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        .loading-dots { font-size: 1rem; color: #64748b; margin-top: 0.5rem; font-weight: 500; }
        .loading-dots .dot { animation: blink 1.4s infinite both; }
        .loading-dots .dot:nth-of-type(1) { animation-delay: 0s; }
        .loading-dots .dot:nth-of-type(2) { animation-delay: 0.2s; }
        .loading-dots .dot:nth-of-type(3) { animation-delay: 0.4s; }
        @keyframes blink { 0%, 80% { opacity: 0; } 40% { opacity: 1; } }
    </style>
    """,
    unsafe_allow_html=True,
)
progress_bar = st.progress(0, text="Scanning folder…")
progress_bar.progress(0.05, text="Folder scanned. Loading HR files in parallel…")

# Preload all raw HR Excel files in parallel first (biggest speedup: I/O in parallel)
def _preload_raw_hr(item):
    get_raw_hr(str(item["path"]), item["mtime"])
    return item["file_name"]

with ThreadPoolExecutor(max_workers=6) as executor:
    futures = [executor.submit(_preload_raw_hr, item) for item in hr_files]
    for _ in as_completed(futures):
        pass  # wait for all; cache is populated

progress_bar.progress(0.08, text="HR files loaded. Validating…")

# Only re-validate when the folder/files change (skip on dropdown-only reruns).
# get_raw_hr is now cache-hit from preload; validation only does normalize + ensure_cols.
validation_cache_key = tuple((x["file_name"], x["mtime"]) for x in hr_files)
if st.session_state["validation_cache_key"] != validation_cache_key:
    validation_errors = []
    for item in hr_files:
        try:
            raw = get_raw_hr(str(item["path"]), item["mtime"])
            normalized = normalize_hr_cols(raw)
            ensure_cols(normalized, HR_MANDATORY_STD, item["file_name"])
        except Exception as e:
            validation_errors.append(f"{item['file_name']}: {e}")

    if validation_errors:
        progress_bar.progress(0.08, text="Validation failed.")
        st.error("HR file validation failed:\n\n" + "\n".join(validation_errors))
        st.stop()
    st.session_state["validation_cache_key"] = validation_cache_key

progress_bar.progress(0.10, text="Validation done. Processing Spartan (if any)…")

# ============================================================
# OPTIONAL SPARTAN PREPROCESSING (cached per file so dropdown changes don't rerun it)
# ============================================================
spartan_df = None
spartan_report = None
spartan_active_ids = set()

if spartan_file is not None:
    spartan_session_key = (spartan_file.name, spartan_file.size)
    if (
        st.session_state["spartan_session_key"] == spartan_session_key
        and st.session_state.get("_spartan_df") is not None
    ):
        spartan_df = st.session_state["_spartan_df"]
        spartan_report = st.session_state["_spartan_report"]
        spartan_active_ids = st.session_state["_spartan_active_ids"]
    else:
        try:
            sp_raw, sp_sheet, sp_header = read_spartan_auto(spartan_file)
            spartan_df = normalize_spartan_cols(sp_raw.dropna(how="all"))

            if "EMPLOYEE ID" not in spartan_df.columns:
                progress_bar.progress(0.12, text="Spartan processing failed.")
                st.error(
                    f"D2 Spartan missing Employee ID column. "
                    f"Found: {list(spartan_df.columns)}. Sheet: {sp_sheet}, header row: {sp_header + 1}"
                )
                st.stop()

            spartan_df["EMPLOYEE ID"] = spartan_df["EMPLOYEE ID"].map(to_id_string)
            spartan_df = spartan_df[spartan_df["EMPLOYEE ID"].notna()].copy()

            if "SPARTAN CATEGORY" in spartan_df.columns:
                spartan_df["SPARTAN CATEGORY"] = clean_text_series(spartan_df["SPARTAN CATEGORY"]).fillna("")
            if "LWD" in spartan_df.columns:
                spartan_df["LWD"] = pd.to_datetime(spartan_df["LWD"], errors="coerce")
            else:
                spartan_df["LWD"] = pd.NaT

            if "D3" in spartan_df.columns:
                d3_raw = clean_text_series(spartan_df["D3"]).fillna("").astype(str).str.strip().str.lower()
                d3_num = pd.to_numeric(d3_raw, errors="coerce")
                d3_is_one = (d3_num.eq(1) | d3_raw.eq("1")).fillna(False)
                spartan_df = spartan_df[d3_is_one].copy()

            spartan_active_ids = set(spartan_df["EMPLOYEE ID"].astype(str))
            spartan_report = {"sheet_used": sp_sheet, "header_row": sp_header + 1}
            st.session_state["spartan_session_key"] = spartan_session_key
            st.session_state["_spartan_df"] = spartan_df
            st.session_state["_spartan_report"] = spartan_report
            st.session_state["_spartan_active_ids"] = spartan_active_ids
        except Exception as e:
            progress_bar.progress(0.12, text="Spartan processing failed.")
            st.exception(e)
            st.stop()
else:
    st.session_state["spartan_session_key"] = None
    st.session_state["_spartan_df"] = None
    st.session_state["_spartan_report"] = None
    st.session_state["_spartan_active_ids"] = None

progress_bar.progress(0.15, text="Building overview & trend…")

# ============================================================
# OVERVIEW BUILD
# ============================================================
overview_cache_key = tuple((x["file_name"], x["mtime"]) for x in hr_files)

if st.session_state["overview_cache_key"] != overview_cache_key:
    overview_rows = []
    pair_tables = {}

    try:
        for i in range(len(hr_files) - 1):
            base_meta = hr_files[i]
            end_meta = hr_files[i + 1]

            base_df, base_counts, _ = load_snapshot_from_path(base_meta["path"], True, base_meta["mtime"])
            end_df, end_counts, _ = load_snapshot_from_path(end_meta["path"], False, end_meta["mtime"])

            base_label = base_meta["month_label"]
            end_label = end_meta["month_label"]

            pair_key = f"{base_meta['month_short']} → {end_meta['month_short']}"
            table = build_hier_table(base_counts, end_counts, base_label, end_label)
            pair_tables[pair_key] = table

            def v(label: str, col: str):
                return int(table.loc[table["Headcount"] == label, col].iloc[0])

            base_total = v("Grand total", base_label)
            end_total = v("Grand total", end_label)
            delivery_base = v("Delivery", base_label)
            delivery_end = v("Delivery", end_label)
            cxo_base = v(BUCKET_CXO, base_label)
            cxo_end = v(BUCKET_CXO, end_label)
            support_base = v("Support Functions", base_label)
            support_end = v("Support Functions", end_label)

            # % change for Delivery, CXO, Support (undefined when base is 0)
            pct_delivery = (delivery_end - delivery_base) / delivery_base if delivery_base else None
            pct_cxo = (cxo_end - cxo_base) / cxo_base if cxo_base else None
            pct_support = (support_end - support_base) / support_base if support_base else None

            overview_rows.append(
                {
                    "Start month": base_meta["month_short"],
                    "End month": end_meta["month_short"],
                    "Start HC": base_total,
                    "End HC": end_total,
                    "Abs change": end_total - base_total,
                    "% change": 0.0 if base_total == 0 else (end_total - base_total) / base_total,
                    "% change in Delivery": pct_delivery,
                    "% change in CXOs": pct_cxo,
                    "% change in Support Functions": pct_support,
                }
            )
    except Exception as e:
        progress_bar.progress(0.35, text="Overview build failed.")
        st.exception(e)
        st.stop()

    st.session_state["overview_rows"] = overview_rows
    st.session_state["pair_tables"] = pair_tables
    st.session_state["overview_cache_key"] = overview_cache_key

progress_bar.progress(0.38, text="Overview done. Loading trend data…")

overview_rows = st.session_state["overview_rows"]
pair_tables = st.session_state["pair_tables"]

overview_df = pd.DataFrame(overview_rows)
if not overview_df.empty:
    # Format % columns: show "x.x%" or "--" when undefined
    def format_pct_or_dash(val):
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "--"
        try:
            v = float(val) * 100
            return f"{v:.1f}%"
        except (TypeError, ValueError):
            return "--"

    overview_df["% change"] = overview_df["% change"].apply(format_pct_or_dash)
    overview_df["% change in Delivery"] = overview_df["% change in Delivery"].apply(format_pct_or_dash)
    overview_df["% change in CXOs"] = overview_df["% change in CXOs"].apply(format_pct_or_dash)
    overview_df["% change in Support Functions"] = overview_df["% change in Support Functions"].apply(format_pct_or_dash)
    # Replace NaN in numeric columns with "--"
    for col in ["Start HC", "End HC", "Abs change"]:
        overview_df[col] = overview_df[col].apply(lambda x: "--" if pd.isna(x) else x)

# Build trend once per HR folder; reuse when only dropdowns change
if st.session_state.get("trend_df_cache_key") != overview_cache_key:
    st.session_state["trend_df"] = build_metric_trend(hr_files)
    st.session_state["trend_df_cache_key"] = overview_cache_key
trend_df = st.session_state["trend_df"]

progress_bar.progress(0.48, text="Building pair preview tables…")

# ============================================================
# PRECOMPUTE ALL MONTH-PAIR PREVIEW TABLES FOR TAB 1
# ============================================================
all_pair_tables_cache_key = tuple((x["file_name"], x["mtime"]) for x in hr_files)

if st.session_state["all_pair_tables_cache_key"] != all_pair_tables_cache_key:
    all_pair_tables = {}

    for i in range(len(hr_files)):
        for j in range(i + 1, len(hr_files)):
            start_meta = hr_files[i]
            end_meta = hr_files[j]

            start_df, start_counts, _ = load_snapshot_from_path(start_meta["path"], True, start_meta["mtime"])
            end_df, end_counts, _ = load_snapshot_from_path(end_meta["path"], False, end_meta["mtime"])

            start_label = start_meta["month_label"]
            end_label = end_meta["month_label"]

            preview_table = build_hier_table(start_counts, end_counts, start_label, end_label)

            all_pair_tables[(start_meta["month_short"], end_meta["month_short"])] = {
                "start_meta": start_meta,
                "end_meta": end_meta,
                "table": preview_table,
            }

    st.session_state["all_pair_tables"] = all_pair_tables
    st.session_state["all_pair_tables_cache_key"] = all_pair_tables_cache_key

all_pair_tables = st.session_state["all_pair_tables"]

progress_bar.progress(0.62, text="Building reconciliation tables…")

# ============================================================
# PRECOMPUTE RECONCILIATION RESULTS FOR ALL MONTH PAIRS
# ============================================================
spartan_signature = (
    tuple((x["file_name"], x["mtime"]) for x in hr_files),
    len(spartan_active_ids),
)

if st.session_state["reconciliation_cache_key"] != spartan_signature:
    reconciliation_results = {}

    for i in range(len(hr_files)):
        for j in range(i + 1, len(hr_files)):
            base_meta_i = hr_files[i]
            end_meta_j = hr_files[j]

            base_df_i, _, _ = load_snapshot_from_path(base_meta_i["path"], True, base_meta_i["mtime"])
            end_df_j, _, _ = load_snapshot_from_path(end_meta_j["path"], False, end_meta_j["mtime"])

            base_ids_i = set(base_df_i["EMPLOYEE ID"].astype(str))
            end_ids_j = set(end_df_j["EMPLOYEE ID"].astype(str))

            sep_only_ids = base_ids_i - end_ids_j
            spartan_exit_ids = sep_only_ids & spartan_active_ids
            bau_attrition_ids = sep_only_ids - spartan_exit_ids
            new_hire_ids = end_ids_j - base_ids_i

            base_counts_rec = base_df_i.groupby("BUCKET")["EMPLOYEE ID"].nunique()
            spartan_counts = counts_from_ids(base_df_i, spartan_exit_ids)
            bau_counts = counts_from_ids(base_df_i, bau_attrition_ids)
            hire_counts = counts_from_ids(end_df_j, new_hire_ids)
            end_counts_rec = end_df_j.groupby("BUCKET")["EMPLOYEE ID"].nunique()

            rec_table = build_reconciliation_table(
                base_counts=base_counts_rec,
                spartan_counts=spartan_counts,
                bau_counts=bau_counts,
                hire_counts=hire_counts,
                end_counts=end_counts_rec,
                base_label=f"{base_meta_i['month_label']} (Baseline)",
                spartan_label=f"-Spartan exits till {end_meta_j['month_label']}",
                bau_label="-BAU attrition",
                hire_label="-New hires",
                end_label=f"{end_meta_j['month_label']} (End-point)",
            )

            reconciliation_results[(base_meta_i["month_short"], end_meta_j["month_short"])] = {
                "base_meta": base_meta_i,
                "end_meta": end_meta_j,
                "base_df": base_df_i,
                "end_df": end_df_j,
                "base_ids": base_ids_i,
                "end_ids": end_ids_j,
                "spartan_exit_ids": spartan_exit_ids,
                "bau_attrition_ids": bau_attrition_ids,
                "new_hire_ids": new_hire_ids,
                "rec_table": rec_table,
            }

    st.session_state["reconciliation_results"] = reconciliation_results
    st.session_state["reconciliation_cache_key"] = spartan_signature

reconciliation_results = st.session_state["reconciliation_results"]

progress_bar.progress(0.80, text="Building Spartan / HRMS checks…")

# ============================================================
# PRECOMPUTE SPARTAN TAB RESULTS FOR ALL MONTH PAIRS
# ============================================================
if st.session_state["spartan_cache_key"] != spartan_signature:
    spartan_results = {}

    for i in range(len(hr_files)):
        for j in range(i + 1, len(hr_files)):
            base_meta_i = hr_files[i]
            end_meta_j = hr_files[j]

            base_df_i, _, _ = load_snapshot_from_path(base_meta_i["path"], True, base_meta_i["mtime"])
            end_df_j, _, _ = load_snapshot_from_path(end_meta_j["path"], False, end_meta_j["mtime"])

            base_ids_i = set(base_df_i["EMPLOYEE ID"].astype(str))
            end_ids_j = set(end_df_j["EMPLOYEE ID"].astype(str))
            hrms_ids_j = set(end_df_j["EMPLOYEE ID"].dropna().astype(str))
            end_date_j = date(end_meta_j["year"], end_meta_j["month"], end_meta_j["day"])

            sep_only_ids = base_ids_i - end_ids_j
            spartan_exit_ids = sep_only_ids & spartan_active_ids
            bau_attrition_ids = sep_only_ids - spartan_exit_ids
            new_hire_ids = end_ids_j - base_ids_i

            result = {
                "base_meta": base_meta_i,
                "end_meta": end_meta_j,
                "base_df": base_df_i,
                "end_df": end_df_j,
                "base_ids": base_ids_i,
                "end_ids": end_ids_j,
                "end_date": end_date_j,
                "spartan_exit_ids": spartan_exit_ids,
                "bau_attrition_ids": bau_attrition_ids,
                "new_hire_ids": new_hire_ids,
                "sp1": pd.DataFrame(),
                "offenders_hrms": pd.DataFrame(),
                "sp2": pd.DataFrame(),
                "overdue_spartan": pd.DataFrame(),
            }

            if spartan_df is not None:
                sp1 = spartan_df.copy()
                sp1["Exists in current HRMS?"] = sp1["EMPLOYEE ID"].astype(str).isin(hrms_ids_j)
                offenders_hrms = sp1[sp1["Exists in current HRMS?"]].copy()

                if "SPARTAN CATEGORY" in sp1.columns:
                    pending = sp1["SPARTAN CATEGORY"].str.lower().str.strip().eq("closed - lwd yet to be completed")
                    sp2 = sp1[pending].copy()
                    sp2["LWD before current snapshot?"] = sp2["LWD"].notna() & (sp2["LWD"].dt.date < end_date_j)
                    overdue_spartan = sp2[sp2["LWD before current snapshot?"]].copy()
                else:
                    sp2 = pd.DataFrame()
                    overdue_spartan = pd.DataFrame()

                result.update(
                    {
                        "sp1": sp1,
                        "offenders_hrms": offenders_hrms,
                        "sp2": sp2,
                        "overdue_spartan": overdue_spartan,
                    }
                )

            spartan_results[(base_meta_i["month_short"], end_meta_j["month_short"])] = result

    st.session_state["spartan_results"] = spartan_results
    st.session_state["spartan_cache_key"] = spartan_signature

spartan_results = st.session_state["spartan_results"]

progress_bar.progress(1.0, text="Complete — results ready.")
_loading_placeholder.empty()  # Remove loading animation when done

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs(
    ["Overall view", "HRMS walk", "Span movement", "Spartan / HRMS / Payroll checks"]
)

# ============================================================
# TAB 1
# ============================================================
with tab1:
    st.subheader("Headcount trend")
    metric_choice = st.selectbox(
        "Choose metric",
        ["Total headcount", "Delivery", "Support Functions", "CXO"],
        index=0,
        key="trend_metric_choice",
    )

    st.plotly_chart(make_trend_chart(trend_df, metric_choice), use_container_width=True)

    st.subheader("Month-on-month overview")
    st.caption("One row per comparison period: Start vs End month with headcount and % changes.")
    _overview_cols = [
        "Start month", "End month", "Start HC", "End HC", "Abs change", "% change",
        "% change in Delivery", "% change in CXOs", "% change in Support Functions",
    ]
    st.dataframe(
        overview_df[_overview_cols],
        use_container_width=True,
        height=280,
        hide_index=True,
    )

    st.subheader("Detailed pair preview")
    month_options = [x["month_short"] for x in hr_files]
    p1, p2 = st.columns(2)
    preview_start_month = p1.selectbox(
        "Beginning month",
        month_options,
        index=0,
        key="preview_start_month_sel",
    )
    preview_end_month = p2.selectbox(
        "End month",
        month_options,
        index=len(month_options) - 1 if len(month_options) > 1 else 0,
        key="preview_end_month_sel",
    )

    preview_start_meta = next(x for x in hr_files if x["month_short"] == preview_start_month)
    preview_end_meta = next(x for x in hr_files if x["month_short"] == preview_end_month)

    if preview_start_meta["month_key"] >= preview_end_meta["month_key"]:
        st.error("End month must be later than beginning month.")
    else:
        preview_key = (preview_start_meta["month_short"], preview_end_meta["month_short"])
        preview_table = all_pair_tables[preview_key]["table"]
        try:
            start_df, _, _ = load_snapshot_from_path(preview_start_meta["path"], True, preview_start_meta["mtime"])
            end_df, _, _ = load_snapshot_from_path(preview_end_meta["path"], False, preview_end_meta["mtime"])
            start_ids = set(start_df["EMPLOYEE ID"].astype(str))
            end_ids = set(end_df["EMPLOYEE ID"].astype(str))
            retained_ids = start_ids & end_ids
            sep_only_ids = start_ids - end_ids
            new_hire_ids = end_ids - start_ids
            spartan_exit_ids = sep_only_ids & spartan_active_ids
            bau_exit_ids = sep_only_ids - spartan_exit_ids
            all_buckets = sorted(set(start_df["BUCKET"]).union(set(end_df["BUCKET"])))

            pair_drill_df = preview_table.drop(columns=["_rowtype"], errors="ignore").copy()
            cols = list(pair_drill_df.columns)
            head_col = cols[0]
            start_col = cols[1] if len(cols) > 1 else None
            end_col = cols[2] if len(cols) > 2 else None

            st.caption(
                f"**Pivot-style:** click a **headcount number** in **{start_col}** (start) or **{end_col}** (end). "
                "The employee list opens below. (Exits / new hires are on **HRMS walk**.)"
            )
            pair_event = st.dataframe(
                pair_drill_df,
                use_container_width=True,
                hide_index=True,
                selection_mode="single-cell",
                on_select="rerun",
                key="pair_pivot_table",
                height=320,
            )
            ri, cname = dataframe_cell_selection(pair_event, pair_drill_df)
            if ri is None or not cname:
                st.info("Click a **start** or **end** period count cell in the table above.")
            elif cname == head_col or cname in ("Abs change", "% change"):
                st.info("Click a **number** in the start or end period column, not the row label or change columns.")
            elif start_col and cname == start_col:
                chosen_label = str(pair_drill_df.iloc[ri][head_col])
                buckets = expand_bucket_selection(chosen_label, all_buckets)
                people_df = people_for_ids_and_buckets(start_df, start_ids, buckets)
                st.subheader(f"People — {chosen_label.strip()} · Start ({preview_start_meta['month_short']})")
                st.caption(f"{len(people_df):,} rows · {people_df['EMPLOYEE ID'].nunique() if not people_df.empty else 0:,} unique IDs")
                if people_df.empty:
                    st.warning("No employees.")
                else:
                    st.dataframe(
                        people_df.drop(columns=["BUCKET"], errors="ignore"),
                        use_container_width=True,
                        hide_index=True,
                        height=min(520, 120 + 28 * min(len(people_df), 25)),
                    )
            elif end_col and cname == end_col:
                chosen_label = str(pair_drill_df.iloc[ri][head_col])
                buckets = expand_bucket_selection(chosen_label, all_buckets)
                people_df = people_for_ids_and_buckets(end_df, end_ids, buckets)
                st.subheader(f"People — {chosen_label.strip()} · End ({preview_end_meta['month_short']})")
                st.caption(f"{len(people_df):,} rows · {people_df['EMPLOYEE ID'].nunique() if not people_df.empty else 0:,} unique IDs")
                if people_df.empty:
                    st.warning("No employees.")
                else:
                    st.dataframe(
                        people_df.drop(columns=["BUCKET"], errors="ignore"),
                        use_container_width=True,
                        hide_index=True,
                        height=min(520, 120 + 28 * min(len(people_df), 25)),
                    )
            else:
                st.info("Click a cell in the **start** or **end** headcount column.")
            with st.expander("Styled table (read-only)", expanded=False):
                st.plotly_chart(make_plotly_table(preview_table), use_container_width=True)
        except Exception as e:
            st.exception(e)

# ============================================================
# TAB 2
# ============================================================
with tab2:
    st.subheader("Detailed reconciliation")

    month_options = [x["month_short"] for x in hr_files]
    default_base = 0
    default_end = len(month_options) - 1 if len(month_options) > 1 else 0

    c1, c2 = st.columns(2)
    base_month = c1.selectbox("Base month", month_options, index=default_base, key="base_month_sel")
    end_month = c2.selectbox("Comparison month", month_options, index=default_end, key="end_month_sel")

    base_meta = next(x for x in hr_files if x["month_short"] == base_month)
    end_meta = next(x for x in hr_files if x["month_short"] == end_month)

    if base_meta["month_key"] >= end_meta["month_key"]:
        st.error("Comparison month must be later than base month.")
    else:
        try:
            rec_key = (base_meta["month_short"], end_meta["month_short"])
            rec_data = reconciliation_results[rec_key]
            rec_table = rec_data["rec_table"]

            count_cols = [c for c in rec_table.columns if c not in ("Headcount", "Abs. change", "% change", "_rowtype")]
            if len(count_cols) >= 5:
                base_col, spartan_col, bau_col, hire_col, end_col = count_cols[:5]
            else:
                base_col = spartan_col = bau_col = hire_col = end_col = None

            drill_df = rec_table.drop(columns=["_rowtype"], errors="ignore").copy()
            st.caption(
                "**Pivot-style:** click any **headcount number** in Baseline, Spartan exits, BAU attrition, New hires, or End-point. "
                "The employee list appears **directly under this table** as **People — …** (scroll down if needed)."
            )
            rec_event = st.dataframe(
                drill_df,
                use_container_width=True,
                hide_index=True,
                selection_mode="single-cell",
                on_select="rerun",
                key="rec_pivot_table",
                height=380,
            )
            option_map = {}
            if base_col:
                option_map[base_col] = (rec_data["base_df"], rec_data["base_ids"], "Baseline")
            if spartan_col:
                option_map[spartan_col] = (rec_data["base_df"], rec_data["spartan_exit_ids"], "Spartan exits")
            if bau_col:
                option_map[bau_col] = (rec_data["base_df"], rec_data["bau_attrition_ids"], "BAU attrition")
            if hire_col:
                option_map[hire_col] = (rec_data["end_df"], rec_data["new_hire_ids"], "New hires")
            if end_col:
                option_map[end_col] = (rec_data["end_df"], rec_data["end_ids"], "End-point")

            ri, cname = dataframe_cell_selection(rec_event, drill_df)
            head_col = "Headcount"
            if ri is None or not cname:
                st.info("Click a **count cell** in Baseline, Spartan exits, BAU attrition, New hires, or End-point.")
            elif cname == head_col or cname in ("Abs. change", "% change"):
                st.info("Click a **number** in one of the five headcount columns, not the row name or change columns.")
            elif cname not in option_map:
                st.info("Click a cell in Baseline, Spartan exits, BAU attrition, New hires, or End-point.")
            else:
                chosen_label = str(drill_df.iloc[ri][head_col])
                all_buckets = sorted(set(rec_data["base_df"]["BUCKET"]).union(set(rec_data["end_df"]["BUCKET"])))
                buckets = expand_bucket_selection(chosen_label, all_buckets)
                df_src, ids_src, sheet = option_map[cname]
                people_df = people_for_ids_and_buckets(df_src, ids_src, buckets)
                st.subheader(f"People — {chosen_label.strip()} · {sheet}")
                st.caption(f"{len(people_df):,} rows · {people_df['EMPLOYEE ID'].nunique() if not people_df.empty else 0:,} unique employee IDs")
                if people_df.empty:
                    st.warning("No employees match this cell.")
                else:
                    st.dataframe(
                        people_df.drop(columns=["BUCKET"], errors="ignore"),
                        use_container_width=True,
                        hide_index=True,
                        height=min(560, 140 + 28 * min(len(people_df), 30)),
                    )
            with st.expander("Styled reconciliation table (read-only)", expanded=False):
                st.plotly_chart(make_plotly_table(rec_table), use_container_width=True)

            dl_rec = df_to_excel_bytes(rec_table.drop(columns=["_rowtype"]), "Reconciliation")
            st.download_button(
                "Download reconciliation table",
                data=dl_rec,
                file_name=f"reconciliation_{base_meta['month_short']}_to_{end_meta['month_short']}.xlsx",
                key=f"rec_dl_{base_meta['month_short']}_{end_meta['month_short']}",
            )
        except Exception as e:
            st.exception(e)

# ============================================================
# TAB 3 — Span movement (IC / TL / M1+ for Conneqt only)
# ============================================================
with tab3:
    st.subheader("Span movement")
    st.caption(
        "Uses the **same Conneqt population as Overall view**, then excludes manpower: **PROCESS** contains the substring **manpower** (any case, even inside a word, e.g. processmanpower) if that column exists; else **MANPOWER CHECK = 1** (Span tab only). "
        "**IC**: (no direct reportees) AND (grade ∈ A1.x, A2.x, PT, AT, NAPS, NATS, INT, A-RT). "
        "**TL**: **mandatory** if grade A1.x/A2.x AND designation matches any phrase in **SPAN_TL_DESIGNATIONS** (**spaces ignored**, e.g. **team lead** matches **teamlead**); OR (≥1 reportee AND all reportees IC); OR (grade A3/A4 AND **no direct reportees** in Conneqt — IC-like). "
        "**M1+**: everyone else. "
        "If any grade appears outside the above list, choose how to treat it below (single-snapshot view waits for **Run**; month-over-month still loads)."
    )
    with st.expander("TL designation phrases (A1 / A2 mandatory TL — space-insensitive substring)", expanded=False):
        st.markdown(
            "If **grade** is A1.x or A2.x and **designation** matches **any** of these after lowercasing: "
            "all **spaces are ignored** when matching (e.g. **team lead** matches **teamlead**).\n\n"
            + "\n".join(f"- `{p}`" for p in sorted(SPAN_TL_DESIGNATIONS))
        )

    # ----- 1) Month-over-month span (shown first so it is always visible) -----
    st.markdown("### Month-over-month span comparison (IC ÷ TL by cluster)")
    st.caption(
        "For each snapshot month and **Cluster**: **Span = IC ÷ TL** (row counts). "
        "**MoM Δ** = change vs the **previous** selected snapshot. If **TL = 0**, span is N/A. "
        "Unknown-grade rules below apply to **all** selected months (computed automatically; cached after first run)."
    )
    trend_month_labels = [x["month_short"] for x in hr_files]
    trend_pick = st.multiselect(
        "Snapshots to compare (chronological order)",
        options=trend_month_labels,
        default=trend_month_labels,
        key="span_trend_months",
    )
    trend_metas = [x for x in hr_files if x["month_short"] in trend_pick]
    trend_metas.sort(key=lambda x: x["month_key"])

    if len(trend_metas) < 1:
        st.warning("Select at least one month.")
        trend_long = pd.DataFrame()
    else:
        union_unk = sorted(span_collect_unknown_grades_union(trend_metas))
        trend_choices: dict[str, str] = {}
        if union_unk:
            st.info(
                f"**{len(union_unk)}** unknown grade(s) in the selected snapshot set — set each once (used for every month in the comparison)."
            )
            for ug in union_unk:
                trend_choices[ug] = st.radio(
                    f"All months — grade **{ug}**",
                    options=["IC", "TL", "M1+"],
                    index=2,
                    key=f"span_trend_grade_{ug}",
                    horizontal=True,
                )
        mk = span_mapping_mtime_key(hr_folder)
        snap_key = tuple(
            (
                str(m["path"]),
                float(m["mtime"]),
                m["month_short"],
                int(m["year"]),
                int(m["month"]),
                int(m["day"]),
            )
            for m in trend_metas
        )
        ck = tuple(sorted(trend_choices.items()))
        with st.spinner("Computing span by cluster for each month…"):
            trend_long = span_trend_ic_tl_by_cluster_cached(snap_key, ck, hr_folder, mk)

        st.divider()
        st.subheader("Service line × month (employee row counts)")
        st.caption(
            "**Columns:** same snapshot labels as above. **Cells:** **row counts** across **all business units** (rows with substring **manpower** in **PROCESS** — any case, any position — are dropped; plus Span **MANPOWER CHECK** path when no PROCESS). "
            "Classification applies **cost-center overrides first**, then **blank-PROCESS** rules using **DIVISION**, **DESIGNATION**, and **JOB_FUNCTION**, then delivery-support **PROCESS** prefixes, then **pivot-style PROCESS overrides** "
            "(e.g. **CLM … | Back office** → CLM; **Collections | FOS/Telecollection** may split by designation), then base **CLM inbound/outbound** and **Collections** PROCESS rules. "
            "Optional checkbox below matches a **Jan/Dec pivot-style population** (Digitide LE, BPM - Practices & Ops, separations, blank MANPOWER). "
            "Use the **debug export** for `service_line_trace` (CC override / Blank PROCESS + Division override / Process override / Base Step 1–3)."
        )

        # Optional Business Unit filter for the service-line (row-count) table.
        # We read BU options from the first selected snapshot.
        bu_options: list[str] = []
        try:
            first_meta = trend_metas[0] if trend_metas else None
            if first_meta is not None:
                span0, _, _, _ = span_load_all_business_units_cached(str(first_meta["path"]), first_meta["mtime"])
                if not span0.empty and "BUSINESS UNIT" in span0.columns:
                    bu_col = span0["BUSINESS UNIT"].astype(str).str.strip()
                    bu_options = sorted([x for x in bu_col.unique().tolist() if x and x.lower() != "nan"])
        except Exception:
            bu_options = []

        selected_bu_options = st.multiselect(
            "Business unit filter (service-line tables)",
            options=bu_options,
            default=bu_options,
            key="span_sl_bu_filter",
            help="Filters the service-line × month headcount tables. IC/TL/M1+ span classification remains based on the full selected population.",
        )
        if not selected_bu_options and bu_options:
            # Treat empty selection as "no filter" for a better UX.
            selected_bu_options = bu_options
        bu_filter_norm_key = tuple(_span_normalize_bu_value(x) for x in selected_bu_options) if selected_bu_options else ()

        match_pivot_pop = st.checkbox(
            "Match Jan/Dec code-delivery pivot population (Digitide legal employer, BPM - Practices & Ops, active separations, blank MANPOWER)",
            value=False,
            key="span_sl_pivot_pop_filter",
            help="Narrows rows to align with a specific pivot workbook. Leave off for all-BU service-line totals.",
        )

        with st.spinner("Building service line × month table…"):
            sl_wide = span_service_line_wide_table_cached(
                snap_key, bu_filter_norm_key, use_code_delivery_pivot_filter=match_pivot_pop
            )
        st.dataframe(sl_wide, use_container_width=True, hide_index=True)
        with st.spinner("Computing service line span (IC ÷ TL) from same IC/TL rules…"):
            sl_span_wide, sl_role_wide = span_service_line_span_and_role_counts_cached(
                snap_key,
                ck,
                bu_filter_norm_key=bu_filter_norm_key,
                use_code_delivery_pivot_filter=match_pivot_pop,
            )
        st.subheader("Service line × month — span (IC ÷ TL)")
        st.caption(
            "Uses the **same** per-row **IC / TL / M1+** classification rules (including unknown-grade choices), "
            "but service-line grouping uses **all business units**. **Span** = IC ÷ TL; empty cell when **TL = 0**. "
            "**Sub-total** aggregates Core Delivery’s three lines. **Δ span** = last month − first month in the selection."
        )
        st.dataframe(sl_span_wide, use_container_width=True, hide_index=True)
        with st.expander("IC / TL / M1+ counts by service line × month", expanded=False):
            st.dataframe(sl_role_wide, use_container_width=True, hide_index=True)
        buf_sl = io.BytesIO()
        with pd.ExcelWriter(buf_sl, engine="openpyxl") as w:
            sl_wide.to_excel(w, sheet_name="Row counts", index=False)
            sl_span_wide.to_excel(w, sheet_name="Span IC per TL", index=False)
            sl_role_wide.to_excel(w, sheet_name="IC TL M1+ counts", index=False)
        buf_sl.seek(0)
        st.download_button(
            "Download service line × month (Excel)",
            data=buf_sl.getvalue(),
            file_name="span_service_line_by_month.xlsx",
            key="span_sl_mo_dl",
        )
        with st.expander("Debug export: classified service-line rows (Excel)", expanded=False):
            with st.spinner("Building row-level classification export…"):
                sl_debug_df = span_service_line_classified_rows_cached(
                    snap_key, bu_filter_norm_key, use_code_delivery_pivot_filter=match_pivot_pop
                )
            st.caption(f"{len(sl_debug_df):,} rows classified across selected months (business unit-filtered; manpower excluded).")
            buf_dbg = io.BytesIO()
            with pd.ExcelWriter(buf_dbg, engine="openpyxl") as w:
                sl_debug_df.to_excel(w, sheet_name="Classified rows", index=False)
            buf_dbg.seek(0)
            st.download_button(
                "Download row-by-row service-line mapping (Excel)",
                data=buf_dbg.getvalue(),
                file_name="span_service_line_classified_rows.xlsx",
                key="span_sl_debug_dl",
            )

    if not trend_long.empty:
        order_cols = ["snapshot_order", "snapshot_date", "month_short", "Cluster", "IC", "TL", "M1+", "Total rows", "Span (IC÷TL)"]
        disp_long = trend_long[[c for c in order_cols if c in trend_long.columns]]

        piv = trend_long.pivot_table(
            index="Cluster",
            columns="snapshot_order",
            values="Span (IC÷TL)",
            aggfunc="first",
        )
        uo = trend_long.sort_values("snapshot_order").drop_duplicates(subset=["snapshot_order"], keep="first")
        order_keys = [int(x) for x in uo["snapshot_order"].tolist()]
        label_map = {int(r["snapshot_order"]): str(r["month_short"]) for _, r in uo.iterrows()}
        for k in order_keys:
            if k not in piv.columns:
                piv[k] = np.nan
        piv = piv[[k for k in order_keys if k in piv.columns]]
        piv.columns = [label_map[k] for k in piv.columns]

        st.subheader("Span level — cluster × month")
        st.dataframe(piv, use_container_width=True)

        col_names = list(piv.columns)
        if len(col_names) >= 2:
            mom_cols = {}
            for i in range(1, len(col_names)):
                a, b = col_names[i - 1], col_names[i]
                mom_cols[f"MoM Δ ({a} → {b})"] = piv[b] - piv[a]
            mom_df = pd.DataFrame(mom_cols)
            st.subheader("Month-over-month change in span (Δ IC÷TL)")
            st.caption("Positive = span went up vs previous month; negative = went down.")
            st.dataframe(mom_df, use_container_width=True)
        else:
            mom_df = pd.DataFrame(index=piv.index)
            st.info("Select **at least two** snapshots above to see month-over-month **Δ** columns.")

        st.subheader("Line chart — span over time")
        clusters_for_plot = sorted(trend_long["Cluster"].dropna().unique().tolist())
        default_plot = [c for c in clusters_for_plot if c != "Unmapped"] or clusters_for_plot
        pick_cl = st.multiselect(
            "Clusters to plot",
            options=clusters_for_plot,
            default=default_plot[: min(12, len(default_plot))],
            key="span_trend_plot_clusters",
        )
        if pick_cl:
            tl = trend_long[trend_long["Cluster"].isin(pick_cl)].copy()
            tl = tl.sort_values(["snapshot_order", "Cluster"])
            fig_t = go.Figure()
            for cl in pick_cl:
                sub = tl[tl["Cluster"] == cl]
                if sub.empty:
                    continue
                fig_t.add_trace(
                    go.Scatter(
                        x=sub["month_short"],
                        y=sub["Span (IC÷TL)"],
                        name=str(cl),
                        mode="lines+markers",
                        connectgaps=False,
                    )
                )
            fig_t.update_layout(
                xaxis_title="Month (snapshot)",
                yaxis_title="Span (IC ÷ TL)",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=480,
            )
            st.plotly_chart(fig_t, use_container_width=True)

        with st.expander("Long-format table (all rows)", expanded=False):
            st.dataframe(disp_long, use_container_width=True, hide_index=True)

        buf_trend = io.BytesIO()
        with pd.ExcelWriter(buf_trend, engine="openpyxl") as w:
            disp_long.to_excel(w, sheet_name="Trend long", index=False)
            piv.to_excel(w, sheet_name="Span pivot")
            if mom_df is not None and not mom_df.empty:
                mom_df.to_excel(w, sheet_name="MoM delta")
        buf_trend.seek(0)
        st.download_button(
            "Download span comparison (Excel)",
            data=buf_trend.getvalue(),
            file_name="span_trend_ic_per_tl_by_cluster.xlsx",
            key="span_trend_dl",
        )
    elif len(trend_metas) >= 1:
        st.warning("No trend rows produced (empty Conneqt for all selected months, or cluster summary missing).")

    st.divider()
    st.markdown("### Single HRMS snapshot (detail)")
    span_month_options = [x["month_short"] for x in hr_files]
    span_default_idx = len(span_month_options) - 1 if span_month_options else 0
    span_selected = st.selectbox(
        "HRMS snapshot (from folder)",
        span_month_options,
        index=span_default_idx,
        key="span_snapshot_sel",
    )
    span_meta = next((x for x in hr_files if x["month_short"] == span_selected), None)

    if span_meta is not None:
        try:
            conneqt_df, reportee_count_series, _, unknown_grades = span_load_conneqt_cached(
                str(span_meta["path"]),
                span_meta["mtime"],
            )

            if conneqt_df.empty:
                st.warning(
                    "No rows in the **Conneqt** bucket for this snapshot (same definition as **Overall view**). "
                    "If you expect Conneqt headcount on Tab 1, refresh data; otherwise check BUSINESS UNIT / BUSINESS."
                )
            else:
                st.success(f"Found **{len(conneqt_df)}** rows (Conneqt Business Solution). Unique employee IDs: **{conneqt_df['EMPLOYEE ID'].nunique()}**.")

                _cdf = conneqt_df
                _rc = reportee_count_series
                unknown_grades = sorted(unknown_grades) if unknown_grades else []
                choices = {}
                show_single_month_classified = True
                if len(unknown_grades) > 0:
                    st.subheader("Unknown grades — your input needed (single snapshot)")
                    st.info(
                        "These grades are not in the known lists (and not A2/A2.x). "
                        "Choose how to treat each grade, then click **Run** to refresh the tables below."
                    )
                    for ug in unknown_grades:
                        val = st.radio(
                            f"Grade **{ug}**",
                            options=["IC", "TL", "M1+"],
                            index=2,
                            key=f"span_grade_{ug}",
                            horizontal=True,
                        )
                        choices[ug] = val
                    run_span = st.button("Run classification with above choices", key="span_run_btn")
                    show_single_month_classified = bool(run_span)
                    if not show_single_month_classified:
                        st.caption("Month-over-month comparison above is unaffected; it uses the **All months** grade rules at the top of this tab.")

                if show_single_month_classified:
                    role_s = span_roles_cached(
                        str(span_meta["path"]),
                        span_meta["mtime"],
                        tuple(sorted(choices.items())),
                    )
                    out_df = _cdf.copy()
                    out_df["IC / TL / M1+"] = role_s.values
                    out_clustered, cluster_summary, cluster_status = span_attach_cluster_and_summarize(out_df, hr_folder)
                    vc = role_s.value_counts()
                    st.caption(
                        f"IC: **{vc.get('IC', 0):,}** · TL: **{vc.get('TL', 0):,}** · M1+: **{vc.get('M1+', 0):,}** (row counts; duplicate IDs may appear on multiple rows)"
                    )
                    if cluster_status:
                        st.info(cluster_status)
                    if cluster_summary is not None and not cluster_summary.empty:
                        st.subheader("Span counts by cluster (vertical)")
                        st.caption(
                            "Rows grouped by **Cluster** from **Conneqt_CostCode_Mapping** (Cost Code = **COST CENTER**)."
                        )
                        st.dataframe(cluster_summary, use_container_width=True, hide_index=True)
                        dl_cl = df_to_excel_bytes(cluster_summary, "Span by cluster")
                        st.download_button(
                            "Download cluster summary (Excel)",
                            data=dl_cl,
                            file_name=f"span_by_cluster_{span_selected.replace(' ', '_')}.xlsx",
                            key="span_cluster_dl",
                        )
                    st.dataframe(out_clustered.head(100), use_container_width=True, hide_index=True)
                    st.caption("Showing first 100 rows (includes **Cluster** when mapping is available). Download for full file.")
                    dl_span = df_to_excel_bytes(out_clustered, "Span movement")
                    st.download_button(
                        "Download Excel (Conneqt + IC/TL/M1+ + Cluster)",
                        data=dl_span,
                        file_name=f"span_movement_ic_tl_m1_{span_selected.replace(' ', '_')}.xlsx",
                        key="span_dl",
                    )
        except Exception as e:
            st.exception(e)

    st.divider()
    st.subheader("Edge cases — please confirm")
    st.markdown("""
    - **Direct reports:** Only rows **in Conneqt** with **MANAGER1 ECODE** equal to your ID count as direct reportees. Managers outside Conneqt are ignored for the graph.
    - **Duplicate EMPLOYEE ID:** Same designation for every row of that employee ID.
    - **Cluster mapping:** **Conneqt_CostCode_Mapping.xlsx** in the HR folder; **COST CENTER** matched to **Cost Code** (case-insensitive). Duplicate codes in the mapping → first row wins. Unmatched → **Unmapped**.

    If any of these should behave differently, tell me and I’ll update the logic.
    """)

# ============================================================
# TAB 4
# ============================================================
with tab4:
    st.subheader("Spartan / HRMS / Payroll checks")

    month_options = [x["month_short"] for x in hr_files]
    default_base_sp = 0
    default_end_sp = len(month_options) - 1 if len(month_options) > 1 else 0

    sc1, sc2 = st.columns(2)
    spartan_base_month = sc1.selectbox(
        "Choose base month for Spartan checks",
        month_options,
        index=default_base_sp,
        key="spartan_base_month_sel",
    )
    spartan_end_month = sc2.selectbox(
        "Choose comparison month for Spartan checks",
        month_options,
        index=default_end_sp,
        key="spartan_end_month_sel",
    )

    spartan_base_meta = next(x for x in hr_files if x["month_short"] == spartan_base_month)
    spartan_end_meta = next(x for x in hr_files if x["month_short"] == spartan_end_month)

    if spartan_base_meta["month_key"] >= spartan_end_meta["month_key"]:
        st.error("Comparison month must be later than base month.")
    else:
        sp_key = (spartan_base_meta["month_short"], spartan_end_meta["month_short"])
        sp_data = spartan_results[sp_key]

        spartan_exit_ids = sp_data["spartan_exit_ids"]
        bau_attrition_ids = sp_data["bau_attrition_ids"]
        new_hire_ids = sp_data["new_hire_ids"]

        info1, info2, info3 = st.columns(3)
        info1.metric("Spartan exits", f"{len(spartan_exit_ids):,}")
        info2.metric("BAU attrition", f"{len(bau_attrition_ids):,}")
        info3.metric("New hires", f"{len(new_hire_ids):,}")

        st.divider()
        st.subheader("D2 Spartan cross-check")

        if spartan_df is None:
            st.info("Upload a D2 Spartan file in the sidebar to run the cross-check.")
        else:
            sp1 = sp_data["sp1"]
            offenders_hrms = sp_data["offenders_hrms"]
            sp2 = sp_data["sp2"]
            overdue_spartan = sp_data["overdue_spartan"]

            st.success(
                f"Spartan read from sheet: {spartan_report['sheet_used']} "
                f"(header row: {spartan_report['header_row']})"
            )

            cc1, cc2 = st.columns(2)
            cc1.metric("Filtered Spartan rows (D3 = 1)", f"{len(sp1):,}")
            cc1.metric("❗ Still in comparison HRMS", f"{len(offenders_hrms):,}")
            cc2.metric("Pending rows (Closed - LWD yet to be completed)", f"{len(sp2):,}")
            cc2.metric("❗ LWD before comparison month-end", f"{len(overdue_spartan):,}")

            with st.expander("❗ People in filtered Spartan list but still present in comparison HRMS", expanded=False):
                show_cols = [c for c in ["EMPLOYEE ID", "NAME", "SPARTAN CATEGORY", "D3", "LWD", "Exists in current HRMS?"] if c in offenders_hrms.columns]
                st.dataframe(offenders_hrms[show_cols], use_container_width=True, height=300)

        st.divider()
        st.subheader("Payroll vs Spartan (LWD) cross-check")

        if payroll_file is None:
            st.session_state["payroll_session_key"] = None
            st.session_state["_payroll_df"] = None
            st.session_state["_payroll_ids"] = None
            st.info("Upload Payroll file in the sidebar to run this check.")
        elif spartan_df is None:
            st.info("Upload a D2 Spartan file in the sidebar to run this check.")
        else:
            try:
                payroll_session_key = (payroll_file.name, payroll_file.size)
                if (
                    st.session_state.get("payroll_session_key") == payroll_session_key
                    and st.session_state.get("_payroll_ids") is not None
                ):
                    pay = st.session_state["_payroll_df"]
                    pay_sheet = st.session_state["_payroll_sheet"]
                    pay_header = st.session_state["_payroll_header"]
                    payroll_ids = st.session_state["_payroll_ids"]
                else:
                    pay_raw, pay_sheet, pay_header = read_payroll_auto(payroll_file)
                    pay = normalize_payroll_cols(pay_raw.dropna(how="all"))

                    if "EMPLOYEE ID" not in pay.columns:
                        st.error(
                            f"Payroll file: could not find an Employee ID column. "
                            f"Found: {list(pay.columns)}. Sheet: {pay_sheet}, header row: {pay_header + 1}"
                        )
                    else:
                        pay["EMPLOYEE ID"] = pay["EMPLOYEE ID"].map(to_id_string)
                        pay = pay[pay["EMPLOYEE ID"].notna()].drop_duplicates(subset=["EMPLOYEE ID"]).copy()
                        payroll_ids = set(pay["EMPLOYEE ID"].astype(str))
                        st.session_state["payroll_session_key"] = payroll_session_key
                        st.session_state["_payroll_df"] = pay
                        st.session_state["_payroll_sheet"] = pay_sheet
                        st.session_state["_payroll_header"] = pay_header
                        st.session_state["_payroll_ids"] = payroll_ids

                if st.session_state.get("_payroll_ids") is not None:
                    tmp = spartan_df.copy()
                    tmp["EMPLOYEE ID"] = tmp["EMPLOYEE ID"].astype(str)
                    tmp["In payroll?"] = tmp["EMPLOYEE ID"].isin(payroll_ids)
                    tmp["LWD <= payroll cycle end?"] = tmp["LWD"].notna() & (tmp["LWD"].dt.date <= payroll_cycle_end)

                    flagged = tmp[tmp["In payroll?"] & tmp["LWD <= payroll cycle end?"]].copy()

                    st.success(f"Payroll read from sheet: {pay_sheet} (header row: {pay_header + 1})")
                    st.write(f"Payroll cycle: **{payroll_cycle_start}** to **{payroll_cycle_end}**")

                    pc1, pc2 = st.columns(2)
                    pc1.metric("Employees in payroll file (unique IDs)", f"{len(payroll_ids):,}")
                    pc2.metric("❗ Flagged (in payroll AND LWD <= payroll cycle end)", f"{len(flagged):,}")

                    with st.expander("❗ Flagged employees (Payroll present + Spartan LWD <= payroll cycle end)", expanded=True):
                        show_cols = [c for c in ["EMPLOYEE ID", "NAME", "SPARTAN CATEGORY", "D3", "LWD", "In payroll?", "LWD <= payroll cycle end?"] if c in flagged.columns]
                        st.dataframe(flagged[show_cols], use_container_width=True, height=320)
            except Exception as e:
                st.exception(e)