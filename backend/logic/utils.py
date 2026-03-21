import io
import calendar
import re
from datetime import date

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


def read_excel_best_sheet(source) -> pd.DataFrame:
    """Read the sheet with the most non-empty rows."""
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


def span_normalize_hrms_ids(df: pd.DataFrame) -> pd.DataFrame:
    """Align EMPLOYEE ID and MANAGER1 ECODE after Excel reads."""
    if "EMPLOYEE ID" in df.columns:
        df["EMPLOYEE ID"] = df["EMPLOYEE ID"].map(to_id_string).fillna("").astype(str).str.strip()
    if "MANAGER1 ECODE" in df.columns:
        df["MANAGER1 ECODE"] = df["MANAGER1 ECODE"].map(to_id_string).fillna("").astype(str).str.strip()
    return df
