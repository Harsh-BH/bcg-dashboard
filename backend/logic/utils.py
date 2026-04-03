import io
import calendar
import re
from datetime import date

import numpy as np
import pandas as pd

from logic.constants import HR_MANDATORY_STD


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


_EMP_ID_ALIASES = frozenset({
    "employee id", "employeeid", "emp id", "empid",
    "employee code", "employee no", "employee number", "employee_id",
})


def read_excel_best_sheet(source) -> pd.DataFrame:
    """Read the sheet most likely to be the HRMS master data.

    Priority (descending):
    1. Sheet name contains "hrms" (case-insensitive).
    2. Sheet has an employee-ID-like column header.
    3. Sheet with the most columns (richer schema = main data).
    4. Sheet with the most non-empty rows.
    """
    xls = pd.ExcelFile(source)
    best_df = None
    best_score: tuple = (-1, -1, -1, -1)
    for sheet_name in xls.sheet_names:
        d = xls.parse(sheet_name)
        if d is None:
            continue
        d2 = d.dropna(how="all")
        cols_lower = {str(c).strip().lower() for c in d2.columns}
        name_has_hrms = int("hrms" in sheet_name.lower())
        has_emp_id = int(bool(cols_lower & _EMP_ID_ALIASES))
        score = (name_has_hrms, has_emp_id, len(d2.columns), len(d2))
        if score > best_score:
            best_score = score
            best_df = d2.copy()
    if best_df is None:
        best_df = xls.parse(xls.sheet_names[0]).dropna(how="all")
    return best_df


def read_spartan_auto(file_bytes: bytes) -> tuple[pd.DataFrame, str, int]:
    buf = io.BytesIO(file_bytes)
    xls = pd.ExcelFile(buf)
    for sheet in xls.sheet_names:
        for header in range(9):
            try:
                d = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet, header=header)
            except Exception:
                continue
            d = d.dropna(how="all")
            cols = [keyify(c) for c in d.columns.astype(str)]
            if ("employee id" in cols) and ("d3" in cols):
                return d, sheet, header
            if ("employee id" in cols) and ("spartan category" in cols):
                return d, sheet, header
    d = pd.read_excel(io.BytesIO(file_bytes), sheet_name=0, header=1).dropna(how="all")
    return d, xls.sheet_names[0], 1


def read_payroll_auto(file_bytes: bytes) -> tuple[pd.DataFrame, str, int]:
    buf = io.BytesIO(file_bytes)
    xls = pd.ExcelFile(buf)
    for sheet in xls.sheet_names:
        for header in range(9):
            try:
                d = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet, header=header)
            except Exception:
                continue
            d = d.dropna(how="all")
            cols = [keyify(c) for c in d.columns.astype(str)]
            if ("employee id" in cols) or ("emp id" in cols) or ("employeeid" in cols):
                return d, sheet, header
    d = pd.read_excel(io.BytesIO(file_bytes), sheet_name=0, header=0).dropna(how="all")
    return d, xls.sheet_names[0], 0


def month_end(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def format_snapshot_date(year: int, month: int, day: int) -> str:
    """Format YYYY_MM_DD as human-readable e.g. '14th March, 2026'."""
    d = date(year, month, day)
    if 10 <= day % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix} {d.strftime('%B')}, {year}"


def normalize_otc_pa_to_cr(series: pd.Series) -> pd.Series:
    """Convert OTC PA to numeric annual salary in ₹ Cr. Non-numeric/blank/NA → 0. Values assumed in rupees."""
    if series is None:
        return pd.Series(dtype="float64")
    s = series.astype("string").fillna("").str.strip()
    low = s.str.lower()
    s = s.mask(low.isin({"", "not existent", "not existing", "na", "n/a", "nan", "none", "null", "nat"}), "")
    s = s.str.replace(",", "", regex=False).str.replace("₹", "", regex=False)
    s = s.str.replace(r"[^0-9.\-]", "", regex=True)
    s = s.replace({"": pd.NA, "-": pd.NA, ".": pd.NA, "-.": pd.NA})
    vals = pd.to_numeric(s, errors="coerce").fillna(0.0)
    vals = vals.where(np.isfinite(vals), 0.0)
    return vals / 1e7


def snapshot_has_salary(df: pd.DataFrame) -> bool:
    """True when this snapshot has an OTC PA-derived salary column available."""
    return (
        df is not None
        and not df.empty
        and "OTC PA (CR)" in df.columns
        and df["OTC PA (CR)"].notna().any()
    )


def salary_series_from_df(df: pd.DataFrame) -> "pd.Series | None":
    """Bucket → salary in ₹ Cr for the whole snapshot, or None if OTC PA missing."""
    if not snapshot_has_salary(df):
        return None
    return df.groupby("BUCKET")["OTC PA (CR)"].sum()


def salary_series_from_ids(df: pd.DataFrame, ids: set) -> "pd.Series | None":
    """Bucket → salary in ₹ Cr for the selected employee IDs, or None if OTC PA missing."""
    if not snapshot_has_salary(df):
        return None
    if not ids:
        return pd.Series(dtype="float64")
    keys = df["EMPLOYEE ID"].map(to_id_string)
    return df[keys.isin(ids)].groupby("BUCKET")["OTC PA (CR)"].sum()


def span_normalize_hrms_ids(df: pd.DataFrame) -> pd.DataFrame:
    """Align EMPLOYEE ID and MANAGER1 ECODE after Excel reads."""
    if "EMPLOYEE ID" in df.columns:
        df["EMPLOYEE ID"] = df["EMPLOYEE ID"].map(to_id_string).fillna("").astype(str).str.strip()
    if "MANAGER1 ECODE" in df.columns:
        df["MANAGER1 ECODE"] = df["MANAGER1 ECODE"].map(to_id_string).fillna("").astype(str).str.strip()
    return df
